from dataclasses import dataclass

@dataclass
class UserEntity:
    uuid: str
    username: str
    email: str
    is_active: bool = True