import requests

from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.widgets import Label, Button, Rule, DataTable
from textual.containers import Vertical
from textual import work


class ServerInfoModal(ModalScreen):

  def __init__(self, server_url: str, installed_models: list[dict], active_model: dict | None):
    super().__init__()
    self.server_url = server_url
    self.installed_models = installed_models
    self.active_model = active_model

  def compose(self) -> ComposeResult:
    with Vertical(id="serverInfoDialog"):
      yield Label("Server & Model Info", id="serverInfoTitle")
      yield Rule()
      yield Label("Server", classes="sectionHeader")
      yield Label(f"  Address: {self.server_url}")
      yield Label("  Status: Checking...", id="statusLabel")
      yield Rule()
      yield Label("Active Model", classes="sectionHeader")
      if self.active_model:
        details = self.active_model.get('details', {})
        yield Label(f"  Name:          {self.active_model.get('name', 'N/A')}")
        yield Label(f"  Family:        {details.get('family', 'N/A')}")
        yield Label(f"  Parameters:    {details.get('parameter_size', 'N/A')}")
        yield Label(f"  Quantization:  {details.get('quantization_level', 'N/A')}")
        size_gb = self.active_model.get('size', 0) / (1024 ** 3)
        yield Label(f"  Size:          {size_gb:.2f} GB")
      else:
        yield Label("  No active model")
      yield Rule()
      yield Label("Installed Models", classes="sectionHeader")
      yield DataTable(id="modelsTable", show_cursor=False)
      yield Button("Close", id="button_closeServerInfo")

  def on_mount(self) -> None:
    table = self.query_one("#modelsTable", DataTable)
    table.add_columns("Name", "Parameters", "Size")
    for m in self.installed_models:
      size_gb = m.get('size', 0) / (1024 ** 3)
      table.add_row(
        m.get('name', 'N/A'),
        m.get('details', {}).get('parameter_size', 'N/A'),
        f"{size_gb:.2f} GB"
      )
    self._check_server_status()

  @work(thread=True)
  def _check_server_status(self) -> None:
    try:
      response = requests.get(f"{self.server_url}/api/version", timeout=3)
      version = response.json().get('version', '?')
      status_text = f"  Status: Online \u2713 (v{version})"
    except Exception:
      status_text = "  Status: Offline \u2717"
    self.app.call_from_thread(self._update_status, status_text)

  def _update_status(self, text: str) -> None:
    self.query_one("#statusLabel", Label).update(text)

  def on_button_pressed(self, event: Button.Pressed) -> None:
    if event.button.id == "button_closeServerInfo":
      self.dismiss()
