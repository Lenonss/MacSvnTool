from dataclasses import dataclass


@dataclass
class RepoInfo:
    url: str
    root: str
    uuid: str
    revision: int
    last_changed_rev: int
    last_changed_date: str
    last_changed_author: str
