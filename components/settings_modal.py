from textual import work
from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.widgets import Label, Button, Rule, TextArea, Input
from textual.containers import Vertical, Horizontal

from utils.ollama_utils import check_connection


class SettingsModal(ModalScreen):

  def __init__(self, current_system_prompt: str, current_url: str):
    super().__init__()
    self.current_system_prompt = current_system_prompt
    self.current_url = current_url

  def compose(self) -> ComposeResult:
    with Vertical(id="settingsDialog"):
      yield Label("Settings", id="settingsTitle")
      yield Rule()
      yield Label("Ollama URL", classes="sectionHeader")
      yield Input(self.current_url, id="ollamaUrlInput")
      yield Label("System Prompt", classes="sectionHeader")
      yield Label("Sent to the model at the start of every conversation.", classes="settingsHint")
      yield TextArea(self.current_system_prompt, id="systemPromptInput")
      yield Label("", id="connectionStatus")
      with Horizontal(id="settingsButtons"):
        yield Button("Save", id="button_saveSettings", variant="success")
        yield Button("Cancel", id="button_cancelSettings")

  def on_button_pressed(self, event: Button.Pressed) -> None:
    if event.button.id == "button_saveSettings":
      url = self.query_one("#ollamaUrlInput", Input).value.strip()
      prompt_text = self.query_one("#systemPromptInput", TextArea).text
      self.query_one("#button_saveSettings", Button).disabled = True
      self.query_one("#connectionStatus", Label).update("Connecting...")
      self._test_connection(url, prompt_text)
    elif event.button.id == "button_cancelSettings":
      self.dismiss(None)

  @work(thread=True)
  def _test_connection(self, url: str, prompt_text: str) -> None:
    success = check_connection(url)
    if success:
      self.app.call_from_thread(self._on_connect_success, {"url": url, "system_prompt": prompt_text})
    else:
      self.app.call_from_thread(self._on_connect_failure, f"Could not connect to {url}")

  def _on_connect_success(self, result: dict) -> None:
    self.dismiss(result)

  def _on_connect_failure(self, error: str) -> None:
    self.query_one("#button_saveSettings", Button).disabled = False
    self.query_one("#connectionStatus", Label).update(error)
