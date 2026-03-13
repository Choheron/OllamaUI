from pathlib import Path
import json
import re

CONVERSATIONS_DIR = Path.home() / ".ollamatermui" / "conversations"


def _sanitize_server_name(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip()


def _convo_path(server_name: str, convo_id: int) -> Path:
    return CONVERSATIONS_DIR / _sanitize_server_name(server_name) / f"{convo_id}.json"


def save_conversation(convo: dict, server_name: str) -> None:
    """Save a conversation to disk. Skips if messages list is empty."""
    if not convo.get('messages'):
        return
    path = _convo_path(server_name, convo['id'])
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(convo, f, indent=2)
    except Exception:
        pass


def load_all_conversations(server_name: str) -> list[dict]:
    """Load all conversations for a server, sorted by id ascending."""
    server_dir = CONVERSATIONS_DIR / _sanitize_server_name(server_name)
    if not server_dir.exists():
        return []
    convos = []
    for path in server_dir.glob('*.json'):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            if all(k in data for k in ('id', 'title', 'model', 'messages')):
                convos.append(data)
        except Exception:
            pass
    return sorted(convos, key=lambda c: c['id'])


def delete_conversation_file(server_name: str, convo_id: int) -> None:
    """Delete the conversation file from disk."""
    try:
        _convo_path(server_name, convo_id).unlink(missing_ok=True)
    except Exception:
        pass


def rename_server_conversations(old_name: str, new_name: str) -> None:
    """Rename the conversation directory when a server is renamed."""
    old_dir = CONVERSATIONS_DIR / _sanitize_server_name(old_name)
    new_dir = CONVERSATIONS_DIR / _sanitize_server_name(new_name)
    try:
        if old_dir.exists() and not new_dir.exists():
            old_dir.rename(new_dir)
    except Exception:
        pass
