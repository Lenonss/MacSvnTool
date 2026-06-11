from dataclasses import dataclass, field


@dataclass
class SvnChangedPath:
    path: str
    action: str
    copy_from_path: str = ""
    copy_from_rev: int = 0


@dataclass
class SvnLogEntry:
    revision: int
    author: str
    date: str
    message: str
    changed_paths: list = field(default_factory=list)
