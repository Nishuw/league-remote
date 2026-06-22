"""Monitor em background que acompanha o estado do cliente do LoL.

Mantem um snapshot thread-safe do estado atual (fase, fila, ready-check,
champ select) e executa acoes automaticas opcionais (auto-accept de
fallback, auto-pick e auto-ban).
"""

import json
import ssl
import threading
import time
from typing import Any, Dict, Optional

try:  # dependencia opcional: sem ela, o monitor cai no polling puro.
    import websocket  # type: ignore
except ImportError:  # pragma: no cover
    websocket = None

from .config import AUTO_ACCEPT_FALLBACK_SECONDS
from .lcu_client import LCUClient

# Eventos da LCU (estilo WAMP). Subscrevemos so o que importa para o controle
# remoto: fase do jogo, sessao do champ select e o ready-check.
WS_SUBSCRIBE = (
    "OnJsonApiEvent_lol-gameflow_v1_gameflow-phase",
    "OnJsonApiEvent_lol-champ-select_v1_session",
    "OnJsonApiEvent_lol-matchmaking_v1_ready-check",
)
# Fases em que NAO ha champ select; usadas para limpar o estado.
_NON_CHAMP_PHASES = {
    "None", "Lobby", "Matchmaking", "ReadyCheck",
    "InProgress", "Reconnect", "WaitingForStats", "PreEndOfGame", "EndOfGame",
}

# Duracao aproximada do ready-check em segundos (o timer conta pra cima).
READY_CHECK_DURATION = 12

# Fases em que vale pesquisar com mais frequencia.
FAST_POLL_PHASES = ("ReadyCheck", "Matchmaking", "ChampSelect")
FAST_POLL_INTERVAL = 0.7
SLOW_POLL_INTERVAL = 1.5

# Filas do ARAM: Desordem (Mayhem). Esses modos usam augments no lugar de
# runas, entao o painel de runas nao se aplica.
MAYHEM_QUEUE_IDS = {2400, 2401, 2402, 2403, 2404, 2405}


def _runes_enabled_for_queue(queue: Optional[Dict[str, Any]]) -> bool:
    """ARAM: Desordem nao tem runas (usa aprimoramentos)."""
    if not queue:
        return True
    if queue.get("id") in MAYHEM_QUEUE_IDS:
        return False
    name = (queue.get("name") or queue.get("description") or "").lower()
    return not ("mayhem" in name or "desordem" in name)


class Monitor:
    """Acompanha o cliente do LoL e mantem o estado compartilhado."""

    def __init__(self, client: LCUClient) -> None:
        self.client = client
        self.lock = threading.Lock()
        self.state: Dict[str, Any] = {
            "connected": False,
            "phase": None,
            "time_in_queue": 0,
            "estimated_queue_time": 0,
            "ready_check": False,
            "player_response": "None",
            "ready_timer": 0,
            "champ_select": None,
            "last_action": "",
            "queue_id": None,
            "mode_name": None,
            "runes_enabled": True,
        }
        self.config: Dict[str, Any] = {
            "auto_pick_enabled": False,
            # Lista de campeoes em ordem de prioridade (tenta o 1o disponivel).
            "auto_pick_champs": [],
            "auto_ban_enabled": False,
            "auto_ban_champs": [],
            # Nao banir um campeao que um aliado esta escolhendo (pick intent).
            "ban_protect_allies": True,
        }
        self._auto_accepted_this_check = False
        self._auto_acted_actions: set = set()

    # ------------------------------------------------------------------
    # Estado compartilhado
    # ------------------------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        with self.lock:
            return dict(self.state)

    def set_last_action(self, msg: str) -> None:
        with self.lock:
            self.state["last_action"] = msg

    # ------------------------------------------------------------------
    # Champ select
    # ------------------------------------------------------------------

    def _build_champ_select(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Transforma a sessao crua da LCU num resumo amigavel."""
        client = self.client
        local_cell = session.get("localPlayerCellId")

        # Vez atual: acao em progresso
        current_actor = None
        current_type = None
        for group in session.get("actions", []) or []:
            for act in group:
                if act.get("isInProgress"):
                    current_actor = act.get("actorCellId")
                    current_type = act.get("type")
                    break
            if current_actor is not None:
                break

        # Quem esta escolhendo agora (acao pick/ban em progresso por cell)
        picking_cells = set()
        my_action_id = None
        my_action_type = None
        for group in session.get("actions", []) or []:
            for act in group:
                if act.get("isInProgress"):
                    picking_cells.add(act.get("actorCellId"))
                    if act.get("actorCellId") == local_cell:
                        my_action_id = act.get("id")
                        my_action_type = act.get("type")

        def build_team(team_key: str, resolve_names: bool = False):
            rows = []
            for p in session.get(team_key, []) or []:
                cell = p.get("cellId")
                champ_id = p.get("championId") or 0
                # Para aliados, mostra hover (pickIntent) se ainda nao travou
                if not champ_id:
                    champ_id = p.get("championPickIntent") or 0
                name = None
                if resolve_names:
                    sid = p.get("summonerId")
                    summ = client.get_summoner_by_id(sid) if sid else None
                    if summ:
                        name = summ.get("gameName") or summ.get("displayName")
                rows.append({
                    "position": (p.get("assignedPosition") or "").lower(),
                    "champion_id": champ_id or None,
                    "champion": client.champ_name(champ_id),
                    "name": name,
                    "is_local": cell == local_cell,
                    "picking": cell in picking_cells,
                })
            return rows

        # Bans a partir das acoes (mais confiavel que session["bans"])
        my_cells = {p.get("cellId") for p in session.get("myTeam", []) or []}
        my_bans, their_bans = [], []
        for group in session.get("actions", []) or []:
            for act in group:
                if act.get("type") == "ban" and act.get("completed"):
                    cid = act.get("championId") or 0
                    if cid <= 0:
                        continue
                    entry = {"champion_id": cid, "champion": client.champ_name(cid)}
                    if act.get("actorCellId") in my_cells:
                        my_bans.append(entry)
                    else:
                        their_bans.append(entry)

        timer = session.get("timer", {}) or {}
        time_left = int((timer.get("adjustedTimeLeftInPhase", 0) or 0) / 1000)

        result = {
            "phase": timer.get("phase"),
            "time_left": max(0, time_left),
            "current_actor_cell": current_actor,
            "current_action_type": current_type,
            "local_cell": local_cell,
            "is_my_turn": my_action_id is not None,
            "my_action_id": my_action_id,
            "my_action_type": my_action_type,
            "my_team": build_team("myTeam", resolve_names=True),
            "their_team": build_team("theirTeam"),
            "my_bans": my_bans,
            "their_bans": their_bans,
            # "draft" (pick/ban por vez) ou "bench" (ARAM: sorteio + banco + troca)
            "mode": "bench" if session.get("benchEnabled") else "draft",
        }

        if result["mode"] == "bench":
            result.update(self._build_bench(session, local_cell))
        return result

    def _build_bench(self, session: Dict[str, Any], local_cell: Any) -> Dict[str, Any]:
        """Dados do ARAM: campeao atual, banco de reserva e trocas."""
        client = self.client

        # Mapas por celula para resolver campeao/invocador nas trocas
        cell_champ: Dict[Any, int] = {}
        cell_sid: Dict[Any, int] = {}
        my_champion_id = 0
        my_spell1 = my_spell2 = 0
        for p in session.get("myTeam", []) or []:
            cell = p.get("cellId")
            cell_champ[cell] = p.get("championId") or 0
            cell_sid[cell] = p.get("summonerId")
            if cell == local_cell:
                my_champion_id = p.get("championId") or 0
                my_spell1 = p.get("spell1Id") or 0
                my_spell2 = p.get("spell2Id") or 0

        bench = [
            {"champion_id": c.get("championId"), "champion": client.champ_name(c.get("championId"))}
            for c in session.get("benchChampions", []) or []
            if c.get("championId")
        ]

        # Escolha INICIAL (subset pessoal): 2-3 campeoes oferecidos na chegada,
        # disponiveis ANTES da roleta (benchChampions) popular. Sem isso, o app
        # so mostrava a roleta e perdia a escolha inicial do ARAM/Desordem.
        subset = [
            {"champion_id": cid, "champion": client.champ_name(cid)}
            for cid in client.get_subset_champion_list()
        ]

        trades = []
        for t in session.get("trades", []) or []:
            cell = t.get("cellId")
            state = t.get("state")
            if cell is None or cell == local_cell or state in (None, "INVALID"):
                continue
            sid = cell_sid.get(cell)
            name = None
            if sid:
                summ = client.get_summoner_by_id(sid)
                if summ:
                    name = summ.get("gameName") or summ.get("displayName")
            champ_id = cell_champ.get(cell) or 0
            trades.append({
                "id": t.get("id"),
                "state": state,  # AVAILABLE, SENT, RECEIVED, BUSY...
                "name": name,
                "champion_id": champ_id or None,
                "champion": client.champ_name(champ_id),
            })

        def spell_info(sid: int) -> Dict[str, Any]:
            meta = client.spell_map.get(sid) or {}
            return {"id": sid or None, "icon": meta.get("icon", ""), "name": meta.get("name", "")}

        return {
            "my_champion_id": my_champion_id or None,
            "my_champion": client.champ_name(my_champion_id),
            "my_spells": [spell_info(my_spell1), spell_info(my_spell2)],
            "subset": subset,
            "bench": bench,
            "trades": trades,
        }

    @staticmethod
    def _as_id_list(value: Any) -> list:
        """Normaliza a config para uma lista de ids inteiros e validos."""
        out = []
        for v in value or []:
            try:
                iv = int(v)
            except (TypeError, ValueError):
                continue
            if iv > 0 and iv not in out:
                out.append(iv)
        return out

    def _choose_pick(self, prefs: list) -> Optional[int]:
        """Primeiro campeao da lista que esteja disponivel para pick."""
        prefs = self._as_id_list(prefs)
        if not prefs:
            return None
        pickable = set(self.client.get_pickable_champion_ids() or [])
        for cid in prefs:
            # Se a LCU nao devolveu a lista, tentamos mesmo assim (cliente decide).
            if not pickable or cid in pickable:
                return cid
        return None

    def _choose_ban(self, prefs: list, cs: Dict[str, Any]) -> Optional[int]:
        """Primeiro campeao da lista banivel, respeitando o pick dos aliados."""
        prefs = self._as_id_list(prefs)
        if not prefs:
            return None
        bannable = set(self.client.get_bannable_champion_ids() or [])
        protected = set()
        if self.config.get("ban_protect_allies"):
            for p in cs.get("my_team", []) or []:
                if not p.get("is_local") and p.get("champion_id"):
                    protected.add(int(p["champion_id"]))
        for cid in prefs:
            if cid in protected:
                continue
            if not bannable or cid in bannable:
                return cid
        return None

    def _maybe_auto_act(self, cs: Dict[str, Any]) -> None:
        """Auto-pick / auto-ban quando for a vez do jogador.

        Protecoes: so age na acao em progresso do jogador, valida contra os
        campeoes disponiveis (pickable/bannable), tenta a lista de prioridade
        em ordem e nao bane o pick de um aliado. Em caso de falha, nao marca a
        acao como concluida, entao tenta de novo no proximo ciclo e mantem a
        selecao manual disponivel.
        """
        action_id = cs.get("my_action_id")
        atype = cs.get("my_action_type")
        if not action_id or action_id in self._auto_acted_actions:
            return
        cfg = self.config

        if atype == "pick" and cfg.get("auto_pick_enabled"):
            champ_id = self._choose_pick(cfg.get("auto_pick_champs"))
            if champ_id is None:
                if cfg.get("auto_pick_champs"):
                    self.set_last_action("Auto-pick: nenhum campeao disponivel, escolha manual")
                return
            if self.client.patch_action(action_id, champ_id, True):
                self._auto_acted_actions.add(action_id)
                self.set_last_action(f"Auto-pick: {self.client.champ_name(champ_id) or champ_id}")

        elif atype == "ban" and cfg.get("auto_ban_enabled"):
            champ_id = self._choose_ban(cfg.get("auto_ban_champs"), cs)
            if champ_id is None:
                if cfg.get("auto_ban_champs"):
                    self.set_last_action("Auto-ban: nenhum campeao disponivel/permitido")
                return
            if self.client.patch_action(action_id, champ_id, True):
                self._auto_acted_actions.add(action_id)
                self.set_last_action(f"Auto-ban: {self.client.champ_name(champ_id) or champ_id}")

    # ------------------------------------------------------------------
    # Loop principal
    # ------------------------------------------------------------------

    def run(self) -> None:
        while True:
            phase = None
            try:
                phase = self._tick()
            except Exception as exc:  # noqa: BLE001 - o loop nunca pode morrer
                # Um erro num ciclo (dado inesperado, rede, etc.) nao pode
                # derrubar a thread: isso congelaria o estado (ex.: champ
                # select nunca atualizaria). Loga e segue para o proximo ciclo.
                print(f"[monitor] erro no ciclo: {exc!r}")
                time.sleep(1)
                continue
            time.sleep(FAST_POLL_INTERVAL if phase in FAST_POLL_PHASES else SLOW_POLL_INTERVAL)

    def _tick(self) -> Optional[str]:
        """Executa um ciclo do monitor e retorna a fase atual."""
        if not self.client.base_url:
            connected = self.client.connect()
            with self.lock:
                self.state["connected"] = connected
            if not connected:
                time.sleep(3)
                return None

        phase = self.client.get_gameflow_phase()
        with self.lock:
            self.state["connected"] = self.client.base_url is not None
            self.state["phase"] = phase

        self._update_queue()

        if phase == "Matchmaking":
            self._handle_matchmaking()
        elif phase == "ReadyCheck":
            self._handle_ready_check()
        elif phase == "ChampSelect":
            self._handle_champ_select()
        else:
            self._handle_idle()
        return phase

    def _handle_matchmaking(self) -> None:
        search = self.client.get_search_state() or {}
        with self.lock:
            self.state["time_in_queue"] = int(search.get("timeInQueue", 0) or 0)
            self.state["estimated_queue_time"] = int(search.get("estimatedQueueTime", 0) or 0)
            self.state["ready_check"] = False
            self.state["player_response"] = "None"
        self._auto_accepted_this_check = False

    def _handle_ready_check(self) -> None:
        rc = self.client.get_ready_check() or {}
        state = rc.get("state")
        timer = int(rc.get("timer", 0) or 0)
        player_response = rc.get("playerResponse", "None")
        in_progress = state == "InProgress"

        with self.lock:
            self.state["ready_check"] = in_progress
            self.state["ready_timer"] = timer
            self.state["player_response"] = player_response
            self.state["time_in_queue"] = 0

        # Auto-accept de fallback: aceita quando faltar pouco para o timer acabar.
        if (
            in_progress
            and player_response == "None"
            and AUTO_ACCEPT_FALLBACK_SECONDS is not None
            and timer >= AUTO_ACCEPT_FALLBACK_SECONDS
            and not self._auto_accepted_this_check
            and timer >= (READY_CHECK_DURATION - AUTO_ACCEPT_FALLBACK_SECONDS)
        ):
            if self.client.accept_match():
                self._auto_accepted_this_check = True
                self.set_last_action("Auto-accept (fallback) acionado")

    def _handle_champ_select(self) -> None:
        session = self.client.get_champ_select_session()
        self._apply_champ_select(session)

    def _apply_champ_select(self, session: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Processa uma sessao de champ select (de polling OU do WebSocket).

        Centralizado para que a thread de eventos (push em tempo real) e o
        polling de fallback produzam exatamente o mesmo estado. E aqui que a
        roleta do ARAM aparece assim que a LCU popula `benchChampions`.
        """
        self.client.load_champion_data()
        self.client.load_summoner_spells()
        cs = self._build_champ_select(session) if session else None
        with self.lock:
            self.state["champ_select"] = cs
            self.state["ready_check"] = False
            self.state["time_in_queue"] = 0
            self.state["player_response"] = "None"
        self._auto_accepted_this_check = False
        if cs and cs.get("is_my_turn"):
            self._maybe_auto_act(cs)
        return cs

    def _update_queue(self) -> None:
        """Le a fila atual para rotular o modo e saber se ha runas."""
        sess = self.client.get_gameflow_session() or {}
        queue = ((sess.get("gameData") or {}).get("queue")) or {}
        with self.lock:
            self.state["queue_id"] = queue.get("id")
            self.state["mode_name"] = queue.get("name") or queue.get("description")
            self.state["runes_enabled"] = _runes_enabled_for_queue(queue)

    def _handle_idle(self) -> None:
        with self.lock:
            self.state["ready_check"] = False
            self.state["time_in_queue"] = 0
            self.state["player_response"] = "None"
            self.state["champ_select"] = None
        self._auto_accepted_this_check = False
        self._auto_acted_actions.clear()

    # ------------------------------------------------------------------
    # WebSocket de eventos (push em tempo real, como o Blitz)
    # ------------------------------------------------------------------

    def run_ws(self) -> None:
        """Loop da thread de eventos: conecta, escuta e reconecta para sempre.

        O polling (`run`) continua rodando como rede de seguranca; esta thread
        so deixa o estado *instantaneo*. Sem a dependencia `websocket-client`,
        retorna e o app segue 100% por polling.
        """
        if websocket is None:
            print("[ws] 'websocket-client' nao instalado; usando so polling.")
            return
        while True:
            try:
                self._ws_session()
            except Exception as exc:  # noqa: BLE001 - a thread nunca pode morrer
                print(f"[ws] desconectado: {exc!r}")
            time.sleep(2)  # backoff antes de reconectar

    def _ws_session(self) -> None:
        """Abre uma conexao WebSocket e processa eventos ate cair."""
        client = self.client
        if not client.base_url and not client.connect():
            time.sleep(2)
            return
        info = client.ws_connection_info()
        if not info:
            time.sleep(2)
            return
        url, header = info
        ws = websocket.create_connection(
            url,
            header=header,
            sslopt={"cert_reqs": ssl.CERT_NONE},
            timeout=5,
        )
        try:
            for event in WS_SUBSCRIBE:
                ws.send(json.dumps([5, event]))  # 5 = SUBSCRIBE (WAMP)
            print("[ws] conectado; eventos em tempo real ativos.")
            # Sincroniza o estado atual uma vez (a LCU so envia *mudancas*).
            self._tick()
            # timeout alto: o champ select envia updates com frequencia; se
            # ficar mudo tempo demais, o recv estoura e reconectamos.
            ws.settimeout(90)
            while True:
                raw = ws.recv()
                if not raw:
                    continue
                self._on_ws_message(raw)
        finally:
            try:
                ws.close()
            except Exception:  # noqa: BLE001
                pass

    def _on_ws_message(self, raw: str) -> None:
        """Decodifica uma mensagem WAMP `[8, event, payload]` e despacha."""
        try:
            msg = json.loads(raw)
        except (ValueError, TypeError):
            return
        if not isinstance(msg, list) or len(msg) < 3:
            return
        payload = msg[2]
        if not isinstance(payload, dict):
            return
        self._on_ws_event(payload.get("uri", ""), payload.get("eventType"), payload.get("data"))

    def _on_ws_event(self, uri: str, etype: Optional[str], data: Any) -> None:
        """Aplica um evento da LCU ao estado compartilhado, na hora."""
        if uri == "/lol-gameflow/v1/gameflow-phase":
            phase = data if isinstance(data, str) else None
            with self.lock:
                self.state["connected"] = True
                self.state["phase"] = phase
            if phase in _NON_CHAMP_PHASES:
                with self.lock:
                    self.state["champ_select"] = None
                if phase != "ReadyCheck":
                    self._auto_acted_actions.clear()

        elif uri == "/lol-champ-select/v1/session":
            # `data` ja e a sessao completa -- nao precisa de novo GET. E aqui
            # que a roleta do ARAM aparece no exato instante em que popula.
            if etype == "Delete" or not data:
                with self.lock:
                    self.state["champ_select"] = None
            else:
                with self.lock:
                    self.state["phase"] = "ChampSelect"
                self._apply_champ_select(data)

        elif uri == "/lol-matchmaking/v1/ready-check":
            if etype == "Delete" or not data:
                with self.lock:
                    self.state["ready_check"] = False
                    self.state["player_response"] = "None"
                return
            state = data.get("state")
            in_progress = state == "InProgress"
            timer = int(data.get("timer", 0) or 0)
            player_response = data.get("playerResponse", "None")
            with self.lock:
                self.state["ready_check"] = in_progress
                self.state["ready_timer"] = timer
                self.state["player_response"] = player_response
            if (
                in_progress
                and player_response == "None"
                and AUTO_ACCEPT_FALLBACK_SECONDS is not None
                and timer >= AUTO_ACCEPT_FALLBACK_SECONDS
                and not self._auto_accepted_this_check
                and timer >= (READY_CHECK_DURATION - AUTO_ACCEPT_FALLBACK_SECONDS)
            ):
                if self.client.accept_match():
                    self._auto_accepted_this_check = True
                    self.set_last_action("Auto-accept (fallback) acionado")
