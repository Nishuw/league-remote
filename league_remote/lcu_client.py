"""Cliente para a LCU API (API local nao-oficial do cliente do LoL).

Le o `lockfile` do cliente para descobrir porta + senha e expoe metodos de
alto nivel para os endpoints usados pela aplicacao (fila, champ select,
runas, elo, historico e dados ao vivo da partida).
"""

import base64
import glob
import os
from typing import Any, Dict, List, Optional

import requests
import urllib3

from .config import COMMON_LOCKFILE_PATHS

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Endpoint local sem autenticacao exposto pelo jogo durante a partida.
LIVE_CLIENT_URL = "https://127.0.0.1:2999/liveclientdata/allgamedata"

# Timeout curto: a LCU e local, entao respostas sao rapidas ou nao chegam.
REQUEST_TIMEOUT = 2


class LCUClient:
    """Cliente para a API local do cliente do LoL (LCU)."""

    def __init__(self) -> None:
        self.port: Optional[str] = None
        self.password: Optional[str] = None
        self.base_url: Optional[str] = None
        self.headers: Dict[str, str] = {}
        self.champ_map: Dict[int, str] = {}
        self.summoner_name_cache: Dict[int, Dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Conexao
    # ------------------------------------------------------------------

    def _find_lockfile(self) -> Optional[str]:
        env_path = os.getenv("LOL_PATH")
        candidates: List[str] = []
        if env_path:
            candidates.append(os.path.join(env_path, "lockfile"))
        candidates.extend(COMMON_LOCKFILE_PATHS)
        for path in candidates:
            if path and os.path.isfile(path):
                return path
        # Ultima tentativa: procurar em qualquer pasta Riot Games dos discos comuns
        for drive in ("C:", "D:", "E:"):
            for hit in glob.glob(drive + r"\\**\\League of Legends\\lockfile", recursive=True):
                return hit
        return None

    def connect(self) -> bool:
        """Le o lockfile e configura a conexao. Retorna True se conectou."""
        lockfile = self._find_lockfile()
        if not lockfile:
            return False
        try:
            with open(lockfile, "r") as f:
                content = f.read().strip()
        except (PermissionError, OSError):
            return False

        # Formato: LeagueClient:PID:PORT:PASSWORD:PROTOCOL
        parts = content.split(":")
        if len(parts) < 5:
            return False

        self.port = parts[2]
        self.password = parts[3]
        self.base_url = f"https://127.0.0.1:{self.port}"
        token = base64.b64encode(f"riot:{self.password}".encode()).decode()
        self.headers = {"Authorization": f"Basic {token}"}
        return True

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    def _request(self, method: str, endpoint: str, **kwargs: Any) -> Optional[requests.Response]:
        if not self.base_url:
            return None
        try:
            return requests.request(
                method,
                self.base_url + endpoint,
                headers=self.headers,
                verify=False,
                timeout=REQUEST_TIMEOUT,
                **kwargs,
            )
        except requests.exceptions.RequestException:
            # Cliente fechou ou trocou de porta -> forca reconexao
            self.base_url = None
            return None

    def _get(self, endpoint: str) -> Optional[Any]:
        r = self._request("GET", endpoint)
        if r is not None and r.status_code == 200:
            return r.json()
        return None

    def _post(self, endpoint: str) -> bool:
        r = self._request("POST", endpoint)
        return r is not None and r.status_code in (200, 204)

    def _patch(self, endpoint: str, payload: Any) -> bool:
        r = self._request("PATCH", endpoint, json=payload)
        return r is not None and r.status_code in (200, 204)

    def _put(self, endpoint: str, payload: Any) -> bool:
        r = self._request("PUT", endpoint, json=payload)
        return r is not None and r.status_code in (200, 204)

    def _delete(self, endpoint: str) -> bool:
        r = self._request("DELETE", endpoint)
        return r is not None and r.status_code in (200, 204)

    def _post_json(self, endpoint: str, payload: Any) -> Optional[Any]:
        r = self._request("POST", endpoint, json=payload)
        if r is not None and r.status_code in (200, 201, 204):
            try:
                return r.json()
            except ValueError:
                return True
        return None

    # ------------------------------------------------------------------
    # Dados de campeoes
    # ------------------------------------------------------------------

    def load_champion_data(self) -> None:
        """Carrega o mapa id->nome de campeoes (uma vez). Dados locais da LCU."""
        if self.champ_map:
            return
        data = self._get("/lol-game-data/assets/v1/champion-summary.json")
        if isinstance(data, list):
            self.champ_map = {
                int(c["id"]): c.get("name", "?")
                for c in data
                if isinstance(c, dict) and "id" in c
            }

    def champ_name(self, champ_id: Optional[int]) -> Optional[str]:
        if not champ_id or champ_id <= 0:
            return None
        return self.champ_map.get(int(champ_id))

    # ------------------------------------------------------------------
    # Gameflow / champ select
    # ------------------------------------------------------------------

    def get_gameflow_phase(self) -> Optional[str]:
        """Lobby, Matchmaking, ReadyCheck, ChampSelect, InProgress, None..."""
        return self._get("/lol-gameflow/v1/gameflow-phase")

    def get_gameflow_session(self) -> Optional[Dict[str, Any]]:
        """Sessao do gameflow; contem gameData.queue (id, nome, modo)."""
        return self._get("/lol-gameflow/v1/session")

    def get_champ_select_session(self) -> Optional[Dict[str, Any]]:
        return self._get("/lol-champ-select/v1/session")

    def get_pickable_champion_ids(self) -> list:
        return self._get("/lol-champ-select/v1/pickable-champion-ids") or []

    def get_bannable_champion_ids(self) -> list:
        return self._get("/lol-champ-select/v1/bannable-champion-ids") or []

    def local_action(self) -> Dict[str, Any]:
        """Acao em progresso do jogador local: {id, type} ou {} se nao for a vez."""
        session = self.get_champ_select_session()
        if not session:
            return {}
        local = session.get("localPlayerCellId")
        for group in session.get("actions", []) or []:
            for act in group:
                if act.get("actorCellId") == local and act.get("isInProgress"):
                    return {"id": act.get("id"), "type": act.get("type")}
        return {}

    def patch_action(self, action_id: int, champion_id: int, completed: bool) -> bool:
        return self._patch(
            f"/lol-champ-select/v1/session/actions/{action_id}",
            {"championId": int(champion_id), "completed": bool(completed)},
        )

    # ------------------------------------------------------------------
    # ARAM: banco de reserva, reroll e trocas
    # ------------------------------------------------------------------

    def reroll(self) -> bool:
        """Re-rola (reroll) o campeao sorteado no ARAM."""
        return self._post("/lol-champ-select/v1/session/my-selection/reroll")

    def bench_swap(self, champion_id: int) -> bool:
        """Troca o campeao atual por um do banco de reserva (ARAM)."""
        return self._post(f"/lol-champ-select/v1/session/bench/swap/{int(champion_id)}")

    def trade_request(self, trade_id: int) -> bool:
        """Oferece troca de campeao a um aliado."""
        return self._post(f"/lol-champ-select/v1/session/trades/{int(trade_id)}/request")

    def trade_accept(self, trade_id: int) -> bool:
        """Aceita uma troca de campeao recebida."""
        return self._post(f"/lol-champ-select/v1/session/trades/{int(trade_id)}/accept")

    def trade_decline(self, trade_id: int) -> bool:
        """Recusa uma troca de campeao recebida."""
        return self._post(f"/lol-champ-select/v1/session/trades/{int(trade_id)}/decline")

    # ------------------------------------------------------------------
    # Runas
    # ------------------------------------------------------------------

    def get_rune_pages(self) -> list:
        return self._get("/lol-perks/v1/pages") or []

    def set_current_rune_page(self, page_id: int) -> bool:
        return self._put("/lol-perks/v1/currentpage", int(page_id))

    def get_perk_styles(self) -> list:
        return self._get("/lol-perks/v1/styles") or []

    def get_perks(self) -> list:
        return self._get("/lol-perks/v1/perks") or []

    def get_current_rune_page(self) -> Optional[Dict[str, Any]]:
        return self._get("/lol-perks/v1/currentpage")

    def apply_runes(self, primary_style: int, sub_style: int, perk_ids: list) -> bool:
        """Edita a pagina de runa atual (ou a primeira editavel) e ativa."""
        cur = self.get_current_rune_page()
        target = cur if (cur and cur.get("isEditable")) else None
        if target is None:
            for p in self.get_rune_pages():
                if p.get("isEditable"):
                    target = p
                    break
        if not target:
            return False
        page_id = target["id"]
        body = {
            "name": target.get("name") or "Runa Celular",
            "primaryStyleId": int(primary_style),
            "subStyleId": int(sub_style),
            "selectedPerkIds": [int(x) for x in perk_ids],
            "current": True,
        }
        ok = self._put(f"/lol-perks/v1/pages/{page_id}", body)
        self.set_current_rune_page(page_id)
        return ok

    def save_rune_page(self, name: str, primary_style: int, sub_style: int, perk_ids: list) -> bool:
        """Cria uma NOVA pagina de runa com nome."""
        body = {
            "name": name or "Runa Celular",
            "primaryStyleId": int(primary_style),
            "subStyleId": int(sub_style),
            "selectedPerkIds": [int(x) for x in perk_ids],
            "current": True,
        }
        return self._post_json("/lol-perks/v1/pages", body) is not None

    # ------------------------------------------------------------------
    # Fila / lobby
    # ------------------------------------------------------------------

    def cancel_matchmaking(self) -> bool:
        return self._delete("/lol-lobby/v1/lobby/matchmaking/search")

    def get_search_state(self) -> Optional[Dict[str, Any]]:
        """Inclui timeInQueue e estimatedQueueTime."""
        return self._get("/lol-matchmaking/v1/search")

    def get_ready_check(self) -> Optional[Dict[str, Any]]:
        """state, playerResponse, timer."""
        return self._get("/lol-matchmaking/v1/ready-check")

    def accept_match(self) -> bool:
        return self._post("/lol-matchmaking/v1/ready-check/accept")

    def decline_match(self) -> bool:
        return self._post("/lol-matchmaking/v1/ready-check/decline")

    # ------------------------------------------------------------------
    # Invocador / elo / historico
    # ------------------------------------------------------------------

    def get_summoner_by_id(self, summoner_id: int) -> Optional[Dict[str, Any]]:
        if not summoner_id:
            return None
        if summoner_id in self.summoner_name_cache:
            return self.summoner_name_cache[summoner_id]
        data = self._get(f"/lol-summoner/v1/summoners/{summoner_id}")
        if data:
            self.summoner_name_cache[summoner_id] = data
        return data

    def get_current_summoner(self) -> Optional[Dict[str, Any]]:
        return self._get("/lol-summoner/v1/current-summoner")

    def get_ranked_stats(self) -> Optional[Dict[str, Any]]:
        return self._get("/lol-ranked/v1/current-ranked-stats")

    def get_match_history(self, count: int = 10) -> Optional[Dict[str, Any]]:
        end = max(0, count - 1)
        return self._get(
            f"/lol-match-history/v1/products/lol/current-summoner/matches?begIndex=0&endIndex={end}"
        )

    # ------------------------------------------------------------------
    # Live Client Data API (porta 2999, sem auth)
    # ------------------------------------------------------------------

    def get_live_game(self) -> Optional[Dict[str, Any]]:
        try:
            r = requests.get(LIVE_CLIENT_URL, verify=False, timeout=REQUEST_TIMEOUT)
            if r.status_code == 200:
                return r.json()
            return None
        except requests.exceptions.RequestException:
            return None
