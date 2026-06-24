# Diário de desenvolvimento — League Remote

> Notas pessoais sobre o que eu construí, as decisões que tomei pelo caminho e
> o que ainda quero explorar. Serve como memória do projeto e roteiro do que
> vem a seguir.

## Visão geral

O **League Remote** é uma aplicação Flask que conversa com a **LCU API** local
do cliente do League of Legends e expõe uma interface web pensada para o
celular. A ideia é controlar a fila e o champ select à distância: aceitar
partida, fazer pick/ban, mexer nas runas e acompanhar a partida ao vivo sem
precisar estar na frente do PC.

Stack: **Python + Flask** no backend, **HTML/CSS/JS puro** no frontend (sem
framework), comunicação com a **LCU API** (porta dinâmica com lockfile) e com a
**Live Client Data API** (porta 2999, durante a partida).

## Estrutura do projeto

Comecei com tudo num único arquivo (`lcu_accept_server.py`) e refatorei para um
pacote modular, separando responsabilidades:

```
league-remote/
├── app.py                       # ponto de entrada: sobe cliente, monitor e servidor
├── league_remote/
│   ├── __init__.py              # versão do pacote (usada no cache-busting)
│   ├── config.py                # configuração central (env vars)
│   ├── lcu_client.py            # cliente da LCU API + Live Client Data API
│   ├── monitor.py               # thread de fundo que observa o estado do cliente
│   ├── server.py                # app factory Flask + rotas
│   ├── templates/index.html     # página web (mobile-first, PWA)
│   └── static/                  # CSS, JS e manifest
├── requirements.txt
├── README.md
└── DEVLOG.md                    # este arquivo
```

Motivos da separação:
- **`lcu_client.py`**: isola toda conversa com a LCU (conexão via lockfile,
  requests autenticados, endpoints específicos). Fica fácil de testar e mockar.
- **`monitor.py`**: roda numa thread separada, faz polling do estado e cuida das
  ações automáticas. Não trava o servidor web.
- **`server.py`**: usa o padrão **app factory** (`create_app`) com injeção do
  monitor. Só define rotas e serve a interface.
- **frontend separado**: tirei o HTML/CSS/JS de dentro do Python e coloquei em
  arquivos próprios, o que deixou tudo muito mais legível.

## O que eu já fiz

### Conexão e ciclo de vida
- Leitura do **lockfile** para descobrir porta/senha da LCU e montar a base URL.
- Cliente HTTP com `verify=False` (cert local) e **timeout curto** (2s), porque
  a LCU é local: ou responde rápido ou não responde.
- Configuração por **variáveis de ambiente**: `LRA_AUTO_ACCEPT`, `LRA_PORT`,
  `LRA_HOST`, `LOL_PATH`.

### Monitor (thread de fundo)
- Loop com **polling adaptativo**: mais rápido (0,7s) em fases sensíveis
  (`ReadyCheck`, `Matchmaking`, `ChampSelect`) e mais lento (1,5s) no resto.
- **Resiliência**: envolvi o loop principal num `try/except` e extraí a lógica
  para `_tick()`. Antes, qualquer exceção não tratada **matava a thread** em
  silêncio e o estado congelava. Agora ele loga o erro e segue.
- Monta o estado do champ select (`_build_champ_select`) cobrindo tanto **draft**
  (pick/ban por vez) quanto **ARAM** (banco/roleta, campeão atual, trocas).
- Detecta a fila (`queueId`/nome) e expõe `mode_name` + `runes_enabled`.

### Aceitar partida + auto-pick/ban com proteções
- Auto-accept opcional do ready check.
- **Auto-pick e auto-ban por lista de prioridade**: tenta na ordem e pula quem
  já foi banido/escolhido. Se nenhum da lista estiver disponível, deixa a
  seleção manual aparecer na minha vez.
- **Proteção contra banir o pick do aliado** (`ban_protect_allies`): não banir
  campeão que um companheiro já escolheu/hoverou.
- Validação contra a lista de campeões realmente disponíveis para a ação.

### Criar e iniciar fila pelo celular
- Antes só dava pra **reagir** (aceitar/recusar/sair). Agora dá pra **montar a fila
  do zero**: na tela inicial aparece um seletor de filas (ARAM, ARAM: Desordem,
  Normal Seleção/Às Cegas, Ranqueada Solo/Flex, Arena).
- Tocar numa fila cria o lobby (`POST /lol-lobby/v2/lobby` com `queueId`); o painel
  troca para **"Encontrar Partida"** (`POST .../lobby/matchmaking/search`) + **Sair
  do lobby** (`DELETE /lol-lobby/v1/lobby`).
- Rotas no servidor: `GET/POST/DELETE /lobby` e `POST /queue/start`. O `GET /lobby`
  devolve um resumo (`queue_id`, `can_start`, `members`) pro celular decidir o que
  mostrar. O seletor some quando já está em `Matchmaking` (aí o botão é "Sair da fila").
- Fluxo completo agora cabe no celular: **criar fila → encontrar → aceitar →
  pick/ban → jogar**.

### Feedback na tela (toast) + cronômetro
- Toda ação (pegar campeão, feitiços, skin, criar/iniciar fila) agora mostra um
  **toast** no rodapé com o resultado — verde pra ok, vermelho pra falha. O
  `/aram/swap` devolve `{ok, status, msg}` (status HTTP da LCU), então o toast diz
  "Travado: Sett" ou "Falhou (409)" direto no celular, sem precisar olhar o terminal.
- No painel do ARAM mostro um **cronômetro** (segundos restantes da fase), que fica
  vermelho nos últimos 5s — deixa claro que a escolha tem tempo limitado.

### Feitiços e skin no champ select (ARAM)
- Abaixo do "seu campeão" mostro os **dois feitiços** (ícones) tocáveis e um botão
  **Skin**. Tocar abre um **bottom-sheet** (modal de baixo) com as opções.
- Feitiços: lista curada dos permitidos no ARAM (Flash e Snowball primeiro). Tocar
  troca via `PATCH /lol-champ-select/v1/session/my-selection`; se eu escolher um que
  já está no outro slot, faz **swap** dos dois.
- Skins: carrossel das skins do campeão (`GET .../skin-carousel-skins`), com a atual
  destacada e as bloqueadas com cadeado; tocar aplica `selectedSkinId`.
- **Detalhe de UI importante:** o `#champ-info` é redesenhado a cada 700ms (tick),
  então o seletor é um **modal separado** (não dentro do champ-info) — assim ele não
  pisca nem fecha sozinho a cada ciclo. Ícones vêm do CommunityDragon via
  `LCUClient.asset_url` (mesma conversão das runas).

### Runas (a qualquer momento)
- Painel de runas acessível **fora do champ select também** (na fila, no menu).
- Troca entre páginas salvas, **monta runa do zero** e **salva como nova página**.

### ARAM e ARAM: Desordem
- Detecto o modo "banco" (`benchEnabled`) e mostro **duas seções distintas**:
  a **escolha inicial** (subset) e a **roleta** (banco), como cartas tocáveis.
- **Escolha inicial (subset).** Os 2-3 campeões que você pega na chegada vêm de
  `GET /lol-lobby-team-builder/champ-select/v1/subset-champion-list` (team-builder
  **legado**) — **não** do `benchChampions`. Já vêm populados **no t=0**, antes
  da roleta. O front mostra **"Escolha seu campeão (toque)"** com essas cartas
  enquanto você ainda não tem campeão. Detalhe completo na seção de bugs abaixo.
- **Roleta (banco).** O `benchChampions` começa **vazio** e popula gradualmente
  (~5s depois: 1, 4, 5, 6...). É o pool de **troca** depois que você já tem
  campeão (e pra onde vai o subset que você **não** escolheu). Mostro como
  "Roleta (toque para trocar/pegar)", sem repetir os campeões que já estão na
  escolha inicial.
- **Mesmo gesto cobre tudo.** Tocar qualquer carta cai no `/aram/swap`, que
  decide pelo estado: sem campeão + pick em progresso → **completa o pick**
  (`patch_action`, trava o campeão); com campeão → **troca pelo banco**
  (`bench/swap`). Validado: vira `my_champion_id`; aliados aparecem com a ação
  `pick` `completed:true`.
- **Fluxo temporal (confirmado por captura ao vivo a 4x/s):** t=0 → subset já
  disponível (`[235, 133]`), `benchChampions` vazio, sua ação de `pick` em
  progresso com `championId 0`. ~5s → roleta começa a popular. ~9s → você
  escolhe (pick `completed`, `my_championId` setado). Depois → roleta vira
  troca, e o subset não-escolhido aparece nela. O subset **persiste** a fase
  toda. Só mostro "sorteando campeões..." no caso raro de nem subset nem roleta
  existirem ainda.
- Trocas com aliados (request/accept/decline) quando o modo permite.
- **Removi os rerolls** (foram tirados do ARAM normal).
- **Desordem não tem runas**: escondo o painel de runas e rotulo o modo certo.
- Ignoro por enquanto as **cartas/augments** do Desordem — foco só na escolha de
  campeão.
- Linguagem da UI ajustada: no ARAM **não falo "escolher campeão"** (é tudo
  sorteado). Uso "Roleta (toque para pegar/trocar)".

### Sair da fila / dodge
- Endpoint único **`/leave`** que decide pela fase: cancela o matchmaking ou dá
  **dodge** no champ select (`quitV2` com fallback para `leave_lobby`).
- Botão de sair com texto dinâmico ("Sair da fila" / "Sair (dodge)") e
  visibilidade correta por fase. Tirei o botão de dentro do `#content` para a
  visibilidade não depender da área de conteúdo.

### Painel ao vivo (durante a partida)
- Removi o aceitar/recusar quando a partida já está rolando.
- Mostro **tempo de jogo, KDA (+ratio), CS, CS/min, visão, nível, ouro** e
  **objetivos** (torres, dragões + **alma/soul**, **arautos**, **larvas do
  vazio**, **barão**), além de um **feed de eventos** rico.
- **Identifico o jogador local** pelo `activePlayer` da Live API: na lista e no
  feed ele vira **"Você"**, com a linha destacada em dourado. No feed os abates
  ficam **"Você eliminou Kalista · 12:34"** (ícones do autor e da vítima, contagem
  de assist, multikills, first blood, roubos de objetivo).
- **Visão (sentinelas)** só aparece no Rift (`gameMode == "CLASSIC"` → normal,
  flex, ranked); no ARAM é escondida (não há wards). Vem do `wardScore`.
- **Feed sem piscar**: feed agora é **estruturado** (campos `kind/a/v/note/...`
  em vez de texto pronto), montado no front com ícones; só redesenho quando a
  assinatura dos eventos muda, preservando a rolagem. Ordeno por tempo no backend.
- **Poller auto-agendado** (≈800ms): a próxima busca só dispara quando a anterior
  responde. Diferente de `setInterval`, **não acumula nem pula ciclos** no
  celular — era isso que deixava o **farm "às vezes rápido, às vezes não"**.
- **Mais info aproveitada da Live API:** `your_level`, `csmin` por jogador,
  `kda` ratio, soul de dragão (`souls`), `HordeKill`/`VoidgrubKill` (larvas),
  `Stolen` (objetivo roubado), tradução PT-BR dos tipos de dragão.
- **Novas métricas analíticas (2ª rodada):**
  - **Itens por jogador**: mini-ícones do build de cada um (scout do inimigo).
    Ícone resolvido por um `item_map` carregado uma vez do
    `/lol-game-data/assets/v1/items.json` (mesmo padrão dos feitiços).
  - **Feitiços de invocador** por jogador (saber Flash/TP do inimigo), ícone
    resolvido pelo `displayName` em `summoner-spells.json`.
  - **Lead de ouro por time** = soma do **preço dos itens** equipados (a Live
    API não expõe o ouro dos inimigos; o valor investido é um bom proxy).
    Mostro o total por time e a **diferença** no cabeçalho ("Azul +2.3k").
  - **Timers de Barão (180s) e Dragão Ancião (150s)**: derivados do último
    `BaronKill`/`DragonKill` Elder; banner com **contagem regressiva local**
    (ticker de 1s, sem refazer fetch) — saber quando o buff inimigo cai.
  - **Progresso de alma**: "alma em 1" / "ALMA" a partir da contagem de dragões.
- **Performance:** o bloco de stats só **re-monta o DOM quando a assinatura muda**
  (igual ao feed). Sem isso, eram 60+ `<img>` de itens recriadas a cada 800ms —
  travava o celular. O countdown dos buffs atualiza à parte, só o texto.

### Live API segmentada (payloads menores no celular)
- **Problema:** o painel ao vivo puxava o `allgamedata` inteiro a cada ~800ms e
  reenviava a lista pesada de jogadores (10 jogadores × itens × feitiços ×
  ícones) **em todo poll**, mesmo quando só o feed mudava. No celular isso é
  tráfego e parse desnecessários.
- **Como ficou:** quebrei em **duas rotas segmentadas** que o front pola em
  cadências diferentes:
  - **`/live/feed`** (leve, rápido — 800ms): só o que vem dos **eventos** —
    feed, objetivos, buffs (Barão/Ancião) e abates por time. Não manda a lista
    de jogadores. Usa `gamestats` + `eventdata` + `playerlist` (só pra mapear
    autor→time/campeão) + `activeplayername` (leve, pra marcar "Você").
  - **`/live/stats`** (pesado, metade da cadência — ~1,6s): jogadores, itens,
    feitiços, CS/KDA/visão e **ouro investido por time**. Usa `gamestats` +
    `playerlist` + `activeplayer` (ouro/nível).
  - **`/live`** (allgamedata) continua como **fallback/compatibilidade** numa só
    chamada.
- **No backend** extraí a lógica do `/live` para **funções puras**
  (`_build_players`, `_process_events`, `_live_meta`, `_build_buffs`,
  `_finalize_objectives`) que operam sobre os blocos crus — então as três rotas
  compartilham exatamente o mesmo processamento (testável sem cliente do LoL).
- **No front** o poller virou **dois loops auto-agendados** (`loadLiveFeed` toda
  iteração, `loadLiveStats` em metade) com **render desacoplado** (`renderLive`
  combina o último feed + último stats). A lista pesada de jogadores passa a
  trafegar ~metade das vezes; o feed/objetivos seguem acompanhando a partida sem
  lag. O diff de DOM por assinatura (feed/stats) continua valendo.

### Perfil na home + honra no pós-jogo
- **Perfil na tela inicial:** card com **ícone, nome (#tag), nível e nível de
  honra** (`/lol-summoner/v1/current-summoner` + `/lol-honor-v2/v1/profile`),
  acima do elo e do histórico. Rota `/profile`.
- **Honrar aliado pelo celular:** ao acabar a partida (fases `WaitingForStats`,
  `PreEndOfGame`, `EndOfGame`) mostro a **cédula de honra**
  (`GET /lol-honor-v2/v1/ballot`) como cartas tocáveis (ícone + campeão + nome);
  1 toque honra (`POST /lol-honor-v2/v1/honor-player`). Rota `/honor` (GET lista
  os elegíveis, POST honra). A leitura da cédula é **defensiva** — os campos
  mudam entre patches, então varro várias chaves (`eligibleAllies`,
  `eligiblePlayers`, ...) e mando `summonerId` + `puuid` no POST.

### UI/UX mobile
- Tema escuro inspirado no visual Hextech/LoL, fontes **Cinzel + Inter**.
- Mobile-first: `viewport-fit=cover`, `safe-area-inset`, `100dvh`, alvos de
  toque maiores, **manifest PWA**.
- Indicador de **build** no rodapé para eu confirmar que o celular pegou o
  código novo.

### Auto-pick / Auto-ban e Runas — UX mobile (refeito)
- **Auto-pick/ban com chips de campeão (era `<select>`):** o `<select>` nativo
  com 160+ campeões era horrível no celular (sem busca, sem ícone). Troquei por
  **chips de prioridade** (1ª/2ª/3ª) — vazio = "+ adicionar", preenchido =
  ícone + nome + (×). Tocar abre um **bottom-sheet com busca e grade de ícones**
  (reaproveita o `#picker-modal`; função `openChampPicker`). Sem duplicados e a
  prioridade compacta sozinha (sem buracos).
- **Badge de estado** no botão "Auto-pick / Auto-ban": mostra `pick`/`ban`
  (verde/vermelho) quando ativos, sem precisar abrir o painel. Carregado uma vez
  no load (`/config`).
- **Config sem `<select>`:** estado em `cfgState` no front; `saveConfig` sincroniza
  os toggles do DOM e re-renderiza chips sem perder os switches.
- **Runas recomendadas (1 toque):** novo `/rune-recommend` consome
  `/lol-perks/v1/recommended-pages` e **normaliza** a estrutura (que varia entre
  patches — `primaryPerkStyleId`/`primaryStyleId`, `perks`/`selectedPerkIds`,
  ints ou dicts) pro mesmo formato do editor. UI lista cada recomendação com
  **ícone das duas árvores + nome/posição** e aplica direto. Fora do champ select
  vem vazio → mostro uma dica em vez de erro.
- **Feedback via `toast`** (era `alert()`/`confirm()`) ao salvar/aplicar runa —
  não bloqueia a tela no celular.

### Monitoramento em tempo real (WebSocket de eventos da LCU)
- **Problema:** no ARAM/Desordem, ao chegar no champ select, os primeiros 2-3s
  o app não acompanhava — a roleta aparecia atrasada e a "minha vez"/pick às
  vezes nem era reconhecida. Causa: eu só fazia **polling** (0,7s no monitor +
  0,7s no frontend), então estava sempre atrás de cada transição rápida do
  `benchChampions`.
- **Como o Blitz faz:** conecta no **WebSocket** da LCU
  (`wss://127.0.0.1:porta/`, mesma auth Basic do REST) e assina
  `OnJsonApiEvent_lol-champ-select_v1_session`. A LCU faz **push** da sessão
  inteira no instante em que ela muda — inclusive quando a roleta popula.
- **O que implementei:** uma segunda thread (`Monitor.run_ws`) que assina
  `gameflow-phase`, `champ-select session` e `ready-check`. O payload do evento
  de sessão **já é a sessão completa**, então reaproveito o
  `_apply_champ_select` (extraído do polling) e atualizo o estado na hora, sem
  novo GET. O **polling continua** como rede de segurança (cobre se o WS cair
  ou faltar a lib). No frontend, o tick virou **adaptativo** (350ms em
  ReadyCheck/ChampSelect, 700ms no resto) pra tela acompanhar o backend
  instantâneo. Dependência nova: `websocket-client`.
- **Validei** o fluxo do ARAM (bench vazio → bench populado → campeão travado)
  alimentando `_on_ws_event` com sessões simuladas: o estado muda no instante
  de cada evento, sem esperar ciclo de polling.

## Decisões e bugs que resolvi (pra eu não esquecer)

- **PowerShell não tem `&&`**: separei os comandos ou usei `;`.
- **Thread do monitor morrendo calada**: resolvido com `try/except` + `_tick()`.
- **Aceitar/Recusar aparecendo em todo lugar**: o CSS `display: flex` da
  `.actionbar` sobrescrevia o atributo `hidden`. Corrigi com uma regra global
  `[hidden] { display: none !important; }` e travei a barra para aparecer só em
  `ReadyCheck`.
- **Navegador cacheando CSS/JS**: `SEND_FILE_MAX_AGE_DEFAULT = 0`,
  `Cache-Control: no-store` e um parâmetro `?v=` (versão + timestamp) nas URLs
  dos estáticos. Build visível no rodapé pra conferência.
- **Feed atualizando rápido demais**: assinatura de eventos para só redesenhar no
  que mudou.
- **Grade com todos os campeões aparecendo no ARAM**: passei a mostrar a grade
  completa **só no draft**; no ARAM/Desordem tudo é pela roleta.
- **Origem dos 2-3 campeões iniciais do ARAM/Desordem (CORRIGIDO).** A
  conclusão antiga estava **errada**: eu achava que os campeões da escolha
  inicial eram os `benchChampions`. **Não são.** Capturei a sessão inteira ao
  vivo (`tools/capture_champ_select.py`, sondando vários endpoints a 4x/s) e
  descobri:
  - O `benchChampions` é a **roleta de troca** — começa vazio e popula só ~5s
    depois (gradual: 1, 4, 5, 6...). Não é a escolha inicial.
  - A **escolha inicial** (os 2-3 campeões que você pega na chegada) vem de
    **`GET /lol-lobby-team-builder/champ-select/v1/subset-champion-list`** —
    um endpoint do team-builder **legado** que **não** aparece na sessão do
    champ-select, nem em `pickable-champion-ids` (que lista todos), nem no
    `/lol-champ-select/v1/subset-champion-list` (esse responde `null`). Ele já
    vem populado **no t=0**, antes da roleta.
  - Exemplo real: subset `[235, 133]` (Senna/Quinn) disponível no t=0; escolhi
    Senna completando a ação de `pick` (`patch_action`); o não-escolhido (133)
    foi parar na roleta depois. A lista do subset **persiste** a fase toda.
  - **Por que o app parecia “não reconhecer”:** ele só lia `benchChampions`,
    então nos primeiros ~5s não mostrava nada de útil (a escolha inicial não
    estava ali). Agora o `_build_bench` busca o `subset-champion-list` e expõe
    `subset`; o front mostra **“Escolha seu campeão (toque)”** com essas cartas
    na chegada e a **“Roleta”** (bench) separada, sem repetir os mesmos
    campeões. Tocar numa carta cai no `/aram/swap` de sempre: sem campeão +
    pick em progresso → `patch_action` (trava); com campeão → `bench/swap`.
  - **Validado** rodando `_build_champ_select` contra a sessão crua capturada:
    no t=0 o `subset` vem `[Senna, Quinn]` mesmo com a roleta vazia.
- **CS/KDA "travando" no painel ao vivo**: era uma corrida entre o poller de 1s e
  um throttle por tempo (`now - lastLiveLoad < 1000` às vezes dava 999ms e
  pulava). Troquei por uma **trava de requisição em andamento** (`liveLoading`)
  com `finally`, então a cada 1s sempre busca de verdade.
- **Ajustes pós-teste do painel ao vivo + lobby/troca (v1.1.1):**
  - **"Encontrar Partida" no saguão dos outros**: o `/lobby` agora expõe
    `is_leader` (de `localMember.isLeader`). Se entrei no lobby de outra pessoa,
    o front esconde o botão e mostra "aguardando o líder iniciar…".
  - **Trocas no ARAM "não funcionavam"**: centralizei `request/accept/decline`
    em `_trade()` no client, mandando `json={}` (alguns endpoints da LCU
    recusam POST sem corpo), guardando `last_status` e logando o código. A rota
    `/aram/trade` devolve `{ok, status, msg}` e o front mostra um **toast** com
    o erro — assim dá pra ver na hora se a LCU respondeu 409/404/etc.
  - **Feed "rell eliminou +4"**: dois problemas. (1) Casing — os eventos da
    Live API às vezes vêm com nome em caixa diferente do `playerlist`, então o
    `pindex` virou **case-insensitive** (indexo exato e em minúsculas) e o nome
    cru, quando não resolve, é capitalizado. (2) Texto — agora é **"Autor matou
    Vítima"** com ícones dos dois e um selo separado "N assist".
  - **Contagem de torres**: a torre é creditada ao **time adversário ao dono da
    estrutura** (`Turret_T1_*` é do azul → ponto do vermelho), via
    `_structure_owner` + `_other`, com fallback no time do autor.
  - **Objetivos por time mais robustos**: `_team_of()` resolve o time pelo
    `pindex` e, p/ minions/estruturas, pelos tokens do nome (Order/Chaos,
    T1/T2, 100/200). Dragão/barão/arauto/larvas são creditados ao time do autor.
  - **Placar das 2 equipes**: troquei as tags soltas por um **scoreboard**
    comparando Azul × Vermelho (abates, ouro, torres e, fora do ARAM,
    dragões/barão/arauto/larvas/alma), destacando quem está na frente.
  - **Ouro inimigo oculto**: a Live API às vezes zera os itens do time inimigo.
    Em vez de mostrar "0.0k" (enganoso), mostro "—" e só comparo ouro quando os
    **dois** times têm dado.
  - **ARAM**: escondo dragão/barão/arauto/larvas/alma (não existem no Abismo);
    mantenho abates, torres e ouro.
  - **`/debug/live`**: rota nova que despeja nomes dos jogadores, eventos crus e
    os objetivos já computados — pra diagnosticar divergências sem adivinhar.

## O que ainda quero explorar

### Cartas / augments do Desordem
Por enquanto **ignorei** a mecânica de cartas/augments. Dá para evoluir lendo os
endpoints de augments do champ select e oferecer a seleção pelo celular.

### Ideias soltas para o futuro
- **Notificações push** (PWA) quando a partida for encontrada, em vez de só som.
- **Pré-configurar pick/ban e runas por fila** (perfis por modo: ranked, normal,
  flex, ARAM).
- **Histórico/estatística** mais rica na tela inicial.
- **Reconexão automática** e mensagens melhores quando a LCU cai.
- **Testes automatizados** do `lcu_client` e do `monitor` (com mocks da LCU).
- **Trocas com aliados no painel ao vivo/champ select** com UI mais clara.
- **Internacionalização** (hoje a UI está em PT-BR).

## Como rodar (lembrete rápido)

1. Instalar dependências: `pip install -r requirements.txt`.
2. Subir o cliente do LoL e logar.
3. Rodar `python app.py`.
4. Acessar `http://SEU_IP:PORTA` pelo celular (mesma rede).

> **Aviso**: projeto pessoal, não oficial e **sem afiliação com a Riot Games**.
> Uso a LCU API local apenas para conveniência própria.
