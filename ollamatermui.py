from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Label, Button, Select, ListView, ListItem
from textual.containers import Horizontal, Vertical
from textual import work

from utils.ollama_utils import get_installed_models
from components.chat_box import ChatBox


class OllamaTermUI(App):
  '''A Textual App to manage and interact with Ollama APIs'''
  TITLE = "Ollama-UI"
  BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]
  CSS_PATH = [
    "tcss/chat_box.tcss",
    "tcss/confirm_clear_modal.tcss",
    "tcss/ollamaui.tcss",
  ]


  def compose(self) -> ComposeResult:
    yield Header()
    with Horizontal(id="statusBar"):
      yield Select([("Loading...", 1)], id="modelSelect", prompt="Loading models...", allow_blank=False)
    with Horizontal():
      with Vertical(id="sidebar"):
        yield Label("Conversations:")
        yield ListView(id="convoListView")
        yield Button("New Conversation", id="button_newConvo", disabled=True)
        yield Button("Convo Persist: ON", id="button_convoPersist", disabled=True, variant="success")
      with Vertical(id="chatContainer"):
        yield Label("Loading models...", id="loadingLabel")
    yield Footer()


  def on_mount(self):
    self.conversations: list[dict] = []
    self.active_convo_id: int | None = None
    self.next_convo_id: int = 1
    self.next_convo_num: int = 1
    self.installed_models: list[dict] = []
    sidebar = self.query_one("#sidebar")
    sidebar.styles.width = "1fr"
    self.chatContainer = self.query_one("#chatContainer")
    self.chatContainer.styles.width = "10fr"
    self.carryOver: bool = True
    self.query_one("#statusBar").border_title = "Current Model:"
    self.load_models()


  @work(thread=True)
  def load_models(self):
    models = get_installed_models()
    self.app.call_from_thread(self._setup_after_models_load, models)


  def _setup_after_models_load(self, models: list[dict]):
    self.installed_models = models
    select = self.query_one("#modelSelect", Select)
    select.set_options([
      (
        f"{m['name']} - {m['details']['parameter_size']} Params - {m['size'] / (1024**3):.2f}GB",
        f"{m['name']}"
      )
      for m in models
    ])
    select.prompt = "Select a model..."
    self.query_one("#loadingLabel").remove()
    self.query_one("#button_newConvo", Button).disabled = False
    self.query_one("#button_convoPersist", Button).disabled = False
    if models:
      self._new_conversation(models[0])


  def _new_conversation(self, model: dict):
    convo_id = self.next_convo_id
    title = f"Convo {self.next_convo_num}"
    self.next_convo_id += 1
    self.next_convo_num += 1
    convo = {'id': convo_id, 'title': title, 'model': model, 'messages': []}
    self.conversations.append(convo)
    self.query_one("#convoListView", ListView).append(
      ListItem(Label(f"{title} - {model['name']}"), id=f"convo_{convo_id}")
    )
    self.call_after_refresh(self._switch_conversation, convo_id)


  async def _switch_conversation(self, convo_id: int):
    self._save_current_messages()
    self.active_convo_id = convo_id
    convo = self._get_conversation(convo_id)
    self.query_one("#modelSelect", Select).value = convo['model']['name']
    await self._remount_chatbox(convo['model'], convo['messages'])


  def _save_current_messages(self):
    if self.active_convo_id is None:
      return
    try:
      chatBox = self.query_one("#chatContainer").query_one("#chatBox", ChatBox)
      convo = self._get_conversation(self.active_convo_id)
      if convo:
        convo['messages'] = list(chatBox.conversation)
    except Exception:
      pass


  async def _remount_chatbox(self, model: dict, messages: list):
    container = self.query_one("#chatContainer")
    try:
      await container.query_one("#chatBox").remove()
    except Exception:
      pass
    await container.mount(ChatBox(model=model, conversation=messages, id="chatBox"))


  def action_toggle_dark(self) -> None:
    self.theme = (
      "textual-dark" if self.theme == "textual-light" else "textual-light"
    )


  def on_button_pressed(self, event: Button.Pressed) -> None:
    if event.button.id == "button_convoPersist":
      self.carryOver = not self.carryOver
      btn = self.query_one("#button_convoPersist", Button)
      if self.carryOver:
        btn.label = "Convo Persist: ON"
        btn.variant = "success"
      else:
        btn.label = "Convo Persist: OFF"
        btn.variant = "default"
    elif event.button.id == "button_newConvo":
      select_value = self.query_one("#modelSelect", Select).value
      model = self._get_model_by_name(select_value) if select_value is not Select.BLANK else None
      if model is None and self.installed_models:
        model = self.installed_models[0]
      if model:
        self._new_conversation(model)


  async def on_select_changed(self, event: Select.Changed) -> None:
    if event.select.id != "modelSelect" or event.value is Select.BLANK:
      return
    if self.active_convo_id is None:
      return
    convo = self._get_conversation(self.active_convo_id)
    if convo is None or convo['model']['name'] == event.value:
      return  # programmatic update during conversation switch — skip
    model = self._get_model_by_name(event.value)
    if not model:
      return
    if self.carryOver:
      # Keep current messages, just swap the model
      self._save_current_messages()
      convo['model'] = model
      self._refresh_convo_title(convo)
      await self._remount_chatbox(model, convo['messages'])
    else:
      # Start a fresh conversation with the selected model
      self._new_conversation(model)


  async def on_list_view_selected(self, event: ListView.Selected) -> None:
    if event.list_view.id != "convoListView":
      return
    convo_id = int(event.item.id.replace("convo_", ""))
    if convo_id != self.active_convo_id:
      await self._switch_conversation(convo_id)


  def _refresh_convo_title(self, convo: dict) -> None:
    item = self.query_one(f"#convo_{convo['id']}", ListItem)
    label = item.query_one(Label)
    label.update(f"{convo['title']} - {convo['model']['name']}")


  async def on_chat_box_delete_conversation_requested(self, _: ChatBox.DeleteConversationRequested) -> None:
    await self._delete_active_conversation()


  async def on_chat_box_update_conversation_title(self, message: ChatBox.UpdateConversationTitle) -> None:
    convo = self._get_conversation(self.active_convo_id)
    convo['title'] = message.title
    self._refresh_convo_title(convo)


  async def _delete_active_conversation(self):
    if self.active_convo_id is None or not self.conversations:
      return
    convo_idx = next(
      (i for i, c in enumerate(self.conversations) if c['id'] == self.active_convo_id),
      None
    )
    if convo_idx is None:
      return
    convo_id = self.active_convo_id
    self.conversations.pop(convo_idx)
    await self.query_one(f"#convo_{convo_id}", ListItem).remove()
    self.active_convo_id = None
    if self.conversations:
      next_idx = min(convo_idx, len(self.conversations) - 1)
      await self._switch_conversation(self.conversations[next_idx]['id'])
    else:
      try:
        await self.query_one("#chatContainer").query_one("#chatBox").remove()
      except Exception:
        pass
      if self.installed_models:
        self._new_conversation(self.installed_models[0])


  def _get_conversation(self, convo_id: int) -> dict | None:
    return next((c for c in self.conversations if c['id'] == convo_id), None)


  def _get_model_by_name(self, name: str) -> dict | None:
    return next((m for m in self.installed_models if m['name'] == name), None)


if __name__ == "__main__":
  app = OllamaTermUI()
  app.run()
