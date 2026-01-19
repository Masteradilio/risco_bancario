/**
 * API Client para o Agente de IA
 */

const API_BASE = 'http://localhost:8000';

export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant' | 'tool';
    content: string;
    toolName?: string;
    createdAt: string;
}

export interface ChatSession {
    id: string;
    titulo: string;
    resumo?: string;
    createdAt: string;
    updatedAt: string;
}

export interface Artifact {
    id: string;
    tipo: string;
    nome: string;
    descricao?: string;
    mimeType: string;
    tamanho: number;
    createdAt: string;
    temVersoes: boolean;
}

export interface ToolInfo {
    name: string;
    description: string;
}

export interface ChatResponse {
    sessionId: string;
    response: string;
    timestamp: string;
    artifactId?: string;
}

/**
 * Envia mensagem para o agente
 */
export async function sendMessage(
    message: string,
    sessionId?: string
): Promise<ChatResponse> {
    const response = await fetch(`${API_BASE}/api/agent/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message,
            session_id: sessionId,
        }),
    });

    if (!response.ok) {
        throw new Error(`Erro ao enviar mensagem: ${response.status}`);
    }

    const data = await response.json();
    return {
        sessionId: data.session_id,
        response: data.response,
        timestamp: data.timestamp,
        artifactId: data.artifact_id,
    };
}

/**
 * Lista sessões do usuário
 */
export async function getSessions(limit = 50): Promise<ChatSession[]> {
    const response = await fetch(`${API_BASE}/api/agent/sessions?limit=${limit}`);

    if (!response.ok) {
        throw new Error(`Erro ao listar sessões: ${response.status}`);
    }

    const data = await response.json();
    return data.map((s: Record<string, unknown>) => ({
        id: s.id,
        titulo: s.titulo,
        resumo: s.resumo,
        createdAt: s.createdAt || s.created_at,
        updatedAt: s.updatedAt || s.updated_at,
    }));
}

/**
 * Cria nova sessão
 */
export async function createSession(titulo = 'Nova Conversa'): Promise<ChatSession> {
    const response = await fetch(`${API_BASE}/api/agent/sessions`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ titulo }),
    });

    if (!response.ok) {
        throw new Error(`Erro ao criar sessão: ${response.status}`);
    }

    const data = await response.json();
    return {
        id: data.id,
        titulo: data.titulo,
        resumo: data.resumo,
        createdAt: data.createdAt || data.created_at,
        updatedAt: data.updatedAt || data.updated_at,
    };
}

/**
 * Obtém mensagens de uma sessão
 */
export async function getSessionMessages(sessionId: string): Promise<ChatMessage[]> {
    const response = await fetch(`${API_BASE}/api/agent/sessions/${sessionId}/messages`);

    if (!response.ok) {
        throw new Error(`Erro ao obter mensagens: ${response.status}`);
    }

    const data = await response.json();
    return data.map((m: Record<string, unknown>) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        toolName: m.toolName || m.tool_name,
        createdAt: m.createdAt || m.created_at,
    }));
}

/**
 * Exclui uma sessão
 */
export async function deleteSession(sessionId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/api/agent/sessions/${sessionId}`, {
        method: 'DELETE',
    });

    if (!response.ok) {
        throw new Error(`Erro ao excluir sessão: ${response.status}`);
    }
}

/**
 * Lista artefatos de uma sessão
 */
export async function getArtifacts(sessionId?: string): Promise<Artifact[]> {
    const url = sessionId
        ? `${API_BASE}/api/agent/artifacts?session_id=${sessionId}`
        : `${API_BASE}/api/agent/artifacts`;

    const response = await fetch(url);

    if (!response.ok) {
        throw new Error(`Erro ao listar artefatos: ${response.status}`);
    }

    const data = await response.json();
    return data.map((a: Record<string, unknown>) => ({
        id: a.id,
        tipo: a.tipo,
        nome: a.nome,
        descricao: a.descricao,
        mimeType: a.mimeType || a.mime_type,
        tamanho: a.tamanho,
        createdAt: a.createdAt || a.created_at,
        temVersoes: a.temVersoes || a.tem_versoes || false,
    }));
}

/**
 * Obtém URL de visualização de um artefato
 */
export function getArtifactViewUrl(artifactId: string, versao: 'dark' | 'light' = 'dark'): string {
    return `${API_BASE}/api/agent/artifacts/${artifactId}?versao=${versao}`;
}

/**
 * Obtém URL de download de um artefato
 */
export function getArtifactDownloadUrl(artifactId: string, versao: 'dark' | 'light' = 'dark'): string {
    return `${API_BASE}/api/agent/artifacts/${artifactId}/download?versao=${versao}`;
}

/**
 * Exclui um artefato
 */
export async function deleteArtifact(artifactId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/api/agent/artifacts/${artifactId}`, {
        method: 'DELETE',
    });

    if (!response.ok) {
        throw new Error(`Erro ao excluir artefato: ${response.status}`);
    }
}

/**
 * Lista ferramentas disponíveis
 */
export async function getTools(): Promise<ToolInfo[]> {
    const response = await fetch(`${API_BASE}/api/agent/tools`);

    if (!response.ok) {
        throw new Error(`Erro ao listar ferramentas: ${response.status}`);
    }

    return response.json();
}

export interface FileUpload {
    id: string;
    nome: string;
    tipo: string;
    tamanho: number;
    createdAt?: string;
}

/**
 * Faz upload de arquivo para contexto do agente
 */
export async function uploadFile(file: File, sessionId: string): Promise<FileUpload> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', sessionId);

    const response = await fetch(`${API_BASE}/api/agent/upload`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `Erro ao enviar arquivo: ${response.status}`);
    }

    return response.json();
}

/**
 * Lista uploads de uma sessão
 */
export async function getUploads(sessionId: string): Promise<FileUpload[]> {
    const response = await fetch(`${API_BASE}/api/agent/uploads?session_id=${sessionId}`);

    if (!response.ok) {
        throw new Error(`Erro ao listar uploads: ${response.status}`);
    }

    return response.json();
}

/**
 * Exclui um upload
 */
export async function deleteUpload(uploadId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/api/agent/uploads/${uploadId}`, {
        method: 'DELETE',
    });

    if (!response.ok) {
        throw new Error(`Erro ao excluir upload: ${response.status}`);
    }
}

export const agentApi = {
    sendMessage,
    getSessions,
    createSession,
    getSessionMessages,
    deleteSession,
    getArtifacts,
    getArtifactViewUrl,
    getArtifactDownloadUrl,
    deleteArtifact,
    getTools,
    uploadFile,
    getUploads,
    deleteUpload,
};

export default agentApi;

