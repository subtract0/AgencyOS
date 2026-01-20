'use client';

import { useState, useEffect, useRef } from 'react';
import ChatMessage from './ChatMessage';
import TypingIndicator from './TypingIndicator';
import { INITIAL_MESSAGE } from '@/lib/prompts';
import {
  getCurrentSession,
  createSession,
  addMessage,
  incrementSteps,
  getTimeOfDay,
  Message,
} from '@/lib/storage';

export default function MicroChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [showInput, setShowInput] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Initialize session on mount
  useEffect(() => {
    let session = getCurrentSession();

    if (!session || session.messages.length === 0) {
      // Start fresh session
      session = createSession();

      // Add initial message from Micro
      const initialMsg = addMessage('assistant', INITIAL_MESSAGE);
      setMessages([initialMsg]);
    } else {
      // Resume existing session
      setMessages(session.messages);
      setShowInput(true); // Show input if resuming
    }
  }, []);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Send message to API
  const sendMessage = async (content: string) => {
    if (!content.trim()) return;

    // Add user message
    const userMsg = addMessage('user', content);
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);
    setInputValue('');

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [...messages, { role: 'user', content }].map((m) => ({
            role: m.role,
            content: m.content,
          })),
          context: `Time of day: ${getTimeOfDay()}`,
        }),
      });

      const data = await response.json();

      // Add assistant response
      const assistantMsg = addMessage('assistant', data.reply);
      setMessages((prev) => [...prev, assistantMsg]);

      // Check if this was a step completion (heuristic: they responded positively)
      const positiveResponses = ['done', 'did it', 'okay', 'yes', 'ok', 'yep'];
      if (positiveResponses.some((r) => content.toLowerCase().includes(r))) {
        incrementSteps();
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMsg = addMessage(
        'assistant',
        "I'm here. Something went wrong, but we can keep going.\n\nTake a breath with me."
      );
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle button click from assistant message
  const handleButtonClick = (text: string) => {
    sendMessage(text);
    setShowInput(true); // Show free input after first interaction
  };

  // Handle form submit
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim()) {
      sendMessage(inputValue);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-night-950">
      {/* Header */}
      <header className="flex-shrink-0 px-4 py-3 border-b border-night-800/50">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-medium text-night-100">Micro</h1>
            <p className="text-xs text-night-400">One tiny step at a time</p>
          </div>
          <div className="w-8 h-8 rounded-full bg-night-800 flex items-center justify-center">
            <span className="text-xs">🌙</span>
          </div>
        </div>
      </header>

      {/* Messages */}
      <main className="flex-1 overflow-y-auto px-4 py-4 chat-container">
        {messages.map((msg, idx) => (
          <ChatMessage
            key={msg.id}
            role={msg.role}
            content={msg.content}
            onButtonClick={handleButtonClick}
            isLatest={idx === messages.length - 1 && msg.role === 'assistant'}
          />
        ))}

        {isLoading && <TypingIndicator />}

        <div ref={messagesEndRef} />
      </main>

      {/* Input */}
      {showInput && (
        <footer className="flex-shrink-0 px-4 py-3 border-t border-night-800/50 safe-bottom">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Type something..."
              className="flex-1 bg-night-800 text-night-100 placeholder-night-500 px-4 py-3 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-night-600"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !inputValue.trim()}
              className="btn-press bg-night-700 hover:bg-night-600 disabled:opacity-50 disabled:cursor-not-allowed text-night-100 px-4 py-3 rounded-xl transition-colors"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                />
              </svg>
            </button>
          </form>
        </footer>
      )}
    </div>
  );
}
