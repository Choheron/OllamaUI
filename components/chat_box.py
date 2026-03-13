from textual.widget import Widget
from textual.widgets import Label, TextArea, Button, Markdown
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.message import Message
from textual import events, work

from utils.ollama_utils import stream_conversation_response

from datetime import datetime


class ConfirmClearModal(ModalScreen):

  def compose(self):
    with Vertical(id="confirmDialog"):
      yield Label("Delete this conversation?")
      with Horizontal(id="confirmButtons"):
        yield Button("Yes, Delete", id="button_confirmClear", variant="error")
        yield Button("Cancel", id="button_cancelClear")

  def on_button_pressed(self, event: Button.Pressed):
    self.dismiss(event.button.id == "button_confirmClear")


class SendableTextArea(TextArea):

  class Submit(Message):
    pass

  def _on_key(self, event: events.Key) -> None:
    if event.key == "enter":
      event.prevent_default()
      event.stop()
      self.post_message(SendableTextArea.Submit())
      return
    super()._on_key(event)


class ChatBox(Widget):
  """Display a chat box with the current model."""

  class DeleteConversationRequested(Message):
    pass

  class RenameConversationRequested(Message):
    pass

  class UpdateConversationTitle(Message):
    """Update title of current conversation"""
    def __init__(self, title: str) -> None:
      self.title = title
      super().__init__()

  class ConversationSaveRequested(Message):
    pass


  def __init__(self, model: dict, conversation: list = None, id=None, readonly: bool = False):
    super().__init__(id=id)
    self.conversation = conversation if (conversation is not None) else []
    self.model = model
    self.readonly = readonly


  def compose(self):
    yield Label(f"Conversation with [green]{self.model['name']}[/green]:")
    with Vertical(id="convoBox"):
      with Vertical(id="convoViewport"):
        if not self.conversation:
          yield Label("Start the conversation by sending a message!", classes="systemMessage")
        else:
          for msg in self.conversation:
            if msg['role'] == 'user':
              yield Label(msg['content'], classes="userMessage")
            elif msg['role'] == 'assistant':
              md = Markdown(msg['content'], classes="modelMessage")
              model_label = msg.get('model', '')
              md.border_title = f"{model_label} Responded" if model_label else ""
              yield md
      if self.readonly:
        yield Label("[yellow]Warning: model not installed — conversation is read-only.[/yellow]", classes="systemMessage")
      else:
        with Horizontal(id="inputTray"):
          yield SendableTextArea(id="userInput")
          yield Button("Send", id="button_sendMessage")
          yield Button("Rename", id="button_renameConvo")
          yield Button("Delete Conversation", id="button_deleteConvo", variant="error")


  def on_mount(self):
    # Convo Viewport
    self.convoViewport: Vertical = self.query_one("#convoViewport")
    if self.conversation:
      self.convoViewport.scroll_end(animate=False)
    if self.readonly:
      return
    # Input Widget
    self.inputTray = self.query_one("#inputTray")
    # User Input Box
    self.inputBox: TextArea = self.query_one("#userInput")
    self.inputBox.focus()
    # Send Button
    self.sendButton: Button = self.query_one("#button_sendMessage")
    self.sendButton.disabled = True


  def _scroll_if_at_bottom(self):
    if self.convoViewport.scroll_y >= self.convoViewport.max_scroll_y - 3:
      self.convoViewport.scroll_end(animate=False)


  def _handle_send(self):
    userText = self.inputBox.text
    if not userText:
      return
    if len(self.conversation) <= 1:
      new_title = userText if len(userText) < 10 else f"{userText[:10]}..."
      self.post_message(ChatBox.UpdateConversationTitle(new_title))
    self.convoViewport.mount(Label(userText, classes="userMessage"))
    self.convoViewport.scroll_end(animate=True)
    self.inputBox.clear()
    self.sendButton.disabled = True
    self.get_model_response(userText)


  def on_sendable_text_area_submit(self, _: SendableTextArea.Submit) -> None:
    if not self.sendButton.disabled:
      self._handle_send()


  async def on_button_pressed(self, event: Button.Pressed) -> None:
    if(event.button.id == "button_sendMessage"):
      self._handle_send()
    elif(event.button.id == "button_renameConvo"):
      self.post_message(ChatBox.RenameConversationRequested())
    elif(event.button.id == "button_deleteConvo"):
      def handle_confirm(confirmed: bool):
        if confirmed:
          self.post_message(ChatBox.DeleteConversationRequested())
      self.app.push_screen(ConfirmClearModal(), handle_confirm)


  async def on_text_area_changed(self, event: TextArea.Changed) -> None:
    # If the text area is empty, disable the input, else enable
    if(event.text_area.id == "userInput"):
      if(event.text_area.text == ""):
        self.sendButton.disabled = True
      else:
        self.sendButton.disabled = False


  @work(exclusive=True, thread=True)
  def get_model_response(self, userText):
    start_ts = datetime.now()
    response_widget = None
    try:
      self.conversation.append({
        "role": "user",
        "content": userText
      })
      self.app.call_from_thread(self.post_message, ChatBox.ConversationSaveRequested())
      response_widget = Markdown("", classes="modelMessage")
      response_widget.border_title = "Thinking..."
      self.app.call_from_thread(self.convoViewport.mount, response_widget)
      accumulated = ""
      system_prompt = getattr(self.app, 'system_prompt', '')
      for chunk in stream_conversation_response(self.model['name'], self.conversation, system_prompt):
        if not chunk.get("done", False):
          accumulated += chunk["message"]["content"]
          self.app.call_from_thread(response_widget.update, accumulated)
          self.app.call_from_thread(self._scroll_if_at_bottom)
      self.conversation.append({"role": "assistant", "content": accumulated, "model": self.model['name']})
      self.app.call_from_thread(self.post_message, ChatBox.ConversationSaveRequested())
    except Exception as e:
      if response_widget is not None:
        self.app.call_from_thread(response_widget.remove)
      self.app.call_from_thread(
          self.convoViewport.mount,
          Label(f"Error: {e}", classes="systemMessage")
      )
      self.conversation.pop()
    finally:
      end_ts = datetime.now()
      thinking_time = end_ts - start_ts
      if response_widget is not None:
        self.app.call_from_thread(
          setattr, response_widget, 'border_title',
          f"{self.model['name']} • Thought for {thinking_time.seconds}s"
        )
      self.app.call_from_thread(setattr, self.sendButton, "disabled", False)
      self.app.call_from_thread(self.inputBox.focus)
      self.app.call_from_thread(self.convoViewport.scroll_end, animate=True)

