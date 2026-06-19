"""Monitor em background que acompanha o estado do cliente do LoL.

Mantem um snapshot thread-safe do estado atual (fase, fila, ready-check,
champ select) e executa acoes automaticas opcionais (auto-accept de
fallback, auto-pick e auto-ban).
"""

import threading
import time
from typing import Any, Dict, Optional

from .config import AUTO_ACCEPT_FALLBACK_SECONDS
from .lcu_client import LCUClient

# Duracao aproximada do ready-check em segundos (o timer conta pra cima).
READY_CHECK_DURATION = 12

# Fases em que vale pesquisar com mais frequencia.
FAST_POLL_PHASES = ("ReadyCheck", "Matchmaking", "ChampSelect")
FAST_POLL_INTERVAL = 0.7
SLOW_POLL_INTERVAL = 1.5


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
        }
        self.config: Dict[str, Any] = {
            "auto_pick_enabled": False,
            "auto_pick_champ": None,
            "auto_ban_enabled": False,
            "auto_ban_champ": None,
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

        return {
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
        }

    def _maybe_auto_act(self, cs: Dict[str, Any]) -> None:
        """Auto-pick / auto-ban quando for a vez do jogador."""
        action_id = cs.get("my_action_id")
        atype = cs.get("my_action_type")
        if not action_id or action_id in self._auto_acted_actions:
            return
        cfg = self.config
        if atype == "pick" and cfg.get("auto_pick_enabled") and cfg.get("auto_pick_champ"):
            champ_id = int(cfg["auto_pick_champ"])
            if self.client.patch_action(action_id, champ_id, True):
                self._auto_acted_actions.add(action_id)
                self.set_last_action(f"Auto-pick: {self.client.champ_name(champ_id) or champ_id}")
        elif atype == "ban" and cfg.get("auto_ban_enabled") and cfg.get("auto_ban_champ"):
            champ_id = int(cfg["auto_ban_champ"])
            if self.client.patch_action(action_id, champ_id, True):
                self._auto_acted_actions.add(action_id)
                self.set_last_action(f"Auto-ban: {self.client.champ_name(champ_id) or champ_id}")

    # ------------------------------------------------------------------
    # Loop principal
    # ------------------------------------------------------------------

    def run(self) -> None:
        while True:
            if not self.client.base_url:
                connected = self.client.connect()
                with self.lock:
                    self.state["connected"] = connected
                if not connected:
                    time.sleep(3)
                    continue

            phase = self.client.get_gameflow_phase()
            with self.lock:
                self.state["connected"] = self.client.base_url is not None
                self.state["phase"] = phase

            if phase == "Matchmaking":
                self._handle_matchmaking()
            elif phase == "ReadyCheck":
                self._handle_ready_check()
            elif phase == "ChampSelect":
                self._handle_champ_select()
            else:
                self._handle_idle()

            time.sleep(FAST_POLL_INTERVAL if phase in FAST_POLL_PHASES else SLOW_POLL_INTERVAL)

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
        self.client.load_champion_data()
        session = self.client.get_champ_select_session()
        cs = self._build_champ_select(session) if session else None
        with self.lock:
            self.state["champ_select"] = cs
            self.state["ready_check"] = False
            self.state["time_in_queue"] = 0
            self.state["player_response"] = "None"
        self._auto_accepted_this_check = False
        if cs and cs.get("is_my_turn"):
            self._maybe_auto_act(cs)

    def _handle_idle(self) -> None:
        with self.lock:
            self.state["ready_check"] = False
            self.state["time_in_queue"] = 0
            self.state["player_response"] = "None"
            self.state["champ_select"] = None
        self._auto_accepted_this_check = False
        self._auto_acted_actions.clear()
