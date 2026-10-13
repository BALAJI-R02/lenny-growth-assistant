import { useCallback, useEffect } from 'react';
import { createSession, fetchHealth, getMessages } from '../utils/api';
import { useChatStore } from '../store/chatStore';

export function useSession() {
  const {
    currentSessionId,
    setCurrentSession,
    addSession,
    setMessages,
    setHealth,
    setUplinkStatus,
  } = useChatStore();

  const startNewSession = useCallback(async () => {
    try {
      const session = await createSession();
      addSession(session);
      setCurrentSession(session.id);
      return session.id;
    } catch (err) {
      console.error('Failed to create session:', err);
      return null;
    }
  }, [addSession, setCurrentSession]);

  const loadSessionMessages = useCallback(
    async (sessionId: string) => {
      try {
        const messages = await getMessages(sessionId);
        setMessages(sessionId, messages);
      } catch (err) {
        console.error('Failed to load messages:', err);
      }
    },
    [setMessages]
  );

  // Poll health every 30s
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const health = await fetchHealth();
        setHealth(health);

        // Determine uplink status
        if (health.llm === 'down') {
          setUplinkStatus('OFFLINE');
        } else if (health.provider === 'ollama') {
          setUplinkStatus('LOCAL');
        } else {
          setUplinkStatus('CLOUD');
        }
      } catch {
        setUplinkStatus('OFFLINE');
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30_000);
    return () => clearInterval(interval);
  }, [setHealth, setUplinkStatus]);

  return { currentSessionId, startNewSession, loadSessionMessages };
}
