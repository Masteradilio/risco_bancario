"""Explicit role-to-permission matrix with separation of duties."""

from enum import StrEnum


class Role(StrEnum):
    ANALYST = "ANALYST"
    MANAGER = "MANAGER"
    AUDITOR = "AUDITOR"
    ADMIN = "ADMIN"


class Permission(StrEnum):
    CALCULATE_INDIVIDUAL = "ecl:calculate:individual"
    CALCULATE_PORTFOLIO = "ecl:calculate:portfolio"
    VIEW_RESULT = "ecl:result:read"
    APPROVE_SCENARIO = "scenario:approve"
    EXPORT_REGULATORY = "regulatory:export"
    VIEW_AUDIT = "audit:read"
    MANAGE_USERS = "user:manage"


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.ANALYST: frozenset({Permission.CALCULATE_INDIVIDUAL, Permission.VIEW_RESULT}),
    Role.MANAGER: frozenset(
        {
            Permission.CALCULATE_INDIVIDUAL,
            Permission.CALCULATE_PORTFOLIO,
            Permission.VIEW_RESULT,
            Permission.APPROVE_SCENARIO,
            Permission.EXPORT_REGULATORY,
        }
    ),
    Role.AUDITOR: frozenset({Permission.VIEW_RESULT, Permission.VIEW_AUDIT}),
    Role.ADMIN: frozenset({Permission.MANAGE_USERS, Permission.VIEW_AUDIT}),
}


def is_allowed(role: Role, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS[role]
