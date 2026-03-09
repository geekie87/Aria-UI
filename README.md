# Aria-UI
ARIA — Adaptive Reasoning Intelligence Assistant
FEATURES
  ├─ Chat: Ollama · OpenAI · LM Studio · Any OpenAI-compatible API
  ├─ STT:  Browser Web Speech API (no API key needed)
  ├─ TTS:  Browser Web Speech · OpenAI tts-1/tts-1-hd · ElevenLabs
  ├─ UI:   Dark/Light theme · Streaming · Command palette (Ctrl+K)
  ├─ Chat: Multi-chat history · Export TXT/MD/JSON
  ├─ Params: Temperature · Top-P/K · Repeat penalty · Max tokens
  ├─ System prompts · 8 persona presets · Custom character name
  ├─ Image attachment (vision models)
  ├─ Full Markdown rendering incl. tables & code highlighting
  ├─ Context menus · Keyboard shortcuts · Slash commands
  └─ Stats: tokens/sec · latency · session usage

- Chat & Providers — Ollama, OpenAI, LM Studio, plus any OpenAI-compatible API (Groq, Mistral, OpenRouter, etc.). ElevenLabs added as a 4th provider. All configured via a single ⚙ modal with per-provider test buttons.
- Voice I/O — STT via Browser Web Speech (no API key, works in Chrome/Edge). TTS with three backends: Browser WebSpeech (free), OpenAI tts-1/tts-1-hd, or ElevenLabs with stability/similarity controls.
- UI & Theme — Dark/Light theme with full CSS variable swap. Sidebar groups chats into Today/Yesterday/This Week/Older. Right panel has 4 tabs: Params, System, TTS, Stats.
- Params — Temperature, Top-P, Top-K, Repeat Penalty, Max Tokens, Context Window, Seed, Stop sequences, Mirostat toggle, Low VRAM toggle, Raw Mode, Auto-Save toggle.
- System Prompts — 8 presets (Helpful Assistant, Senior Developer, Data Analyst, Creative Writer, Concise Mode, Patient Tutor, Security Expert, ARIA Persona) plus custom character name field.
- Command Palette (Ctrl+K) — searchable, keyboard-navigable list of every action. Slash commands in the input (/clear, /new, /export, /theme, /help, /stats, /tts, /voice, /regen).
- Keyboard Shortcuts — 15+ shortcuts, shown in a modal (? key). Context menus on right-click with copy, copy code blocks, regenerate, speak, delete.
- Markdown — headers, bold/italic/strikethrough, inline/fenced code with copy buttons and language labels, blockquotes, ordered/unordered lists, tables, links, horizontal rules.
- Export — TXT, Markdown, or JSON with metadata.
