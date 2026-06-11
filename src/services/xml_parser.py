import xml.etree.ElementTree as ET
from datetime import datetime

from src.models.svn_status import SvnStatus, SvnItemStatus
from src.models.svn_log import SvnLogEntry, SvnChangedPath
from src.models.repo_info import RepoInfo


class SvnError(Exception):
    def __init__(self, message: str, command: str = "", stderr: str = ""):
        self.message = message
        self.command = command
        self.stderr = stderr
        super().__init__(message)

    def __str__(self):
        parts = [self.message]
        if self.command:
            parts.append(f"命令: {self.command}")
        if self.stderr:
            parts.append(self.stderr.strip())
        return "\n".join(parts)


STATUS_MAP = {
    "modified": SvnItemStatus.MODIFIED,
    "added": SvnItemStatus.ADDED,
    "deleted": SvnItemStatus.DELETED,
    "conflicted": SvnItemStatus.CONFLICTED,
    "unversioned": SvnItemStatus.UNVERSIONED,
    "missing": SvnItemStatus.MISSING,
    "replaced": SvnItemStatus.REPLACED,
    "normal": SvnItemStatus.NORMAL,
}


class XmlParser:

    @staticmethod
    def parse_status(xml_string: str) -> list:
        root = ET.fromstring(xml_string)
        result = []
        for target in root.findall("target"):
            for entry in target.findall("entry"):
                path = entry.get("path", "")
                wc_status = entry.find("wc-status")
                if wc_status is None:
                    continue
                item = wc_status.get("item", "normal")
                status = STATUS_MAP.get(item, SvnItemStatus.NORMAL)
                revision_str = wc_status.get("revision", "0")
                revision = int(revision_str) if revision_str else 0
                last_author = ""
                last_date = ""
                commit_elem = wc_status.find("commit")
                if commit_elem is not None:
                    author_elem = commit_elem.find("author")
                    if author_elem is not None and author_elem.text:
                        last_author = author_elem.text
                    date_elem = commit_elem.find("date")
                    if date_elem is not None and date_elem.text:
                        last_date = XmlParser._format_date(date_elem.text)
                result.append(SvnStatus(
                    path=path,
                    status=status,
                    revision=revision,
                    last_author=last_author,
                    last_date=last_date
                ))
        return result

    @staticmethod
    def parse_log(xml_string: str) -> list:
        root = ET.fromstring(xml_string)
        result = []
        for entry in root.findall("logentry"):
            revision = int(entry.get("revision", "0"))
            author_elem = entry.find("author")
            author = author_elem.text if author_elem is not None and author_elem.text else ""
            date_elem = entry.find("date")
            date = XmlParser._format_date(date_elem.text) if date_elem is not None and date_elem.text else ""
            msg_elem = entry.find("msg")
            message = msg_elem.text if msg_elem is not None and msg_elem.text else ""
            changed_paths = []
            paths_elem = entry.find("paths")
            if paths_elem is not None:
                for p in paths_elem.findall("path"):
                    changed_paths.append(SvnChangedPath(
                        path=p.text if p.text else "",
                        action=p.get("action", "M"),
                        copy_from_path=p.get("copyfrom-path", ""),
                        copy_from_rev=int(p.get("copyfrom-rev", "0")) if p.get("copyfrom-rev") else 0
                    ))
            result.append(SvnLogEntry(
                revision=revision,
                author=author,
                date=date,
                message=message,
                changed_paths=changed_paths
            ))
        return result

    @staticmethod
    def parse_info(xml_string: str) -> RepoInfo:
        root = ET.fromstring(xml_string)
        entry = root.find("entry")
        if entry is None:
            raise ValueError("Invalid svn info XML: missing entry element")
        url = entry.findtext("url", "")
        repo = entry.find("repository")
        root_path = repo.findtext("root", "") if repo is not None else ""
        uuid = repo.findtext("uuid", "") if repo is not None else ""
        commit_elem = entry.find("commit")
        revision = int(commit_elem.get("revision", "0")) if commit_elem is not None else 0
        wc_info = entry.find("wc-info")
        if wc_info is not None:
            wc_commit_elem = wc_info.find("commit")
            last_changed_rev = int(wc_commit_elem.get("revision", "0")) if wc_commit_elem is not None else 0
            last_changed_date = ""
            last_changed_author = ""
            if wc_commit_elem is not None:
                date_elem = wc_commit_elem.find("date")
                if date_elem is not None and date_elem.text:
                    last_changed_date = XmlParser._format_date(date_elem.text)
                author_elem = wc_commit_elem.find("author")
                if author_elem is not None and author_elem.text:
                    last_changed_author = author_elem.text
        else:
            last_changed_rev = revision
            last_changed_date = ""
            last_changed_author = ""
        return RepoInfo(
            url=url,
            root=root_path,
            uuid=uuid,
            revision=revision,
            last_changed_rev=last_changed_rev,
            last_changed_date=last_changed_date,
            last_changed_author=last_changed_author
        )

    @staticmethod
    def _format_date(date_str: str) -> str:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                dt = datetime.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S")
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                return date_str
