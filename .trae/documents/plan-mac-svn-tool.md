# MacSvnTool — 项目计划

## 摘要

开发一款跨平台（Windows 开发 → Mac 运行）的 SVN 图形化管理工具，核心设计参考 TortoiseSVN。第一阶段聚焦于独立窗口应用，实现 SVN 的日常核心操作，后续可扩展 Finder 集成。

## 当前状态分析

- **仓库状态**：空项目，无任何代码
- **开发环境**：Windows 主机（Python 3.x 可用）
- **目标平台**：macOS（通过 PyInstaller/PySide6 打包为 .app）

## 技术决策

| 决策项 | 选择 | 理由 |
|---------|------|------|
| 框架 | Python + PySide6 | 跨平台，开发效率高，封装 SVN CLI 自然 |
| 前端 | PySide6 Qt Widgets | Qt 控件成熟，`QTreeView` / `QTableView` 天然适合文件列表和日志 |
| SVN 交互 | 封装 `svn` CLI + `--xml` | 最简单可靠，--xml 输出结构化易解析 |
| 打包 | PyInstaller | 将 Python 应用打包为独立 .app，无需用户安装 Python |
| Finder 集成 | 暂不实现 | 后续版本迭代，需要原生 Swift 扩展 |

## 架构概览

```
MacSvnTool/
├── main.py                    # 应用入口，初始化 QApplication
├── requirements.txt           # PySide6, lxml 等
├── src/
│   ├── __init__.py
│   ├── ui/                    # UI 层 —— 所有界面组件
│   │   ├── __init__.py
│   │   ├── main_window.py     # 主窗口：菜单栏 + 工具栏 + 状态栏 + 中央工作区
│   │   ├── repo_browser.py    # 仓库浏览器：树形文件列表 + 状态图标
│   │   ├── log_viewer.py      # 日志查看器：表格展示提交历史
│   │   ├── diff_viewer.py     # 差异对比器：左右双栏 diff 展示
│   │   ├── commit_dialog.py   # 提交对话框：文件勾选 + 提交信息
│   │   ├── checkout_dialog.py # 检出对话框：URL 输入 + 路径选择
│   │   └── status_widget.py   # 状态面板：文件修改状态列表
│   ├── services/              # 服务层 —— SVN 操作封装
│   │   ├── __init__.py
│   │   ├── svn_service.py     # SVN 命令行调用封装
│   │   └── xml_parser.py      # SVN --xml 输出解析
│   └── models/                # 数据模型
│       ├── __init__.py
│       ├── svn_status.py      # SvnStatus: path, status, revision
│       ├── svn_log.py         # SvnLogEntry: revision, author, date, message
│       └── repo_info.py       # RepoInfo: url, root, uuid, revision
└── resources/                 # 资源文件
    └── icons/                 # SVN 状态图标 (modified, added, deleted, conflicted, etc.)
```

## 分层设计

### 1. Models 层（数据模型）

使用 Python `dataclass` 定义纯数据结构：

- **SvnStatus**：文件路径、状态类型（M/A/D/C/?/!）、版本号、最后修改者
- **SvnLogEntry**：版本号、作者、日期、提交信息、变更文件列表
- **RepoInfo**：仓库 URL、根路径、UUID、当前版本号

### 2. Services 层（SVN 命令封装）

核心类 `SvnService`，通过 `subprocess` 调用系统 `svn` 命令：

| 方法 | SVN 命令 | 返回类型 |
|------|----------|----------|
| `checkout(url, path)` | `svn checkout` | `bool` |
| `update(path)` | `svn update` | `int` (revision) |
| `commit(paths, message)` | `svn commit -m` | `int` (revision) |
| `status(path)` | `svn status --xml` | `List[SvnStatus]` |
| `log(path, limit)` | `svn log --xml -l N` | `List[SvnLogEntry]` |
| `diff(path, revision)` | `svn diff` | `str` |
| `info(path)` | `svn info --xml` | `RepoInfo` |
| `revert(paths)` | `svn revert` | `bool` |
| `add(paths)` | `svn add` | `bool` |
| `cleanup(path)` | `svn cleanup` | `bool` |

`XmlParser` 负责解析 `svn --xml` 的结构化输出，使用 Python 标准库 `xml.etree.ElementTree`。

### 3. UI 层（界面组件）

| 组件 | 功能 | 关键 Qt 控件 |
|------|------|-------------|
| `MainWindow` | 主窗口框架 | `QMainWindow`, `QMenuBar`, `QToolBar`, `QStatusBar` |
| `RepoBrowser` | 工作副本文件浏览 | `QTreeView` + 自定义 `QFileSystemModel` + 状态图标 |
| `LogViewer` | 提交历史表格 | `QTableView` + 自定义 Model，支持点击查看详情 |
| `DiffViewer` | 文件差异对比 | `QSplitter` 分左右，`QPlainTextEdit` 显示差异，支持语法高亮行 |
| `CommitDialog` | 提交对话框 | `QDialog`, `QListWidget`(文件勾选), `QPlainTextEdit`(提交信息) |
| `CheckoutDialog` | 检出对话框 | `QDialog`, `QLineEdit`(URL), 路径选择器 |
| `StatusWidget` | 变更状态列表 | `QTreeView` 展示所有变更文件及状态 |

**设计原则**：
- 主窗口使用 **Tab 式** 或 **Dock 式** 布局，可同时打开多个工作副本
- 工具栏提供快捷操作按钮（更新、提交、日志、刷新）
- 所有耗时 SVN 操作在 **后台线程** (`QThread`) 中执行，避免阻塞 UI
- 操作进度通过信号/槽机制实时反馈到状态栏

## 实施步骤（6 个阶段）

### Phase 1：项目骨架与环境搭建
- 创建项目目录结构
- 编写 `requirements.txt`（PySide6, lxml 等）
- 编写 `main.py` 应用入口，启动空窗口
- 验证 PySide6 在 Windows 上可正常运行

### Phase 2：SVN 服务层
- 实现 `SvnService` 类 —— 封装所有 SVN CLI 调用
- 实现 `XmlParser` 类 —— 解析 `svn status --xml` 和 `svn log --xml` 输出
- 实现基础异常处理（svn 未安装、命令失败等）
- 实现 `WorkerThread(QThread)` 基类，所有 SVN 操作在后台线程执行
- 编写单元测试验证各命令输出解析正确

### Phase 3：数据模型层
- 定义 `SvnStatus` dataclass
- 定义 `SvnLogEntry` dataclass
- 定义 `RepoInfo` dataclass

### Phase 4：核心 UI 组件
- 实现 `MainWindow`（菜单栏、工具栏、状态栏）
- 实现 `RepoBrowser`（打开工作副本路径，树形展示文件 + 状态图标）
- 实现 `StatusWidget`（展示 `svn status` 结果）
- 实现 `CheckoutDialog`（检出仓库）

### Phase 5：进阶 UI 组件
- 实现 `LogViewer`（提交历史列表 + 详情查看）
- 实现 `CommitDialog`（勾选文件 + 输入提交信息）
- 实现 `DiffViewer`（左右对比差异）

### Phase 6：集成与打包
- 将各组件串联到主窗口的菜单/工具栏
- 实现"打开工作副本"流程
- 编写 PyInstaller 打包脚本
- 在 Windows 上验证打包，确保无缺漏依赖

## 待定 / 后续迭代

- Finder 集成（FinderSync Extension + Swift 原生扩展）
- 图标叠加（在 Finder 中显示文件 SVN 状态图标）
- 右键菜单（在 Finder 中右键执行 SVN 操作）
- 分支/合并图形化界面
- 冲突解决可视化工具
- 仓库浏览器（浏览远程仓库结构）
- SVN Blame / 属性编辑器
- 多标签页支持同时管理多个工作副本

## 验证方式

1. **Phase 2 验证**：运行 `svn_service.py` 中的测试函数，对本地 SVN 工作副本执行 status/log/info 等操作
2. **Phase 4-5 验证**：启动应用，手动测试每个 UI 组件的交互
3. **Phase 6 验证**：PyInstaller 打包后在干净环境运行 .app / .exe

## 假设与风险

| 假设/风险 | 应对 |
|-----------|------|
| 用户系统已安装 `svn` 命令行工具 | 启动时检测，未安装则弹窗提示并给出安装指引 |
| PySide6 在 Mac 上行为与 Windows 一致 | 利用 PySide6 的跨平台抽象层，使用 `QStyle` 保持一致体验 |
| `svn --xml` 输出格式跨版本稳定 | 仅解析已知字段，未知字段忽略，使用 `try/except` 防护 |
| Python 打包的 .app 在 Mac 上体积较大 | 可接受，核心功能优先，后续可用 nuitka 等优化 |
