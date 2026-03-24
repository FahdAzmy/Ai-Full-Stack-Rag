'use client';

import { useRef, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '@/store/store';
import {
  appendUserMessage,
  startStreamingMessage,
  appendTokenToStreamingMessage,
  finalizeStreamingMessage,
  setQuerying,
  setChatError,
} from '@/store/chat/chat-slice';
import { createChat } from '@/store/chat/chat-actions';
import { getAccessToken, setAccessToken } from '@/lib/axios';

/**
 * Custom hook that encapsulates the entire SSE streaming query logic.
 * - Creates a chat if none is active
 * - Sends the query via SSE
 * - Handles token expiration / refresh
 * - Supports cancellation via AbortController
 */
export function useStreamingQuery() {
  const dispatch = useDispatch<AppDispatch>();
  const { activeChat, querying } = useSelector((state: RootState) => state.chat);
  const { selectedDocumentIds } = useSelector((state: RootState) => state.documents);
  const abortControllerRef = useRef<AbortController | null>(null);

  const abort = useCallback(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
  }, []);

  const sendQuery = useCallback(
    async (question: string) => {
      if (!question.trim() || querying) return;

      const questionToAsk = question.trim();

      // Abort any in-flight stream
      abort();

      dispatch(setQuerying(true));

      let chatId = activeChat?.id;

      // Create a new chat if one doesn't exist
      if (!chatId) {
        try {
          const actionResult = await dispatch(createChat(undefined)).unwrap();
          chatId = actionResult.id;
        } catch (err: unknown) {
          const msg = err instanceof Error ? err.message : 'Failed to create chat';
          dispatch(setChatError(msg));
          dispatch(setQuerying(false));
          return;
        }
      }

      // Optimistic user message
      dispatch(
        appendUserMessage({
          id: `temp-${Date.now()}`,
          role: 'user',
          content: questionToAsk,
          source_chunks: null,
          created_at: new Date().toISOString(),
        }),
      );

      const controller = new AbortController();
      abortControllerRef.current = controller;

      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const token = getAccessToken();

        let response = await fetch(`${apiUrl}/chats/${chatId}/query/stream`, {
          method: 'POST',
          signal: controller.signal,
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({
            question: questionToAsk,
            document_ids: selectedDocumentIds.length > 0 ? selectedDocumentIds : null,
          }),
        });

        // Handle token expiration — retry once after refreshing
        if (response.status === 401) {
          try {
            const axiosMod = await import('@/lib/axios');
            const refreshRes = await axiosMod.default.post('/refresh');
            const newToken = refreshRes.data.access_token;
            setAccessToken(newToken);

            response = await fetch(`${apiUrl}/chats/${chatId}/query/stream`, {
              method: 'POST',
              signal: controller.signal,
              headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${newToken}`,
              },
              body: JSON.stringify({
                question: questionToAsk,
                document_ids: selectedDocumentIds.length > 0 ? selectedDocumentIds : null,
              }),
            });
          } catch {
            if (typeof window !== 'undefined') {
              window.location.href = '/auth';
            }
            throw new Error('Session expired. Please log in again.');
          }
        }

        if (!response.ok) {
          throw new Error('Query failed');
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        let streamStarted = false;
        let buffer = '';

        if (reader) {
          try {
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;

              buffer += decoder.decode(value, { stream: true });
              const lines = buffer.split('\n');
              buffer = lines.pop() || '';

              for (const line of lines) {
                if (line.trim() === '') continue;
                if (line.startsWith('data: ')) {
                  const dataStr = line.slice(6);
                  if (!dataStr) continue;

                  try {
                    const data = JSON.parse(dataStr);

                    if (data.type === 'sources') {
                      dispatch(startStreamingMessage({ sources: data.sources }));
                      streamStarted = true;
                    } else if (data.type === 'chunk') {
                      if (!streamStarted) {
                        dispatch(startStreamingMessage({ sources: null }));
                        streamStarted = true;
                      }
                      dispatch(appendTokenToStreamingMessage(data.content));
                    } else if (data.type === 'done') {
                      dispatch(
                        finalizeStreamingMessage({
                          id: data.message_id,
                          sources: data.sources,
                          title: data.chat_title,
                        }),
                      );
                    } else if (data.type === 'error') {
                      throw new Error(data.error);
                    }
                  } catch (e) {
                    if (e instanceof SyntaxError) {
                      console.error('Error parsing SSE line:', line, e);
                    } else {
                      throw e;
                    }
                  }
                }
              }
            }
          } finally {
            reader.releaseLock();
          }
        }
      } catch (err: unknown) {
        // Don't report abort errors as user-facing errors
        if (err instanceof DOMException && err.name === 'AbortError') {
          dispatch(setQuerying(false));
          return;
        }
        const msg = err instanceof Error ? err.message : 'An error occurred';
        dispatch(setChatError(msg));
        dispatch(setQuerying(false));
      }
    },
    [activeChat?.id, querying, selectedDocumentIds, dispatch, abort],
  );

  return { sendQuery, abort, querying };
}
