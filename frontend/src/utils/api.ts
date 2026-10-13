import axios from 'axios';
import type { Artifact, HealthResponse, Message, Session } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 600_000, // 10 min for local CPU essay generation
});

// Sessions
export const createSession = async (): Promise<Session> => {
  const { data } = await api.post<Session>('/api/v1/sessions');
  return data;
};

export const getMessages = async (sessionId: string): Promise<Message[]> => {
  const { data } = await api.get<Message[]>(`/api/v1/sessions/${sessionId}/messages`);
  return data;
};

// Chat
export const sendMessage = async (
  sessionId: string,
  content: string
): Promise<Message> => {
  const { data } = await api.post<Message>(
    `/api/v1/sessions/${sessionId}/chat`,
    { content }
  );
  return data;
};

// Artifacts
export const getArtifact = async (artifactId: string): Promise<Artifact> => {
  const { data } = await api.get<Artifact>(`/api/v1/artifacts/${artifactId}`);
  return data;
};

export const getArtifactRaw = async (artifactId: string): Promise<string> => {
  const { data } = await api.get<string>(`/api/v1/artifacts/${artifactId}/raw`);
  return data;
};

// Health
export const fetchHealth = async (): Promise<HealthResponse> => {
  const { data } = await api.get<HealthResponse>('/health');
  return data;
};
