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

### Runas (a qualquer momento)
- Painel de runas acessível **fora do champ select também** (na fila, no menu).
- Troca entre páginas salvas, **monta runa do zero** e **salva como nova página**.

### ARAM e ARAM: Desordem
- Detecto o modo "banco" (`benchEnabled`) e mostro a **roleta** com os campeões
  disponíveis como cartas tocáveis.
- Toque numa carta tenta **trocar pelo banco**; se eu ainda não tenho campeão
  (escolha inicial), o backend faz **fallback** completando a ação de `pick` com
  aquele campeão. Assim o mesmo gesto cobre escolha inicial e troca depois.
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
- Mostro **tempo de jogo, KDA, CS, nível, ouro, objetivos** (torres, dragões,
  barão) e um **feed de eventos** (abates, multikills, first blood, etc.),
  resolvendo autor/vítima pelo nome → campeão/ícone.
- **Feed sem piscar**: só redesenho quando há evento novo (comparo uma
  assinatura dos eventos), preservando a rolagem.
- **Poller dedicado de 1s**, independente do tick de UI (700ms), que começa ao
  entrar na partida e para ao sair.

### UI/UX mobile
- Tema escuro inspirado no visual Hextech/LoL, fontes **Cinzel + Inter**.
- Mobile-first: `viewport-fit=cover`, `safe-area-inset`, `100dvh`, alvos de
  toque maiores, **manifest PWA**.
- Indicador de **build** no rodapé para eu confirmar que o celular pegou o
  código novo.

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
- **CS/KDA "travando" no painel ao vivo**: era uma corrida entre o poller de 1s e
  um throttle por tempo (`now - lastLiveLoad < 1000` às vezes dava 999ms e
  pulava). Troquei por uma **trava de requisição em andamento** (`liveLoading`)
  com `finally`, então a cada 1s sempre busca de verdade.

## O que ainda quero explorar

### ARAM: Desordem — escolha inicial dos 2-3 campeões
Ainda não confirmei **de onde** vêm os 2-3 campeões que aparecem para escolher ao
cair no saguão. Os dumps que peguei foram sempre no extremo errado: ou no
comecinho do `BAN_PICK` (com `benchChampions` vazio) ou na `FINALIZATION` (já com
campeão escolhido e banco cheio). Falta capturar o **dump no instante exato** em
que as cartas aparecem (`/debug/champ-select`, que já traz `pickable-champion-ids`
e outros endpoints) para cravar a origem e garantir que as cartas iniciais
apareçam certinho no celular.

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
