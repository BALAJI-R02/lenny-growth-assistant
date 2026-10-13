// Shared TypeScript types

export interface Citation {
  ref: number;
  episode: string;
  guest: string;
  source_path: string;
  snippet: string;
}

export interface ChunkResult {
  id: string;
  episode: string;
  guest: string;
  source_path: string;
  text: string;
  score: number;
}

export interface Message {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  citations: Citation[];
  route?: string;
  provider?: string;
  model?: string;
  latency_ms?: number;
  artifact_id?: string;
  retrieval_chunks: ChunkResult[];
  created_at: string;
}

export interface Session {
  id: string;
  created_at: string;
  user_meta: Record<string, unknown>;
}

export interface Artifact {
  id: string;
  session_id: string;
  type: 'markdown' | 'html';
  title: string;
  content: string;
  created_at: string;
}

export interface HealthResponse {
  status: string;
  db: string;
  llm: string;
  index: string;
  chunk_count: number;
  provider: string;
  model: string;
  fallback_available: boolean;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    request_id: string;
  };
}

export type UplinkStatus = 'LOCAL' | 'CLOUD' | 'FALLBACK' | 'OFFLINE' | 'CHECKING';
