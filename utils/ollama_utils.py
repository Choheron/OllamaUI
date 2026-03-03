import requests
import json

OLLAMA_BASE_URL = "http://192.168.1.200:11434"

def get_installed_models():
  # Query server for models
  response = requests.get(f"{OLLAMA_BASE_URL}/api/tags")
  modelList = response.json()['models']
  return modelList


def get_response(model: str, prompt: str):
  """Query the passed in model for a response."""
  # Build query JSON
  reqBody = {
    "model": model,
    "prompt": prompt,
    "stream": False
  }
  # Query Backend
  response = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=reqBody)
  modelResponse =  response.json()['response']
  return modelResponse


def get_converstaion_response(model: str, conversation: list[dict]):
  """Query the passed in model for a response based on passed in conversation data. Returns raw response from Ollama."""
  # Build query JSON
  reqBody = {
    "model": model,
    "messages": conversation,
    "stream": False
  }
  # Query Backend
  response = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=reqBody)
  resData =  response.json()
  return resData


def delete_model(model_name: str) -> bool:
  """Delete a model from the Ollama server. Returns True on success."""
  try:
    response = requests.delete(f"{OLLAMA_BASE_URL}/api/delete", json={"name": model_name}, timeout=30)
    return response.status_code == 200
  except Exception:
    return False


def stream_conversation_response(model: str, conversation: list[dict], system_prompt: str = ""):
  """Query the passed in model for a streaming response. Yields parsed response chunks until done."""
  messages = ([{"role": "system", "content": system_prompt}] + conversation) if system_prompt else conversation
  reqBody = {
    "model": model,
    "messages": messages,
    "stream": True
  }
  response = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=reqBody, stream=True)
  for line in response.iter_lines():
    if line:
      yield json.loads(line)