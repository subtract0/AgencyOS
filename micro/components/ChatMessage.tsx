'use client';

import { useEffect, useState } from 'react';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  onButtonClick?: (text: string) => void;
  isLatest?: boolean;
}

export default function ChatMessage({
  role,
  content,
  onButtonClick,
  isLatest = false,
}: ChatMessageProps) {
  const [visible, setVisible] = useState(!isLatest);

  useEffect(() => {
    if (isLatest) {
      // Small delay for animation
      const timer = setTimeout(() => setVisible(true), 50);
      return () => clearTimeout(timer);
    }
  }, [isLatest]);

  // Parse content to extract buttons (lines starting with [])
  const parseContent = (text: string) => {
    const lines = text.split('\n');
    const textLines: string[] = [];
    const buttons: string[] = [];

    lines.forEach((line) => {
      const trimmed = line.trim();
      if (trimmed.startsWith('[') && trimmed.endsWith(']')) {
        buttons.push(trimmed.slice(1, -1));
      } else if (trimmed) {
        textLines.push(trimmed);
      }
    });

    return { text: textLines.join('\n'), buttons };
  };

  const { text, buttons } = parseContent(content);

  if (role === 'user') {
    return (
      <div
        className={`flex justify-end mb-4 transition-opacity duration-300 ${
          visible ? 'opacity-100' : 'opacity-0'
        }`}
      >
        <div className="bg-night-700 text-night-100 px-4 py-3 rounded-2xl rounded-br-md max-w-[85%]">
          <p className="text-sm leading-relaxed">{content}</p>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`flex flex-col items-start mb-4 transition-all duration-300 ${
        visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'
      }`}
    >
      {/* Text content */}
      {text && (
        <div className="bg-night-800/50 text-night-100 px-4 py-3 rounded-2xl rounded-bl-md max-w-[85%] mb-3">
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{text}</p>
        </div>
      )}

      {/* Button options */}
      {buttons.length > 0 && isLatest && (
        <div className="flex flex-col gap-2 w-full max-w-[85%]">
          {buttons.map((btn, idx) => (
            <button
              key={idx}
              onClick={() => onButtonClick?.(btn)}
              className="btn-press bg-night-700 hover:bg-night-600 text-night-100 px-4 py-3 rounded-xl text-sm text-left transition-colors border border-night-600/50"
            >
              {btn}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
