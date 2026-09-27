"""B05: one environment-variable contract shared by the app, Docker Compose and .env."""
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

from backend import config

ROOT = Path(__file__).resolve().parent.parent


def test_database_url_takes_precedence(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@db:5432/x")
    monkeypatch.setenv("POSTGRES_HOST", "ignored")
    assert config.build_database_url() == "postgresql://u:p@db:5432/x"


def test_postgres_parts_are_used_without_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    for k, v in {"POSTGRES_USER": "alice", "POSTGRES_PASSWORD": "secret", "POSTGRES_HOST": "db",
                 "POSTGRES_PORT": "6543", "POSTGRES_DB": "gt"}.items():
        monkeypatch.setenv(k, v)
    assert config.build_database_url() == "postgresql://alice:secret@db:6543/gt"


def test_dotenv_file_is_loaded_and_real_env_wins(tmp_path):
    (tmp_path / "backend").mkdir()
    shutil.copy(ROOT / "backend" / "config.py", tmp_path / "backend" / "config.py")
    (tmp_path / "backend" / "__init__.py").write_text("")
    (tmp_path / ".env").write_text("OLLAMA_URL=http://from-dotenv:11434\nOLLAMA_MODEL=from-dotenv\n")
    code = "from backend import config; print(config.OLLAMA_URL, config.OLLAMA_MODEL)"
    env = {"PATH": "", "OLLAMA_MODEL": "from-env"}
    out = subprocess.run([sys.executable, "-c", code], cwd=tmp_path, env=env, capture_output=True, text=True, check=True)
    assert out.stdout.split() == ["http://from-dotenv:11434", "from-env"]


def test_compose_uses_only_variables_the_app_reads():
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text())
    env = compose["services"]["app"]["environment"]
    env = dict(e.split("=", 1) for e in env) if isinstance(env, list) else env
    source = (ROOT / "backend" / "config.py").read_text()
    for name in env:
        assert f'"{name}"' in source, f"docker-compose sets {name} but backend/config.py never reads it"
    assert "@db:" in env["DATABASE_URL"], "the app container must reach the db service by its compose name"
    assert "localhost" not in env["OLLAMA_URL"], "localhost inside a container is the container itself"
