from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.widgets import Label, Button, Rule, TextArea
from textual.containers import Vertical, Horizontal


class SettingsModal(ModalScreen):

  def __init__(self, current_system_prompt: str):
    super().__init__()
    self.current_system_prompt = current_system_prompt

  def compose(self) -> ComposeResult:
    with Vertical(id="settingsDialog"):
      yield Label("Settings", id="settingsTitle")
      yield Rule()
      yield Label("System Prompt", classes="sectionHeader")
      yield Label("Sent to the model at the start of every conversation.", classes="settingsHint")
      yield TextArea(self.current_system_prompt, id="systemPromptInput")
      with Horizontal(id="settingsButtons"):
        yield Button("Save", id="button_saveSettings", variant="success")
        yield Button("Cancel", id="button_cancelSettings")

  def on_button_pressed(self, event: Button.Pressed) -> None:
    if event.button.id == "button_saveSettings":
      prompt_text = self.query_one("#systemPromptInput", TextArea).text
      self.dismiss(prompt_text)
    elif event.button.id == "button_cancelSettings":
      self.dismiss(None)
