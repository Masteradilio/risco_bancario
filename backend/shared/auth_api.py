"""
Módulo de Autenticação e Autorização RBAC
Sistema de Gestão de Risco Bancário

Integração com Windows NTLM/SSO
Perfis: ANALISTA, GESTOR, AUDITOR, ADMIN
Timeout de sessão: 30 minutos
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List
from functools import wraps
import hashlib
import uuid
import logging

from fastapi import HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from jose import JWTError, jwt

# Configurações
SECRET_KEY = "your-secret-key-change-in-production"  # TODO: Mover para .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS E MODELOS
# ============================================================================

class UserRole(str, Enum):
    """Perfis de acesso do sistema"""
    ANALISTA = "ANALISTA"
    GESTOR = "GESTOR"
    AUDITOR = "AUDITOR"
    ADMIN = "ADMIN"


class User(BaseModel):
    """Modelo de usuário"""
    id: str
    nome: str
    email: EmailStr
    matricula: str
    login_windows: str
    role: UserRole
    departamento: Optional[str] = None
    cargo: Optional[str] = None
    is_externo: bool = False
    data_expiracao: Optional[datetime] = None
    ativo: bool = True
    ultimo_login: Optional[datetime] = None


class UserCreate(BaseModel):
    """Modelo para criação de usuário"""
    nome: str = Field(..., min_length=3, max_length=255)
    email: EmailStr
    matricula: str = Field(..., min_length=3, max_length=20)
    login_windows: str = Field(..., min_length=3, max_length=50)
    role: UserRole = UserRole.ANALISTA
    departamento: Optional[str] = None
    cargo: Optional[str] = None
    is_externo: bool = False
    dias_validade: Optional[int] = Field(None, ge=1, le=365, description="Dias até expiração (para externos)")


class UserUpdate(BaseModel):
    """Modelo para atualização de usuário"""
    nome: Optional[str] = None
    role: Optional[UserRole] = None
    departamento: Optional[str] = None
    cargo: Optional[str] = None
    ativo: Optional[bool] = None


class Token(BaseModel):
    """Resposta de token"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60


class TokenData(BaseModel):
    """Dados dentro do token JWT"""
    user_id: str
    email: str
    role: UserRole
    exp: datetime


class AuditLog(BaseModel):
    """Log de atividade do usuário"""
    usuario_id: Optional[str]
    usuario_nome: str
    usuario_role: Optional[UserRole]
    acao: str
    recurso: Optional[str]
    detalhes: Optional[dict]
    ip_address: Optional[str]
    status: str = "SUCESSO"
    erro_mensagem: Optional[str] = None


class SystemError(BaseModel):
    """Log de erro do sistema"""
    nivel: str = "ERROR"
    modulo: Optional[str]
    funcao: Optional[str]
    mensagem: str
    stacktrace: Optional[str]
    usuario_id: Optional[str]
    request_id: Optional[str]
    ip_address: Optional[str]
    request_path: Optional[str]


# ============================================================================
# MAPEAMENTO DE PERMISSÕES
# ============================================================================

PERMISSIONS: dict[UserRole, list[str]] = {
    UserRole.ANALISTA: [
        "view:prinad",
        "view:ecl",
        "view:propensao",
        "classify:individual",
        "classify:batch",
        "calculate:ecl",
    ],
    UserRole.GESTOR: [
        "view:prinad",
        "view:ecl",
        "view:propensao",
        "view:dashboard",
        "view:analytics",
        "classify:individual",
        "classify:batch",
        "calculate:ecl",
        "export:pdf",
        "export:csv",
        "export:bacen",
        "generate:xml",
    ],
    UserRole.AUDITOR: [
        "view:prinad",
        "view:ecl",
        "view:propensao",
        "view:dashboard",
        "view:audit",
        "view:user_activity_logs",
        "export:audit_reports",
        "export:compliance_reports",
    ],
    UserRole.ADMIN: [
        "*",  # Acesso total
    ],
}


# ============================================================================
# STORE TEMPORÁRIO (MOCK - SUBSTITUIR POR BANCO DE DADOS)
# ============================================================================

# Em produção, isso será buscado do MySQL
_users_db: dict[str, dict] = {
    "maria.silva": {
        "id": str(uuid.uuid4()),
        "nome": "Maria Silva",
        "email": "maria.silva@banco.local",
        "matricula": "A12345",
        "login_windows": "maria.silva",
        "role": UserRole.ANALISTA,
        "departamento": "Crédito",
        "cargo": "Analista de Crédito Jr",
        "is_externo": False,
        "ativo": True,
    },
    "joao.santos": {
        "id": str(uuid.uuid4()),
        "nome": "João Santos",
        "email": "joao.santos@banco.local",
        "matricula": "G54321",
        "login_windows": "joao.santos",
        "role": UserRole.GESTOR,
        "departamento": "Riscos",
        "cargo": "Gerente de Riscos",
        "is_externo": False,
        "ativo": True,
    },
    "ana.costa": {
        "id": str(uuid.uuid4()),
        "nome": "Ana Costa",
        "email": "ana.costa@banco.local",
        "matricula": "AU9999",
        "login_windows": "ana.costa",
        "role": UserRole.AUDITOR,
        "departamento": "Auditoria Interna",
        "cargo": "Auditora Sênior",
        "is_externo": False,
        "ativo": True,
    },
    "carlos.admin": {
        "id": str(uuid.uuid4()),
        "nome": "Carlos Admin",
        "email": "carlos.admin@banco.local",
        "matricula": "ADM001",
        "login_windows": "carlos.admin",
        "role": UserRole.ADMIN,
        "departamento": "TI",
        "cargo": "Administrador de Sistemas",
        "is_externo": False,
        "ativo": True,
    },
}

_audit_logs: list[dict] = []
_system_errors: list[dict] = []


# ============================================================================
# FUNÇÕES DE TOKEN JWT
# ============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Cria token JWT de acesso"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Cria token JWT de refresh"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[TokenData]:
    """Decodifica e valida token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenData(
            user_id=payload.get("sub"),
            email=payload.get("email"),
            role=UserRole(payload.get("role")),
            exp=datetime.fromtimestamp(payload.get("exp")),
        )
    except JWTError:
        return None


def hash_token(token: str) -> str:
    """Cria hash SHA256 do token para armazenamento"""
    return hashlib.sha256(token.encode()).hexdigest()


# ============================================================================
# AUTENTICAÇÃO WINDOWS (MOCK - SUBSTITUIR POR NTLM REAL)
# ============================================================================

def authenticate_windows_user(login_windows: str) -> Optional[User]:
    """
    Autentica usuário via Windows NTLM/SSO.
    
    Em produção, usar biblioteca como python-ntlm3 ou pyspnego
    para validar credenciais contra o Active Directory.
    """
    # Mock: busca usuário no store temporário
    user_data = _users_db.get(login_windows)
    
    if not user_data:
        return None
    
    if not user_data.get("ativo", True):
        return None
    
    # Verificar se usuário expirou (externos)
    if user_data.get("data_expiracao"):
        if datetime.now() > user_data["data_expiracao"]:
            return None
    
    return User(**user_data)


# ============================================================================
# DEPENDÊNCIAS FASTAPI
# ============================================================================

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Obtém usuário atual a partir do token JWT"""
    token = credentials.credentials
    token_data = decode_token(token)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Buscar usuário pelo login
    user = None
    for login, data in _users_db.items():
        if data["id"] == token_data.user_id:
            user = User(**data)
            break
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
        )
    
    if not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário desativado",
        )
    
    return user


def require_permission(permission: str):
    """Decorator para exigir permissão específica"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, user: User = Depends(get_current_user), **kwargs):
            if not check_permission(user.role, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permissão '{permission}' negada para perfil {user.role.value}",
                )
            return await func(*args, user=user, **kwargs)
        return wrapper
    return decorator


def require_roles(roles: List[UserRole]):
    """Dependency para exigir um dos perfis especificados"""
    async def check_roles(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso restrito a: {', '.join([r.value for r in roles])}",
            )
        return user
    return check_roles


# ============================================================================
# FUNÇÕES DE PERMISSÃO
# ============================================================================

def check_permission(role: UserRole, permission: str) -> bool:
    """Verifica se o perfil tem a permissão especificada"""
    role_permissions = PERMISSIONS.get(role, [])
    
    # Admin tem acesso total
    if "*" in role_permissions:
        return True
    
    return permission in role_permissions


def get_user_permissions(role: UserRole) -> List[str]:
    """Retorna lista de permissões do perfil"""
    perms = PERMISSIONS.get(role, [])
    if "*" in perms:
        # Coletar todas as permissões menos admin-specific
        all_perms = set()
        for role_perms in PERMISSIONS.values():
            all_perms.update([p for p in role_perms if p != "*"])
        return list(all_perms)
    return perms


# ============================================================================
# FUNÇÕES DE AUDITORIA
# ============================================================================

def log_activity(
    request: Request,
    user: Optional[User],
    acao: str,
    recurso: Optional[str] = None,
    detalhes: Optional[dict] = None,
    status: str = "SUCESSO",
    erro_mensagem: Optional[str] = None,
):
    """Registra atividade do usuário no log de auditoria"""
    log_entry = AuditLog(
        usuario_id=user.id if user else None,
        usuario_nome=user.nome if user else "Sistema",
        usuario_role=user.role if user else None,
        acao=acao,
        recurso=recurso,
        detalhes=detalhes,
        ip_address=request.client.host if request.client else None,
        status=status,
        erro_mensagem=erro_mensagem,
    )
    
    # Mock: adiciona ao store temporário
    _audit_logs.append({
        **log_entry.model_dump(),
        "timestamp": datetime.now().isoformat(),
    })
    
    logger.info(f"[AUDIT] {acao} | {user.nome if user else 'Sistema'} | {status}")


def log_error(
    nivel: str,
    modulo: str,
    mensagem: str,
    funcao: Optional[str] = None,
    stacktrace: Optional[str] = None,
    request: Optional[Request] = None,
    user: Optional[User] = None,
):
    """Registra erro no log de sistema (visível apenas para Admin)"""
    error_entry = SystemError(
        nivel=nivel,
        modulo=modulo,
        funcao=funcao,
        mensagem=mensagem,
        stacktrace=stacktrace,
        usuario_id=user.id if user else None,
        ip_address=request.client.host if request and request.client else None,
        request_path=str(request.url) if request else None,
    )
    
    # Mock: adiciona ao store temporário
    _system_errors.append({
        **error_entry.model_dump(),
        "timestamp": datetime.now().isoformat(),
    })
    
    logger.error(f"[SYSTEM] {nivel} | {modulo} | {mensagem}")


# ============================================================================
# FUNÇÕES DE GERENCIAMENTO DE USUÁRIOS (ADMIN ONLY)
# ============================================================================

def create_user(user_data: UserCreate, created_by: User) -> User:
    """Cria novo usuário (somente Admin)"""
    # Verificar duplicidade
    if user_data.login_windows in _users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Login Windows já existe",
        )
    
    # Calcular data de expiração para externos
    data_expiracao = None
    if user_data.is_externo:
        dias = user_data.dias_validade or 30  # Padrão 30 dias para externos
        data_expiracao = datetime.now() + timedelta(days=dias)
    
    new_user = {
        "id": str(uuid.uuid4()),
        "nome": user_data.nome,
        "email": user_data.email,
        "matricula": user_data.matricula,
        "login_windows": user_data.login_windows,
        "role": user_data.role,
        "departamento": user_data.departamento,
        "cargo": user_data.cargo,
        "is_externo": user_data.is_externo,
        "data_expiracao": data_expiracao,
        "ativo": True,
    }
    
    _users_db[user_data.login_windows] = new_user
    
    return User(**new_user)


def list_users() -> List[User]:
    """Lista todos os usuários"""
    return [User(**data) for data in _users_db.values()]


def get_user_by_id(user_id: str) -> Optional[User]:
    """Busca usuário por ID"""
    for data in _users_db.values():
        if data["id"] == user_id:
            return User(**data)
    return None


def update_user(user_id: str, update_data: UserUpdate) -> Optional[User]:
    """Atualiza usuário"""
    for login, data in _users_db.items():
        if data["id"] == user_id:
            if update_data.nome:
                data["nome"] = update_data.nome
            if update_data.role:
                data["role"] = update_data.role
            if update_data.departamento:
                data["departamento"] = update_data.departamento
            if update_data.cargo:
                data["cargo"] = update_data.cargo
            if update_data.ativo is not None:
                data["ativo"] = update_data.ativo
            return User(**data)
    return None


def delete_user(user_id: str) -> bool:
    """Desativa usuário (soft delete)"""
    for login, data in _users_db.items():
        if data["id"] == user_id:
            data["ativo"] = False
            return True
    return False


def get_audit_logs(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    usuario_id: Optional[str] = None,
    acao: Optional[str] = None,
    limit: int = 100,
) -> List[dict]:
    """Retorna logs de auditoria com filtros"""
    logs = _audit_logs.copy()
    
    # Aplicar filtros
    if usuario_id:
        logs = [l for l in logs if l.get("usuario_id") == usuario_id]
    if acao:
        logs = [l for l in logs if l.get("acao") == acao]
    if start_date:
        logs = [l for l in logs if datetime.fromisoformat(l["timestamp"]) >= start_date]
    if end_date:
        logs = [l for l in logs if datetime.fromisoformat(l["timestamp"]) <= end_date]
    
    # Ordenar por timestamp decrescente e limitar
    logs.sort(key=lambda x: x["timestamp"], reverse=True)
    return logs[:limit]


def get_system_errors(
    nivel: Optional[str] = None,
    modulo: Optional[str] = None,
    limit: int = 100,
) -> List[dict]:
    """Retorna logs de erros do sistema (Admin only)"""
    errors = _system_errors.copy()
    
    if nivel:
        errors = [e for e in errors if e.get("nivel") == nivel]
    if modulo:
        errors = [e for e in errors if e.get("modulo") == modulo]
    
    errors.sort(key=lambda x: x["timestamp"], reverse=True)
    return errors[:limit]


# ============================================================================
# EXPORTS
# ============================================================================

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
    # Auth functions
    "authenticate_windows_user",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "get_current_user",
    "require_permission",
    "require_roles",
    # Permission functions
    "check_permission",
    "get_user_permissions",
    "PERMISSIONS",
    # Audit functions
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
]
