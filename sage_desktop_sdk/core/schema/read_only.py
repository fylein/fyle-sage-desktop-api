from dataclasses import dataclass

@dataclass
class Account:
    id: str
    code: str
    version: int
    is_active: bool
    is_archived: bool
    name: int
