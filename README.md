# League Remote

Controle a **fila** e a **seleção de campeão** do League of Legends pelo **celular**,
acessando uma página web pelo IP do PC na mesma rede Wi-Fi.

Funciona **100% local**: o programa fala direto com o cliente do LoL na sua máquina
(via **LCU API**). **Não precisa de chave/API da Riot Games** nem de conta de desenvolvedor.

> ⚠️ A LCU API é a API local **não-oficial** do cliente do LoL. Recursos de auto-accept,
> auto-pick e auto-ban podem violar os Termos de Serviço da Riot. Use por sua conta e risco.

## Como usar

1. Instale as dependências:

```bash
pip install -r requirements.txt
```

2. Abra o **cliente do League of Legends** e faça login.
3. Rode o servidor:

```bash
python app.py
```

4. O terminal mostra o endereço, ex.: `http://192.168.0.10:5000`
5. No **celular (mesma Wi-Fi)**, abra esse endereço no navegador.
   Dica: use "Adicionar à tela inicial" para abrir como app.

## Funções no celular

- **Fila**: tempo de fila em tempo real e botão **Sair da fila**.
- **Partida encontrada**: botões **Aceitar** / **Recusar** (barra fixa na base) + **alarme**
  (vibra e toca som).
- **Auto-accept de fallback**: o PC aceita sozinho ~3s antes do timer acabar (configurável).
- **Seleção de campeão**: mostra o time, bans e nomes dos aliados; **escolhe/bane**
  campeão (lista completa com busca) e tem **Auto-pick / Auto-ban** (trava o favorito
  na sua vez).
- **Runas**: troca entre páginas salvas, **monta runa do zero** e **salva como nova página**.
- **Em partida**: placar ao vivo com tempo de jogo e KDA/CS (via Live Client Data API).
- **Tela inicial**: seu elo/PDL (Solo/Duo e Flex) e histórico das últimas partidas.

## Estrutura do projeto

```
league-remote/
├── app.py                       # ponto de entrada (sobe monitor + servidor)
├── league_remote/
│   ├── config.py                # constantes e variáveis de ambiente
│   ├── lcu_client.py            # cliente da LCU API
│   ├── monitor.py               # monitor em background do estado do cliente
│   ├── server.py                # app factory Flask + rotas
│   ├── templates/index.html     # página web
│   └── static/                  # CSS, JS e manifest (PWA)
├── requirements.txt
├── README.md
└── LICENSE
```

## Configuração

Tudo pode ser ajustado por **variáveis de ambiente** (sem editar código):

| Variável          | Padrão       | Descrição                                                        |
| ----------------- | ------------ | ---------------------------------------------------------------- |
| `LRA_AUTO_ACCEPT` | `3`          | Segundos antes do fim para auto-accept. `none` desativa.         |
| `LRA_PORT`        | `5000`       | Porta do servidor web.                                           |
| `LRA_HOST`        | `0.0.0.0`    | Host de bind (`0.0.0.0` expõe na rede local).                    |
| `LOL_PATH`        | (auto)       | Pasta de instalação do LoL, caso o lockfile não seja detectado.  |

Exemplo (PowerShell): `\$env:LRA_AUTO_ACCEPT="none"; python app.py`

## Resolução de problemas

- **Celular não abre a página**: libere a porta `5000` no Firewall do Windows para o
  Python (permita nas redes Privadas) e confirme que PC e celular estão na mesma rede.
- **Placar ao vivo vazio**: a Live Client Data API só responde durante a partida.
- **Ícones não aparecem**: as imagens de campeões/runas vêm da internet (Community
  Dragon), então o celular precisa de acesso à rede.

## ⏱️ Importante

O ready check dura só **~12 segundos**. Para aceitar manualmente pelo celular você
precisa estar olhando a tela; por isso o auto-accept de fallback vem ligado por padrão.

## Licença

[MIT](LICENSE). Projeto independente, sem afiliação com a Riot Games.
