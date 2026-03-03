import requests

from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.widgets import Label, Button, Rule, DataTable, Select
from textual.containers import Vertical, Horizontal
from textual import work

from utils.ollama_utils import delete_model


class ConfirmDeleteModal(ModalScreen):

  def __init__(self, model_name: str):
    super().__init__()
    self.model_name = model_name

  def compose(self) -> ComposeResult:
    with Vertical(id="confirmDeleteDialog"):
      yield Label(f'Delete "{self.model_name}"?')
      yield Label("This will remove it from the server.", classes="confirmDeleteHint")
      with Horizontal(id="confirmDeleteButtons"):
        yield Button("Yes, Delete", id="button_confirmDelete", variant="error")
        yield Button("Cancel", id="button_cancelDelete")

  def on_button_pressed(self, event: Button.Pressed) -> None:
    self.dismiss(event.button.id == "button_confirmDelete")


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
      yield DataTable(id="modelsTable", cursor_type="row")
      yield Label("", id="deleteStatusLabel")
      yield Button("Delete Model", id="button_deleteModel", variant="error", disabled=True)
      yield Rule()
      yield Button("Close", id="button_closeServerInfo")

  def on_mount(self) -> None:
    self._selected_model_name: str | None = None
    table = self.query_one("#modelsTable", DataTable)
    table.add_columns("Name", "Parameters", "Size")
    for m in self.installed_models:
      size_gb = m.get('size', 0) / (1024 ** 3)
      table.add_row(
        m.get('name', 'N/A'),
        m.get('details', {}).get('parameter_size', 'N/A'),
        f"{size_gb:.2f} GB",
        key=m.get('name')
      )
    self._check_server_status()

  def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
    self._selected_model_name = event.row_key.value
    self.query_one("#button_deleteModel", Button).disabled = False

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
    elif event.button.id == "button_deleteModel" and self._selected_model_name:
      model_name = self._selected_model_name
      def handle_confirm(confirmed: bool):
        if confirmed:
          self._do_delete(model_name)
      self.app.push_screen(ConfirmDeleteModal(model_name), handle_confirm)

  @work(thread=True)
  def _do_delete(self, model_name: str) -> None:
    success = delete_model(model_name)
    self.app.call_from_thread(self._on_delete_result, model_name, success)

  def _on_delete_result(self, model_name: str, success: bool) -> None:
    status_label = self.query_one("#deleteStatusLabel", Label)
    if success:
      self.query_one("#modelsTable", DataTable).remove_row(model_name)
      self.installed_models = [m for m in self.installed_models if m['name'] != model_name]
      self.app.installed_models = [m for m in self.app.installed_models if m['name'] != model_name]
      self.app.query_one("#modelSelect", Select).set_options([
        (
          f"{m['name']} - {m['details']['parameter_size']} Params - {m['size'] / (1024**3):.2f}GB",
          m['name']
        )
        for m in self.app.installed_models
      ])
      status_label.update(f'"{model_name}" deleted.')
      self._selected_model_name = None
      self.query_one("#button_deleteModel", Button).disabled = True
    else:
      status_label.update("Error: deletion failed.")
