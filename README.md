![Ollama Terminal UI Icon, A Llama with VR goggles on and a terminal icon.](/assets/OllamaTermUI_TitleCard.png "OllamaTermUI")

# OllamaTermUI

A terminal-based chat interface for [Ollama](https://ollama.com), built with [Textual](https://textual.textualize.io). Run multiple conversations simultaneously, switch between models on the fly, manage multiple Ollama servers, and get streaming responses with real-time markdown rendering — all without leaving the terminal.

---

## Features

- **Multi-conversation sidebar** — Maintain several independent conversations at once, each with its own model and message history
- **Model switching** — Change the active model from the top dropdown mid-session; carry the conversation history over or start fresh depending on the persistence toggle
- **Multi-server management** — Save multiple named Ollama server configurations and switch between them from the Settings panel; connection is validated before a server is added
- **Per-server system prompts** — Each server stores its own system prompt, which is automatically injected at the start of every conversation on that server
- **Streaming responses** — Responses stream in token by token with live markdown rendering and smart auto-scroll (only follows the bottom if you're already there)
- **Server info & model management** — View server status, connection health, and active model details; browse all installed models and delete them directly from the UI
- **Conversation summary** — Generate an AI summary of any conversation using the currently selected model
- **Persistent config** — Server list, active server, and system prompts are saved to `~/.ollamatermui/config.json` and restored on launch

---

## Requirements

- Python 3.10+
- An [Ollama](https://ollama.com) server running and accessible on your network with at least one model pulled
- The dependencies listed in `requirements.txt`:

```
textual
requests
```

---

## Getting Started

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run

```bash
python ollamatermui.py
```

### 3. Configure your server

On first launch the app defaults to `http://192.168.1.200:11434`. Open the **Settings** panel (⚙ button, top-left) to add your Ollama server URL and give it a name. The app will test the connection before saving. Your server list is persisted to `~/.ollamatermui/config.json` and loaded automatically on every subsequent launch.

---

## Usage

### Managing Conversations

- **New Conversation** — Opens a new chat with the currently selected model
- **Conversation list** — Click an entry in the sidebar to switch to it
- **Delete Conversation** — Click the red **Delete Conversation** button inside the chat area (confirmation required)

### Model Switching

Select a model from the dropdown at the top. The **Convo Persist** toggle controls what happens next:

| Persist | Behaviour |
|---|---|
| **ON** | The current message history carries over to the newly selected model |
| **OFF** | A brand new conversation is started with the selected model |

### Settings

Click the gear icon in the top-left to open Settings.

**Servers tab:**
- The table lists all saved servers; the active one is marked with `●`
- Select a row and click **Set Active** to switch to a different server — the model list reloads automatically
- **Test & Add** tests connectivity before adding a new server; invalid or unreachable URLs are rejected
- The last remaining server cannot be deleted

**System Prompt:**
- Each server has its own system prompt, shown and editable below the server table
- Switching "Set Active" to a different server swaps the textarea to that server's prompt
- The system prompt is injected silently at the start of every new message; it does not appear in the conversation history

Settings are saved to `~/.ollamatermui/config.json` when you click **Save**.

### Server Info

Click the info icon inside the status bar to open the server panel:

- Live connection status and server version
- Active model details: family, parameter count, quantization level, disk size
- Full list of all models installed on the server
- Select a model row and click **Delete** to remove it from the server (confirmation required)

### Summarize Conversation

The **Summarize Conversation** button appears in the sidebar once a conversation has at least one message. Clicking it sends the current conversation to the active model and displays a summary in a modal. The button is disabled on empty conversations.
