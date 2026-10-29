"""Command line entry point: `agent-dex serve`."""

from __future__ import annotations

import argparse
import secrets
import socket
import sys
import webbrowser
from pathlib import Path

from . import __version__
from .config import DEFAULT_PORT, HOST, load_settings


def _free_port(start: int) -> int:
    for port in range(start, start + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex((HOST, port)) != 0:
                return port
    raise SystemExit(f"No hay puertos libres entre {start} y {start + 19}.")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="agent-dex", description="Agent Dex: coleccionador y gimnasio de agentes."
    )
    parser.add_argument("--version", action="version", version=f"agent-dex {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    serve = sub.add_parser("serve", help="Inicia el servicio local y la interfaz web.")
    serve.add_argument("--port", type=int, default=None, help=f"Puerto (por defecto {DEFAULT_PORT}).")
    serve.add_argument("--open", action="store_true", help="Abre el navegador al iniciar.")
    serve.add_argument(
        "--project-dir", type=Path, default=None, help="Carpeta de proyecto (por defecto, la actual)."
    )
    args = parser.parse_args(argv)

    if args.command == "serve":
        import os

        import uvicorn

        from .main import create_app

        if args.project_dir:
            os.environ["AGENT_DEX_PROJECT_DIR"] = str(args.project_dir.resolve())
        requested = args.port or int(os.environ.get("AGENT_DEX_PORT", DEFAULT_PORT))
        port = _free_port(requested)
        settings = load_settings(port)
        token = secrets.token_urlsafe(24)
        app = create_app(settings, token)
        url = f"http://{HOST}:{port}/#t={token}"
        print(f"Agent Dex {__version__}", flush=True)
        print(
            f"Abre esta dirección (el código es privado, válido solo en esta sesión):\n  {url}\n", flush=True
        )
        print("Ctrl+C para detener.", flush=True)
        if args.open:
            webbrowser.open(url)
        try:
            uvicorn.run(app, host=HOST, port=port, log_level="warning", ws_max_size=1_000_000)
        except KeyboardInterrupt:
            sys.exit(0)


if __name__ == "__main__":
    main()
