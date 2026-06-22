"""Aplicacao Flask: rotas da API e pagina web.

Usa o padrao app factory (`create_app`) recebendo o `Monitor` por injecao,
evitando estado global e facilitando testes.
"""

import time

from flask import Flask, jsonify, render_template, request

from . import __version__
from .monitor import Monitor

# Muda a cada inicializacao do servidor; usado para invalidar o cache do
# navegador nos arquivos estaticos (CSS/JS).
_ASSET_VERSION = f"{__version__}-{int(time.time())}"


def _perk_icon(icon_path: str) -> str:
    """Converte iconPath da LCU em URL publica (CommunityDragon)."""
    if not icon_path:
        return ""
    p = icon_path.lower().lstrip("/").replace("lol-game-data/assets/", "")
    return "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/" + p


def create_app(monitor: Monitor) -> Flask:
    """Cria e configura a aplicacao Flask para o monitor informado."""
    app = Flask(__name__)
    client = monitor.client

    # Nao deixa o navegador cachear arquivos estaticos (CSS/JS): assim, ao
    # reiniciar o servidor, o celular sempre pega a versao nova.
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

    @app.after_request
    def _no_cache(resp):
        if request.path.startswith("/static/"):
            resp.headers["Cache-Control"] = "no-store, max-age=0"
        return resp

    # ------------------------------------------------------------------
    # Pagina
    # ------------------------------------------------------------------

    @app.route("/")
    def index():
        return render_template("index.html", v=_ASSET_VERSION)

    # ------------------------------------------------------------------
    # Estado / fila
    # ------------------------------------------------------------------

    @app.route("/status")
    def status():
        return jsonify(monitor.snapshot())

    @app.route("/accept", methods=["POST"])
    def accept():
        ok = client.accept_match()
        monitor.set_last_action("Aceito pelo celular" if ok else "Falha ao aceitar")
        return jsonify({"ok": ok})

    @app.route("/decline", methods=["POST"])
    def decline():
        ok = client.decline_match()
        monitor.set_last_action("Recusado pelo celular" if ok else "Falha ao recusar")
        return jsonify({"ok": ok})

    @app.route("/leave-queue", methods=["POST"])
    def leave_queue():
        ok = client.cancel_matchmaking()
        monitor.set_last_action("Saiu da fila pelo celular" if ok else "Falha ao sair da fila")
        return jsonify({"ok": ok})

    # ------------------------------------------------------------------
    # Lobby / iniciar fila pelo celular
    # ------------------------------------------------------------------

    @app.route("/lobby", methods=["GET"])
    def lobby_get():
        """Resumo do lobby atual (ou in_lobby=False se nao houver)."""
        lob = client.get_lobby()
        if not isinstance(lob, dict):
            return jsonify({"in_lobby": False})
        gc = lob.get("gameConfig") or {}
        return jsonify({
            "in_lobby": True,
            "queue_id": gc.get("queueId"),
            "can_start": bool(lob.get("canStartActivity")),
            "members": len(lob.get("members") or []),
        })

    @app.route("/lobby", methods=["POST"])
    def lobby_create():
        """Cria um lobby para a fila informada (queueId)."""
        data = request.get_json(force=True, silent=True) or {}
        qid = data.get("queueId")
        if qid is None:
            return jsonify({"ok": False, "error": "queueId ausente"})
        ok = client.create_lobby(int(qid))
        monitor.set_last_action(
            f"Lobby criado (fila {qid}) pelo celular" if ok else "Falha ao criar lobby"
        )
        return jsonify({"ok": ok})

    @app.route("/lobby", methods=["DELETE"])
    def lobby_leave():
        ok = client.leave_lobby()
        monitor.set_last_action("Saiu do lobby pelo celular" if ok else "Falha ao sair do lobby")
        return jsonify({"ok": ok})

    @app.route("/queue/start", methods=["POST"])
    def queue_start():
        """Inicia a busca por partida (Encontrar Partida)."""
        ok = client.start_matchmaking()
        monitor.set_last_action("Fila iniciada pelo celular" if ok else "Falha ao iniciar a fila")
        return jsonify({"ok": ok})

    @app.route("/leave", methods=["POST"])
    def leave():
        """Sair de forma ciente da fase: cancela a fila ou da dodge no champ select."""
        phase = monitor.snapshot().get("phase") or client.get_gameflow_phase()
        if phase == "ChampSelect":
            ok = client.dodge_champ_select()
            msg = "Dodge do champ select pelo celular" if ok else "Falha ao sair do champ select"
        else:
            ok = client.cancel_matchmaking()
            msg = "Saiu da fila pelo celular" if ok else "Falha ao sair da fila"
        monitor.set_last_action(msg)
        return jsonify({"ok": ok})

    # ------------------------------------------------------------------
    # Champ select
    # ------------------------------------------------------------------

    @app.route("/champ-options")
    def champ_options():
        """Lista de campeoes disponiveis para a acao atual (pick ou ban)."""
        client.load_champion_data()
        session = client.get_champ_select_session() or {}
        is_bench = bool(session.get("benchEnabled"))
        action = client.local_action()
        atype = action.get("type")
        all_ids = [cid for cid in client.champ_map.keys() if cid and cid > 0]
        if atype == "ban":
            ids = client.get_bannable_champion_ids() or all_ids
        elif atype == "pick":
            pickable = client.get_pickable_champion_ids()
            # No ARAM (modo banco) so pode escolher o subconjunto oferecido;
            # nao cai no fallback de "todos os campeoes". No draft normal sim.
            ids = pickable if (is_bench or pickable) else all_ids
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
        action = client.local_action()
        if not action.get("id"):
            return jsonify({"ok": False, "error": "nao e sua vez"})
        ok = client.patch_action(action["id"], int(champion_id), complete)
        if ok and complete:
            verb = "Banido" if action.get("type") == "ban" else "Pick travado"
            monitor.set_last_action(f"{verb} pelo celular")
        return jsonify({"ok": ok})

    @app.route("/debug/champ-select")
    def debug_champ_select():
        """Dump cru de varios endpoints do champ select.

        Serve para diagnosticar ARAM/Desordem: abra esta rota no momento exato
        em que os campeoes aparecem para escolher, para descobrir em qual campo
        a LCU expoe as opcoes.
        """
        session = client.get_champ_select_session()
        bench = session.get("benchChampions") if isinstance(session, dict) else None
        # Tenta varios endpoints relacionados; os que nao existirem viram null.
        extra = {
            ep: client._get(ep)
            for ep in (
                "/lol-champ-select/v1/pickable-champion-ids",
                "/lol-champ-select/v1/bannable-champion-ids",
                "/lol-champ-select/v1/session/my-selection",
                "/lol-champ-select/v1/all-grid-champions",
                "/lol-champ-select/v1/disabled-champion-ids",
                # Escolha inicial do ARAM/Desordem (subset pessoal de 2-3 champs).
                "/lol-lobby-team-builder/champ-select/v1/subset-champion-list",
                "/lol-champ-select-legacy/v1/session",
            )
        }
        return jsonify({
            "connected": client.base_url is not None,
            "champ_select_keys": sorted(session.keys()) if isinstance(session, dict) else None,
            "benchEnabled": session.get("benchEnabled") if isinstance(session, dict) else None,
            "benchChampions": bench,
            "local_action": client.local_action(),
            "champ_select": session,
            "endpoints": extra,
            "gameflow": client.get_gameflow_session(),
        })

    # ------------------------------------------------------------------
    # Feiticos de invocador + skin (champ select)
    # ------------------------------------------------------------------

    # Feiticos permitidos no ARAM (Flash e Snowball primeiro, depois os comuns).
    _ARAM_SPELLS = [4, 32, 7, 6, 21, 1, 3, 14, 13]

    @app.route("/champ-select/spells", methods=["GET"])
    def cs_spells_get():
        client.load_summoner_spells()
        session = client.get_champ_select_session() or {}
        local = session.get("localPlayerCellId")
        me = next((p for p in session.get("myTeam", []) or [] if p.get("cellId") == local), {})
        options = [
            {"id": sid, **(client.spell_map.get(sid) or {"name": str(sid), "icon": ""})}
            for sid in _ARAM_SPELLS
            if sid in client.spell_map
        ]
        return jsonify({
            "spell1Id": me.get("spell1Id"),
            "spell2Id": me.get("spell2Id"),
            "options": options,
        })

    @app.route("/champ-select/spells", methods=["POST"])
    def cs_spells_set():
        data = request.get_json(force=True, silent=True) or {}
        payload = {}
        if data.get("spell1Id") is not None:
            payload["spell1Id"] = int(data["spell1Id"])
        if data.get("spell2Id") is not None:
            payload["spell2Id"] = int(data["spell2Id"])
        if not payload:
            return jsonify({"ok": False, "error": "sem feiticos"})
        ok = client.set_my_selection(payload)
        monitor.set_last_action("Feiticos trocados pelo celular" if ok else "Falha ao trocar feiticos")
        return jsonify({"ok": ok})

    @app.route("/champ-select/skins", methods=["GET"])
    def cs_skins_get():
        session = client.get_champ_select_session() or {}
        local = session.get("localPlayerCellId")
        me = next((p for p in session.get("myTeam", []) or [] if p.get("cellId") == local), {})
        skins = []
        for sk in client.get_skin_carousel():
            if not isinstance(sk, dict) or sk.get("id") is None:
                continue
            owned = sk.get("unlocked")
            if owned is None:
                owned = (sk.get("ownership") or {}).get("owned", False)
            skins.append({
                "id": sk.get("id"),
                "name": sk.get("name") or "",
                "disabled": bool(sk.get("disabled")),
                "owned": bool(owned),
                "tile": client.asset_url(sk.get("tilePath")),
            })
        return jsonify({"selectedSkinId": me.get("selectedSkinId"), "skins": skins})

    @app.route("/champ-select/skin", methods=["POST"])
    def cs_skin_set():
        data = request.get_json(force=True, silent=True) or {}
        sid = data.get("skinId")
        if sid is None:
            return jsonify({"ok": False, "error": "skinId ausente"})
        ok = client.set_my_selection({"selectedSkinId": int(sid)})
        monitor.set_last_action("Skin trocada pelo celular" if ok else "Falha ao trocar skin")
        return jsonify({"ok": ok})

    @app.route("/aram/swap", methods=["POST"])
    def aram_swap():
        data = request.get_json(force=True, silent=True) or {}
        champion_id = data.get("championId")
        if champion_id is None:
            return jsonify({"ok": False, "error": "championId ausente"})
        cid = int(champion_id)
        # No ARAM/Desordem a chegada e um estado especial: voce NAO tem campeao
        # (championId 0) e ha uma acao de "pick" em progresso. Os campeoes
        # oferecidos vem em benchChampions, mas a escolha inicial precisa ser
        # COMPLETADA pela acao de pick -- o bench/swap so funciona depois que
        # voce ja tem um campeao para trocar. Por isso decidimos pelo estado:
        session = client.get_champ_select_session() or {}
        local_cell = session.get("localPlayerCellId")
        my_champ = 0
        for p in session.get("myTeam", []) or []:
            if p.get("cellId") == local_cell:
                my_champ = p.get("championId") or 0
                break
        action = client.local_action()
        initial_pick = (
            not my_champ
            and action.get("type") == "pick"
            and action.get("id") is not None
        )
        print(
            f"[aram] swap req champ={cid} local_cell={local_cell} "
            f"my_champ={my_champ} action={action} initial_pick={initial_pick}"
        )
        if initial_pick:
            # Escolha inicial: completa a acao de pick; se a LCU recusar, tenta
            # o bench/swap como alternativa (a prova de balas).
            ok = client.patch_action(action["id"], cid, True)
            if not ok:
                ok = client.bench_swap(cid)
        else:
            # Ja tem campeao: troca normal pelo banco.
            ok = client.bench_swap(cid)
            if not ok and action.get("id") is not None and action.get("type") == "pick":
                ok = client.patch_action(action["id"], cid, True)
        nome = client.champ_name(cid) or str(cid)
        if ok:
            msg = ("Travado: " if initial_pick else "Pego: ") + nome
        else:
            msg = f"Falhou ({client.last_status or '?'}) - {nome}"
        monitor.set_last_action(msg + " [celular]")
        return jsonify({"ok": ok, "status": client.last_status, "msg": msg})

    @app.route("/aram/trade", methods=["POST"])
    def aram_trade():
        data = request.get_json(force=True, silent=True) or {}
        trade_id = data.get("id")
        action = (data.get("action") or "").lower()
        if trade_id is None or action not in ("request", "accept", "decline"):
            return jsonify({"ok": False, "error": "parametros invalidos"})
        fn = {
            "request": client.trade_request,
            "accept": client.trade_accept,
            "decline": client.trade_decline,
        }[action]
        ok = fn(int(trade_id))
        labels = {"request": "Troca oferecida", "accept": "Troca aceita", "decline": "Troca recusada"}
        monitor.set_last_action(labels[action] if ok else "Falha na troca")
        return jsonify({"ok": ok})

    @app.route("/champ-list")
    def champ_list():
        client.load_champion_data()
        champs = sorted(
            ({"id": cid, "name": name} for cid, name in client.champ_map.items() if cid and cid > 0),
            key=lambda c: c["name"],
        )
        return jsonify(champs)

    # ------------------------------------------------------------------
    # Runas
    # ------------------------------------------------------------------

    @app.route("/runes")
    def runes():
        pages = client.get_rune_pages()
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
        ok = client.set_current_rune_page(int(page_id))
        monitor.set_last_action("Runa trocada pelo celular" if ok else "Falha ao trocar runa")
        return jsonify({"ok": ok})

    @app.route("/rune-data")
    def rune_data():
        """Estrutura completa para montar runa: arvores, runas e fragmentos."""
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
        ok = client.apply_runes(primary, sub, perks)
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
        ok = client.save_rune_page(name, primary, sub, perks)
        monitor.set_last_action(f"Runa '{name}' salva" if ok else "Falha ao salvar runa")
        return jsonify({"ok": ok})

    # ------------------------------------------------------------------
    # Elo / historico / partida ao vivo
    # ------------------------------------------------------------------

    @app.route("/rank")
    def rank():
        stats = client.get_ranked_stats() or {}
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

    # Traducao PT-BR dos tipos de dragao da Live API.
    _DRAGON_PT = {
        "Fire": "Infernal", "Earth": "Montanha", "Water": "Oceano",
        "Air": "Nuvem", "Hextech": "Hextech", "Chemtech": "Quimtech",
        "Elder": "Ancião",
    }

    @app.route("/live")
    def live():
        data = client.get_live_game()
        if not data:
            return jsonify({"in_game": False})
        game = data.get("gameData", {}) or {}
        client.load_champion_data()
        name_to_id = {v: k for k, v in client.champ_map.items()}
        game_time = int(game.get("gameTime", 0) or 0)
        minutes = max(game_time / 60.0, 1 / 60.0)  # evita divisao por zero
        mode = game.get("gameMode") or ""
        # Visao (sentinelas) so faz sentido no Rift (CLASSIC). No ARAM nao ha wards.
        show_vision = mode == "CLASSIC"

        # Identifica o jogador local pelo activePlayer (e "voce" no feed/lista).
        active = data.get("activePlayer", {}) or {}
        local_name = None
        if isinstance(active, dict):
            rid = active.get("riotId") or ""
            local_name = (
                active.get("riotIdGameName")
                or active.get("summonerName")
                or (rid.split("#")[0] if rid else None)
            )

        # Indice por nome (os eventos usam o nome do jogador, nao do campeao)
        # para resolver autor/vitima -> time, campeao, icone e se e "voce".
        pindex = {}
        players = []
        team_kills = {"ORDER": 0, "CHAOS": 0}
        for p in data.get("allPlayers", []) or []:
            sc = p.get("scores", {}) or {}
            team = p.get("team")
            cname = p.get("championName")
            cid = name_to_id.get(cname)
            gname = p.get("riotIdGameName") or p.get("summonerName")
            is_local = bool(local_name and gname == local_name)
            info = {"team": team, "champion": cname, "champion_id": cid, "is_local": is_local}
            for key in (p.get("riotIdGameName"), p.get("summonerName"), p.get("riotId"), cname):
                if key:
                    pindex[key] = info
            k = int(sc.get("kills", 0) or 0)
            d = int(sc.get("deaths", 0) or 0)
            a = int(sc.get("assists", 0) or 0)
            cs = int(sc.get("creepScore", 0) or 0)
            if team in team_kills:
                team_kills[team] += k
            players.append({
                "name": gname,
                "champion": cname,
                "champion_id": cid,
                "team": team,
                "is_local": is_local,
                "k": k, "d": d, "a": a,
                "kda": round((k + a) / d, 1) if d else (k + a),
                "cs": cs,
                "csmin": round(cs / minutes, 1),
                "vision": round(float(sc.get("wardScore", 0) or 0), 1),
                "level": int(p.get("level", 0) or 0),
                "dead": bool(p.get("isDead")),
                "respawn": int(p.get("respawnTimer", 0) or 0),
                "position": (p.get("position") or "").lower(),
            })

        def who(n):
            return pindex.get(n) or {}

        def label(n):
            """Rotulo do autor/vitima no feed: 'Você' para o jogador local."""
            w = who(n)
            if w.get("is_local"):
                return "Você"
            return w.get("champion") or n or "?"

        def actor(n):
            w = who(n)
            return {"name": label(n), "cid": w.get("champion_id"), "team": w.get("team"), "local": bool(w.get("is_local"))}

        # Objetivos e feed a partir dos eventos da partida.
        objectives = {
            "ORDER": {"towers": 0, "dragons": 0, "barons": 0, "heralds": 0, "grubs": 0, "inhibs": 0, "souls": []},
            "CHAOS": {"towers": 0, "dragons": 0, "barons": 0, "heralds": 0, "grubs": 0, "inhibs": 0, "souls": []},
        }
        multi_labels = {2: "Double Kill", 3: "Triple Kill", 4: "Quadra Kill", 5: "PENTA KILL"}
        feed = []
        for ev in (data.get("events", {}) or {}).get("Events", []) or []:
            name = ev.get("EventName")
            killer = ev.get("KillerName")
            ki = actor(killer)
            tm = ki.get("team")
            t = int(ev.get("EventTime", 0) or 0)
            base = {"t": t, "a": ki["name"], "a_cid": ki["cid"], "team": tm, "local": ki["local"]}

            if name == "ChampionKill":
                victim = ev.get("VictimName")
                vi = actor(victim)
                assists = ev.get("Assisters") or []
                feed.append({**base, "kind": "kill", "v": vi["name"], "v_cid": vi["cid"],
                             "note": f"+{len(assists)}" if assists else "",
                             "local": ki["local"] or vi["local"]})
            elif name == "Multikill":
                streak = int(ev.get("KillStreak", 0) or 0)
                feed.append({**base, "kind": "multi", "note": multi_labels.get(streak, f"{streak} Kills")})
            elif name == "FirstBlood":
                ri = actor(ev.get("Recipient"))
                feed.append({"t": t, "kind": "fb", "a": ri["name"], "a_cid": ri["cid"],
                             "team": ri["team"], "local": ri["local"], "note": "First Blood"})
            elif name == "TurretKilled":
                tk = ev.get("TurretKilled", "")
                ot = "CHAOS" if "_T1_" in tk else ("ORDER" if "_T2_" in tk else None)
                if ot:
                    objectives[ot]["towers"] += 1
            elif name == "InhibKilled":
                ik = ev.get("InhibKilled", "")
                ot = "CHAOS" if "_T1_" in ik else ("ORDER" if "_T2_" in ik else None)
                if ot:
                    objectives[ot]["inhibs"] += 1
            elif name == "DragonKill":
                dt = ev.get("DragonType")
                dt_pt = _DRAGON_PT.get(dt, dt or "")
                if tm in objectives:
                    objectives[tm]["dragons"] += 1
                    if dt and dt != "Elder":
                        objectives[tm]["souls"].append(dt_pt)
                stolen = " (roubado!)" if ev.get("Stolen") == "True" else ""
                feed.append({**base, "kind": "dragon", "note": f"Dragão {dt_pt}{stolen}".strip()})
            elif name == "HeraldKill":
                if tm in objectives:
                    objectives[tm]["heralds"] += 1
                stolen = " (roubado!)" if ev.get("Stolen") == "True" else ""
                feed.append({**base, "kind": "herald", "note": f"Arauto{stolen}"})
            elif name in ("HordeKill", "VoidgrubKill"):
                if tm in objectives:
                    objectives[tm]["grubs"] += 1
                feed.append({**base, "kind": "grub", "note": "Larva do Vazio"})
            elif name == "BaronKill":
                if tm in objectives:
                    objectives[tm]["barons"] += 1
                stolen = " (roubado!)" if ev.get("Stolen") == "True" else ""
                feed.append({**base, "kind": "baron", "note": f"Barão{stolen}"})
            elif name == "Ace":
                acer = actor(ev.get("Acer"))
                feed.append({"t": t, "kind": "ace", "a": acer["name"], "a_cid": acer["cid"],
                             "team": ev.get("AcingTeam"), "local": acer["local"], "note": "ACE!"})

        # A Live API normalmente ja vem em ordem cronologica, mas garantimos:
        # ordena por tempo e mantem os 24 eventos mais recentes.
        feed.sort(key=lambda e: e.get("t", 0))

        gold = active.get("currentGold") if isinstance(active, dict) else None
        active_level = active.get("level") if isinstance(active, dict) else None

        return jsonify({
            "in_game": True,
            "game_time": game_time,
            "mode": mode,
            "map": game.get("mapName"),
            "show_vision": show_vision,
            "team_kills": team_kills,
            "objectives": objectives,
            "your_gold": int(gold) if isinstance(gold, (int, float)) else None,
            "your_level": int(active_level) if isinstance(active_level, (int, float)) else None,
            "feed": feed[-24:],
            "players": players,
        })

    # ------------------------------------------------------------------
    # Config (auto-pick / auto-ban)
    # ------------------------------------------------------------------

    @app.route("/config", methods=["GET", "POST"])
    def config():
        if request.method == "POST":
            data = request.get_json(force=True, silent=True) or {}
            for key in ("auto_pick_enabled", "auto_ban_enabled", "ban_protect_allies"):
                if key in data:
                    monitor.config[key] = bool(data[key])
            for key in ("auto_pick_champs", "auto_ban_champs"):
                if key in data:
                    monitor.config[key] = Monitor._as_id_list(data[key])
            monitor.set_last_action("Config de auto-pick/ban atualizada")
        return jsonify(monitor.config)

    return app
