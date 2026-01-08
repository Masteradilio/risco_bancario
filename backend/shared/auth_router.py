"""
Router de Autenticação e Gerenciamento de Usuários
Sistema de Gestão de Risco Bancário

Endpoints:
- POST /auth/login - Login via Windows SSO
- POST /auth/logout - Encerra sessão
- POST /auth/refresh - Renova token
- GET /auth/me - Dados do usuário atual
- CRUD /usuarios - Gerenciamento de usuários (Admin)
- GET /auditoria/logs - Logs de atividade (Auditor+)
- GET /sistema/erros - Logs de erros (Admin)
"""

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
from pydantic import BaseModel, EmailStr

from .auth_api import (
    UserRole,
    User,
    UserCreate,
    UserUpdate,
    Token,
    authenticate_windows_user,
    create_access_token,
    create_refresh_token,
    get_current_user,
    require_roles,
    check_permission,
    get_user_permissions,
    log_activity,
    create_user,
    list_users,
    get_user_by_id,
    update_user,
    delete_user,
    get_audit_logs,
    get_system_errors,
)


# ============================================================================
# ROUTER
# ============================================================================

router = APIRouter(tags=["Autenticação e Usuários"])


# ============================================================================
# MODELOS DE REQUEST/RESPONSE
# ============================================================================

class LoginRequest(BaseModel):
    """Request para login"""
    login_windows: str


class LoginResponse(BaseModel):
    """Response do login"""
    user: User
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    """Request para refresh de token"""
    refresh_token: str


class UserResponse(BaseModel):
    """Response de usuário (sem dados sensíveis)"""
    id: str
    nome: str
    email: EmailStr
    matricula: str
    role: UserRole
    departamento: Optional[str]
    cargo: Optional[str]
    is_externo: bool
    ativo: bool
    permissions: List[str]


class AuditLogResponse(BaseModel):
    """Response de log de auditoria"""
    usuario_id: Optional[str]
    usuario_nome: str
    usuario_role: Optional[str]
    acao: str
    recurso: Optional[str]
    detalhes: Optional[dict]
    ip_address: Optional[str]
    status: str
    timestamp: str


class SystemErrorResponse(BaseModel):
    """Response de erro do sistema"""
    nivel: str
    modulo: Optional[str]
    funcao: Optional[str]
    mensagem: str
    timestamp: str


# ============================================================================
# ENDPOINTS DE AUTENTICAÇÃO
# ============================================================================

@router.post("/auth/login", response_model=LoginResponse)
async def login(request: Request, login_data: LoginRequest):
    """
    Autentica usuário via Windows NTLM/SSO.
    
    Em produção, o login_windows será obtido automaticamente
    via headers NTLM do IIS/nginx.
    """
    user = authenticate_windows_user(login_data.login_windows)
    
    if not user:
        log_activity(
            request=request,
            user=None,
            acao="LOGIN_FALHA",
            detalhes={"login_tentado": login_data.login_windows},
            status="FALHA",
            erro_mensagem="Usuário não encontrado ou inativo",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas ou usuário não cadastrado",
        )
    
    # Criar tokens
    token_data = {
        "sub": user.id,
        "email": user.email,
        "role": user.role.value,
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    # Log de sucesso
    log_activity(
        request=request,
        user=user,
        acao="LOGIN",
        detalhes={"role": user.role.value},
    )
    
    return LoginResponse(
        user=user,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=30 * 60,  # 30 minutos em segundos
    )


@router.post("/auth/logout")
async def logout(request: Request, user: User = Depends(get_current_user)):
    """Encerra sessão do usuário atual."""
    log_activity(
        request=request,
        user=user,
        acao="LOGOUT",
    )
    return {"message": "Sessão encerrada com sucesso"}


@router.post("/auth/refresh", response_model=Token)
async def refresh_token(request: Request, refresh_data: RefreshRequest):
    """Renova token de acesso usando refresh token."""
    from .auth_api import decode_token
    
    token_data = decode_token(refresh_data.refresh_token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou expirado",
        )
    
    # Criar novo access token
    new_token_data = {
        "sub": token_data.user_id,
        "email": token_data.email,
        "role": token_data.role.value,
    }
    new_access_token = create_access_token(new_token_data)
    new_refresh_token = create_refresh_token(new_token_data)
    
    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
    )


@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(user: User = Depends(get_current_user)):
    """Retorna dados do usuário atual com suas permissões."""
    permissions = get_user_permissions(user.role)
    return UserResponse(
        id=user.id,
        nome=user.nome,
        email=user.email,
        matricula=user.matricula,
        role=user.role,
        departamento=user.departamento,
        cargo=user.cargo,
        is_externo=user.is_externo,
        ativo=user.ativo,
        permissions=permissions,
    )


# ============================================================================
# ENDPOINTS DE GERENCIAMENTO DE USUÁRIOS (ADMIN ONLY)
# ============================================================================

@router.get("/usuarios", response_model=List[UserResponse])
async def listar_usuarios(
    user: User = Depends(require_roles([UserRole.ADMIN]))
):
    """Lista todos os usuários do sistema. (Admin only)"""
    users = list_users()
    return [
        UserResponse(
            id=u.id,
            nome=u.nome,
            email=u.email,
            matricula=u.matricula,
            role=u.role,
            departamento=u.departamento,
            cargo=u.cargo,
            is_externo=u.is_externo,
            ativo=u.ativo,
            permissions=get_user_permissions(u.role),
        )
        for u in users
    ]


@router.post("/usuarios", response_model=UserResponse)
async def criar_usuario(
    request: Request,
    user_data: UserCreate,
    user: User = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Cria novo usuário. (Admin only)
    
    Para auditores externos, definir is_externo=true.
    A conta expira automaticamente após dias_validade (padrão 30).
    """
    new_user = create_user(user_data, user)
    
    log_activity(
        request=request,
        user=user,
        acao="CRIAR_USUARIO",
        recurso=f"/usuarios/{new_user.id}",
        detalhes={
            "novo_usuario": new_user.nome,
            "role": new_user.role.value,
            "is_externo": new_user.is_externo,
        },
    )
    
    return UserResponse(
        id=new_user.id,
        nome=new_user.nome,
        email=new_user.email,
        matricula=new_user.matricula,
        role=new_user.role,
        departamento=new_user.departamento,
        cargo=new_user.cargo,
        is_externo=new_user.is_externo,
        ativo=new_user.ativo,
        permissions=get_user_permissions(new_user.role),
    )


@router.get("/usuarios/{user_id}", response_model=UserResponse)
async def obter_usuario(
    user_id: str,
    user: User = Depends(get_current_user)
):
    """
    Obtém dados de um usuário.
    
    Admin pode ver qualquer usuário.
    Outros usuários só podem ver seus próprios dados.
    """
    # Verificar permissão
    if user.role != UserRole.ADMIN and user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode visualizar seus próprios dados",
        )
    
    target_user = get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )
    
    return UserResponse(
        id=target_user.id,
        nome=target_user.nome,
        email=target_user.email,
        matricula=target_user.matricula,
        role=target_user.role,
        departamento=target_user.departamento,
        cargo=target_user.cargo,
        is_externo=target_user.is_externo,
        ativo=target_user.ativo,
        permissions=get_user_permissions(target_user.role),
    )


@router.put("/usuarios/{user_id}", response_model=UserResponse)
async def atualizar_usuario(
    request: Request,
    user_id: str,
    update_data: UserUpdate,
    user: User = Depends(require_roles([UserRole.ADMIN]))
):
    """Atualiza dados de um usuário. (Admin only)"""
    updated_user = update_user(user_id, update_data)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )
    
    log_activity(
        request=request,
        user=user,
        acao="ATUALIZAR_USUARIO",
        recurso=f"/usuarios/{user_id}",
        detalhes={"campos_atualizados": update_data.model_dump(exclude_none=True)},
    )
    
    return UserResponse(
        id=updated_user.id,
        nome=updated_user.nome,
        email=updated_user.email,
        matricula=updated_user.matricula,
        role=updated_user.role,
        departamento=updated_user.departamento,
        cargo=updated_user.cargo,
        is_externo=updated_user.is_externo,
        ativo=updated_user.ativo,
        permissions=get_user_permissions(updated_user.role),
    )


@router.delete("/usuarios/{user_id}")
async def desativar_usuario(
    request: Request,
    user_id: str,
    user: User = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Desativa um usuário (soft delete). (Admin only)
    
    O usuário não é removido do banco, apenas marcado como inativo.
    """
    if user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode desativar sua própria conta",
        )
    
    success = delete_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )
    
    log_activity(
        request=request,
        user=user,
        acao="DESATIVAR_USUARIO",
        recurso=f"/usuarios/{user_id}",
    )
    
    return {"message": "Usuário desativado com sucesso"}


# ============================================================================
# ENDPOINTS DE AUDITORIA (AUDITOR + ADMIN)
# ============================================================================

@router.get("/auditoria/logs", response_model=List[AuditLogResponse])
async def listar_logs_auditoria(
    request: Request,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    usuario_id: Optional[str] = None,
    acao: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    user: User = Depends(require_roles([UserRole.AUDITOR, UserRole.ADMIN]))
):
    """
    Lista logs de atividade para auditoria. (Auditor, Admin)
    
    Filtros disponíveis:
    - start_date: Data inicial
    - end_date: Data final
    - usuario_id: ID de usuário específico
    - acao: Tipo de ação (LOGIN, LOGOUT, CALCULAR_ECL, etc.)
    """
    logs = get_audit_logs(
        start_date=start_date,
        end_date=end_date,
        usuario_id=usuario_id,
        acao=acao,
        limit=limit,
    )
    
    log_activity(
        request=request,
        user=user,
        acao="CONSULTAR_LOGS_AUDITORIA",
        detalhes={"filtros": {"start_date": str(start_date), "end_date": str(end_date), "acao": acao}},
    )
    
    return [
        AuditLogResponse(
            usuario_id=log.get("usuario_id"),
            usuario_nome=log.get("usuario_nome", ""),
            usuario_role=log.get("usuario_role"),
            acao=log.get("acao", ""),
            recurso=log.get("recurso"),
            detalhes=log.get("detalhes"),
            ip_address=log.get("ip_address"),
            status=log.get("status", "SUCESSO"),
            timestamp=log.get("timestamp", ""),
        )
        for log in logs
    ]


# ============================================================================
# ENDPOINTS DE LOGS DE SISTEMA (ADMIN ONLY)
# ============================================================================

@router.get("/sistema/erros", response_model=List[SystemErrorResponse])
async def listar_erros_sistema(
    request: Request,
    nivel: Optional[str] = None,
    modulo: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    user: User = Depends(require_roles([UserRole.ADMIN]))
):
    """
    Lista logs de erros do sistema. (Admin only)
    
    Filtros disponíveis:
    - nivel: DEBUG, INFO, WARNING, ERROR, CRITICAL
    - modulo: prinad, ecl, propensao, auth
    """
    errors = get_system_errors(nivel=nivel, modulo=modulo, limit=limit)
    
    return [
        SystemErrorResponse(
            nivel=error.get("nivel", "ERROR"),
            modulo=error.get("modulo"),
            funcao=error.get("funcao"),
            mensagem=error.get("mensagem", ""),
            timestamp=error.get("timestamp", ""),
        )
        for error in errors
    ]


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ["router"]
