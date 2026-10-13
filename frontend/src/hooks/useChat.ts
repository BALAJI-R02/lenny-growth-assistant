import { useCallback } from 'react';
import { getArtifact, sendMessage } from '../utils/api';
import { useChatStore } from '../store/chatStore';
import type { Message } from '../types';

export function useChat() {
  const {
    currentSessionId,
    addMessage,
    setActiveArtifact,
    setIsSending,
    setIsLoadingArtifact,
  } = useChatStore();

  const send = useCallback(
    async (content: string): Promise<Message | null> => {
      if (!currentSessionId || !content.trim()) return null;

      // Optimistic user message
      const optimistic: Message = {
        id: crypto.randomUUID(),
        session_id: currentSessionId,
        role: 'user',
        content,
        citations: [],
        retrieval_chunks: [],
        created_at: new Date().toISOString(),
      };
      addMessage(currentSessionId, optimistic);
      setIsSending(true);

      try {
        const response = await sendMessage(currentSessionId, content);
        addMessage(currentSessionId, response);

        // If message has an artifact, load it
        if (response.artifact_id) {
          setIsLoadingArtifact(true);
          try {
            const artifact = await getArtifact(response.artifact_id);
            setActiveArtifact(artifact);
          } catch (err) {
            console.error('Failed to load artifact:', err);
          } finally {
            setIsLoadingArtifact(false);
          }
        }

        return response;
      } catch (err: unknown) {
        // Add error message to chat
        const errMessage = err instanceof Error ? err.message : 'Request failed';
        const errorMsg: Message = {
          id: crypto.randomUUID(),
          session_id: currentSessionId,
          role: 'assistant',
          content: `⚠️ **UPLINK FAILURE**: ${errMessage}`,
          citations: [],
          retrieval_chunks: [],
          created_at: new Date().toISOString(),
        };
        addMessage(currentSessionId, errorMsg);
        return null;
      } finally {
        setIsSending(false);
      }
    },
    [currentSessionId, addMessage, setActiveArtifact, setIsSending, setIsLoadingArtifact]
  );

  return { send };
}
