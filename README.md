![Ollama Terminal UI Icon, A Llama with VR goggles on and a terminal icon.](/assets/OllamaTermUI_TitleCard.png "OllamaTermUI")

# OllamaTermUI

A terminal-based chat interface for [Ollama](https://ollama.com), built with [Textual](https://textual.textualize.io). Run multiple conversations simultaneously, switch between models on the fly, and get streaming responses with real-time markdown rendering — all without leaving the terminal.

---

## Features

- **Conversation Management Sidebar** — Have several conversations at once, each independently tracked with its own model and history
- **Model switching** — Change the active model mid-session from the top dropdown. Doing this causes the conversation to either carry or start fresh depending on persistence toggle state.
- **Conversation persistence toggle** — Decide whether message history follows you when you switch models
- **Streaming responses** — Responses stream in token by token with live markdown rendering.
- **Server info** — Click the `ℹ` button to see your server address, connection status, active model details, and a full list of installed models

---

## Requirements

- Python 3.10+
- An [Ollama](https://ollama.com) server running and accessible on your network with at least one model pulled
- The dependencies listed in `requirements.txt`:

```
textual
textual-dev
requests
```

---

## Getting Started

### 1. Configure your server

Open `utils/ollama_utils.py` and update `OLLAMA_BASE_URL` to point at your Ollama instance:

```python
OLLAMA_BASE_URL = "http://192.168.1.200:11434"
```

If Ollama is running locally, that would be `http://localhost:11434`.

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run

```bash
python ollamatermui.py
```

The app will connect to your Ollama server on startup and populate the model list automatically. If the server is unreachable, it will fail at this step — make sure Ollama is running and the URL is correct.

---

## Usage

### Managing Conversations

- **New Conversation** — opens a fresh chat using whichever model is currently selected in the dropdown
- **Conversation list** — click any conversation in the sidebar to switch to it; your current messages are saved automatically
- **Delete Conversation** — click the red **Delete Conversation** button inside the chat; a confirmation dialog will appear before anything is removed

### Model Switching

Select a different model from the dropdown at the top. What happens next depends on the **Convo Persist** toggle:

| Persist | Behaviour |
|---|---|
| **ON** | The current message history carries over to the newly selected model |
| **OFF** | A brand new conversation is started with the selected model |

### Server Info

Click the `ℹ` button in the top-right of the status bar to open the server info panel. It shows your server address, checks the connection live, displays the active model's details (family, parameter count, quantization, disk size), and lists every model currently installed on the server.

### Keyboard Shortcuts

| Key | Action |
|---|---|
| `d` | Toggle dark / light mode |
| `Enter` | Send message (when input is focused) |
| `Escape` | Close any open modal |

---

## Built With

- [Textual](https://textual.textualize.io) — terminal UI framework for Python
- [Ollama](https://ollama.com) — local LLM inference server
