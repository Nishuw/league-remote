"""Ponto de entrada do League Remote.

Inicializa o cliente LCU, sobe o monitor em background e serve a aplicacao
web. Execute com `python app.py` e abra o endereco mostrado no celular.
"""

import socket
import sys
import threading

from league_remote import __version__
from league_remote.config import (
    AUTO_ACCEPT_FALLBACK_SECONDS,
    WEB_HOST,
    WEB_PORT,
)
from league_remote.lcu_client import LCUClient
from league_remote.monitor import Monitor
from league_remote.server import create_app


def get_local_ip() -> str:
    """Descobre o IP da maquina na rede local (o que o celular deve acessar)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def _print_banner(ip: str) -> None:
    line = "=" * 60
    print(line)
    print(f" League Remote v{__version__}")
    print(line)
    print(f" No celular (mesma Wi-Fi), abra:  http://{ip}:{WEB_PORT}")
    print(f" Neste PC, abra:                  http://127.0.0.1:{WEB_PORT}")
    if AUTO_ACCEPT_FALLBACK_SECONDS is not None:
        print(f" Auto-accept de fallback: ligado (~{AUTO_ACCEPT_FALLBACK_SECONDS}s antes do fim)")
    else:
        print(" Auto-accept de fallback: desligado")
    print(" Deixe o cliente do LoL aberto. Ctrl+C para sair.")
    print(line)


def main() -> None:
    client = LCUClient()
    monitor = Monitor(client)

    thread = threading.Thread(target=monitor.run, daemon=True)
    thread.start()

    app = create_app(monitor)

    _print_banner(get_local_ip())

    # threaded=True para atender o celular + polling ao mesmo tempo.
    app.run(host=WEB_HOST, port=WEB_PORT, threaded=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nEncerrado.")
        sys.exit(0)
