# MacSvnTool v1.0 — Spec

## Why
macOS 用户缺少一款像 TortoiseSVN 那样的 SVN 图形化管理工具。本项目为 Mac 用户提供一款独立窗口的 SVN 客户端，覆盖检出、更新、提交、日志查看、差异对比、状态浏览等日常核心操作。

## What Changes
- 新建项目骨架：Python + PySide6 + 分层架构
- SVN 服务层：封装 `svn` CLI 命令，支持 status/log/info/diff/commit/update/checkout/revert/add/cleanup
- 数据模型层：SvnStatus、SvnLogEntry、RepoInfo
- UI 层：MainWindow、RepoBrowser、StatusWidget、CheckoutDialog、CommitDialog、LogViewer、DiffViewer
- 后台线程 WorkerThread：所有耗时操作异步执行，UI 不阻塞
- 打包：PyInstaller 生成独立 .app

## Impact
- Affected specs: 无（新项目）
- Affected code: 全部新建，约 12 个源文件

---

## ADDED Requirements

### Requirement: 项目骨架与环境
项目 SHALL 包含 Python 3.9+ 的项目结构，使用 PySide6 作为 GUI 框架，通过 `venv` 管理依赖。

#### Scenario: 启动应用
- **GIVEN** 系统已安装 Python 3.9+ 和 svn 命令行工具
- **WHEN** 用户运行 `python main.py`
- **THEN** 应用窗口正常显示，标题为 "MacSvnTool"

#### Scenario: svn 命令不可用
- **GIVEN** 系统未安装 svn 命令行工具
- **WHEN** 用户启动应用
- **THEN** 弹窗提示"未检测到 SVN 命令行工具"，应用仍可启动但功能受限

---

### Requirement: SVN 服务层
系统 SHALL 通过 `subprocess` 封装 svn CLI 命令，所有方法为同步调用，通过 `--xml` 参数获取结构化输出。

#### Scenario: 获取工作副本状态
- **GIVEN** 存在一个 SVN 工作副本目录
- **WHEN** 调用 `SvnService.status(path)`
- **THEN** 返回 `List[SvnStatus]`，包含所有文件的路径、状态类型、版本号、最后修改者

#### Scenario: 获取提交日志
- **GIVEN** 存在一个 SVN 工作副本目录
- **WHEN** 调用 `SvnService.log(path, limit=50)`
- **THEN** 返回 `List[SvnLogEntry]`，每条包含版本号、作者、日期、提交信息、变更文件列表

#### Scenario: 获取文件差异
- **GIVEN** 工作副本中某文件已被修改
- **WHEN** 调用 `SvnService.diff(path, revision="BASE:WORKING")`
- **THEN** 返回 unified diff 格式字符串

#### Scenario: 提交变更
- **GIVEN** 工作副本中有待提交的文件
- **WHEN** 调用 `SvnService.commit(paths, message)`
- **THEN** 提交成功，返回新版本号

#### Scenario: 检出仓库
- **GIVEN** 合法的 SVN 仓库 URL 和空的本地目录
- **WHEN** 调用 `SvnService.checkout(url, path)`
- **THEN** 检出成功，返回最新版本号

#### Scenario: 操作失败抛出 SvnError
- **GIVEN** 目标路径不是有效的 SVN 工作副本
- **WHEN** 调用任意需要工作副本的 SvnService 方法
- **THEN** 抛出 `SvnError` 异常，包含错误信息和 stderr 输出

---

### Requirement: 数据模型层
系统 SHALL 使用 Python `dataclass` 定义数据结构：SvnStatus（文件状态）、SvnLogEntry（日志条目，含 SvnChangedPath）、RepoInfo（仓库信息）。

#### Scenario: SvnStatus 数据模型
- **GIVEN** svn status --xml 输出
- **WHEN** XmlParser 解析该输出
- **THEN** 生成 `SvnStatus` 对象列表，每个对象包含 path、status、revision、last_author、last_date

#### Scenario: SvnLogEntry 数据模型
- **GIVEN** svn log --xml 输出
- **WHEN** XmlParser 解析该输出
- **THEN** 生成 `SvnLogEntry` 对象列表，每个包含 revision、author、date、message、changed_paths

#### Scenario: RepoInfo 数据模型
- **GIVEN** svn info --xml 输出
- **WHEN** XmlParser 解析该输出
- **THEN** 生成 `RepoInfo` 对象，包含 url、root、uuid、revision 等字段

---

### Requirement: 主窗口
系统 SHALL 提供一个主窗口（MainWindow），包含菜单栏、工具栏、状态栏和左右分栏的中央工作区。

#### Scenario: 主窗口初始状态
- **GIVEN** 用户启动应用，尚未打开任何工作副本
- **WHEN** 主窗口显示
- **THEN** 中央区域显示提示文字"打开工作副本或检出仓库"，工具栏按钮除[检出]外均禁用

#### Scenario: 打开工作副本
- **GIVEN** 主窗口处于空状态
- **WHEN** 用户点击 "文件→打开工作副本" 并选择一个 SVN 工作副本目录
- **THEN** RepoBrowser 显示文件树和状态图标，StatusWidget 显示变更文件列表，状态栏更新路径和版本号

#### Scenario: 工具栏操作
- **GIVEN** 已打开一个工作副本
- **WHEN** 用户点击工具栏[刷新]按钮
- **THEN** RepoBrowser 和 StatusWidget 重新加载最新状态

---

### Requirement: 文件浏览器 (RepoBrowser)
系统 SHALL 以树形结构展示工作副本的所有文件和目录，并在文件名前显示 SVN 状态图标。

#### Scenario: 文件列表显示
- **GIVEN** 已打开一个 SVN 工作副本
- **WHEN** RepoBrowser 加载完成
- **THEN** 树形视图显示所有文件/目录，状态图标用颜色编码区分不同 SVN 状态

#### Scenario: 右键菜单
- **GIVEN** 在 RepoBrowser 中选中一个文件
- **WHEN** 用户右键点击该文件
- **THEN** 弹出上下文菜单，包含"更新""提交...""比较差异""查看日志""还原""添加""在访达中显示"

---

### Requirement: 变更状态列表 (StatusWidget)
系统 SHALL 在右侧面板展示所有变更文件（非 normal 状态），包含文件名、状态文本、版本号、最后修改者、最后修改时间。

#### Scenario: 变更文件列表
- **GIVEN** 工作副本中有 modified、added、deleted 状态的文件
- **WHEN** StatusWidget 加载完成
- **THEN** 列表显示所有变更文件，每行包含状态图标、文件名、状态描述、版本号、作者、日期
- **AND** normal 状态的文件不显示

#### Scenario: 双击打开差异
- **GIVEN** StatusWidget 显示变更文件列表
- **WHEN** 用户双击某行
- **THEN** 打开 DiffViewer 展示该文件的差异

---

### Requirement: 检出对话框 (CheckoutDialog)
系统 SHALL 提供对话框让用户输入仓库 URL、目标路径和版本号来检出 SVN 仓库。

#### Scenario: 检出仓库
- **GIVEN** 用户打开检出对话框
- **WHEN** 填写合法的仓库 URL、选择空目录作为目标路径，点击[检出]
- **THEN** 后台线程执行检出，成功后自动打开该工作副本

#### Scenario: 检出验证失败
- **GIVEN** 检出对话框中 URL 为空
- **WHEN** 用户点击[检出]
- **THEN** 提示"请输入仓库 URL"，不执行操作

---

### Requirement: 提交对话框 (CommitDialog)
系统 SHALL 提供提交对话框，展示待提交文件列表（可勾选），要求用户输入提交信息。

#### Scenario: 提交变更
- **GIVEN** 工作副本中有已修改文件
- **WHEN** 用户打开提交对话框，勾选文件，输入提交信息，点击[提交]
- **THEN** 提交成功，显示新版本号，自动刷新状态

#### Scenario: 提交信息为空
- **GIVEN** 提交对话框中未输入提交信息
- **WHEN** 用户点击[提交]
- **THEN** 提示"请输入提交信息"，不执行操作

---

### Requirement: 日志查看器 (LogViewer)
系统 SHALL 以表格形式展示提交历史，选中条目后在下方详情面板显示完整信息。

#### Scenario: 查看提交历史
- **GIVEN** 已打开工作副本
- **WHEN** 用户点击"查看日志"
- **THEN** 表格显示最近 50 条提交记录（版本号、作者、日期、信息），下方显示选中条目的详情

#### Scenario: 加载更多
- **GIVEN** 日志查看器已显示 50 条记录
- **WHEN** 用户点击"加载更多"
- **THEN** 追加显示更早的 50 条记录

---

### Requirement: 差异查看器 (DiffViewer)
系统 SHALL 以左右分栏方式展示文件差异，支持语法高亮（新增=绿、删除=红）。

#### Scenario: 查看文件差异
- **GIVEN** 用户在 RepoBrowser 右键点击某文件并选择"比较差异"
- **WHEN** DiffViewer 打开
- **THEN** 左侧显示 BASE 版本，右侧显示 WORKING 版本，新增行绿色背景，删除行红色背景

---

### Requirement: 后台线程
系统 SHALL 通过 WorkerThread(QThread) 将所有耗时 SVN 操作在后台线程执行，通过信号通知 UI。

#### Scenario: 后台操作不阻塞 UI
- **GIVEN** 正在执行 svn checkout（耗时操作）
- **WHEN** checkout 操作进行中
- **THEN** UI 保持响应，状态栏显示进度提示

#### Scenario: 操作失败通知
- **GIVEN** WorkerThread 执行 SVN 操作
- **WHEN** 操作失败（如网络中断）
- **THEN** 通过信号 emit 错误消息，UI 层弹出错误对话框
