'use client';

import { RefObject } from 'react';
import { Message } from './chat-layout';

interface ChatMessagesProps {
  messages: Message[];
  isTyping: boolean;
  messagesEndRef: RefObject<HTMLDivElement | null>;
}

export function ChatMessages({ messages, isTyping, messagesEndRef }: ChatMessagesProps) {
  return (
    <div className="flex-1 overflow-y-auto chat-scrollbar p-6">
      <div className="max-w-4xl mx-auto space-y-8">
        {messages.map((message) =>
          message.role === 'assistant' ? (
            <AssistantMessage key={message.id} message={message} />
          ) : (
            <UserMessage key={message.id} message={message} />
          )
        )}

        {/* Typing indicator */}
        {isTyping && (
          <div className="flex gap-4 animate-in fade-in-0 slide-in-from-bottom-4 duration-300">
            <div className="size-10 rounded-lg bg-teal-100 dark:bg-teal-900/40 flex items-center justify-center shrink-0">
              <svg className="w-5 h-5 text-teal-600 dark:text-teal-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 0 0-2.455 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z" />
              </svg>
            </div>
            <div className="max-w-[80%]">
              <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-2xl rounded-tl-none shadow-sm">
                <div className="flex items-center gap-1.5">
                  <div className="w-2 h-2 rounded-full bg-teal-500 animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 rounded-full bg-teal-500 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 rounded-full bg-teal-500 animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}

function AssistantMessage({ message }: { message: Message }) {
  return (
    <div className="flex gap-4 animate-in fade-in-0 slide-in-from-bottom-4 duration-300">
      {/* AI avatar */}
      <div className="size-10 rounded-lg bg-teal-100 dark:bg-teal-900/40 flex items-center justify-center shrink-0">
        <svg className="w-5 h-5 text-teal-600 dark:text-teal-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 0 0-2.455 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z" />
        </svg>
      </div>
      <div className="max-w-[80%]">
        <div
          className="bg-gray-100 dark:bg-gray-800 p-4 rounded-2xl rounded-tl-none text-gray-800 dark:text-gray-200 leading-relaxed shadow-sm"
          dangerouslySetInnerHTML={{ __html: message.content }}
        />
        <span className="text-[10px] text-gray-400 dark:text-gray-600 mt-1 block ms-1">
          {message.timestamp}
        </span>
      </div>
    </div>
  );
}

function UserMessage({ message }: { message: Message }) {
  return (
    <div className="flex gap-4 justify-end animate-in fade-in-0 slide-in-from-bottom-4 duration-300">
      <div className="max-w-[80%] text-end">
        <div
          className="text-white p-4 rounded-2xl rounded-tr-none shadow-md text-start inline-block"
          style={{ background: 'linear-gradient(135deg, #0d9488, #0f766e)' }}
        >
          {message.content}
        </div>
        <span className="text-[10px] text-gray-400 dark:text-gray-600 mt-1 block me-1">
          {message.timestamp}
        </span>
      </div>
    </div>
  );
}
