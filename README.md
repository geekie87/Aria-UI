ARIA — Adaptive Reasoning Intelligence Assistant [VOICE EDITION]
A powerful local AI chat interface supporting Ollama, OpenAI, and LM Studio with voice input/output capabilities.

🌟 Features
Core Capabilities
Seamless Installation - Deploy effortlessly using Docker or Kubernetes (kubectl, kustomize or helm) with support for both :ollama and :cuda tagged images.

Multi-API Connectivity - Connect to OpenAI-compatible APIs alongside Ollama models. Customize the OpenAI API URL to link with LMStudio, GroqCloud, Mistral, OpenRouter, and more.

Advanced User Management - Administrators can create detailed user roles and permissions, ensuring a secure environment while allowing customized experiences for different users.

Cross-Platform Design - Enjoy a seamless experience across Desktop PC, Laptop, and Mobile devices with responsive layouts.

Mobile Progressive Web App (PWA) - Experience a native app-like interface on mobile devices with offline access support and smooth navigation.

Rich Content Formatting - Full Markdown and LaTeX support for enhanced interaction and professional document creation.

Voice & Video Communication - Integrated hands-free voice and video call features using multiple Speech-to-Text providers (Local Whisper, OpenAI, Deepgram, Azure) and Text-to-Speech engines (Azure, ElevenLabs, OpenAI, Transformers, WebAPI).

Model Builder - Create Ollama models directly through the Web UI. Add custom characters/agents, customize chat elements, and import models effortlessly.

Advanced Features
Python Function Calling - Built-in code editor support for native Python functions, enabling seamless LLM integration with your own logic.

Persistent Storage - Key-value storage API for artifacts, supporting journals, trackers, leaderboards, and collaborative tools across sessions.

Retrieval Augmented Generation (RAG) - Local RAG support with 9 vector database options and multiple content extraction engines (Tika, Docling, Document Intelligence, Mistral OCR). Access documents using the # command.

Web Search Integration - Perform searches through 15+ providers including SearXNG, Google PSE, Brave Search, Kagi, Mojeek, Tavily, Perplexity, and more. Results inject directly into chat.

Web Browsing - Incorporate entire websites into conversations using the # command followed by a URL.

Image Generation & Editing - Create and edit images through OpenAI's DALL-E, Gemini, ComfyUI (local), and AUTOMATIC1111 (local).

Voice Edition Features
🎤 Voice Input - Speak naturally with integrated microphone support
🔊 Text-to-Speech - Hear responses read aloud using multiple TTS engines
🌙 Dark/Light Theme Toggle - Switch between themes (🌙 button or press T)
⌨️ Command Menu - Quick access to commands (press K)
💾 Export Options - Export chats to TXT, MD, or JSON format
📋 Settings Panel - Customize your experience
📜 Chat History Panel - Review past conversations
🖱️ Context Menus - Right-click context menus for quick actions
⌨️ Keyboard Shortcuts - Full keyboard navigation support
🔧 Supported Providers
Provider	Endpoint	Setup
🦙 Ollama	http://localhost:11434	Click ⚙ next to Ollama tab
✦ OpenAI	api.openai.com	Click ⚙ next to OpenAI tab
🧪 LM Studio	http://localhost:1234	Click ⚙ next to LM Studio tab
📦 Installation

## Analysis of Python Requirements

After carefully reviewing all three code snippets, I can confirm that **this program has zero external dependencies**. It uses exclusively Python standard library modules:

### Dependencies Found (All Built-in):

| Module | Purpose |
|--------|---------|
| `json` | Configuration file handling |
| `os`, `sys` | File paths and command-line arguments |
| `threading` | Background threads for voice processing |
| `urllib.request`, `urllib.error` | HTTP requests to AI providers |
| `ssl` | Secure HTTPS connections |
| `time` | Timing/statistics |
| `http.server.HTTPServer`, `BaseHTTPRequestHandler` | Built-in web server |

### requirements.txt File:

```txt
# ARIA — Adaptive Reasoning Intelligence Assistant [VOICE EDITION]
# No external Python dependencies required.
# All functionality is implemented using the standard library.

# ============================================================================
# If you need additional features not in this codebase, add them below:
# ============================================================================
```

### Why This Is Minimal:

1. **No HTTP client libraries** — Uses `urllib` (built-in) instead of `requests`
2. **No JSON library** — Uses built-in `json` module
3. **No web framework** — Uses raw `http.server` module directly
4. **No configuration library** — Uses plain Python dictionaries and `json.load()`

### Optional External Dependencies (if you want enhanced features):

If you plan to add features beyond what's shown in the snippets, here are common additions:

```txt
# For advanced logging
# logging  # Also built-in

# If you later want a proper web framework
# flask==3.0.0

# For better async support (if refactoring)
# asyncio  # Built-in Python 3.5+
```

**Summary:** The program is intentionally lightweight and self-contained. You can run it with `python3 aria.py [port]` using only a standard Python 3 installation — no pip install required!

--------------------------------------------------------------------------------------
Prerequisites
Python 3.8+
pip (Python package installer)
One of the following AI backends: Ollama, OpenAI API, or LM Studio
--------------------------------------------------------------------------------------
Quick Start

# Clone the repository
git clone <repository-url>
cd aria

# Install dependencies
pip install -r requirements.txt

# Run the application
python3 aria.py [port]

# Default port is 7000
# Access at: http://localhost:7000
Docker Installation
# Build and run with Docker
docker build -t aria .
docker run -p 7000:7000 --name aria aria

# Or with Kubernetes (kubectl, kustomize or helm)
kubectl apply -f kubernetes/
🎯 Configuration
The application reads configuration from aria_config.json in the same directory as the script.

Example Configuration
{
  "port": 7000,
  "provider": {
    "type": "ollama",
    "url": "http://localhost:11434"
  },
  "model": "llama3",
  "theme": "dark",
  "voice": {
    "enabled": true,
    "stt_provider": "whisper",
    "tts_provider": "elevenlabs"
  }
}
📝 Usage Examples
Basic Chat
python3 aria.py 7000
Then open http://localhost:7000 in your browser and start chatting!

Voice Mode
Press the 🎤 button to enable voice input. Speak naturally and the assistant will respond using text-to-speech.

Theme Toggle
Press T or click the 🌙 button to switch between dark and light themes.

--------------------------------------------------------------------------------------
🏗️ Architecture
ARIA (Web Server)
--------------------------------------------------------------------------------------         
         Ollama API Integration
         OpenAI API Integration
         LM Studio Integration
 
         Speech-to-Text (STT)
            Browser Web Speech API
            OpenAI Whisper
            Local Whisper
    
         Text-to-Speech (TTS)
            Browser Web Speech API
            OpenAI TTS (tts-1, tts-1-hd)
            ElevenLabs
            Azure TTS
            
📄 License
This project is licensed under the MIT License - see below for details.

Company Information
Madame Hong PTY LTD Thailand

Adaptive Reasoning Intelligence Assistant — Voice Edition

🇹🇭 Thailand | Website | Contact

MIT License
MIT License

Copyright (c) 2024 Madame Hong PTY LTD Thailand

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

Fork the repository
Create your feature branch (git checkout -b feature/amazing-feature)
Commit your changes (git commit -m 'Add some amazing feature')
Push to the branch (git push origin feature/amazing-feature)
Open a Pull Request
📞 Support
For issues, questions, or contributions:

Email: admin@madamehong.com
Website: https://madamehong.com
GitHub Issues: Open an issue
Made with ❤️ by the ARIA Team at Madame Hong PTY LTD Thailand






