"""Run the existing browser journey against disposable local app servers."""
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from alembic import command
from alembic.config import Config

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"


def wait_for(url, process):
    for _ in range(100):
        if process.poll() is not None:
            raise RuntimeError(f"Server exited {process.returncode}: {url}")
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError(f"Server did not become ready: {url}")


def main():
    backend_port = int(os.environ.get("SMOKE_BACKEND_PORT", "8000"))
    frontend_port = int(os.environ.get("SMOKE_FRONTEND_PORT", "3001"))
    # Never terminate/reuse a user's existing application server.
    for port in (backend_port, frontend_port):
        with socket.socket() as check:
            check.bind(("127.0.0.1", port))
    with tempfile.TemporaryDirectory(prefix="cybersos-0B-smoke-") as directory:
        env = {**os.environ,
               "DATABASE_URL": "sqlite:///" + (Path(directory) / "smoke.sqlite").as_posix(),
               "LOCAL_STORAGE_ROOT": str(Path(directory) / "evidence"),
               "CORS_ORIGINS": f"http://localhost:{frontend_port}",
               "CASE_COOKIE_SECURE": "false",
               "SUPABASE_URL": "", "SUPABASE_SERVICE_ROLE_KEY": "",
               "EXTRACTION_PROVIDER": "heuristic", "SUMMARY_PROVIDER": "template",
               "ANTHROPIC_API_KEY": "", "ANTHROPIC_MODEL": "",
               "SMOKE_FRONTEND_URL": f"http://localhost:{frontend_port}",
               "SMOKE_API_URL": f"http://localhost:{backend_port}"}
        os.environ.update(env)
        from app.core.config import get_settings
        get_settings.cache_clear()
        config = Config(str(BACKEND / "alembic.ini"))
        config.set_main_option("script_location", str(BACKEND / "alembic"))
        command.upgrade(config, "head")
        processes = []
        try:
            backend = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(backend_port)],
                                       cwd=BACKEND, env=env)
            processes.append(backend)
            frontend = subprocess.Popen(["node", str(FRONTEND / "node_modules/next/dist/bin/next"), "start", "--hostname", "127.0.0.1", "--port", str(frontend_port)],
                                        cwd=FRONTEND, env=env)
            processes.append(frontend)
            wait_for(f"http://127.0.0.1:{backend_port}/health", backend)
            wait_for(f"http://127.0.0.1:{frontend_port}", frontend)
            return subprocess.run(["node", "__tests__/smoke-journey.cjs"], cwd=FRONTEND, env=env).returncode
        finally:
            for process in reversed(processes):
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            # Migration imports may initialize the application's pooled engine.
            # Release its SQLite handles before TemporaryDirectory removes files.
            from app.db.session import engine
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
