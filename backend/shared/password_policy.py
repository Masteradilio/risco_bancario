# -*- coding: utf-8 -*-
"""
Módulo de Política de Senhas
============================

Implementa política de senhas conforme boas práticas de segurança bancária:
- Complexidade mínima (12 caracteres, upper, lower, number, special)
- Expiração a cada 90 dias
- Histórico para impedir reutilização (últimas 5)

Autor: Sistema ECL
Data: Janeiro 2026
"""

import re
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ForcaSenha(str, Enum):
    """Níveis de força da senha."""
    MUITO_FRACA = "muito_fraca"
    FRACA = "fraca"
    MEDIA = "media"
    FORTE = "forte"
    MUITO_FORTE = "muito_forte"


@dataclass
class ResultadoValidacao:
    """Resultado da validação de senha."""
    valida: bool
    forca: ForcaSenha
    score: int  # 0-100
    erros: List[str]
    avisos: List[str]


class PasswordPolicy:
    """
    Política de senhas para ambiente bancário.
    
    Requisitos:
    - Mínimo 12 caracteres
    - Pelo menos 1 letra maiúscula
    - Pelo menos 1 letra minúscula
    - Pelo menos 1 número
    - Pelo menos 1 caractere especial
    - Não pode conter informações do usuário
    - Não pode reutilizar últimas 5 senhas
    - Expira a cada 90 dias
    """
    
    # Configurações
    MIN_LENGTH = 12
    MAX_LENGTH = 128
    MIN_UPPERCASE = 1
    MIN_LOWERCASE = 1
    MIN_DIGITS = 1
    MIN_SPECIAL = 1
    EXPIRATION_DAYS = 90
    HISTORY_SIZE = 5
    
    # Caracteres especiais aceitos
    SPECIAL_CHARS = r"!@#$%^&*()_+-=[]{}|;':\",./<>?"
    
    # Padrões proibidos (sequências comuns)
    FORBIDDEN_PATTERNS = [
        r"123456", r"654321", r"qwerty", r"asdfgh", r"zxcvbn",
        r"abcdef", r"password", r"senha", r"admin", r"banco"
    ]
    
    def __init__(self):
        """Inicializa a política de senhas."""
        # Store de histórico de senhas por usuário
        self._historico: Dict[str, List[str]] = {}
        # Store de datas de última troca
        self._ultima_troca: Dict[str, datetime] = {}
    
    def validar_senha(
        self,
        senha: str,
        usuario_id: str = None,
        nome_usuario: str = None,
        email: str = None
    ) -> ResultadoValidacao:
        """
        Valida uma senha contra a política.
        
        Args:
            senha: Senha a validar
            usuario_id: ID do usuário (para verificar histórico)
            nome_usuario: Nome do usuário (para evitar inclusão na senha)
            email: Email do usuário
            
        Returns:
            ResultadoValidacao com detalhes
        """
        erros = []
        avisos = []
        score = 0
        
        # 1. Verificar comprimento
        if len(senha) < self.MIN_LENGTH:
            erros.append(f"Senha deve ter no mínimo {self.MIN_LENGTH} caracteres")
        else:
            score += 20
            if len(senha) >= 16:
                score += 10
        
        if len(senha) > self.MAX_LENGTH:
            erros.append(f"Senha não pode exceder {self.MAX_LENGTH} caracteres")
        
        # 2. Verificar maiúsculas
        uppercase_count = len(re.findall(r"[A-Z]", senha))
        if uppercase_count < self.MIN_UPPERCASE:
            erros.append("Senha deve conter pelo menos 1 letra maiúscula")
        else:
            score += 15
        
        # 3. Verificar minúsculas
        lowercase_count = len(re.findall(r"[a-z]", senha))
        if lowercase_count < self.MIN_LOWERCASE:
            erros.append("Senha deve conter pelo menos 1 letra minúscula")
        else:
            score += 15
        
        # 4. Verificar números
        digit_count = len(re.findall(r"\d", senha))
        if digit_count < self.MIN_DIGITS:
            erros.append("Senha deve conter pelo menos 1 número")
        else:
            score += 15
        
        # 5. Verificar caracteres especiais
        special_count = len(re.findall(rf"[{re.escape(self.SPECIAL_CHARS)}]", senha))
        if special_count < self.MIN_SPECIAL:
            erros.append(f"Senha deve conter pelo menos 1 caractere especial ({self.SPECIAL_CHARS[:10]}...)")
        else:
            score += 20
        
        # 6. Verificar padrões proibidos
        senha_lower = senha.lower()
        for pattern in self.FORBIDDEN_PATTERNS:
            if pattern in senha_lower:
                erros.append(f"Senha contém padrão proibido: {pattern}")
                score -= 10
        
        # 7. Verificar informações do usuário
        if nome_usuario:
            partes_nome = nome_usuario.lower().split()
            for parte in partes_nome:
                if len(parte) >= 3 and parte in senha_lower:
                    erros.append("Senha não pode conter seu nome")
                    score -= 10
        
        if email:
            usuario_email = email.split("@")[0].lower()
            if len(usuario_email) >= 3 and usuario_email in senha_lower:
                erros.append("Senha não pode conter seu email")
                score -= 10
        
        # 8. Verificar histórico
        if usuario_id and self._esta_no_historico(usuario_id, senha):
            erros.append(f"Senha foi usada recentemente (últimas {self.HISTORY_SIZE})")
            score -= 20
        
        # 9. Calcular variação de caracteres (entropia simplificada)
        charset_size = 0
        if uppercase_count > 0:
            charset_size += 26
        if lowercase_count > 0:
            charset_size += 26
        if digit_count > 0:
            charset_size += 10
        if special_count > 0:
            charset_size += len(self.SPECIAL_CHARS)
        
        if charset_size >= 70 and len(senha) >= 14:
            score += 5
        
        # Normalizar score
        score = max(0, min(100, score))
        
        # Determinar força
        if score >= 80:
            forca = ForcaSenha.MUITO_FORTE
        elif score >= 60:
            forca = ForcaSenha.FORTE
        elif score >= 40:
            forca = ForcaSenha.MEDIA
        elif score >= 20:
            forca = ForcaSenha.FRACA
        else:
            forca = ForcaSenha.MUITO_FRACA
        
        # Avisos (não impedem validação)
        if len(senha) < 14:
            avisos.append("Recomendado usar 14+ caracteres para maior segurança")
        if special_count == 1:
            avisos.append("Usar mais caracteres especiais aumenta a segurança")
        
        return ResultadoValidacao(
            valida=len(erros) == 0,
            forca=forca,
            score=score,
            erros=erros,
            avisos=avisos
        )
    
    def hash_senha(self, senha: str) -> str:
        """
        Cria hash seguro da senha.
        
        NOTA: Em produção, usar bcrypt ou argon2.
        
        Args:
            senha: Senha em texto plano
            
        Returns:
            Hash SHA256 da senha (para demo)
        """
        # Em produção: usar bcrypt.hashpw(senha.encode(), bcrypt.gensalt())
        return hashlib.sha256(senha.encode()).hexdigest()
    
    def verificar_senha(self, senha: str, hash_armazenado: str) -> bool:
        """
        Verifica se a senha corresponde ao hash.
        
        Args:
            senha: Senha em texto plano
            hash_armazenado: Hash armazenado
            
        Returns:
            True se corresponde
        """
        # Em produção: usar bcrypt.checkpw(senha.encode(), hash_armazenado)
        return self.hash_senha(senha) == hash_armazenado
    
    def adicionar_ao_historico(self, usuario_id: str, senha_hash: str) -> None:
        """
        Adiciona hash de senha ao histórico do usuário.
        
        Args:
            usuario_id: ID do usuário
            senha_hash: Hash da senha
        """
        if usuario_id not in self._historico:
            self._historico[usuario_id] = []
        
        self._historico[usuario_id].insert(0, senha_hash)
        
        # Manter apenas últimas N
        if len(self._historico[usuario_id]) > self.HISTORY_SIZE:
            self._historico[usuario_id] = self._historico[usuario_id][:self.HISTORY_SIZE]
        
        # Registrar data da troca
        self._ultima_troca[usuario_id] = datetime.now()
    
    def _esta_no_historico(self, usuario_id: str, senha: str) -> bool:
        """Verifica se senha já foi usada recentemente."""
        if usuario_id not in self._historico:
            return False
        
        senha_hash = self.hash_senha(senha)
        return senha_hash in self._historico[usuario_id]
    
    def verificar_expiracao(self, usuario_id: str) -> Dict:
        """
        Verifica status de expiração da senha.
        
        Args:
            usuario_id: ID do usuário
            
        Returns:
            Dict com status de expiração
        """
        ultima_troca = self._ultima_troca.get(usuario_id)
        
        if not ultima_troca:
            return {
                "expirada": True,
                "dias_desde_troca": None,
                "dias_restantes": 0,
                "mensagem": "Senha nunca foi definida ou troca obrigatória"
            }
        
        dias_desde_troca = (datetime.now() - ultima_troca).days
        dias_restantes = self.EXPIRATION_DAYS - dias_desde_troca
        
        return {
            "expirada": dias_restantes <= 0,
            "dias_desde_troca": dias_desde_troca,
            "dias_restantes": max(0, dias_restantes),
            "aviso_expiracao": 0 < dias_restantes <= 7,
            "data_expiracao": (ultima_troca + timedelta(days=self.EXPIRATION_DAYS)).isoformat(),
            "mensagem": (
                "Senha expirada. Troque imediatamente." if dias_restantes <= 0
                else f"Senha expira em {dias_restantes} dias" if dias_restantes <= 7
                else None
            )
        }
    
    def gerar_sugestao_senha(self) -> str:
        """
        Gera uma senha aleatória que atende à política.
        
        Returns:
            Senha gerada
        """
        import secrets
        import string
        
        # Garantir requisitos mínimos
        senha = [
            secrets.choice(string.ascii_uppercase),  # 1 maiúscula
            secrets.choice(string.ascii_lowercase),  # 1 minúscula
            secrets.choice(string.digits),           # 1 número
            secrets.choice(self.SPECIAL_CHARS[:10])  # 1 especial
        ]
        
        # Completar com caracteres aleatórios
        todos_chars = string.ascii_letters + string.digits + self.SPECIAL_CHARS[:10]
        for _ in range(self.MIN_LENGTH - 4):
            senha.append(secrets.choice(todos_chars))
        
        # Embaralhar
        import random
        random.shuffle(senha)
        
        return "".join(senha)


# Instância global
_password_policy: Optional[PasswordPolicy] = None


def get_password_policy() -> PasswordPolicy:
    """Obtém ou cria instância da política de senhas."""
    global _password_policy
    if _password_policy is None:
        _password_policy = PasswordPolicy()
    return _password_policy


__all__ = [
    "ForcaSenha",
    "ResultadoValidacao",
    "PasswordPolicy",
    "get_password_policy"
]
