from typing import Protocol

class ChatRepositoryProtcol(Protocol):
    def save_message():
        pass

    def load_chat_history():
        pass