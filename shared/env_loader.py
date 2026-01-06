from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


def _candidate_env_paths() -> list[Path]:
    paths: list[Path] = []
    env_file = os.getenv("AGENCY_ENV_FILE")
    if env_file:
        paths.append(Path(env_file).expanduser())

    base_dir = Path(os.getenv("AGENCY_CONFIG_DIR", "~/.config/agencyos")).expanduser()
    paths.append(base_dir / "agency.env")
    paths.append(Path("~/.agency/agency.env").expanduser())
    paths.append(Path(".env"))
    return paths


def load_agency_env(override: bool = False) -> None:
    """Load AgencyOS environment variables from standard local locations."""
    for path in _candidate_env_paths():
        if path.is_file():
            load_dotenv(dotenv_path=path, override=override)
