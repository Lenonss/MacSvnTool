from dataclasses import dataclass
from enum import Enum


class SvnItemStatus(Enum):
    MODIFIED = "modified"
    ADDED = "added"
    DELETED = "deleted"
    CONFLICTED = "conflicted"
    UNVERSIONED = "unversioned"
    MISSING = "missing"
    REPLACED = "replaced"
    NORMAL = "normal"


@dataclass
class SvnStatus:
    path: str
    status: SvnItemStatus
    revision: int = 0
    last_author: str = ""
    last_date: str = ""
