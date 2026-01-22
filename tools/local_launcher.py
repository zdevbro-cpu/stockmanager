import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_DIR = os.path.join(ROOT, "apps", "api")
WEB_DIR = os.path.join(ROOT, "apps", "web")


def run_detached(command: str, cwd: str) -> subprocess.Popen:
    if os.name == "nt":
        return subprocess.Popen(
            command,
            cwd=cwd,
            shell=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
    return subprocess.Popen(command, cwd=cwd, shell=True)


def main() -> int:
    try:
        subprocess.check_call("docker compose up -d", cwd=ROOT, shell=True)
    except subprocess.CalledProcessError as exc:
        print(f"docker compose failed: {exc}")
        return 1

    run_detached("uvicorn app.main:app --reload --port 8010", API_DIR)
    run_detached("npm run dev -- --host", WEB_DIR)
    print("Done. Close the opened consoles to stop API/Web.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
