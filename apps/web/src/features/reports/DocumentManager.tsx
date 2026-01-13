import { useState, useEffect } from 'react';
import { useSettings } from '../../contexts/SettingsContext';
import { createApiClient } from '../../lib/apiClient';

interface Document {
    id: number;
    type: string;
    filename: string;
    ext: string;
    created_at: string;
}

interface Props {
    companyId: string;
}

export default function DocumentManager({ companyId }: Props) {
    const { apiBaseUrl } = useSettings();
    const [documents, setDocuments] = useState<Document[]>([]);
    const [isUploading, setIsUploading] = useState(false);

    useEffect(() => {
        if (companyId) {
            fetchDocuments();
        }
    }, [companyId]);

    const fetchDocuments = async () => {
        try {
            const client = createApiClient(apiBaseUrl);
            const resp = await client.get(`/documents/${companyId}`);
            setDocuments(resp.data);
        } catch (error) {
            console.error("Failed to fetch documents", error);
        }
    };

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (!files || files.length === 0) return;

        setIsUploading(true);
        const formData = new FormData();
        formData.append('file', files[0]);
        formData.append('company_id', companyId);

        try {
            // Native fetch for multipart since apiClient might need config tweak
            // But apiClient uses axios, it should handle FormData automatically if not content-type forced.
            const client = createApiClient(apiBaseUrl);
            const uploadResp = await client.post('/documents/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });

            const docId = uploadResp.data.document_id;
            if (docId) {
                // Auto-trigger parsing
                await client.post(`/documents/${docId}/parse`);
            }

            await fetchDocuments();
        } catch (error) {
            console.error("Upload failed", error);
            alert("업로드 실패");
        } finally {
            setIsUploading(false);
            // Reset input
            e.target.value = '';
        }
    };

    return (
        <div className="bg-card-dark border border-border-dark rounded-xl p-6 mb-6">
            <h3 className="font-bold text-white mb-4 flex items-center gap-2">
                <span className="material-symbols-outlined text-green-400">folder_open</span>
                IR/사업보고서 문서 관리 (RAG 소스)
            </h3>

            <div className="flex flex-col gap-4">
                {/* Upload Area */}
                <div className="border-2 border-dashed border-gray-600 rounded-lg p-6 text-center hover:border-gray-400 transition-colors">
                    <input
                        type="file"
                        id="file-upload"
                        className="hidden"
                        onChange={handleFileUpload}
                        accept=".pdf,.docx,.txt"
                        disabled={!companyId || isUploading}
                    />
                    <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center gap-2">
                        {isUploading ? (
                            <span className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin"></span>
                        ) : (
                            <span className="material-symbols-outlined text-3xl text-gray-400">cloud_upload</span>
                        )}
                        <span className="text-sm text-gray-300 font-medium">
                            {isUploading ? '업로드 중...' : '클릭하여 PDF/문서 업로드'}
                        </span>
                        <span className="text-xs text-gray-500">지원 형식: PDF, DOCX, TXT (최대 10MB)</span>
                    </label>
                </div>

                {/* File List */}
                <div className="flex flex-col gap-2">
                    {documents.map((doc) => (
                        <div key={doc.id} className="flex items-center justify-between bg-white/5 px-4 py-3 rounded-lg border border-white/10">
                            <div className="flex items-center gap-3">
                                <span className="material-symbols-outlined text-gray-400">description</span>
                                <div className="flex flex-col">
                                    <span className="text-sm text-gray-200 font-medium">{doc.filename}</span>
                                    <span className="text-xs text-gray-500">{new Date(doc.created_at).toLocaleString()}</span>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className={`text-[10px] px-2 py-0.5 rounded border ${doc.type === 'UPLOAD' ? 'border-blue-500/30 text-blue-400' : 'border-gray-500 text-gray-400'}`}>
                                    {doc.type}
                                </span>
                                {/* Future: Parse Status */}
                                <span className="text-xs text-yellow-500 flex items-center gap-1">
                                    <span className="w-1.5 h-1.5 bg-yellow-500 rounded-full"></span>
                                    대기중
                                </span>
                            </div>
                        </div>
                    ))}
                    {documents.length === 0 && (
                        <div className="text-center text-xs text-gray-600 py-2">
                            등록된 문서가 없습니다.
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
