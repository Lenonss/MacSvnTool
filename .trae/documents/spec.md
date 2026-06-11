# MacSvnTool — 技术规格说明书

## 1. 产品定义

### 1.1 产品名称
**MacSvnTool** — macOS SVN 图形化管理工具

### 1.2 产品定位
面向 macOS 用户的 Subversion (SVN) 版本控制客户端。参考 TortoiseSVN 的设计理念，以独立窗口应用形式提供 SVN 核心操作（检出、更新、提交、日志、差异、状态）的图形化界面。后续可扩展 Finder 集成。

### 1.3 目标用户
- 使用 SVN 进行版本控制的 macOS 开发者
- 习惯 TortoiseSVN 操作方式但迁移到 Mac 的用户
- 希望用图形界面替代 SVN 命令行的用户

### 1.4 功能范围 (v1.0)

**包含 (In Scope):**
- SVN 仓库检出 (Checkout)
- 工作副本状态查看 (Status)
- 文件差异对比 (Diff)
- 提交变更 (Commit)
- 更新工作副本 (Update)
- 提交日志查看 (Log)
- 文件还原 (Revert)
- 新增文件到版本控制 (Add)
- 工作副本清理 (Cleanup)
- 仓库信息查看 (Info)
- 文件浏览器 + SVN 状态图标叠加

**不包含 (Out of Scope v1.0):**
- Finder 右键菜单集成
- Finder 文件图标叠加
- 分支/合并图形化界面
- 冲突解决可视化工具
- SVN Blame / 属性编辑
- 远程仓库浏览器
- Shelve / Checkpoint

---

## 2. 技术架构

### 2.1 技术栈

| 层级 | 技术 | 版本要求 |
|------|------|----------|
| 语言 | Python | 3.9+ |
| GUI 框架 | PySide6 (Qt for Python) | 6.5+ |
| XML 解析 | xml.etree.ElementTree | 标准库 |
| SVN 交互 | 系统 `svn` 命令行 | 1.10+ |
| 打包工具 | PyInstaller | 5.0+ |
| 包管理 | pip / venv | — |

### 2.2 架构分层

```
┌─────────────────────────────────────────────────┐
│                  UI Layer (PySide6)              │
│  MainWindow / RepoBrowser / LogViewer / Diff... │
├─────────────────────────────────────────────────┤
│              Service Layer                       │
│  SvnService (CLI wrapper) / XmlParser            │
├─────────────────────────────────────────────────┤
│               Model Layer                        │
│  SvnStatus / SvnLogEntry / RepoInfo              │
└─────────────────────────────────────────────────┘
```

**依赖方向：UI → Service → Model（单向依赖）**

### 2.3 目录结构

```
MacSvnTool/
├── main.py
├── requirements.txt
├── build.py                    # PyInstaller 打包脚本
├── src/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── svn_status.py
│   │   ├── svn_log.py
│   │   └── repo_info.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── svn_service.py
│   │   ├── xml_parser.py
│   │   └── worker_thread.py
│   └── ui/
│       ├── __init__.py
│       ├── main_window.py
│       ├── repo_browser.py
│       ├── log_viewer.py
│       ├── diff_viewer.py
│       ├── commit_dialog.py
│       ├── checkout_dialog.py
│       └── status_widget.py
└── resources/
    └── icons/
        ├── modified.png
        ├── added.png
        ├── deleted.png
        ├── conflicted.png
        ├── unversioned.png
        ├── missing.png
        ├── normal.png
        └── app_icon.png
```

---

## 3. 数据模型规格

### 3.1 SvnStatus

```python
from dataclasses import dataclass, field
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
```

**字段说明：**

| 字段 | 类型 | 来源 | 示例 |
|------|------|------|------|
| `path` | `str` | `svn status --xml` → `<entry path="...">` | `"src/main.py"` |
| `status` | `SvnItemStatus` | `<wc-status item="...">` 映射 | `SvnItemStatus.MODIFIED` |
| `revision` | `int` | `<wc-status revision="...">` | `42` |
| `last_author` | `str` | `<commit><author>` in status XML | `"john"` |
| `last_date` | `str` | `<commit><date>` in status XML | `"2024-01-15T10:30:00Z"` |

### 3.2 SvnLogEntry

```python
@dataclass
class SvnLogEntry:
    revision: int
    author: str
    date: str
    message: str
    changed_paths: list = field(default_factory=list)

@dataclass
class SvnChangedPath:
    path: str
    action: str          # "A" / "M" / "D" / "R"
    copy_from_path: str = ""
    copy_from_rev: int = 0
```

**字段说明：**

| 字段 | 类型 | 来源 | 示例 |
|------|------|------|------|
| `revision` | `int` | `<logentry revision="...">` | `100` |
| `author` | `str` | `<author>` | `"alice"` |
| `date` | `str` | `<date>` （格式化为可读字符串） | `"2024-03-15 14:22:10"` |
| `message` | `str` | `<msg>` | `"修复登录Bug"` |
| `changed_paths` | `list[SvnChangedPath]` | `<paths><path>` | — |

### 3.3 RepoInfo

```python
@dataclass
class RepoInfo:
    url: str
    root: str
    uuid: str
    revision: int
    last_changed_rev: int
    last_changed_date: str
    last_changed_author: str
```

---

## 4. 服务层接口规格

### 4.1 SvnService

所有 SVN 操作的核心封装类。**所有公共方法均为同步调用**（内部使用 `subprocess.run`），由上层 UI 负责通过 `WorkerThread` 实现异步。

```python
class SvnService:
    """SVN 命令行调用封装。假定系统已安装 svn 命令。"""

    @staticmethod
    def is_available() -> bool:
        """检测 svn 命令是否可用。"""
        ...

    @staticmethod
    def checkout(url: str, path: str) -> int:
        """检出仓库。返回最新版本号。异常时抛出 SvnError。"""
        ...

    @staticmethod
    def update(path: str, revision: str = "HEAD") -> int:
        """更新工作副本到指定版本。返回更新后的版本号。"""
        ...

    @staticmethod
    def commit(paths: list[str], message: str) -> int:
        """提交指定文件。返回新版本号。"""
        ...

    @staticmethod
    def status(path: str, recursive: bool = True) -> list[SvnStatus]:
        """获取工作副本状态。返回状态列表。"""
        ...

    @staticmethod
    def log(path: str, limit: int = 50, revision: str = "HEAD:1") -> list[SvnLogEntry]:
        """获取提交日志。返回日志条目列表。"""
        ...

    @staticmethod
    def diff(path: str, revision: str = "BASE:WORKING") -> str:
        """获取差异文本。返回 unified diff 字符串。"""
        ...

    @staticmethod
    def info(path: str) -> RepoInfo:
        """获取仓库信息。"""
        ...

    @staticmethod
    def revert(paths: list[str], recursive: bool = False) -> None:
        """还原文件变更。异常时抛出 SvnError。"""
        ...

    @staticmethod
    def add(paths: list[str], recursive: bool = False) -> None:
        """将文件添加到版本控制。"""
        ...

    @staticmethod
    def cleanup(path: str) -> None:
        """清理工作副本。"""
        ...
```

### 4.2 SvnError

```python
class SvnError(Exception):
    """SVN 操作异常。"""
    def __init__(self, message: str, command: str = "", stderr: str = ""):
        self.message = message
        self.command = command
        self.stderr = stderr
        super().__init__(message)
```

### 4.3 异常处理规范

| 场景 | 行为 |
|------|------|
| `svn` 命令不可用 | `SvnService.is_available()` 返回 `False`，启动时弹窗提示 |
| 路径不是工作副本 | `SvnError`，包含 stderr 信息 |
| 网络不可达 | `SvnError`，显示网络错误提示 |
| 认证失败 | `SvnError`，提示用户检查凭据 |
| 命令执行超时 | 60 秒超时，`SvnError` |

### 4.4 XmlParser

```python
class XmlParser:
    """将 svn --xml 输出解析为数据模型。"""

    @staticmethod
    def parse_status(xml_string: str) -> list[SvnStatus]:
        """解析 svn status --xml 输出。"""
        ...

    @staticmethod
    def parse_log(xml_string: str) -> list[SvnLogEntry]:
        """解析 svn log --xml 输出。"""
        ...

    @staticmethod
    def parse_info(xml_string: str) -> RepoInfo:
        """解析 svn info --xml 输出。"""
        ...
```

### 4.5 WorkerThread

```python
from PySide6.QtCore import QThread, Signal

class WorkerThread(QThread):
    """SVN 操作后台线程基类。"""

    finished = Signal(object)     # 成功时 emit 结果数据
    error = Signal(str)           # 失败时 emit 错误消息

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

    def run(self):
        try:
            result = self._fn(*self._args, **self._kwargs)
            self.finished.emit(result)
        except SvnError as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(f"未知错误: {e}")
```

---

## 5. UI 组件规格

### 5.1 MainWindow（主窗口）

```
┌──────────────────────────────────────────────────────┐
│  菜单栏: 文件 | SVN操作 | 视图 | 帮助                   │
├──────────────────────────────────────────────────────┤
│  工具栏: [检出] [更新] [提交] [日志] [还原] [刷新]       │
├──────────────────────────────────────────────────────┤
│                                                       │
│  ┌──────────────────────┐ ┌────────────────────────┐  │
│  │   RepoBrowser (树)    │ │   StatusWidget (列表)   │  │
│  │   - 文件目录树        │ │   - 已修改文件          │  │
│  │   - SVN 状态图标      │ │   - 状态/版本号         │  │
│  │                      │ │                        │  │
│  │                      │ │                        │  │
│  └──────────────────────┘ └────────────────────────┘  │
│                                                       │
├──────────────────────────────────────────────────────┤
│  状态栏: 当前工作副本路径 | 版本号 | 就绪                 │
└──────────────────────────────────────────────────────┘
```

**布局：** 左右分栏 (QSplitter)，左侧文件浏览器，右侧变更状态列表。

**菜单结构：**

| 菜单 | 菜单项 | 快捷键 | 功能 |
|------|--------|--------|------|
| 文件 | 打开工作副本... | Ctrl+O | 选择本地 SVN 工作副本目录打开 |
| 文件 | 检出... | Ctrl+Shift+O | 打开检出对话框 |
| 文件 | 退出 | Ctrl+Q | 退出应用 |
| SVN操作 | 更新 | Ctrl+U | 更新当前工作副本 |
| SVN操作 | 提交... | Ctrl+M | 打开提交对话框 |
| SVN操作 | 查看日志 | Ctrl+L | 打开日志查看器 |
| SVN操作 | 还原 | — | 还原选中文件 |
| SVN操作 | 添加 | — | 添加选中文件 |
| SVN操作 | 清理 | — | 清理工作副本 |
| 视图 | 刷新 | F5 | 刷新状态 |
| 帮助 | 关于 | — | 关于对话框 |

### 5.2 RepoBrowser（文件浏览器）

- **控件：** `QTreeView` + 自定义 `QFileSystemModel`
- **功能：**
  - 以树形结构展示工作副本的所有文件/目录
  - 在文件名前显示 SVN 状态图标（modified/added/deleted/conflicted/normal）
  - 支持右键菜单（更新、提交、还原、差异、日志）
  - 双击文件在系统默认编辑器中打开
  - 首次打开工作副本后自动加载状态

**图标映射：**

| SVN 状态 | 图标文件 | 描述 |
|----------|----------|------|
| `modified` | `modified.png` | 红色感叹号 |
| `added` | `added.png` | 蓝色加号 |
| `deleted` | `deleted.png` | 红色叉号 |
| `conflicted` | `conflicted.png` | 黄色警告 |
| `unversioned` | `unversioned.png` | 灰色问号 |
| `missing` | `missing.png` | 红色叉号 |
| `normal` | `normal.png` | 绿色勾号 |

**右键菜单结构：**

```
┌─────────────┐
│ 更新         │
│ 提交...      │
│─────────────│
│ 比较差异     │
│ 查看日志     │
│─────────────│
│ 还原         │
│ 添加         │
│─────────────│
│ 在访达中显示  │
└─────────────┘
```

### 5.3 StatusWidget（变更状态列表）

- **控件：** `QTreeView` + 自定义 Model
- **列定义：**
  - 文件名（带图标）
  - 状态文本（"已修改"/"已添加"/"已删除"/"冲突"）
  - 版本号
  - 最后修改者
  - 最后修改时间
- **功能：**
  - 显示 `svn status` 结果中所有非 normal 状态的条目
  - 支持按列排序
  - 支持多选，批量操作（还原、添加）
  - 双击文件行打开差异查看器

### 5.4 CheckoutDialog（检出对话框）

```
┌──────────────────────────────────────────┐
│  检出仓库                                  │
├──────────────────────────────────────────┤
│                                          │
│  仓库URL:  [________________] [浏览...]   │
│                                          │
│  目标路径: [________________] [选择...]   │
│                                          │
│  版本:     ○ HEAD  ○ 指定: [____]        │
│                                          │
├──────────────────────────────────────────┤
│                    [取消]    [检出]        │
└──────────────────────────────────────────┘
```

- **控件：** `QDialog`
- **字段：**
  - `QLineEdit` — 仓库 URL
  - `QLineEdit` + `QPushButton` — 本地目标路径（打开 `QFileDialog` 选择目录）
  - `QRadioButton` — 版本选择（HEAD / 指定版本号）
- **验证：**
  - URL 不能为空
  - 目标路径不能为空，且不能是已有工作副本
  - 检出操作在后台线程执行，显示进度（通过解析 `svn checkout` 的输出行）
- **结果：** 检出成功后自动打开该工作副本

### 5.5 CommitDialog（提交对话框）

```
┌──────────────────────────────────────────────┐
│  提交变更                                      │
├──────────────────────────────────────────────┤
│                                              │
│  ┌────────────────────────────────────┐      │
│  │ ☑ src/main.py         已修改       │      │
│  │ ☑ src/utils.py        已修改       │      │
│  │ ☐ src/legacy.py       已删除       │      │
│  │ ☐ new_feature.py      已添加       │      │
│  └────────────────────────────────────┘      │
│                                              │
│  提交信息:                                    │
│  ┌────────────────────────────────────┐      │
│  │ 修复了登录页面的验证逻辑              │      │
│  │                                    │      │
│  └────────────────────────────────────┘      │
│                                              │
│  ☐ 提交后更新到最新                           │
│                                              │
├──────────────────────────────────────────────┤
│                      [取消]    [提交]          │
└──────────────────────────────────────────────┘
```

- **控件：** `QDialog`
- **文件列表：** `QListWidget`，每项带复选框 + 状态图标 + 文件名 + 状态文本
  - 默认全选（除了 unversioned 文件）
- **提交信息：** `QPlainTextEdit`，最少 1 个字符
- **选项：** `QCheckBox` — "提交后更新到最新"
- **验证：**
  - 至少勾选一个文件
  - 提交信息不能为空
- **提交后行为：**
  - 显示成功提示（含新版本号）
  - 自动刷新状态

### 5.6 LogViewer（日志查看器）

```
┌──────────────────────────────────────────────┐
│  提交日志 - /path/to/working/copy              │
├──────────────────────────────────────────────┤
│ ┌──────┬────────┬──────────────────┬───────┐ │
│ │ 版本  │ 作者   │ 日期              │ 信息   │ │
│ ├──────┼────────┼──────────────────┼───────┤ │
│ │ 100  │ alice  │ 2024-03-15 14:22 │ 修复. │ │
│ │ 99   │ bob    │ 2024-03-14 09:15 │ 重构. │ │
│ │ 98   │ alice  │ 2024-03-13 18:00 │ 新增. │ │
│ └──────┴────────┴──────────────────┴───────┘ │
│ ┌──────────────────────────────────────────┐ │
│ │ 详情:                                     │ │
│ │ 版本 100 - alice - 2024-03-15 14:22:10    │ │
│ │                                           │ │
│ │ 修复了登录页面的验证逻辑                    │ │
│ │                                           │ │
│ │ 变更文件:                                  │ │
│ │   M  src/main.py                          │ │
│ │   M  src/utils.py                         │ │
│ │   D  src/legacy.py                        │ │
│ └──────────────────────────────────────────┘ │
├──────────────────────────────────────────────┤
│ [差异对比] [还原到此版本]          [关闭]      │
└──────────────────────────────────────────────┘
```

- **控件：** `QDialog`
- **日志列表：** `QTableView`，列：版本号、作者、日期、提交信息（截断）
- **详情面板：** 下半部分 `QTextEdit`（只读），显示选中条目的完整信息
  - 提交信息全文
  - 变更文件列表（路径 + 操作类型 A/M/D/R）
- **分页：** 初始加载 50 条，底部有"加载更多"按钮
- **按钮：**
  - "差异对比" — 打开 DiffViewer 对比此版本与上一版本
  - "还原到此版本" — 对选中文件执行 revert

### 5.7 DiffViewer（差异查看器）

```
┌──────────────────────────────────────────────┐
│  差异对比 - src/main.py                        │
├──────────────────────────────────────────────┤
│  版本: [BASE(版本98) ▼] → [WORKING ▼]         │
├──────────────────────────────────────────────┤
│ ┌──────────────────┬──────────────────────┐  │
│ │  BASE (旧版)      │  WORKING (当前变更)   │  │
│ │ ──────────────── │ ──────────────────── │  │
│ │  86: old_code    │  86: new_code        │  │
│ │  87: unchanged   │  87: unchanged       │  │
│ │                  │  88: + added_line    │  │
│ │  89: removed_line│                      │  │
│ └──────────────────┴──────────────────────┘  │
├──────────────────────────────────────────────┤
│                              [关闭]           │
└──────────────────────────────────────────────┘
```

- **控件：** `QDialog`
- **版本选择器：** 两个 `QComboBox` — 旧版本 / 新版本
  - 选项：BASE（当前检出版本）、WORKING（本地修改）、HEAD、指定版本号
- **对比显示：** `QSplitter` 水平分割
  - 左侧 `QPlainTextEdit`（只读）— 旧版本文件内容
  - 右侧 `QPlainTextEdit`（只读）— 新版本文件内容
- **语法高亮：**
  - 绿色背景 = 新增行
  - 红色背景 = 删除行
  - 通过解析 unified diff 输出逐行着色

---

## 6. 交互流程

### 6.1 应用启动流程

```
启动 main.py
  → 检测 svn 命令是否可用
    → 否: 弹窗提示安装，退出或继续（功能受限）
    → 是: 初始化 QApplication
  → 显示 MainWindow（空状态，提示"打开工作副本或检出仓库"）
  → 等待用户操作
```

### 6.2 打开工作副本流程

```
用户点击"文件 → 打开工作副本" 或工具栏按钮
  → QFileDialog 选择目录
  → 验证目录是否为 SVN 工作副本 (svn info)
    → 否: 弹窗提示"所选目录不是有效的SVN工作副本"
    → 是:
      → 后台线程执行 svn status + svn info
      → RepoBrowser 加载文件树 + 状态图标
      → StatusWidget 显示变更文件列表
      → 状态栏更新路径和版本号
```

### 6.3 提交流程

```
用户在 StatusWidget 选中文件，点击"提交"
  → 打开 CommitDialog，自动勾选已修改/已添加/已删除文件
  → 用户输入提交信息，确认
  → 后台线程执行 svn commit
  → 成功: 显示成功提示（含版本号），刷新状态
  → 失败: 显示错误详情
```

---

## 7. 错误处理规范

| 错误场景 | 用户提示 | 日志 |
|----------|----------|------|
| svn 命令未找到 | "未检测到 SVN 命令行工具。请确保已安装 Subversion。" | WARNING |
| 目录非工作副本 | "所选目录不是有效的 SVN 工作副本。" | INFO |
| 网络连接失败 | "无法连接到 SVN 服务器，请检查网络连接。" | ERROR |
| 认证失败 | "SVN 认证失败，请检查用户名和密码。" | ERROR |
| 提交信息为空 | "请输入提交信息。"（表单级验证，不触发操作） | — |
| 检出目录已存在 | "目标目录已存在，请选择其他路径。" | INFO |
| 命令执行超时 | "SVN 操作超时，请检查网络连接后重试。" | ERROR |

---

## 8. 资源文件规范

### 8.1 图标规格

- 格式：PNG，透明背景
- 尺寸：16×16 px（列表/树形视图）
- 颜色编码：
  - 绿色 = normal
  - 红色 = modified / deleted / missing
  - 蓝色 = added
  - 黄色/橙色 = conflicted
  - 灰色 = unversioned

**v1.0 方案：** 使用 Unicode 字符绘制简易图标（`●` 绿色圆点、`✚` 蓝色加号等），避免额外图片资源依赖。后续版本替换为真正的图标文件。

### 8.2 窗口默认规格

| 属性 | 值 |
|------|-----|
| 默认宽度 | 1200 px |
| 默认高度 | 800 px |
| 最小宽度 | 800 px |
| 最小高度 | 600 px |
| 标题 | `MacSvnTool - [工作副本路径]` |
