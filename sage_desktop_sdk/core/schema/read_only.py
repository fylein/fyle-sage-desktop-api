from dataclasses import dataclass

@dataclass
class Account:
    id: str
    code: str
    version: int
    is_active: bool
    is_archived: bool
    name: int


    @classmethod
    def from_dict(cls, account_dict):
        return cls(
            id=account_dict['Id'],
            code=account_dict['Code'],
            version=account_dict['Version'],
            is_active=account_dict['IsActive'],
            is_archived=account_dict['IsArchived'],
            name=account_dict['Name'],
        )
