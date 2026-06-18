"""
LoL Queue Remote Accept
=======================

Monitora a fila do League of Legends (via LCU API local) e permite que voce
aceite a partida pelo celular, acessando uma pagina web pelo IP do PC na mesma
rede Wi-Fi.

Como funciona:
- Le o `lockfile` do cliente do LoL para descobrir porta + senha da LCU API.
- Fica observando a fase do jogo e o "ready check" (aquela tela de Aceitar).
- Sobe um servidor web simples; abra no celular: http://IP-DO-PC:5000
- Quando a partida e encontrada, o celular mostra o botao ACEITAR.
- Opcional: auto-accept de fallback (aceita sozinho se voce nao responder a tempo).

ATENCAO: a LCU API e nao-oficial. Use por conta e risco.
"""

import os
import sys
import time
import glob
import base64
import socket
import threading
from typing import Optional, Dict, Any

import requests
import urllib3
from flask import Flask, jsonify, render_template_string, request

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ============================================================
# Configuracao
# ============================================================

# Segundos antes do timer acabar para o PC aceitar sozinho (fallback).
# Defina como None para desativar o auto-accept e depender so do celular.
AUTO_ACCEPT_FALLBACK_SECONDS: Optional[int] = 3

# Porta do servidor web (a que voce abre no celular).
WEB_PORT = 5000

# Caminhos comuns do lockfile no Windows. O caminho pode ser sobrescrito
# pela variavel de ambiente LOL_PATH (pasta de instalacao do LoL).
COMMON_LOCKFILE_PATHS = [
    r"C:\Riot Games\League of Legends\lockfile",
    r"D:\Riot Games\League of Legends\lockfile",
    r"E:\Riot Games\League of Legends\lockfile",
    os.path.expandvars(r"%LOCALAPPDATA%\Riot Games\League of Legends\lockfile"),
]


# ============================================================
# Cliente LCU
# ============================================================

class LCUClient:
    """Cliente para a API local do cliente do LoL (LCU)."""

    def __init__(self):
        self.port: Optional[str] = None
        self.password: Optional[str] = None
        self.base_url: Optional[str] = None
        self.headers: Dict[str, str] = {}
        self.champ_map: Dict[int, str] = {}
        self.summoner_name_cache: Dict[int, Dict[str, Any]] = {}

    def _find_lockfile(self) -> Optional[str]:
        env_path = os.getenv("LOL_PATH")
        candidates = []
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

    def _get(self, endpoint: str) -> Optional[Any]:
        if not self.base_url:
            return None
        try:
            r = requests.get(
                self.base_url + endpoint,
                headers=self.headers,
                verify=False,
                timeout=2,
            )
            if r.status_code == 200:
                return r.json()
            return None
        except requests.exceptions.RequestException:
            # Cliente fechou ou trocou de porta -> forca reconexao
            self.base_url = None
            return None

    def _post(self, endpoint: str) -> bool:
        if not self.base_url:
            return False
        try:
            r = requests.post(
                self.base_url + endpoint,
                headers=self.headers,
                verify=False,
                timeout=2,
            )
            return r.status_code in (200, 204)
        except requests.exceptions.RequestException:
            self.base_url = None
            return False

    def _patch(self, endpoint: str, payload: Any) -> bool:
        if not self.base_url:
            return False
        try:
            r = requests.patch(
                self.base_url + endpoint,
                headers=self.headers,
                json=payload,
                verify=False,
                timeout=2,
            )
            return r.status_code in (200, 204)
        except requests.exceptions.RequestException:
            self.base_url = None
            return False

    def _put(self, endpoint: str, payload: Any) -> bool:
        if not self.base_url:
            return False
        try:
            r = requests.put(
                self.base_url + endpoint,
                headers=self.headers,
                json=payload,
                verify=False,
                timeout=2,
            )
            return r.status_code in (200, 204)
        except requests.exceptions.RequestException:
            self.base_url = None
            return False

    def _delete(self, endpoint: str) -> bool:
        if not self.base_url:
            return False
        try:
            r = requests.delete(
                self.base_url + endpoint,
                headers=self.headers,
                verify=False,
                timeout=2,
            )
            return r.status_code in (200, 204)
        except requests.exceptions.RequestException:
            self.base_url = None
            return False

    def _post_json(self, endpoint: str, payload: Any) -> Optional[Any]:
        if not self.base_url:
            return None
        try:
            r = requests.post(
                self.base_url + endpoint,
                headers=self.headers,
                json=payload,
                verify=False,
                timeout=2,
            )
            if r.status_code in (200, 201, 204):
                try:
                    return r.json()
                except ValueError:
                    return True
            return None
        except requests.exceptions.RequestException:
            self.base_url = None
            return None

    # ---- Endpoints de interesse ----

    def load_champion_data(self):
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

    def get_gameflow_phase(self) -> Optional[str]:
        """Lobby, Matchmaking, ReadyCheck, ChampSelect, InProgress, None..."""
        return self._get("/lol-gameflow/v1/gameflow-phase")

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

    # ---- Fila / lobby ----

    def cancel_matchmaking(self) -> bool:
        return self._delete("/lol-lobby/v1/lobby/matchmaking/search")

    # ---- Invocador (nomes) ----

    def get_summoner_by_id(self, summoner_id: int) -> Optional[Dict[str, Any]]:
        if not summoner_id:
            return None
        if summoner_id in self.summoner_name_cache:
            return self.summoner_name_cache[summoner_id]
        data = self._get(f"/lol-summoner/v1/summoners/{summoner_id}")
        if data:
            self.summoner_name_cache[summoner_id] = data
        return data

    # ---- Ranqueada / historico ----

    def get_ranked_stats(self) -> Optional[Dict[str, Any]]:
        return self._get("/lol-ranked/v1/current-ranked-stats")

    def get_match_history(self, count: int = 10) -> Optional[Dict[str, Any]]:
        end = max(0, count - 1)
        return self._get(
            f"/lol-match-history/v1/products/lol/current-summoner/matches?begIndex=0&endIndex={end}"
        )

    def get_current_summoner(self) -> Optional[Dict[str, Any]]:
        return self._get("/lol-summoner/v1/current-summoner")

    # ---- Live Client Data API (porta 2999, sem auth) ----

    def get_live_game(self) -> Optional[Dict[str, Any]]:
        try:
            r = requests.get(
                "https://127.0.0.1:2999/liveclientdata/allgamedata",
                verify=False,
                timeout=2,
            )
            if r.status_code == 200:
                return r.json()
            return None
        except requests.exceptions.RequestException:
            return None

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


# ============================================================
# Estado compartilhado + monitor em background
# ============================================================

class Monitor:
    def __init__(self, client: LCUClient):
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
        self.config = {
            "auto_pick_enabled": False,
            "auto_pick_champ": None,
            "auto_ban_enabled": False,
            "auto_ban_champ": None,
        }
        self._auto_accepted_this_check = False
        self._auto_acted_actions = set()

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

    def snapshot(self) -> Dict[str, Any]:
        with self.lock:
            return dict(self.state)

    def set_last_action(self, msg: str):
        with self.lock:
            self.state["last_action"] = msg

    def _maybe_auto_act(self, cs: Dict[str, Any]):
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

    def run(self):
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
                search = self.client.get_search_state() or {}
                with self.lock:
                    self.state["time_in_queue"] = int(search.get("timeInQueue", 0) or 0)
                    self.state["estimated_queue_time"] = int(search.get("estimatedQueueTime", 0) or 0)
                    self.state["ready_check"] = False
                    self.state["player_response"] = "None"
                self._auto_accepted_this_check = False

            elif phase == "ReadyCheck":
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

                # Auto-accept de fallback
                if (
                    in_progress
                    and player_response == "None"
                    and AUTO_ACCEPT_FALLBACK_SECONDS is not None
                    and timer >= AUTO_ACCEPT_FALLBACK_SECONDS
                    and not self._auto_accepted_this_check
                ):
                    # timer conta pra cima ate ~12s; aceita quando faltar pouco
                    if timer >= (12 - AUTO_ACCEPT_FALLBACK_SECONDS):
                        if self.client.accept_match():
                            self._auto_accepted_this_check = True
                            self.set_last_action("Auto-accept (fallback) acionado")
            elif phase == "ChampSelect":
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

            else:
                with self.lock:
                    self.state["ready_check"] = False
                    self.state["time_in_queue"] = 0
                    self.state["player_response"] = "None"
                    self.state["champ_select"] = None
                self._auto_accepted_this_check = False
                self._auto_acted_actions.clear()

            # Polling rapido durante ready-check/champ-select, mais lento no resto
            time.sleep(0.7 if phase in ("ReadyCheck", "Matchmaking", "ChampSelect") else 1.5)


# ============================================================
# Servidor web
# ============================================================

app = Flask(__name__)
monitor: Optional[Monitor] = None

PAGE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>LoL Accept</title>
<style>
  * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
  body {
    margin: 0; font-family: -apple-system, Segoe UI, Roboto, sans-serif;
    background: #0a0e14; color: #e6e6e6; min-height: 100vh;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    padding: 24px; text-align: center;
  }
  h1 { font-size: 20px; letter-spacing: 1px; color: #c8aa6e; margin: 0 0 4px; }
  .sub { font-size: 12px; color: #5b6b7c; margin-bottom: 28px; }
  .card {
    background: #111722; border: 1px solid #1e2a3a; border-radius: 16px;
    padding: 28px 22px; width: 100%; max-width: 420px;
  }
  .status { font-size: 13px; color: #7a8a9a; text-transform: uppercase; letter-spacing: 2px; }
  .big { font-size: 34px; font-weight: 700; margin: 10px 0; }
  .queue { font-size: 52px; font-weight: 800; color: #4fd1c5; margin: 8px 0; font-variant-numeric: tabular-nums; }
  .muted { color: #5b6b7c; font-size: 13px; }
  .accept {
    display: none; width: 100%; margin-top: 22px; padding: 26px;
    font-size: 26px; font-weight: 800; letter-spacing: 1px;
    border: none; border-radius: 14px; cursor: pointer;
    background: linear-gradient(135deg, #1e9e57, #14b85f); color: #fff;
    box-shadow: 0 8px 24px rgba(20,184,95,.35);
  }
  .accept:active { transform: scale(.98); }
  .dot { display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: 6px; }
  .on { background: #14b85f; } .off { background: #d24b4b; }
  .flash { animation: pulse 1s infinite; }
  @keyframes pulse { 0%,100% { opacity: 1 } 50% { opacity: .55 } }
  .foot { margin-top: 18px; font-size: 11px; color: #3d4a59; min-height: 14px; }

  .card.wide { max-width: 640px; }
  .champ { display: none; margin-top: 4px; }
  .turn { font-size: 14px; color: #c8aa6e; margin-bottom: 14px; min-height: 18px; }
  .turn b { color: #fff; }
  .teams { display: flex; gap: 12px; }
  .team { flex: 1; min-width: 0; }
  .team h3 { font-size: 11px; letter-spacing: 1px; text-transform: uppercase; margin: 0 0 8px; }
  .team.ally h3 { color: #4f93d1; }
  .team.enemy h3 { color: #d24b6a; }
  .row {
    display: flex; align-items: center; gap: 8px; padding: 6px;
    border-radius: 8px; background: #0d131d; margin-bottom: 6px; text-align: left;
  }
  .row.me { outline: 1px solid #c8aa6e; }
  .row.turn-now { background: #1a2433; animation: pulse 1.1s infinite; }
  .row img, .row .noimg {
    width: 34px; height: 34px; border-radius: 6px; flex: 0 0 34px;
    background: #1e2a3a; object-fit: cover;
  }
  .row .info { min-width: 0; }
  .row .cname { font-size: 13px; font-weight: 600; color: #e6e6e6; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .row .pos { font-size: 10px; color: #5b6b7c; text-transform: uppercase; }
  .row .cname.empty { color: #5b6b7c; font-weight: 400; font-style: italic; }
  .bans { display: flex; align-items: center; gap: 6px; margin-top: 12px; flex-wrap: wrap; }
  .bans .lbl { font-size: 10px; color: #5b6b7c; text-transform: uppercase; }
  .bans img { width: 24px; height: 24px; border-radius: 4px; filter: grayscale(1) brightness(.8); }

  .pickbar { display: flex; gap: 8px; margin: 16px 0 10px; }
  #champ-search {
    flex: 1; min-width: 0; padding: 12px; border-radius: 8px;
    border: 1px solid #1e2a3a; background: #0d131d; color: #e6e6e6; font-size: 15px;
  }
  .lockbtn {
    padding: 12px 18px; border: none; border-radius: 8px; font-weight: 800; font-size: 15px;
    background: linear-gradient(135deg, #c8aa6e, #a8863f); color: #1a1205; cursor: pointer;
  }
  .lockbtn.ban { background: linear-gradient(135deg, #d24b6a, #a8324b); color: #fff; }
  .lockbtn:active { transform: scale(.97); }
  .grid {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(62px, 1fr)); gap: 6px;
    max-height: 320px; overflow-y: auto; padding: 6px; background: #0a0e14; border-radius: 8px;
  }
  .gitem { display: flex; flex-direction: column; align-items: center; gap: 3px; padding: 4px; border-radius: 6px; cursor: pointer; }
  .gitem img { width: 46px; height: 46px; border-radius: 6px; background: #1e2a3a; }
  .gitem span { font-size: 9px; color: #8a99a8; max-width: 58px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .gitem.sel { background: #1a2433; outline: 2px solid #c8aa6e; }
  .runebtn {
    margin-top: 16px; width: 100%; padding: 13px; border: none; border-radius: 8px;
    background: #16202e; color: #c8aa6e; font-weight: 700; font-size: 14px; cursor: pointer;
  }
  .runepage {
    padding: 13px; margin-top: 6px; border-radius: 8px; background: #0d131d;
    cursor: pointer; text-align: left; font-size: 14px;
  }
  .runepage.cur { outline: 1px solid #14b85f; color: #9fd6b4; }
  .loading { color: #5b6b7c; font-size: 13px; padding: 12px; }

  .rune-editor { margin-top: 10px; text-align: left; }
  .rune-sec-title { font-size: 11px; letter-spacing: 1px; text-transform: uppercase; color: #c8aa6e; margin: 14px 0 6px; }
  .rune-styles { display: flex; gap: 8px; flex-wrap: wrap; }
  .rstyle { display: flex; flex-direction: column; align-items: center; gap: 3px; cursor: pointer; opacity: .5; }
  .rstyle.sel { opacity: 1; }
  .rstyle img { width: 40px; height: 40px; }
  .rstyle span { font-size: 9px; color: #8a99a8; }
  .rune-row { display: flex; gap: 10px; margin: 8px 0; flex-wrap: wrap; }
  .rperk { width: 46px; height: 46px; border-radius: 50%; cursor: pointer; opacity: .35; background: #0d131d; padding: 2px; }
  .rperk.key { border-radius: 8px; width: 52px; height: 52px; }
  .rperk.sel { opacity: 1; outline: 2px solid #c8aa6e; }
  .rperk.shard { width: 34px; height: 34px; }
  .applybtn {
    margin-top: 18px; width: 100%; padding: 15px; border: none; border-radius: 10px;
    font-size: 16px; font-weight: 800; cursor: pointer;
    background: linear-gradient(135deg, #1e9e57, #14b85f); color: #fff;
  }
  .applybtn:disabled { background: #2a3340; color: #5b6b7c; cursor: not-allowed; }

  .declinebtn {
    display: none; margin: 12px auto 0; padding: 10px 22px; border: 1px solid #5a2b35;
    border-radius: 10px; background: transparent; color: #d24b6a; font-size: 14px; cursor: pointer;
  }
  .leavebtn {
    display: none; margin: 16px auto 0; padding: 11px 20px; border: 1px solid #5a2b35;
    border-radius: 10px; background: transparent; color: #d24b6a; font-size: 14px; cursor: pointer;
  }
  .saverow { display: flex; gap: 8px; margin-top: 10px; }
  #rune-save-name {
    flex: 1; min-width: 0; padding: 12px; border-radius: 8px; border: 1px solid #1e2a3a;
    background: #0d131d; color: #e6e6e6; font-size: 14px;
  }
  .savebtn { padding: 12px 16px; border: none; border-radius: 8px; font-weight: 700; background: #16202e; color: #c8aa6e; cursor: pointer; }

  .rank-box { display: flex; gap: 10px; margin-top: 18px; }
  .rank-card { flex: 1; background: #0d131d; border-radius: 10px; padding: 12px; }
  .rank-card .q { font-size: 10px; color: #5b6b7c; text-transform: uppercase; }
  .rank-card .t { font-size: 16px; font-weight: 700; color: #c8aa6e; margin: 4px 0; }
  .rank-card .wl { font-size: 11px; color: #7a8a9a; }
  .hist { margin-top: 16px; text-align: left; }
  .hist .htitle { font-size: 11px; letter-spacing: 1px; text-transform: uppercase; color: #5b6b7c; margin-bottom: 8px; }
  .hrow { display: flex; align-items: center; gap: 8px; padding: 6px 8px; border-radius: 8px; margin-bottom: 4px; background: #0d131d; border-left: 3px solid #444; }
  .hrow.win { border-left-color: #14b85f; }
  .hrow.loss { border-left-color: #d24b6a; }
  .hrow img { width: 30px; height: 30px; border-radius: 6px; }
  .hrow .hc { flex: 1; font-size: 13px; }
  .hrow .hres { font-size: 11px; font-weight: 700; }
  .hrow.win .hres { color: #14b85f; } .hrow.loss .hres { color: #d24b6a; }
  .hrow .hkda { font-size: 12px; color: #9aa; }

  .live { display: none; margin-top: 8px; }
  .live .gt { font-size: 28px; font-weight: 800; color: #4fd1c5; font-variant-numeric: tabular-nums; }
  .live .lteam { margin-top: 12px; }
  .live .lteam h4 { font-size: 11px; text-transform: uppercase; margin: 0 0 6px; text-align: left; }
  .live .ally h4 { color: #4f93d1; } .live .enemy h4 { color: #d24b6a; }
  .lprow { display: flex; align-items: center; gap: 8px; padding: 5px 8px; background: #0d131d; border-radius: 7px; margin-bottom: 4px; text-align: left; }
  .lprow .lc { flex: 1; font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .lprow .lk { font-size: 13px; color: #e6e6e6; font-variant-numeric: tabular-nums; }
  .lprow .lcs { font-size: 11px; color: #7a8a9a; width: 52px; text-align: right; }

  .cfgbtn {
    margin-top: 14px; width: 100%; max-width: 420px; padding: 11px; border: none; border-radius: 10px;
    background: #111722; color: #7a8a9a; font-size: 13px; cursor: pointer; border: 1px solid #1e2a3a;
  }
  .cfg-panel { width: 100%; max-width: 420px; background: #111722; border: 1px solid #1e2a3a; border-radius: 12px; padding: 16px; margin-top: 8px; text-align: left; }
  .cfg-row { display: flex; align-items: center; justify-content: space-between; margin: 10px 0; }
  .cfg-row label { font-size: 14px; color: #e6e6e6; }
  .cfg-row select { padding: 8px; border-radius: 8px; background: #0d131d; color: #e6e6e6; border: 1px solid #1e2a3a; max-width: 180px; }
  .switch { position: relative; width: 46px; height: 26px; }
  .switch input { display: none; }
  .slider { position: absolute; inset: 0; background: #2a3340; border-radius: 26px; transition: .2s; cursor: pointer; }
  .slider:before { content: ""; position: absolute; width: 20px; height: 20px; left: 3px; top: 3px; background: #fff; border-radius: 50%; transition: .2s; }
  .switch input:checked + .slider { background: #14b85f; }
  .switch input:checked + .slider:before { transform: translateX(20px); }
</style>
</head>
<body>
  <h1>LEAGUE REMOTE ACCEPT</h1>
  <div class="sub"><span id="conn-dot" class="dot off"></span><span id="conn">conectando...</span></div>
  <div class="card" id="card">
    <div class="status" id="phase">--</div>
    <div id="content">
      <div class="queue" id="queue">--</div>
      <div class="muted" id="queue-label">tempo de fila</div>
      <button class="leavebtn" id="leavebtn" onclick="leaveQueue()">Sair da fila</button>
      <div id="idle-extra"></div>
    </div>
    <button class="accept" id="accept" onclick="accept()">ACEITAR</button>
    <button class="declinebtn" id="declinebtn" onclick="decline()">Recusar</button>
    <div class="champ" id="champ"></div>
    <div class="live" id="live"></div>
  </div>
  <button class="cfgbtn" id="cfgbtn" onclick="toggleConfig()">&#9881; Auto-pick / Auto-ban</button>
  <div class="cfg-panel" id="cfg-panel" style="display:none"></div>
  <div class="foot" id="foot"></div>

<script>
let accepting = false;

function fmt(s) {
  s = Math.max(0, parseInt(s) || 0);
  const m = Math.floor(s / 60), r = s % 60;
  return m + ":" + String(r).padStart(2, "0");
}

async function accept() {
  if (accepting) return;
  accepting = true;
  stopAlarm();
  const btn = document.getElementById("accept");
  btn.textContent = "ACEITANDO...";
  try {
    const r = await fetch("/accept", { method: "POST" });
    const j = await r.json();
    btn.textContent = j.ok ? "ACEITO!" : "FALHOU - tentar de novo";
  } catch (e) {
    btn.textContent = "ERRO - tentar de novo";
  }
  setTimeout(() => { accepting = false; }, 1500);
}

async function decline() {
  stopAlarm();
  try { await fetch("/decline", { method: "POST" }); } catch (e) {}
}

async function leaveQueue() {
  if (!confirm("Sair da fila?")) return;
  try { await fetch("/leave-queue", { method: "POST" }); } catch (e) {}
}

// ---- Alarme (vibrar + som) ----
let audioCtx = null;
let alarmTimer = null;
function beep() {
  try {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    if (audioCtx.state === "suspended") audioCtx.resume();
    const o = audioCtx.createOscillator(), g = audioCtx.createGain();
    o.type = "square"; o.frequency.value = 880;
    o.connect(g); g.connect(audioCtx.destination);
    g.gain.setValueAtTime(0.001, audioCtx.currentTime);
    g.gain.exponentialRampToValueAtTime(0.3, audioCtx.currentTime + 0.02);
    g.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.4);
    o.start(); o.stop(audioCtx.currentTime + 0.45);
  } catch (e) {}
}
function startAlarm() {
  if (alarmTimer) return;
  const fire = () => { beep(); if (navigator.vibrate) navigator.vibrate([300, 150, 300]); };
  fire();
  alarmTimer = setInterval(fire, 1200);
}
function stopAlarm() {
  if (alarmTimer) { clearInterval(alarmTimer); alarmTimer = null; }
  if (navigator.vibrate) navigator.vibrate(0);
}

const PHASE_PT = {
  None: "No menu", Lobby: "No lobby", Matchmaking: "Na fila",
  ReadyCheck: "Partida encontrada!", ChampSelect: "Selecao de campeao",
  InProgress: "Em partida", PreEndOfGame: "Fim de jogo", EndOfGame: "Fim de jogo",
};

const POS_PT = {
  top: "Top", jungle: "Jungle", middle: "Mid", bottom: "ADC", utility: "Suporte",
};

function champIcon(id) {
  return "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champion-icons/" + id + ".png";
}

function rowHtml(p) {
  const cls = "row" + (p.is_local ? " me" : "") + (p.picking ? " turn-now" : "");
  const icon = p.champion_id
    ? '<img src="' + champIcon(p.champion_id) + '" onerror="this.style.visibility=\\'hidden\\'">'
    : '<div class="noimg"></div>';
  let name;
  if (p.champion) name = '<div class="cname">' + p.champion + '</div>';
  else if (p.picking) name = '<div class="cname empty">escolhendo...</div>';
  else name = '<div class="cname empty">--</div>';
  let sub = "";
  if (p.name) sub = '<div class="pos">' + p.name + '</div>';
  else if (p.position) sub = '<div class="pos">' + (POS_PT[p.position] || p.position) + '</div>';
  return '<div class="' + cls + '">' + icon + '<div class="info">' + name + sub + '</div></div>';
}

function bansHtml(label, bans) {
  let imgs = bans.map(b => '<img src="' + champIcon(b.champion_id) + '" title="' + (b.champion || '') + '" onerror="this.style.display=\\'none\\'">').join("");
  if (!imgs) imgs = '<span class="pos">nenhum</span>';
  return '<div class="bans"><span class="lbl">' + label + '</span>' + imgs + '</div>';
}

function renderChamp(cs) {
  let turn = "";
  if (cs.current_actor_cell != null) {
    const mine = cs.current_actor_cell === cs.local_cell;
    const act = cs.current_action_type === "ban" ? "banir" : "escolher";
    turn = mine
      ? '<b>SUA VEZ</b> de ' + act + '! (' + cs.time_left + 's)'
      : 'Vez de ' + act + '... (' + cs.time_left + 's)';
  } else if (cs.time_left) {
    turn = 'Tempo: ' + cs.time_left + 's';
  }
  return (
    '<div class="turn">' + turn + '</div>' +
    '<div class="teams">' +
      '<div class="team ally"><h3>Seu time</h3>' + cs.my_team.map(rowHtml).join("") + '</div>' +
      '<div class="team enemy"><h3>Inimigos</h3>' + cs.their_team.map(rowHtml).join("") + '</div>' +
    '</div>' +
    bansHtml("Bans aliados", cs.my_bans) +
    bansHtml("Bans inimigos", cs.their_bans)
  );
}

let csActionId = undefined;
let csSelected = null;

function ensureChampLayout() {
  const champ = document.getElementById("champ");
  if (!document.getElementById("champ-info")) {
    champ.innerHTML =
      '<div id="champ-info"></div>' +
      '<div id="champ-controls"></div>' +
      '<div id="runes-area"></div>';
    loadRunes();
  }
}

function resetChampLayout() {
  const champ = document.getElementById("champ");
  if (champ.innerHTML !== "") champ.innerHTML = "";
  csActionId = undefined;
  csSelected = null;
}

async function loadChampControls(cs) {
  const ctr = document.getElementById("champ-controls");
  if (!ctr) return;
  if (!cs.is_my_turn) {
    if (csActionId !== undefined) { ctr.innerHTML = ""; csActionId = undefined; csSelected = null; }
    return;
  }
  if (cs.my_action_id === csActionId) return;
  csActionId = cs.my_action_id;
  csSelected = null;
  ctr.innerHTML = '<div class="loading">carregando campeoes...</div>';
  try {
    const data = await (await fetch("/champ-options")).json();
    const isBan = data.type === "ban";
    const verb = isBan ? "BANIR" : "TRAVAR";
    ctr.innerHTML =
      '<div class="pickbar">' +
        '<input id="champ-search" placeholder="buscar campeao..." oninput="filterChamps()">' +
        '<button class="lockbtn ' + (isBan ? "ban" : "") + '" id="lockbtn" onclick="doLock()">' + verb + '</button>' +
      '</div>' +
      '<div class="grid" id="champ-grid">' +
        data.champions.map(c =>
          '<div class="gitem" data-name="' + c.name.toLowerCase() + '" data-id="' + c.id + '" onclick="selectChamp(' + c.id + ')">' +
            '<img loading="lazy" src="' + champIcon(c.id) + '" onerror="this.style.visibility=\\'hidden\\'">' +
            '<span>' + c.name + '</span>' +
          '</div>'
        ).join("") +
      '</div>';
  } catch (e) {
    ctr.innerHTML = '<div class="loading">erro ao carregar campeoes</div>';
    csActionId = undefined;
  }
}

function filterChamps() {
  const q = document.getElementById("champ-search").value.toLowerCase();
  document.querySelectorAll("#champ-grid .gitem").forEach(el => {
    el.style.display = el.dataset.name.includes(q) ? "" : "none";
  });
}

async function selectChamp(id) {
  csSelected = id;
  document.querySelectorAll("#champ-grid .gitem").forEach(el => {
    el.classList.toggle("sel", parseInt(el.dataset.id) === id);
  });
  try {
    await fetch("/champ-action", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ championId: id, complete: false })
    });
  } catch (e) {}
}

async function doLock() {
  if (!csSelected) return;
  const btn = document.getElementById("lockbtn");
  const original = btn.textContent;
  btn.textContent = "...";
  try {
    const j = await (await fetch("/champ-action", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ championId: csSelected, complete: true })
    })).json();
    btn.textContent = j.ok ? "OK!" : "FALHOU";
  } catch (e) { btn.textContent = "ERRO"; }
  setTimeout(() => { if (btn) btn.textContent = original; }, 1500);
}

function loadRunes() {
  const area = document.getElementById("runes-area");
  if (!area || area.dataset.init) return;
  area.dataset.init = "1";
  area.innerHTML =
    '<button class="runebtn" onclick="toggleRunes()">Paginas de runa salvas</button>' +
    '<div id="rune-list" style="display:none"></div>' +
    '<button class="runebtn" onclick="toggleRuneEditor()">Montar runa</button>' +
    '<div id="rune-editor" style="display:none"></div>';
}

async function renderRuneList() {
  const list = document.getElementById("rune-list");
  const pages = await (await fetch("/runes")).json();
  list.innerHTML = pages.map(p =>
    '<div class="runepage' + (p.current ? " cur" : "") + '" onclick="selectRune(' + p.id + ')">' +
      p.name + (p.current ? " &#10003;" : "") +
    '</div>'
  ).join("") || '<div class="loading">nenhuma pagina salva</div>';
}

async function toggleRunes() {
  const list = document.getElementById("rune-list");
  if (list.style.display === "none") {
    list.style.display = "block";
    await renderRuneList();
  } else {
    list.style.display = "none";
  }
}

async function selectRune(id) {
  try {
    await fetch("/runes/select", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id })
    });
    await renderRuneList();
  } catch (e) {}
}

// ---- Editor de runas ----
let runeData = null;
let runeSel = { primary: null, keystone: null, minors: [null, null, null], sub: null, secondary: [null, null, null], shards: [null, null, null] };

async function toggleRuneEditor() {
  const ed = document.getElementById("rune-editor");
  if (ed.style.display === "none") {
    ed.style.display = "block";
    if (!runeData) {
      ed.innerHTML = '<div class="loading">carregando runas...</div>';
      try { runeData = await (await fetch("/rune-data")).json(); prefillRunes(); }
      catch (e) { ed.innerHTML = '<div class="loading">erro ao carregar runas</div>'; return; }
    }
    renderRuneEditor();
  } else {
    ed.style.display = "none";
  }
}

function styleById(id) { return runeData.styles.find(s => s.id === id); }

function prefillRunes() {
  const c = runeData.current || {};
  const ids = c.selectedPerkIds || [];
  if (c.primaryStyleId) runeSel.primary = c.primaryStyleId;
  if (c.subStyleId) runeSel.sub = c.subStyleId;
  if (ids.length === 9) {
    runeSel.keystone = ids[0];
    runeSel.minors = [ids[1], ids[2], ids[3]];
    // mapeia as 2 secundarias para as linhas da arvore secundaria
    const sub = styleById(runeSel.sub);
    runeSel.secondary = [null, null, null];
    if (sub) {
      [ids[4], ids[5]].forEach(pid => {
        sub.rows.forEach((row, r) => { if (row.some(p => p.id === pid)) runeSel.secondary[r] = pid; });
      });
    }
    runeSel.shards = [ids[6], ids[7], ids[8]];
  }
}

function renderRuneEditor() {
  const ed = document.getElementById("rune-editor");
  const prim = runeSel.primary ? styleById(runeSel.primary) : null;
  const sub = runeSel.sub ? styleById(runeSel.sub) : null;
  let h = "";

  h += '<div class="rune-sec-title">Arvore primaria</div><div class="rune-styles">';
  runeData.styles.forEach(s => {
    h += '<div class="rstyle' + (s.id === runeSel.primary ? " sel" : "") + '" onclick="pickPrimary(' + s.id + ')">' +
      '<img src="' + s.icon + '" onerror="this.style.visibility=\\'hidden\\'"><span>' + s.name + '</span></div>';
  });
  h += '</div>';

  if (prim) {
    h += '<div class="rune-sec-title">Runa principal</div><div class="rune-row">';
    prim.keystones.forEach(p => {
      h += '<img class="rperk key' + (p.id === runeSel.keystone ? " sel" : "") + '" src="' + p.icon +
        '" title="' + p.name + '" onerror="this.style.visibility=\\'hidden\\'" onclick="pickKeystone(' + p.id + ')">';
    });
    h += '</div>';
    prim.rows.forEach((row, r) => {
      h += '<div class="rune-row">';
      row.forEach(p => {
        h += '<img class="rperk' + (p.id === runeSel.minors[r] ? " sel" : "") + '" src="' + p.icon +
          '" title="' + p.name + '" onerror="this.style.visibility=\\'hidden\\'" onclick="pickMinor(' + r + ',' + p.id + ')">';
      });
      h += '</div>';
    });

    h += '<div class="rune-sec-title">Arvore secundaria</div><div class="rune-styles">';
    runeData.styles.filter(s => s.id !== runeSel.primary).forEach(s => {
      h += '<div class="rstyle' + (s.id === runeSel.sub ? " sel" : "") + '" onclick="pickSub(' + s.id + ')">' +
        '<img src="' + s.icon + '" onerror="this.style.visibility=\\'hidden\\'"><span>' + s.name + '</span></div>';
    });
    h += '</div>';

    if (sub) {
      h += '<div class="rune-sec-title">Runas secundarias (escolha 2)</div>';
      sub.rows.forEach((row, r) => {
        h += '<div class="rune-row">';
        row.forEach(p => {
          h += '<img class="rperk' + (p.id === runeSel.secondary[r] ? " sel" : "") + '" src="' + p.icon +
            '" title="' + p.name + '" onerror="this.style.visibility=\\'hidden\\'" onclick="pickSecondary(' + r + ',' + p.id + ')">';
        });
        h += '</div>';
      });
    }
  }

  if (runeData.shards.length) {
    h += '<div class="rune-sec-title">Fragmentos</div>';
    runeData.shards.forEach((row, r) => {
      h += '<div class="rune-row">';
      row.forEach(p => {
        h += '<img class="rperk shard' + (p.id === runeSel.shards[r] ? " sel" : "") + '" src="' + p.icon +
          '" title="' + p.name + '" onerror="this.style.visibility=\\'hidden\\'" onclick="pickShard(' + r + ',' + p.id + ')">';
      });
      h += '</div>';
    });
  }

  const valid = runeValid();
  h += '<button class="applybtn" id="applybtn" ' + (valid ? "" : "disabled") + ' onclick="applyRunes()">APLICAR RUNA</button>';
  h += '<div class="saverow"><input id="rune-save-name" placeholder="nome da nova pagina"><button class="savebtn" onclick="saveRunePage()">Salvar</button></div>';
  ed.innerHTML = h;
}

async function saveRunePage() {
  if (!runeValid()) { alert("Monte a runa completa antes de salvar."); return; }
  const name = (document.getElementById("rune-save-name").value || "").trim();
  if (!name) { alert("Digite um nome para a pagina."); return; }
  try {
    const j = await (await fetch("/rune-save", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, primaryStyleId: runeSel.primary, subStyleId: runeSel.sub, selectedPerkIds: buildPerkIds() })
    })).json();
    alert(j.ok ? "Pagina '" + name + "' salva!" : "Falha ao salvar.");
  } catch (e) { alert("Erro ao salvar."); }
}

function pickPrimary(id) {
  if (runeSel.primary === id) return;
  runeSel.primary = id;
  runeSel.keystone = null; runeSel.minors = [null, null, null];
  if (runeSel.sub === id) { runeSel.sub = null; runeSel.secondary = [null, null, null]; }
  renderRuneEditor();
}
function pickKeystone(id) { runeSel.keystone = id; renderRuneEditor(); }
function pickMinor(r, id) { runeSel.minors[r] = id; renderRuneEditor(); }
function pickSub(id) {
  if (runeSel.sub === id) return;
  runeSel.sub = id; runeSel.secondary = [null, null, null];
  renderRuneEditor();
}
function pickSecondary(r, id) {
  if (runeSel.secondary[r] === id) { runeSel.secondary[r] = null; renderRuneEditor(); return; }
  const count = runeSel.secondary.filter(x => x !== null).length;
  if (runeSel.secondary[r] === null && count >= 2) return; // ja tem 2
  runeSel.secondary[r] = id;
  renderRuneEditor();
}
function pickShard(r, id) { runeSel.shards[r] = id; renderRuneEditor(); }

function runeValid() {
  const s = runeSel;
  return s.primary && s.keystone && s.minors.every(x => x) &&
    s.sub && s.secondary.filter(x => x !== null).length === 2 &&
    s.shards.every(x => x);
}

function buildPerkIds() {
  const s = runeSel;
  const sec = [];
  s.secondary.forEach(x => { if (x !== null) sec.push(x); });
  return [s.keystone, s.minors[0], s.minors[1], s.minors[2], sec[0], sec[1], s.shards[0], s.shards[1], s.shards[2]];
}

async function applyRunes() {
  if (!runeValid()) return;
  const btn = document.getElementById("applybtn");
  btn.textContent = "APLICANDO...";
  try {
    const j = await (await fetch("/rune-apply", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ primaryStyleId: runeSel.primary, subStyleId: runeSel.sub, selectedPerkIds: buildPerkIds() })
    })).json();
    btn.textContent = j.ok ? "RUNA APLICADA!" : "FALHOU";
  } catch (e) { btn.textContent = "ERRO"; }
  setTimeout(() => { const b = document.getElementById("applybtn"); if (b) b.textContent = "APLICAR RUNA"; }, 1800);
}

// ---- Painel ao vivo ----
let lastLiveLoad = 0;
async function loadLive() {
  const now = Date.now();
  if (now - lastLiveLoad < 2000) return;
  lastLiveLoad = now;
  try {
    const d = await (await fetch("/live")).json();
    const live = document.getElementById("live");
    if (!d.in_game) { live.innerHTML = '<div class="loading">carregando dados da partida...</div>'; return; }
    const mins = Math.floor(d.game_time / 60), secs = d.game_time % 60;
    const order = {};
    const teams = { ORDER: [], CHAOS: [] };
    d.players.forEach(p => { (teams[p.team] || (teams[p.team] = [])).push(p); });
    const teamHtml = (arr, cls, title) =>
      '<div class="lteam ' + cls + '"><h4>' + title + '</h4>' +
      arr.map(p =>
        '<div class="lprow"><span class="lc">' + (p.champion || p.name || "?") + '</span>' +
        '<span class="lk">' + p.k + '/' + p.d + '/' + p.a + '</span>' +
        '<span class="lcs">' + p.cs + ' cs</span></div>'
      ).join("") + '</div>';
    live.innerHTML =
      '<div class="gt">' + mins + ':' + String(secs).padStart(2, "0") + '</div>' +
      teamHtml(teams.ORDER || [], "ally", "Time Azul") +
      teamHtml(teams.CHAOS || [], "enemy", "Time Vermelho");
  } catch (e) {
    document.getElementById("live").innerHTML = '<div class="loading">sem dados ao vivo (ative a API no jogo)</div>';
  }
}

// ---- Elo + historico (tela ociosa) ----
let lastIdleLoad = 0;
async function loadIdleExtra() {
  const now = Date.now();
  if (now - lastIdleLoad < 20000) return;
  lastIdleLoad = now;
  const el = document.getElementById("idle-extra");
  try {
    const [rk, hist] = await Promise.all([
      (await fetch("/rank")).json(),
      (await fetch("/history")).json(),
    ]);
    let h = "";
    const card = (q, lbl) => q ?
      '<div class="rank-card"><div class="q">' + lbl + '</div><div class="t">' + q.tier + '</div>' +
      '<div class="wl">' + q.lp + ' PDL &middot; ' + q.wins + 'V/' + q.losses + 'D</div></div>' : "";
    if (rk.solo || rk.flex) h += '<div class="rank-box">' + card(rk.solo, "Solo/Duo") + card(rk.flex, "Flex") + '</div>';
    if (Array.isArray(hist) && hist.length) {
      h += '<div class="hist"><div class="htitle">Ultimas partidas</div>' +
        hist.map(g => {
          const m = Math.floor((g.duration || 0) / 60);
          return '<div class="hrow ' + (g.win ? "win" : "loss") + '">' +
            '<img src="' + champIcon(g.champion_id) + '" onerror="this.style.visibility=\\'hidden\\'">' +
            '<span class="hc">' + (g.champion || "?") + '</span>' +
            '<span class="hkda">' + g.k + '/' + g.d + '/' + g.a + '</span>' +
            '<span class="hres">' + (g.win ? "VITORIA" : "DERROTA") + '</span></div>';
        }).join("") + '</div>';
    }
    el.innerHTML = h || '<div class="muted">aguardando fila</div>';
  } catch (e) {
    el.innerHTML = "";
  }
}

// ---- Config auto-pick/ban ----
let champListCache = null;
async function toggleConfig() {
  const panel = document.getElementById("cfg-panel");
  if (panel.style.display === "none") {
    panel.style.display = "block";
    if (!champListCache) champListCache = await (await fetch("/champ-list")).json();
    const cfg = await (await fetch("/config")).json();
    renderConfig(cfg);
  } else {
    panel.style.display = "none";
  }
}

function champOptions(selected) {
  return '<option value="">-- nenhum --</option>' +
    champListCache.map(c => '<option value="' + c.id + '"' + (c.id === selected ? " selected" : "") + '>' + c.name + '</option>').join("");
}

function renderConfig(cfg) {
  const panel = document.getElementById("cfg-panel");
  panel.innerHTML =
    '<div class="cfg-row"><label>Auto-pick</label>' +
      '<label class="switch"><input type="checkbox" id="cfg-pick-on" ' + (cfg.auto_pick_enabled ? "checked" : "") + ' onchange="saveConfig()"><span class="slider"></span></label></div>' +
    '<div class="cfg-row"><label>Campeao</label><select id="cfg-pick-champ" onchange="saveConfig()">' + champOptions(cfg.auto_pick_champ) + '</select></div>' +
    '<div class="cfg-row"><label>Auto-ban</label>' +
      '<label class="switch"><input type="checkbox" id="cfg-ban-on" ' + (cfg.auto_ban_enabled ? "checked" : "") + ' onchange="saveConfig()"><span class="slider"></span></label></div>' +
    '<div class="cfg-row"><label>Campeao</label><select id="cfg-ban-champ" onchange="saveConfig()">' + champOptions(cfg.auto_ban_champ) + '</select></div>' +
    '<div class="muted" style="font-size:11px;margin-top:6px">Trava automaticamente na sua vez. O alarme/aceitar continua valendo.</div>';
}

async function saveConfig() {
  const body = {
    auto_pick_enabled: document.getElementById("cfg-pick-on").checked,
    auto_ban_enabled: document.getElementById("cfg-ban-on").checked,
    auto_pick_champ: document.getElementById("cfg-pick-champ").value || null,
    auto_ban_champ: document.getElementById("cfg-ban-champ").value || null,
  };
  try { await fetch("/config", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }); } catch (e) {}
}

async function tick() {
  try {
    const r = await fetch("/status");
    const s = await r.json();

    document.getElementById("conn").textContent = s.connected ? "cliente conectado" : "cliente do LoL fechado";
    document.getElementById("conn-dot").className = "dot " + (s.connected ? "on" : "off");

    const phaseEl = document.getElementById("phase");
    phaseEl.textContent = PHASE_PT[s.phase] || (s.phase || "--");

    const btn = document.getElementById("accept");
    const decl = document.getElementById("declinebtn");
    const content = document.getElementById("content");
    const champ = document.getElementById("champ");
    const live = document.getElementById("live");
    const card = document.getElementById("card");
    const queue = document.getElementById("queue");
    const label = document.getElementById("queue-label");
    const leave = document.getElementById("leavebtn");
    const idleExtra = document.getElementById("idle-extra");

    const hideAll = () => {
      btn.style.display = "none";
      decl.style.display = "none";
      content.style.display = "none";
      champ.style.display = "none";
      live.style.display = "none";
    };

    if (s.ready_check && s.player_response === "None") {
      hideAll();
      resetChampLayout();
      card.classList.remove("wide");
      btn.style.display = "block";
      decl.style.display = "block";
      phaseEl.classList.add("flash");
      if (!accepting) btn.textContent = "ACEITAR";
      startAlarm();
    } else if (s.phase === "ChampSelect" && s.champ_select) {
      stopAlarm();
      hideAll();
      card.classList.add("wide");
      champ.style.display = "block";
      ensureChampLayout();
      document.getElementById("champ-info").innerHTML = renderChamp(s.champ_select);
      loadChampControls(s.champ_select);
      phaseEl.classList.remove("flash");
    } else if (s.phase === "InProgress") {
      stopAlarm();
      hideAll();
      card.classList.add("wide");
      live.style.display = "block";
      loadLive();
      phaseEl.classList.remove("flash");
    } else if (s.player_response === "Accepted") {
      stopAlarm();
      hideAll();
      resetChampLayout();
      card.classList.remove("wide");
      content.style.display = "block";
      leave.style.display = "none";
      idleExtra.innerHTML = "";
      phaseEl.classList.remove("flash");
      queue.textContent = "OK";
      label.textContent = "partida aceita";
    } else {
      stopAlarm();
      hideAll();
      resetChampLayout();
      card.classList.remove("wide");
      content.style.display = "block";
      phaseEl.classList.remove("flash");
      if (s.phase === "Matchmaking") {
        queue.textContent = fmt(s.time_in_queue);
        label.textContent = "tempo de fila";
        leave.style.display = "block";
        idleExtra.innerHTML = "";
      } else {
        queue.style.display = "none";
        label.style.display = "none";
        leave.style.display = "none";
        loadIdleExtra();
      }
    }
    if (s.phase === "Matchmaking" || s.ready_check) {
      queue.style.display = ""; label.style.display = "";
    }
    document.getElementById("foot").textContent = s.last_action || "";
  } catch (e) {
    document.getElementById("conn").textContent = "servidor offline";
    document.getElementById("conn-dot").className = "dot off";
  }
}

setInterval(tick, 700);
tick();
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(PAGE)


@app.route("/status")
def status():
    return jsonify(monitor.snapshot())


@app.route("/accept", methods=["POST"])
def accept():
    ok = monitor.client.accept_match()
    monitor.set_last_action("Aceito pelo celular" if ok else "Falha ao aceitar")
    return jsonify({"ok": ok})


@app.route("/decline", methods=["POST"])
def decline():
    ok = monitor.client.decline_match()
    monitor.set_last_action("Recusado pelo celular" if ok else "Falha ao recusar")
    return jsonify({"ok": ok})


@app.route("/champ-options")
def champ_options():
    """Lista de campeoes disponiveis para a acao atual (pick ou ban)."""
    client = monitor.client
    client.load_champion_data()
    action = client.local_action()
    atype = action.get("type")
    all_ids = [cid for cid in client.champ_map.keys() if cid and cid > 0]
    if atype == "ban":
        ids = client.get_bannable_champion_ids() or all_ids
    elif atype == "pick":
        ids = client.get_pickable_champion_ids() or all_ids
    else:
        ids = []
    champs = sorted(
        ({"id": int(i), "name": client.champ_name(i) or str(i)} for i in ids),
        key=lambda c: c["name"],
    )
    return jsonify({"type": atype, "action_id": action.get("id"), "champions": champs})


@app.route("/champ-action", methods=["POST"])
def champ_action():
    """Da hover (complete=false) ou trava/bane (complete=true) o campeao."""
    data = request.get_json(force=True, silent=True) or {}
    champion_id = data.get("championId")
    complete = bool(data.get("complete"))
    if champion_id is None:
        return jsonify({"ok": False, "error": "championId ausente"})
    action = monitor.client.local_action()
    if not action.get("id"):
        return jsonify({"ok": False, "error": "nao e sua vez"})
    ok = monitor.client.patch_action(action["id"], int(champion_id), complete)
    if ok and complete:
        verb = "Banido" if action.get("type") == "ban" else "Pick travado"
        monitor.set_last_action(f"{verb} pelo celular")
    return jsonify({"ok": ok})


@app.route("/runes")
def runes():
    pages = monitor.client.get_rune_pages()
    out = []
    for p in pages:
        if not p.get("name"):
            continue
        if p.get("isValid") is False:
            continue
        out.append({
            "id": p.get("id"),
            "name": p.get("name"),
            "current": bool(p.get("current") or p.get("isActive")),
        })
    return jsonify(out)


@app.route("/runes/select", methods=["POST"])
def runes_select():
    data = request.get_json(force=True, silent=True) or {}
    page_id = data.get("id")
    if page_id is None:
        return jsonify({"ok": False, "error": "id ausente"})
    ok = monitor.client.set_current_rune_page(int(page_id))
    monitor.set_last_action("Runa trocada pelo celular" if ok else "Falha ao trocar runa")
    return jsonify({"ok": ok})


def _perk_icon(icon_path: str) -> str:
    """Converte iconPath da LCU em URL publica (CommunityDragon)."""
    if not icon_path:
        return ""
    p = icon_path.lower().lstrip("/").replace("lol-game-data/assets/", "")
    return "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/" + p


@app.route("/rune-data")
def rune_data():
    """Estrutura completa para montar runa: arvores, runas e fragmentos."""
    client = monitor.client
    styles = client.get_perk_styles()
    perks = client.get_perks()
    perk_map = {
        int(p["id"]): {"id": int(p["id"]), "name": p.get("name", "?"), "icon": _perk_icon(p.get("iconPath", ""))}
        for p in perks if "id" in p
    }

    def perk(pid):
        return perk_map.get(int(pid), {"id": int(pid), "name": str(pid), "icon": ""})

    out_styles = []
    shards = None
    for st in styles:
        slots = st.get("slots", []) or []
        keystones, rows, stat_rows = [], [], []
        for slot in slots:
            stype = slot.get("type")
            ids = slot.get("perks", []) or []
            if stype == "kKeyStone":
                keystones = [perk(i) for i in ids]
            elif stype == "kStatMod":
                stat_rows.append([perk(i) for i in ids])
            else:  # kMixedRegularSplashable -> runas menores
                rows.append([perk(i) for i in ids])
        out_styles.append({
            "id": st.get("id"),
            "name": st.get("name"),
            "icon": _perk_icon(st.get("iconPath", "")),
            "allowedSubStyles": st.get("allowedSubStyles", []),
            "keystones": keystones,
            "rows": rows,
        })
        if shards is None and stat_rows:
            shards = stat_rows

    cur = client.get_current_rune_page() or {}
    current = {
        "primaryStyleId": cur.get("primaryStyleId"),
        "subStyleId": cur.get("subStyleId"),
        "selectedPerkIds": cur.get("selectedPerkIds", []),
    }
    return jsonify({"styles": out_styles, "shards": shards or [], "current": current})


@app.route("/rune-apply", methods=["POST"])
def rune_apply():
    data = request.get_json(force=True, silent=True) or {}
    primary = data.get("primaryStyleId")
    sub = data.get("subStyleId")
    perks = data.get("selectedPerkIds")
    if not primary or not sub or not perks or len(perks) != 9:
        return jsonify({"ok": False, "error": "dados de runa incompletos"})
    ok = monitor.client.apply_runes(primary, sub, perks)
    monitor.set_last_action("Runa montada pelo celular" if ok else "Falha ao montar runa")
    return jsonify({"ok": ok})


@app.route("/rune-save", methods=["POST"])
def rune_save():
    data = request.get_json(force=True, silent=True) or {}
    name = (data.get("name") or "").strip()
    primary = data.get("primaryStyleId")
    sub = data.get("subStyleId")
    perks = data.get("selectedPerkIds")
    if not name or not primary or not sub or not perks or len(perks) != 9:
        return jsonify({"ok": False, "error": "dados incompletos"})
    ok = monitor.client.save_rune_page(name, primary, sub, perks)
    monitor.set_last_action(f"Runa '{name}' salva" if ok else "Falha ao salvar runa")
    return jsonify({"ok": ok})


@app.route("/leave-queue", methods=["POST"])
def leave_queue():
    ok = monitor.client.cancel_matchmaking()
    monitor.set_last_action("Saiu da fila pelo celular" if ok else "Falha ao sair da fila")
    return jsonify({"ok": ok})


@app.route("/rank")
def rank():
    stats = monitor.client.get_ranked_stats() or {}
    qmap = stats.get("queueMap", {}) or {}

    def fmt_q(q):
        if not q:
            return None
        tier = q.get("tier") or ""
        if not tier or tier == "NONE":
            return {"tier": "Unranked", "lp": 0, "wins": 0, "losses": 0}
        return {
            "tier": (tier.capitalize() + " " + (q.get("division") or "")).strip(),
            "lp": q.get("leaguePoints", 0),
            "wins": q.get("wins", 0),
            "losses": q.get("losses", 0),
        }

    return jsonify({
        "solo": fmt_q(qmap.get("RANKED_SOLO_5x5")),
        "flex": fmt_q(qmap.get("RANKED_FLEX_SR")),
    })


@app.route("/history")
def history():
    client = monitor.client
    client.load_champion_data()
    me = client.get_current_summoner() or {}
    my_puuid = me.get("puuid")
    data = client.get_match_history(10) or {}
    games = (data.get("games") or {}).get("games", []) or []
    out = []
    for g in games:
        my_pid = None
        for idt in g.get("participantIdentities", []) or []:
            if idt.get("player", {}).get("puuid") == my_puuid:
                my_pid = idt.get("participantId")
                break
        part = None
        for pt in g.get("participants", []) or []:
            if pt.get("participantId") == my_pid:
                part = pt
                break
        if not part:
            continue
        st = part.get("stats", {}) or {}
        out.append({
            "win": bool(st.get("win")),
            "champion_id": part.get("championId"),
            "champion": client.champ_name(part.get("championId")),
            "k": st.get("kills", 0),
            "d": st.get("deaths", 0),
            "a": st.get("assists", 0),
            "duration": g.get("gameDuration", 0),
            "queue": g.get("queueId"),
        })
    return jsonify(out)


@app.route("/live")
def live():
    data = monitor.client.get_live_game()
    if not data:
        return jsonify({"in_game": False})
    game = data.get("gameData", {}) or {}
    players = []
    for p in data.get("allPlayers", []) or []:
        sc = p.get("scores", {}) or {}
        players.append({
            "name": p.get("riotIdGameName") or p.get("summonerName"),
            "champion": p.get("championName"),
            "team": p.get("team"),
            "k": sc.get("kills", 0),
            "d": sc.get("deaths", 0),
            "a": sc.get("assists", 0),
            "cs": sc.get("creepScore", 0),
            "level": p.get("level", 0),
        })
    return jsonify({
        "in_game": True,
        "game_time": int(game.get("gameTime", 0) or 0),
        "mode": game.get("gameMode"),
        "players": players,
    })


@app.route("/champ-list")
def champ_list():
    client = monitor.client
    client.load_champion_data()
    champs = sorted(
        ({"id": cid, "name": name} for cid, name in client.champ_map.items() if cid and cid > 0),
        key=lambda c: c["name"],
    )
    return jsonify(champs)


@app.route("/config", methods=["GET", "POST"])
def config():
    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        for key in ("auto_pick_enabled", "auto_ban_enabled"):
            if key in data:
                monitor.config[key] = bool(data[key])
        for key in ("auto_pick_champ", "auto_ban_champ"):
            if key in data:
                val = data[key]
                monitor.config[key] = int(val) if val else None
        monitor.set_last_action("Config de auto-pick/ban atualizada")
    return jsonify(monitor.config)


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def main():
    global monitor
    client = LCUClient()
    monitor = Monitor(client)

    t = threading.Thread(target=monitor.run, daemon=True)
    t.start()

    ip = get_local_ip()
    print("=" * 60)
    print(" LoL Queue Remote Accept")
    print("=" * 60)
    print(f" No celular (mesma Wi-Fi), abra:  http://{ip}:{WEB_PORT}")
    print(f" Neste PC, abra:                  http://127.0.0.1:{WEB_PORT}")
    if AUTO_ACCEPT_FALLBACK_SECONDS is not None:
        print(f" Auto-accept de fallback: ligado (~{AUTO_ACCEPT_FALLBACK_SECONDS}s antes do fim)")
    else:
        print(" Auto-accept de fallback: desligado")
    print(" Deixe o cliente do LoL aberto. Ctrl+C para sair.")
    print("=" * 60)

    # threaded=True para atender celular + polling ao mesmo tempo
    app.run(host="0.0.0.0", port=WEB_PORT, threaded=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nEncerrado.")
        sys.exit(0)
