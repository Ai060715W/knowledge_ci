"""Command-line entry point for the T01 baseline."""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

import uvicorn
from pydantic import ValidationError

from knowledge_ci import __version__
from knowledge_ci.app import create_app
from knowledge_ci.config import load_settings, verify_pilot
from knowledge_ci.contracts.errors import field_errors
from knowledge_ci.storage.database import StorageError, database_path, upgrade


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="knowledge-ci", description="Knowledge CI local application"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--env-file", help="Configuration file (default: optional .env)")
    commands = parser.add_subparsers(dest="command")
    check = commands.add_parser("check-config", help="Validate local configuration")
    check.add_argument(
        "--require-pilot", action="store_true", help="Also verify the local Git commit"
    )
    commands.add_parser("migrate", help="Create or upgrade the local database")
    commands.add_parser("serve", help="Start the local HTTP application")
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    env_file = args.env_file if args.env_file is not None else ".env"
    env_file_path = Path(env_file)
    env_file_loaded = env_file_path.is_file()

    try:
        if args.env_file is not None and not env_file_loaded:
            raise ValueError("Requested configuration file is missing or not a regular file")
        settings = load_settings(env_file)
        if args.command == "check-config":
            result: dict[str, object] = {
                "status": "ok",
                "env_file_loaded": env_file_loaded,
                "pilot_configured": settings.pilot_configured,
                "model_provider": settings.model_provider,
                "source_egress": settings.allow_source_egress,
                "model_budget_usd": str(settings.model_budget_usd),
            }
            if args.require_pilot:
                result["pilot"] = verify_pilot(settings)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if args.command == "migrate":
            revision = upgrade(database_path(settings.data_dir))
            print(json.dumps({"status": "ok", "revision": revision}, indent=2))
            return 0
    except StorageError as exc:
        print(f"Storage error: {exc}", file=sys.stderr)
        return 2
    except ValidationError as exc:
        errors = [
            f"{detail.field}: {detail.message}" if detail.field else detail.message
            for detail in field_errors(exc)
        ]
        print("Configuration error: " + "; ".join(errors), file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2
    except OSError:
        print(
            "Configuration error: cannot access local configuration or repository", file=sys.stderr
        )
        return 2

    try:
        uvicorn.run(
            create_app(settings),
            host=settings.host,
            port=settings.port,
            log_level=settings.log_level,
        )
    except KeyboardInterrupt:
        return 0
    return 0
