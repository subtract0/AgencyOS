import { NextRequest, NextResponse } from 'next/server';
import OpenAI from 'openai';
import { SYSTEM_PROMPT } from '@/lib/prompts';

// Configuration for local vs cloud mode
const USE_LOCAL = process.env.USE_LOCAL_MODEL === 'true';
const LOCAL_API_BASE = process.env.LOCAL_API_BASE || 'http://localhost:1234/v1';
const LOCAL_MODEL = process.env.LOCAL_MODEL || 'vcoder-120b-1.0-hi-mlx';

// Initialize OpenAI client (works with both OpenAI and local OpenAI-compatible servers)
const openai = new OpenAI({
  apiKey: USE_LOCAL ? 'not-needed' : process.env.OPENAI_API_KEY,
  baseURL: USE_LOCAL ? LOCAL_API_BASE : undefined,
});

export async function POST(request: NextRequest) {
  try {
    const { messages, context } = await request.json();

    // Build the full message array with system prompt
    const fullMessages = [
      {
        role: 'system' as const,
        content: SYSTEM_PROMPT + (context ? `\n\n[Context: ${context}]` : ''),
      },
      ...messages.map((m: { role: string; content: string }) => ({
        role: m.role as 'user' | 'assistant',
        content: m.content,
      })),
    ];

    // Call API (OpenAI or local model)
    const completion = await openai.chat.completions.create({
      model: USE_LOCAL ? LOCAL_MODEL : 'gpt-4o-mini',
      messages: fullMessages,
      temperature: 0.7,
      max_tokens: 300,
      presence_penalty: 0.1,
      frequency_penalty: 0.1,
    });

    const reply = completion.choices[0]?.message?.content || "I'm here with you.";

    return NextResponse.json({
      reply,
      _debug: USE_LOCAL ? { mode: 'local', model: LOCAL_MODEL } : { mode: 'cloud' }
    });
  } catch (error) {
    console.error('Chat API error:', error);

    // Graceful fallback - don't leave them hanging
    return NextResponse.json(
      {
        reply: "I'm having a moment. But I'm still here with you.\n\nTake a breath. We can try again.",
        error: true,
      },
      { status: 200 } // Return 200 so the UI doesn't break
    );
  }
}
