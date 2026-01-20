'use client';

export default function TypingIndicator() {
  return (
    <div className="flex items-start mb-4 animate-fade-in">
      <div className="bg-night-800/50 px-4 py-3 rounded-2xl rounded-bl-md">
        <div className="flex gap-1">
          <span className="typing-dot w-2 h-2 bg-night-400 rounded-full"></span>
          <span className="typing-dot w-2 h-2 bg-night-400 rounded-full"></span>
          <span className="typing-dot w-2 h-2 bg-night-400 rounded-full"></span>
        </div>
      </div>
    </div>
  );
}
