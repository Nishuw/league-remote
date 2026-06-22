# LCU API — o que dá pra usar no League Remote

Referência curada da **LCU API** (API local do cliente do LoL) focada no que faz
sentido para um controle remoto pelo celular. Levantada do próprio cliente em
runtime (`/help` → 1455 funções, 924 recursos REST).

- **Lista completa de recursos REST**: [`lcu-endpoints.md`](lcu-endpoints.md)
- **Descrições de todas as funções**: [`lcu-help.json`](lcu-help.json)
- **Como descobrir você mesmo**: com o cliente aberto, leia o `lockfile`
  (porta + senha) e chame `GET /help` com `Authorization: Basic base64("riot:senha")`,
  `verify=False`. Os nomes de evento `OnJsonApiEvent_<plugin>_<v>_<recurso>` mapeiam
  1:1 para os caminhos REST (`_` vira `/`).

> Notação: ✅ = já usamos no `lcu_client.py` · ➕ = sugestão de adição.

---

## 0. WebSocket de eventos — monitoramento em tempo real (como o Blitz)

Além do REST, a LCU expõe um **WebSocket** na mesma porta/senha. É assim que o
Blitz e overlays acompanham o champ select **sem lag de polling**.

- **URL:** `wss://127.0.0.1:<porta>/` · **Auth:** mesmo header
  `Authorization: Basic base64("riot:senha")` · `verify=False` (cert local).
- **Protocolo:** estilo WAMP em JSON. Para assinar um evento, envie
  `[5, "OnJsonApiEvent_<plugin>_<v>_<recurso>"]`. Os eventos chegam como
  `[8, "<evento>", {"uri": "/caminho/rest", "eventType": "Create|Update|Delete", "data": {...}}]`.
  O `data` **já é o recurso completo** (igual ao `GET`) — não precisa refazer a chamada.
- **Usamos (`monitor.py` → `run_ws`):**
  - `OnJsonApiEvent_lol-gameflow_v1_gameflow-phase` — muda de fase na hora.
  - `OnJsonApiEvent_lol-champ-select_v1_session` — **a roleta/subset do ARAM
    aparecem no instante** em que a LCU muda a sessão.
  - `OnJsonApiEvent_lol-matchmaking_v1_ready-check` — aceitar mais rápido.
- O **polling continua** como rede de segurança (se o WS cair ou faltar a lib
  `websocket-client`). Se ficar mudo demais (lobby ocioso), o `recv` estoura por
  timeout e a thread reconecta sozinha.

---

## 1. Fila / lobby — hoje só reagimos; dá pra **iniciar** tudo pelo celular

Hoje o app só cancela a fila (`DELETE .../matchmaking/search`). Com o lobby dá
pra montar a fila do zero e dar play remoto.

| | Método | Endpoint | Para quê |
|---|---|---|---|
| ✅ | `POST` | `/lol-lobby/v2/lobby` | Cria lobby de uma fila. Body: `{"queueId": 450}` (450=ARAM, 430=normal, 420=ranked solo, 440=flex, 490=normal rápido, 2400=ARAM Desordem). |
| ✅ | `GET` | `/lol-lobby/v2/lobby` | Estado do lobby atual (membros, fila, se pode iniciar). |
| ✅ | `DELETE` | `/lol-lobby/v1/lobby` | Sair do lobby. |
| ✅ | `POST` | `/lol-lobby/v2/lobby/matchmaking/search` | **Iniciar a fila** (dar "Encontrar Partida"). |
| ✅ | `DELETE` | `/lol-lobby/v1/lobby/matchmaking/search` | Cancelar a busca. |
| ➕ | `GET` | `/lol-lobby/v2/received-invitations` | Convites recebidos. |
| ➕ | `POST` | `/lol-lobby/v2/received-invitations/{id}/accept` | Aceitar convite de duo/grupo. |
| ➕ | `GET` | `/lol-lobby/v2/eligibility/party` | Quais filas o grupo pode jogar (valida antes de criar). |

> Habilita um fluxo completo: **abrir fila → aceitar → pick/ban → jogar**, tudo do sofá.

---

## 2. Matchmaking / ready check ✅ (já coberto)

| | Método | Endpoint | Para quê |
|---|---|---|---|
| ✅ | `GET` | `/lol-matchmaking/v1/search` | `timeInQueue`, `estimatedQueueTime`. |
| ✅ | `GET` | `/lol-matchmaking/v1/ready-check` | Estado do ready check. |
| ✅ | `POST` | `/lol-matchmaking/v1/ready-check/accept` · `/decline` | Aceitar / recusar. |

---

## 3. Champ select — extras que faltam

| | Método | Endpoint | Para quê |
|---|---|---|---|
| ✅ | `GET` | `/lol-champ-select/v1/session` | Sessão completa (times, ações, banco). |
| ✅ | `PATCH` | `/lol-champ-select/v1/session/actions/{id}` | Pick/ban/hover. |
| ✅ | `POST` | `/lol-champ-select/v1/session/bench/swap/{championId}` | Trocar pelo banco/roleta (ARAM). |
| ✅ | `GET` | `/lol-lobby-team-builder/champ-select/v1/subset-champion-list` | **Escolha inicial do ARAM/Desordem**: os 2-3 campeões que você pega na chegada. Endpoint do team-builder **legado** — **não** aparece na sessão do champ-select, e o `/lol-champ-select/v1/subset-champion-list` "moderno" responde `null`. Já vem populado no t=0 (antes da roleta popular). Retorna lista de ids; tocar → completa a ação de `pick` (`patch_action`). |
| ✅ | `POST` | `/lol-champ-select/v1/session/trades/{id}/(request\|accept\|decline)` | Trocas com aliado. |
| ✅ | `GET` | `/lol-champ-select/v1/(pickable\|bannable)-champion-ids` | Disponíveis (lista **todos**; não serve pra escolha inicial do ARAM). |
| ✅ | `PATCH` | `/lol-champ-select/v1/session/my-selection` | Definir **feitiços** (`spell1Id`/`spell2Id`), **skin** (`selectedSkinId`) e ward. Útil no ARAM pra trocar Flash/Snowball pelo celular. |
| ✅ | `GET` | `/lol-champ-select/v1/skin-carousel-skins` | Skins disponíveis do campeão atual (pra seletor de skin). |
| ➕ | `GET` | `/lol-champ-select/v1/ongoing-champion-swap` | Estado da troca de campeão em andamento (melhora a UI de trocas). |
| ➕ | `GET` | `/lol-champ-select/v1/current-champion` | Id do campeão atual (atalho mais leve que ler a sessão toda). |
| ➕ | `POST` | `/lol-champ-select/v1/session/my-selection/reroll` | **Reroll** do ARAM (quando `rerollsRemaining > 0`). Foi removido antes; dá pra reativar. |

---

## 4. Runas — recomendação automática por campeão

Hoje montamos/salvamos página manualmente. A LCU recomenda runas prontas.

| | Método | Endpoint | Para quê |
|---|---|---|---|
| ✅ | `GET/PUT/POST` | `/lol-perks/v1/pages`, `/currentpage`, `/styles`, `/perks` | Ler/editar/criar/ativar páginas. |
| ➕ | `GET` | `/lol-perks/v1/inventory` | Quantas páginas custom o jogador tem / pode criar. |
| ➕ | `GET` | `/lol-perks/v1/recommended-pages` | Páginas de runa **recomendadas** para o campeão/posição atuais — aplicar com 1 toque. |
| ➕ | `POST` | `/lol-perks/v1/rune-recommender-auto-select` | Deixa o cliente escolher a runa recomendada automaticamente. |

---

## 5. Perfil / home — enriquecer a tela inicial

| | Método | Endpoint | Para quê |
|---|---|---|---|
| ✅ | `GET` | `/lol-summoner/v1/current-summoner` | Nome, nível, ícone, level. |
| ✅ | `GET` | `/lol-ranked/v1/current-ranked-stats` | Elo solo/flex. |
| ➕ | `GET` | `/lol-summoner/v1/current-summoner/summoner-profile` | Ícone de fundo, bandeira, troféus do perfil. |
| ➕ | `GET` | `/lol-honor-v2/v1/profile` | Nível de honra. |
| ➕ | `GET` | `/lol-challenges/v1/summary-player-data/local-player` | Pontos de desafios, título, top challenges. |
| ➕ | `PUT` | `/lol-chat/v1/me` | Definir **status/availability** (`chat`, `away`, `dnd`) e mensagem de status pelo celular. |

---

## 6. Pós-jogo / histórico

| | Método | Endpoint | Para quê |
|---|---|---|---|
| ✅ | `GET` | `/lol-match-history/v1/products/lol/current-summoner/matches?begIndex=0&endIndex=N` | Histórico recente. |
| ➕ | `GET` | `/lol-end-of-game/v1/eog-stats-block` | Placar de fim de jogo (KDA, dano, ouro) na tela de pós-partida — só existe logo após a partida. |
| ➕ | `GET` | `/lol-honor-v2/v1/ballot` | Cédula de honra do fim de jogo. |
| ➕ | `POST` | `/lol-honor-v2/v1/honor-player` | Honrar um aliado pelo celular. |

---

## 7. Live Client Data API (porta 2999, sem auth) — durante a partida

Hoje puxamos `allgamedata` inteiro. Há sub-rotas mais leves para polling:

| | Endpoint | Para quê |
|---|---|---|
| ✅ | `GET https://127.0.0.1:2999/liveclientdata/allgamedata` | Tudo de uma vez. |
| ➕ | `.../activeplayer` | Só o jogador local (ouro, runas, stats) — mais leve. |
| ➕ | `.../playerlist` | Lista de jogadores (KDA, itens, nível). |
| ➕ | `.../eventdata` | Só o feed de eventos (abates, objetivos) — ideal pro feed sem baixar o resto. |
| ➕ | `.../playerscores?riotId=<nome>` | Placar de um jogador específico. |

---

## Prioridade sugerida

1. ~~**Criar/iniciar fila pelo celular** (§1)~~ — ✅ **feito** (seletor de filas + Encontrar Partida).
2. ~~**Feitiços + skin no champ select** (§3, `my-selection`)~~ — ✅ **feito** (bottom-sheet: feitiços tocáveis + carrossel de skins).
3. **Runas recomendadas** (§4) — 1 toque em vez de montar do zero. ← próximo
4. **Live API segmentada** (§7) — feed/stats mais leves e sem piscar.
5. **Perfil na home + honra no pós-jogo** (§5, §6) — polimento.
