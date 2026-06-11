import subprocess
import shutil

from src.services.xml_parser import XmlParser, SvnError


class SvnService:

    SVN_COMMAND = "svn"
    TIMEOUT = 60

    @classmethod
    def is_available(cls) -> bool:
        return shutil.which(cls.SVN_COMMAND) is not None

    @classmethod
    def checkout(cls, url: str, path: str) -> int:
        result = cls._run(["checkout", url, path])
        output = result.stdout.strip()
        revision = 0
        for line in output.splitlines():
            stripped = line.strip()
            if stripped.startswith("Checked out revision") or stripped.startswith("At revision"):
                parts = stripped.rsplit(" ", 1)
                if parts:
                    try:
                        revision = int(parts[-1].rstrip("."))
                    except ValueError:
                        pass
        return revision

    @classmethod
    def update(cls, path: str, revision: str = "HEAD") -> int:
        result = cls._run(["update", path, "-r", revision])
        output = result.stdout.strip()
        rev = 0
        for line in output.splitlines():
            stripped = line.strip()
            if stripped.startswith("Updated to revision") or stripped.startswith("At revision"):
                parts = stripped.rsplit(" ", 1)
                if parts:
                    try:
                        rev = int(parts[-1].rstrip("."))
                    except ValueError:
                        pass
        return rev

    @classmethod
    def commit(cls, paths: list, message: str) -> int:
        args = ["commit", "-m", message] + paths
        result = cls._run(args)
        output = result.stdout.strip()
        revision = 0
        for line in output.splitlines():
            stripped = line.strip()
            if stripped.startswith("Committed revision"):
                parts = stripped.rsplit(" ", 1)
                if parts:
                    try:
                        revision = int(parts[-1].rstrip("."))
                    except ValueError:
                        pass
        return revision

    @classmethod
    def status(cls, path: str, recursive: bool = True) -> list:
        args = ["status", "--xml"]
        if not recursive:
            args.append("--depth=immediates")
        args.append(path)
        result = cls._run(args)
        return XmlParser.parse_status(result.stdout)

    @classmethod
    def log(cls, path: str, limit: int = 50, revision: str = "HEAD:1") -> list:
        args = ["log", "--xml", "--verbose", "-l", str(limit), "-r", revision, path]
        result = cls._run(args)
        return XmlParser.parse_log(result.stdout)

    @classmethod
    def diff(cls, path: str, revision: str = "BASE:WORKING") -> str:
        if revision:
            result = cls._run(["diff", "-r", revision, path])
        else:
            result = cls._run(["diff", path])
        return result.stdout

    @classmethod
    def info(cls, path: str):
        result = cls._run(["info", "--xml", path])
        return XmlParser.parse_info(result.stdout)

    @classmethod
    def revert(cls, paths: list, recursive: bool = False):
        args = ["revert"]
        if recursive:
            args.append("--recursive")
        args.extend(paths)
        cls._run(args)

    @classmethod
    def add(cls, paths: list, recursive: bool = False):
        args = ["add"]
        if recursive:
            args.append("--recursive")
        args.extend(paths)
        cls._run(args)

    @classmethod
    def cleanup(cls, path: str):
        cls._run(["cleanup", path])

    @classmethod
    def _run(cls, args: list) -> subprocess.CompletedProcess:
        cmd = [cls.SVN_COMMAND] + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=cls.TIMEOUT
            )
            if result.returncode != 0:
                raise SvnError(
                    f"SVN 命令执行失败 (返回码: {result.returncode})",
                    command=" ".join(cmd),
                    stderr=result.stderr
                )
            return result
        except subprocess.TimeoutExpired:
            raise SvnError(
                "SVN 操作超时，请检查网络连接后重试",
                command=" ".join(cmd)
            )
        except FileNotFoundError:
            raise SvnError(
                "未检测到 SVN 命令行工具。请确保已安装 Subversion。",
                command=cls.SVN_COMMAND
            )
