"""
Módulo de Autenticação e RBAC
Backend Shared Module

Exports principais:
- UserRole, User, UserCreate, UserUpdate
- authenticate_windows_user, get_current_user
- require_permission, require_roles
- check_permission, get_user_permissions
- log_activity, log_error
- router (FastAPI router para endpoints de auth)
"""

from .auth_api import (
    # Enums
    UserRole,
    # Models
    User,
    UserCreate,
    UserUpdate,
    Token,
    TokenData,
    AuditLog,
    SystemError,
    # Auth functions
    authenticate_windows_user,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    require_permission,
    require_roles,
    # Permission functions
    check_permission,
    get_user_permissions,
    PERMISSIONS,
    # Audit functions
    log_activity,
    log_error,
    get_audit_logs,
    get_system_errors,
    # User management
    create_user,
    list_users,
    get_user_by_id,
    update_user,
    delete_user,
)

from .auth_router import router as auth_router

__all__ = [
    # Enums
    "UserRole",
    # Models
    "User",
    "UserCreate", 
    "UserUpdate",
    "Token",
    "TokenData",
    "AuditLog",
    "SystemError",
    # Auth
    "authenticate_windows_user",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "get_current_user",
    "require_permission",
    "require_roles",
    # Permissions
    "check_permission",
    "get_user_permissions",
    "PERMISSIONS",
    # Audit
    "log_activity",
    "log_error",
    "get_audit_logs",
    "get_system_errors",
    # User management
    "create_user",
    "list_users",
    "get_user_by_id",
    "update_user",
    "delete_user",
    # Router
    "auth_router",
]
