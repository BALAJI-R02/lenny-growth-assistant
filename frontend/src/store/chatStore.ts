import { create } from 'zustand';
import type { Artifact, HealthResponse, Message, Session, UplinkStatus } from '../types';

interface ChatStore {
  // Sessions
  sessions: Session[];
  currentSessionId: string | null;

  // Messages
  messages: Record<string, Message[]>; // session_id -> messages

  // Active artifact
  activeArtifact: Artifact | null;

  // Health / status
  health: HealthResponse | null;
  uplinkStatus: UplinkStatus;
  isBooted: boolean;

  // Loading
  isSending: boolean;
  isLoadingArtifact: boolean;

  // Actions
  setCurrentSession: (id: string) => void;
  addSession: (session: Session) => void;
  addMessage: (sessionId: string, message: Message) => void;
  setMessages: (sessionId: string, messages: Message[]) => void;
  setActiveArtifact: (artifact: Artifact | null) => void;
  setHealth: (health: HealthResponse) => void;
  setUplinkStatus: (status: UplinkStatus) => void;
  setIsBooted: (booted: boolean) => void;
  setIsSending: (sending: boolean) => void;
  setIsLoadingArtifact: (loading: boolean) => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  sessions: [],
  currentSessionId: null,
  messages: {},
  activeArtifact: null,
  health: null,
  uplinkStatus: 'CHECKING',
  isBooted: false,
  isSending: false,
  isLoadingArtifact: false,

  setCurrentSession: (id) => set({ currentSessionId: id }),
  addSession: (session) =>
    set((state) => ({ sessions: [session, ...state.sessions] })),
  addMessage: (sessionId, message) =>
    set((state) => ({
      messages: {
        ...state.messages,
        [sessionId]: [...(state.messages[sessionId] || []), message],
      },
    })),
  setMessages: (sessionId, messages) =>
    set((state) => ({
      messages: { ...state.messages, [sessionId]: messages },
    })),
  setActiveArtifact: (artifact) => set({ activeArtifact: artifact }),
  setHealth: (health) => set({ health }),
  setUplinkStatus: (status) => set({ uplinkStatus: status }),
  setIsBooted: (booted) => set({ isBooted: booted }),
  setIsSending: (sending) => set({ isSending: sending }),
  setIsLoadingArtifact: (loading) => set({ isLoadingArtifact: loading }),
}));
