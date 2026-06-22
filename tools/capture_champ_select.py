"""Captura a sessao crua do champ select durante o ARAM/Desordem.

Roda em loop rapido (4x/s). No instante em que a fase vira ChampSelect,
comeca a gravar snapshots com timestamp de:
  - /lol-champ-select/v1/session (sessao completa)
  - benchChampions e os campos relacionados a "pick"
Salva tudo em tools/champ_select_dump.json para a gente analisar onde a LCU
expoe os campeoes da roleta nesse modo.

Uso: python tools/capture_champ_select.py  (deixe rodando, entre na fila e aceite)
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from league_remote.lcu_client import LCUClient  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "champ_select_dump.json")


def main() -> None:
    c = LCUClient()
    snapshots = []
    last_phase = None
    started = None
    print("Aguardando ChampSelect... (Ctrl+C para parar e salvar)")
    try:
        while True:
            if not c.base_url and not c.connect():
                time.sleep(1)
                continue
            phase = c.get_gameflow_phase()
            if phase != last_phase:
                print(f"  fase: {last_phase} -> {phase}")
                last_phase = phase
            if phase == "ChampSelect":
                if started is None:
                    started = time.time()
                    print("  >>> ChampSelect! gravando snapshots...")
                sess = c.get_champ_select_session()
                if sess:
                    t = round(time.time() - started, 2)
                    local = sess.get("localPlayerCellId")
                    me = next(
                        (p for p in sess.get("myTeam", []) or [] if p.get("cellId") == local),
                        {},
                    )
                    actions = []
                    for grp in sess.get("actions", []) or []:
                        for a in grp:
                            actions.append({
                                "id": a.get("id"), "cell": a.get("actorCellId"),
                                "type": a.get("type"), "inProgress": a.get("isInProgress"),
                                "completed": a.get("completed"), "championId": a.get("championId"),
                            })
                    # Sonda endpoints candidatos a "subset" (os 2-3 campeoes
                    # iniciais que voce escolhe antes do resto ir pra roleta).
                    probes = {
                        ep: c._get(ep)
                        for ep in (
                            "/lol-champ-select/v1/subset-champion-list",
                            "/lol-lobby-team-builder/champ-select/v1/subset-champion-list",
                            "/lol-champ-select/v1/pickable-champion-ids",
                            "/lol-champ-select/v1/all-grid-champions",
                        )
                    }
                    snap = {
                        "t": t,
                        "phase_timer": (sess.get("timer") or {}).get("phase"),
                        "benchEnabled": sess.get("benchEnabled"),
                        "benchChampions": sess.get("benchChampions"),
                        "session_keys": sorted(sess.keys()),
                        "my_championId": me.get("championId"),
                        "my_championPickIntent": me.get("championPickIntent"),
                        "my_actions": [a for a in actions if a["cell"] == local],
                        "all_actions": actions,
                        "probes": probes,
                        "raw_session": sess,  # sessao inteira pra nao perder nada
                    }
                    snapshots.append(snap)
                    subset = probes["/lol-champ-select/v1/subset-champion-list"]
                    subset_n = len(subset) if isinstance(subset, list) else subset
                    print(
                        f"  t={t}s bench={len(sess.get('benchChampions') or [])} "
                        f"my_champ={snap['my_championId']} "
                        f"subset={subset_n} "
                        f"my_actions={snap['my_actions']}"
                    )
                time.sleep(0.25)
            else:
                if started is not None:
                    print("  ChampSelect terminou. Salvando dump.")
                    break
                time.sleep(0.4)
    except KeyboardInterrupt:
        print("\nInterrompido.")
    finally:
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(snapshots, f, ensure_ascii=False, indent=2)
        print(f"\nSalvo {len(snapshots)} snapshots em {OUT}")


if __name__ == "__main__":
    main()
