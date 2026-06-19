"""Configuracoes da aplicacao.

Os valores podem ser sobrescritos por variaveis de ambiente, permitindo
ajustar o comportamento sem editar o codigo.
"""

import os
from typing import List, Optional


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_optional_int(name: str, default: Optional[int]) -> Optional[int]:
    """Le um int que pode ser desativado com '', 'none', 'off' ou '0-' explicito."""
    raw = os.getenv(name)
    if raw is None:
        return default
    raw = raw.strip().lower()
    if raw in ("", "none", "off", "disabled", "false"):
        return None
    try:
        return int(raw)
    except ValueError:
        return default


# Segundos antes do timer do ready-check acabar para o PC aceitar sozinho.
# Defina LRA_AUTO_ACCEPT="none" para desativar e depender so do celular.
AUTO_ACCEPT_FALLBACK_SECONDS: Optional[int] = _env_optional_int("LRA_AUTO_ACCEPT", 3)

# Porta do servidor web (a que voce abre no celular).
WEB_PORT: int = _env_int("LRA_PORT", 5000)

# Host de bind. 0.0.0.0 expoe na rede local (necessario para o celular).
WEB_HOST: str = os.getenv("LRA_HOST", "0.0.0.0")

# Caminhos comuns do lockfile no Windows. Pode ser sobrescrito pela
# variavel de ambiente LOL_PATH (pasta de instalacao do LoL).
COMMON_LOCKFILE_PATHS: List[str] = [
    r"C:\Riot Games\League of Legends\lockfile",
    r"D:\Riot Games\League of Legends\lockfile",
    r"E:\Riot Games\League of Legends\lockfile",
    os.path.expandvars(r"%LOCALAPPDATA%\Riot Games\League of Legends\lockfile"),
]
