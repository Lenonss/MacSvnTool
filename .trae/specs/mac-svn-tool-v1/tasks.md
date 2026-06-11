# MacSvnTool v1.0 — Tasks

## Phase 1: 项目骨架与环境搭建

- [x] **Task 1.1**: 创建项目目录结构和 `__init__.py` 文件
  - 创建 `src/models/__init__.py`
  - 创建 `src/services/__init__.py`
  - 创建 `src/ui/__init__.py`
  - 创建 `src/__init__.py`
  - 创建 `resources/icons/` 目录
  - **验证**: 目录结构符合架构概览中的设计

- [x] **Task 1.2**: 编写 `requirements.txt`
  - 添加 `PySide6>=6.5`
  - 添加 `pyinstaller>=5.0`
  - **验证**: `pip install -r requirements.txt` 无错误

- [x] **Task 1.3**: 编写 `main.py` 应用入口
  - 初始化 `QApplication`
  - 创建 `MainWindow` 实例并显示
  - 启动前检测 `svn` 命令可用性
  - **验证**: `python main.py` 可启动空窗口

## Phase 2: 数据模型层

- [x] **Task 2.1**: 实现 `src/models/svn_status.py`
  - 定义 `SvnItemStatus` 枚举（MODIFIED, ADDED, DELETED, CONFLICTED, UNVERSIONED, MISSING, REPLACED, NORMAL）
  - 定义 `SvnStatus` dataclass（path, status, revision, last_author, last_date）
  - **验证**: 可正常 import，dataclass 可实例化

- [x] **Task 2.2**: 实现 `src/models/svn_log.py`
  - 定义 `SvnChangedPath` dataclass（path, action, copy_from_path, copy_from_rev）
  - 定义 `SvnLogEntry` dataclass（revision, author, date, message, changed_paths）
  - **验证**: 可正常 import，dataclass 可实例化

- [x] **Task 2.3**: 实现 `src/models/repo_info.py`
  - 定义 `RepoInfo` dataclass（url, root, uuid, revision, last_changed_rev, last_changed_date, last_changed_author）
  - **验证**: 可正常 import，dataclass 可实例化

## Phase 3: SVN 服务层

- [x] **Task 3.1**: 实现 `SvnError` 异常类和 `src/services/xml_parser.py`
  - `SvnError`: message, command, stderr 字段
  - `XmlParser.parse_status()`: 解析 `svn status --xml` → `List[SvnStatus]`
  - `XmlParser.parse_log()`: 解析 `svn log --xml` → `List[SvnLogEntry]`
  - `XmlParser.parse_info()`: 解析 `svn info --xml` → `RepoInfo`
  - **验证**: 用真实 SVN 工作副本的 `--xml` 输出测试解析

- [x] **Task 3.2**: 实现 `src/services/svn_service.py` 核心方法
  - `is_available()`: 检测 svn 命令
  - `checkout()` / `update()` / `commit()` / `revert()` / `add()` / `cleanup()`: 修改操作
  - `status()` / `log()` / `diff()` / `info()`: 查询操作
  - 所有方法通过 `subprocess.run` 调用，60 秒超时
  - 失败时抛出 `SvnError`
  - **验证**: 用真实 SVN 工作副本测试每个方法

- [x] **Task 3.3**: 实现 `src/services/worker_thread.py`
  - `WorkerThread(QThread)`: 接收函数和参数，run() 中执行
  - `finished` 信号 emit 成功结果
  - `error` 信号 emit 错误消息
  - **验证**: 在测试脚本中创建 WorkerThread，验证可异步执行和信号传递

## Phase 4: 核心 UI 组件

- [x] **Task 4.1**: 实现 `src/ui/main_window.py`
  - `QMainWindow` 子类
  - 菜单栏：文件 | SVN操作 | 视图 | 帮助
  - 工具栏：[检出] [更新] [提交] [日志] [还原] [刷新]
  - 状态栏：显示路径/版本号/就绪状态
  - 中央区域：`QSplitter` 左右分栏（预留 RepoBrowser + StatusWidget 占位符）
  - **验证**: 启动后窗口正确显示，菜单和工具栏可交互

- [x] **Task 4.2**: 实现 `src/ui/repo_browser.py`
  - `QWidget`，包含 `QTreeView` + 自定义 `QFileSystemModel`
  - 加载目录树
  - 实现状态图标叠加（v1.0 使用 Unicode 字符作为图标：● ✚ ✖ ⚠ ? ! ☑）
  - 实现右键菜单（更新、提交、比较差异、查看日志、还原、添加、在访达中显示）
  - 双击打开文件（`QDesktopServices.openUrl`）
  - **验证**: 打开工作副本后，树形视图显示文件，状态图标正确

- [x] **Task 4.3**: 实现 `src/ui/status_widget.py`
  - `QWidget`，包含 `QTreeView` + 自定义 Model
  - 列：文件名(带图标)、状态文本、版本号、最后修改者、最后修改时间
  - 支持多选和按列排序
  - 双击打开 DiffViewer
  - 工具栏集成"提交""还原""添加"按钮
  - **验证**: 打开工作副本后，变更文件列表正确显示

- [x] **Task 4.4**: 实现 `src/ui/checkout_dialog.py`
  - `QDialog`，包含 URL 输入、路径选择、版本选择
  - 输入验证（非空检查）
  - 后台线程执行检出
  - 检出成功后回调主窗口打开工作副本
  - **验证**: 输入合法参数后检出成功

## Phase 5: 进阶 UI 组件

- [x] **Task 5.1**: 实现 `src/ui/commit_dialog.py`
  - `QDialog`，包含文件列表（复选框）、提交信息输入框、"提交后更新"选项
  - 文件列表显示状态图标 + 文件名 + 状态描述
  - 默认勾选所有非 unversioned 文件
  - 输入验证（至少选一个文件 + 提交信息非空）
  - 后台线程执行提交
  - **验证**: 提交成功后显示新版本号，状态刷新

- [x] **Task 5.2**: 实现 `src/ui/log_viewer.py`
  - `QDialog`，上半部分 `QTableView`（版本号、作者、日期、信息），下半部分 `QTextEdit`（详情）
  - 详情区显示提交信息全文 + 变更文件列表
  - "加载更多"按钮追加历史记录
  - "差异对比"按钮打开 DiffViewer
  - **验证**: 日志列表正确显示，详情面板联动更新

- [x] **Task 5.3**: 实现 `src/ui/diff_viewer.py`
  - `QDialog`，顶部版本选择器（两个 QComboBox）+ 底部左右分栏
  - 左栏 BASE 版本（只读），右栏 WORKING 版本（只读）
  - 解析 unified diff，绿色背景标记新增行，红色背景标记删除行
  - 版本选项：BASE / WORKING / HEAD / 指定版本号
  - **验证**: 修改文件后打开 DiffViewer，差异正确高亮显示

## Phase 6: 集成与打包

- [x] **Task 6.1**: 串联所有 UI 组件到 MainWindow
  - 统一信号/槽连接，连通所有菜单和工具栏操作
  - 实现"打开工作副本"完整流程（选择目录→验证→加载）
  - 实现工具栏按钮的启用/禁用状态管理
  - **验证**: 启动→打开工作副本→更新→提交→日志→差异 全流程走通

- [x] **Task 6.2**: 编写 `build.py` 打包脚本并验证
  - PyInstaller 配置，入口 `main.py`
  - 处理 `PySide6` 的隐式导入（`--hidden-import`）
  - 打包为独立可执行文件
  - **验证**: 打包后在无 Python 环境运行成功

# Task Dependencies
- Task 2.1~2.3（数据模型）无依赖，可与 Phase 1 并行
- Task 3.1（Svnerror + XmlParser）依赖 Task 2.1~2.3
- Task 3.2（SvnService）依赖 Task 3.1
- Task 3.3（WorkerThread）无依赖，可独立实现
- Task 4.1（MainWindow）依赖 Task 3.3
- Task 4.2~4.4（核心 UI）依赖 Task 3.2 + 3.3 + 4.1
- Task 5.1~5.3（进阶 UI）依赖 Task 3.2 + 4.1
- Task 6.1（集成）依赖 Task 4.1~4.4 + 5.1~5.3
- Task 6.2（打包）依赖 Task 6.1
