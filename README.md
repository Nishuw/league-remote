# League Remote Accept

Controle a **fila** e a **seleção de campeão** do League of Legends pelo **celular**,
acessando uma página web pelo IP do PC na mesma rede Wi-Fi.

Funciona **100% local**: o programa fala direto com o cliente do LoL na sua máquina
(via **LCU API**). **Não precisa de chave/API da Riot Games** nem de conta de desenvolvedor.

> ⚠️ A LCU API é a API local não-oficial do cliente do LoL. Use por sua conta e risco.

## Como usar

1. Instale as dependências:

```bash
pip install -r requirements.txt
```

2. Abra o **cliente do League of Legends** e faça login.
3. Rode o servidor:

```bash
python lcu_accept_server.py
```

4. O terminal mostra o endereço, ex: `http://192.168.0.10:5000`
5. No **celular (mesma Wi-Fi)**, abra esse endereço no navegador.

## Funções no celular

- **Fila**: tempo de fila em tempo real e botão **Sair da fila**.
- **Partida encontrada**: botões **Aceitar** / **Recusar** + **alarme** (vibra e toca som).
- **Auto-accept de fallback**: o PC aceita sozinho ~3s antes do timer acabar (configurável).
- **Seleção de campeão**: mostra o time, bans e nomes dos aliados; **escolhe/bane**
  campeão (lista completa com busca) e tem **Auto-pick / Auto-ban** (trava o favorito
  na sua vez).
- **Runas**: troca entre páginas salvas, **monta runa do zero** e **salva como nova página**.
- **Em partida**: placar ao vivo com tempo de jogo e KDA/CS (via Live Client Data API).
- **Tela inicial**: seu elo/PDL (Solo/Duo e Flex) e histórico das últimas partidas.

## Configuração

- O **auto-accept de fallback** vem ligado. Para desligar e depender só do celular,
  defina `AUTO_ACCEPT_FALLBACK_SECONDS = None` no topo do `lcu_accept_server.py`.
- A porta do servidor é `5000` (constante `WEB_PORT`).
- Se o lockfile do LoL não for detectado, defina a pasta de instalação:
  `setx LOL_PATH "C:\Riot Games\League of Legends"` (e reabra o terminal).

## Resolução de problemas

- **Celular não abre a página**: libere a porta `5000` no Firewall do Windows para o
  Python (permita nas redes Privadas) e confirme que PC e celular estão na mesma rede.
- **Placar ao vivo vazio**: a Live Client Data API só responde durante a partida.
- **Ícones não aparecem**: as imagens de campeões/runas vêm da internet (Community
  Dragon), então o celular precisa de acesso à rede.

## ⏱️ Importante

O ready check dura só **~12 segundos**. Para aceitar manualmente pelo celular você
precisa estar olhando a tela; por isso o auto-accept de fallback vem ligado por padrão.
