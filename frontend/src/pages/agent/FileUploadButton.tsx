/**
 * Componente de Upload de Arquivos
 * Permite anexar arquivos ao contexto do agente
 */

import { useState, useRef } from 'react';
import {
    Paperclip,
    X,
    File,
    FileSpreadsheet,
    FileText,
    FileImage,
    Loader2
} from 'lucide-react';
import { uploadFile, FileUpload, deleteUpload } from '../../lib/api/agent_api';
import { cn } from '@/lib/utils';

interface FileUploadProps {
    sessionId?: string;
    onUploadComplete?: (upload: FileUpload) => void;
    onError?: (error: string) => void;
}

// Ícone por tipo
const getFileIcon = (tipo: string) => {
    switch (tipo) {
        case 'excel':
        case 'csv':
            return <FileSpreadsheet className="w-4 h-4 text-green-400" />;
        case 'image':
            return <FileImage className="w-4 h-4 text-blue-400" />;
        case 'txt':
        case 'markdown':
        case 'docx':
            return <FileText className="w-4 h-4 text-gray-400" />;
        default:
            return <File className="w-4 h-4 text-muted-foreground" />;
    }
};

// Formatar tamanho
const formatSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

export function FileUploadButton({ sessionId, onUploadComplete, onError }: FileUploadProps) {
    const [uploading, setUploading] = useState(false);
    const [uploadedFiles, setUploadedFiles] = useState<FileUpload[]>([]);
    const inputRef = useRef<HTMLInputElement>(null);

    const handleClick = () => {
        inputRef.current?.click();
    };

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (!files || files.length === 0 || !sessionId) return;

        setUploading(true);

        try {
            for (const file of Array.from(files)) {
                const result = await uploadFile(file, sessionId);
                setUploadedFiles(prev => [...prev, result]);
                onUploadComplete?.(result);
            }
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Erro ao enviar arquivo';
            onError?.(message);
        } finally {
            setUploading(false);
            if (inputRef.current) {
                inputRef.current.value = '';
            }
        }
    };

    const handleRemove = async (uploadId: string) => {
        try {
            await deleteUpload(uploadId);
            setUploadedFiles(prev => prev.filter(f => f.id !== uploadId));
        } catch (error) {
            console.error('Erro ao remover arquivo:', error);
        }
    };

    return (
        <div className="flex flex-col gap-2">
            {/* Arquivos anexados */}
            {uploadedFiles.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-2">
                    {uploadedFiles.map(file => (
                        <div
                            key={file.id}
                            className="flex items-center gap-2 bg-secondary/50 border border-border rounded-lg px-2 py-1 text-xs"
                        >
                            {getFileIcon(file.tipo)}
                            <span className="text-foreground max-w-[120px] truncate">
                                {file.nome}
                            </span>
                            <span className="text-muted-foreground">
                                ({formatSize(file.tamanho)})
                            </span>
                            <button
                                onClick={() => handleRemove(file.id)}
                                className="p-0.5 hover:bg-destructive/20 rounded transition-colors"
                            >
                                <X className="w-3 h-3 text-destructive" />
                            </button>
                        </div>
                    ))}
                </div>
            )}

            {/* Botão de upload */}
            <div className="flex items-center">
                <input
                    ref={inputRef}
                    type="file"
                    onChange={handleFileChange}
                    multiple
                    accept=".csv,.xlsx,.xls,.txt,.md,.docx,.png,.jpg,.jpeg"
                    className="hidden"
                />
                <button
                    type="button"
                    onClick={handleClick}
                    disabled={uploading || !sessionId}
                    className={cn(
                        "p-2 rounded-lg transition-all",
                        "hover:bg-secondary text-muted-foreground hover:text-foreground",
                        "disabled:opacity-50 disabled:cursor-not-allowed"
                    )}
                    title="Anexar arquivo (CSV, Excel, TXT, Word, imagem)"
                >
                    {uploading ? (
                        <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                        <Paperclip className="w-5 h-5" />
                    )}
                </button>
            </div>
        </div>
    );
}

export default FileUploadButton;
