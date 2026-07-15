"""Interactively create an initial local API user without exposing its password."""

from __future__ import annotations

import argparse
import getpass

from src.infrastructure.database import DatabaseManager
from src.security.auth import AuthService
from src.security.rbac import Role
from src.security.settings import SecuritySettings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("username")
    parser.add_argument("role", choices=[role.value for role in Role])
    arguments = parser.parse_args()
    password = getpass.getpass("Password: ")
    confirmation = getpass.getpass("Confirm password: ")
    if password != confirmation:
        parser.error("password confirmation does not match")

    database = DatabaseManager()
    database.apply_migrations()
    service = AuthService(database, SecuritySettings.from_env())
    principal = service.create_user(arguments.username, password, Role(arguments.role))
    print(f"Created user {principal.user_id} with role {principal.role.value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
