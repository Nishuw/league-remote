"""Aplicacao Flask: rotas da API e pagina web.

Usa o padrao app factory (`create_app`) recebendo o `Monitor` por injecao,
evitando estado global e facilitando testes.
"""

from flask import Flask, jsonify, render_template, request

from .monitor import Monitor


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

    # ------------------------------------------------------------------
    # Pagina
    # ------------------------------------------------------------------

    @app.route("/")
    def index():
        return render_template("index.html")

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
    # Champ select
    # ------------------------------------------------------------------

    @app.route("/champ-options")
    def champ_options():
        """Lista de campeoes disponiveis para a acao atual (pick ou ban)."""
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
        action = client.local_action()
        if not action.get("id"):
            return jsonify({"ok": False, "error": "nao e sua vez"})
        ok = client.patch_action(action["id"], int(champion_id), complete)
        if ok and complete:
            verb = "Banido" if action.get("type") == "ban" else "Pick travado"
            monitor.set_last_action(f"{verb} pelo celular")
        return jsonify({"ok": ok})

    @app.route("/aram/reroll", methods=["POST"])
    def aram_reroll():
        ok = client.reroll()
        monitor.set_last_action("Reroll pelo celular" if ok else "Falha no reroll")
        return jsonify({"ok": ok})

    @app.route("/aram/swap", methods=["POST"])
    def aram_swap():
        data = request.get_json(force=True, silent=True) or {}
        champion_id = data.get("championId")
        if champion_id is None:
            return jsonify({"ok": False, "error": "championId ausente"})
        ok = client.bench_swap(int(champion_id))
        monitor.set_last_action(
            f"Trocou pelo banco: {client.champ_name(int(champion_id)) or champion_id}"
            if ok else "Falha ao trocar pelo banco"
        )
        return jsonify({"ok": ok})

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

    @app.route("/live")
    def live():
        data = client.get_live_game()
        if not data:
            return jsonify({"in_game": False})
        game = data.get("gameData", {}) or {}
        client.load_champion_data()
        name_to_id = {v: k for k, v in client.champ_map.items()}

        champ_team = {}
        players = []
        team_kills = {"ORDER": 0, "CHAOS": 0}
        for p in data.get("allPlayers", []) or []:
            sc = p.get("scores", {}) or {}
            team = p.get("team")
            cname = p.get("championName")
            champ_team[cname] = team
            if team in team_kills:
                team_kills[team] += int(sc.get("kills", 0) or 0)
            players.append({
                "name": p.get("riotIdGameName") or p.get("summonerName"),
                "champion": cname,
                "champion_id": name_to_id.get(cname),
                "team": team,
                "k": sc.get("kills", 0),
                "d": sc.get("deaths", 0),
                "a": sc.get("assists", 0),
                "cs": sc.get("creepScore", 0),
                "wards": sc.get("wardScore", 0),
                "level": p.get("level", 0),
                "dead": bool(p.get("isDead")),
                "respawn": int(p.get("respawnTimer", 0) or 0),
                "position": (p.get("position") or "").lower(),
            })

        # Objetivos e feed a partir dos eventos da partida
        objectives = {
            "ORDER": {"towers": 0, "dragons": 0, "barons": 0, "heralds": 0, "inhibs": 0},
            "CHAOS": {"towers": 0, "dragons": 0, "barons": 0, "heralds": 0, "inhibs": 0},
        }
        feed = []
        for ev in (data.get("events", {}) or {}).get("Events", []) or []:
            name = ev.get("EventName")
            killer = ev.get("KillerName")
            t = int(ev.get("EventTime", 0) or 0)
            if name == "TurretKilled":
                tk = ev.get("TurretKilled", "")
                if "_T1_" in tk:
                    objectives["CHAOS"]["towers"] += 1
                elif "_T2_" in tk:
                    objectives["ORDER"]["towers"] += 1
            elif name == "InhibKilled":
                ik = ev.get("InhibKilled", "")
                if "_T1_" in ik:
                    objectives["CHAOS"]["inhibs"] += 1
                elif "_T2_" in ik:
                    objectives["ORDER"]["inhibs"] += 1
            elif name == "DragonKill":
                team = champ_team.get(killer)
                if team in objectives:
                    objectives[team]["dragons"] += 1
                dt = ev.get("DragonType")
                feed.append({"t": t, "txt": f"{killer or '?'} matou o Dragao" + (f" {dt}" if dt else "")})
            elif name == "HeraldKill":
                team = champ_team.get(killer)
                if team in objectives:
                    objectives[team]["heralds"] += 1
                feed.append({"t": t, "txt": f"{killer or '?'} matou o Arauto"})
            elif name == "BaronKill":
                team = champ_team.get(killer)
                if team in objectives:
                    objectives[team]["barons"] += 1
                feed.append({"t": t, "txt": f"{killer or '?'} matou o Barao"})
            elif name == "FirstBlood":
                feed.append({"t": t, "txt": "Primeiro abate (First Blood)"})
            elif name == "Ace":
                feed.append({"t": t, "txt": "ACE!"})

        active = data.get("activePlayer", {}) or {}
        gold = active.get("currentGold") if isinstance(active, dict) else None

        return jsonify({
            "in_game": True,
            "game_time": int(game.get("gameTime", 0) or 0),
            "mode": game.get("gameMode"),
            "map": game.get("mapName"),
            "team_kills": team_kills,
            "objectives": objectives,
            "your_gold": int(gold) if isinstance(gold, (int, float)) else None,
            "feed": feed[-6:],
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
