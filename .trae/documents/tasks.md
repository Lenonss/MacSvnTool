# MacSvnTool — 实施任务清单

## Phase 1: 项目骨架与环境搭建

### T1.1 创建项目目录结构
- 创建 `MacSvnTool/src/`、`MacSvnTool/src/models/`、`MacSvnTool/src/services/`、`MacSvnTool/src/ui/`、`MacSvnTool/resources/icons/`
- 创建各目录下的 `__init__.py`
- **产出:** 完整目录结构，所有 `__init__.py` 存在
- **对应验收:** CHK-003

### T1.2 编写 requirements.txt
- 添加 `PySide6>=6.5`
- 添加打包相关（`pyinstaller>=5.0`）
- **产出:** `requirements.txt`
- **对应验收:** CHK-002

### T1.3 编写 main.py 入口
- 创建 `QApplication` 实例
- 启动时调用 `SvnService.is_available()` 检测 svn
- 未检测到 svn 时弹 `QMessageBox.warning` 提示
- 实例化 `MainWindow` 并显示
- **产出:** `main.py` 可启动空窗口
- **对应验收:** CHK-001, CHK-004

---

## Phase 2: SVN 服务层

### T2.1 实现 SvnService 基础框架
- 文件: `src/services/svn_service.py`
- 创建 `SvnService` 类（所有方法为 `@staticmethod`）
- 创建 `SvnError` 异常类
- 实现 `_run_command(cmd_args, timeout=60)` 私有方法，封装 `subprocess.run`
- 实现 `is_available()` — 尝试运行 `svn --version`
- **产出:** `svn_service.py` + `SvnError`
- **对应验收:** CHK-005

### T2.2 实现 SvnService.status() 和 info()
- `status(path)` → `svn status --xml [path]` → 返回 XML 字符串
- `info(path)` → `svn info --xml [path]` → 返回 XML 字符串
- XML 字符串交由 `XmlParser` 解析
- **产出:** `status()` 和 `info()` 方法
- **对应验收:** CHK-006, CHK-008

### T2.3 实现 SvnService.log() 和 diff()
- `log(path, limit=50)` → `svn log --xml -l N -v [path]`
- `diff(path, revision)` → `svn diff -r REV [path]`，返回原始文本
- **产出:** `log()` 和 `diff()` 方法
- **对应验收:** CHK-007, CHK-012

### T2.4 实现 SvnService 修改操作
- `checkout(url, path)` → `svn checkout URL PATH`
- `update(path, revision)` → `svn update -r REV PATH`
- `commit(paths, message)` → `svn commit -m MSG PATHS...`
- `revert(paths)` → `svn revert PATHS...`
- `add(paths)` → `svn add PATHS...`
- `cleanup(path)` → `svn cleanup PATH`
- 所有方法包含异常处理和超时机制
- **产出:** 全部修改操作方法
- **对应验收:** CHK-009 ~ CHK-017

### T2.5 实现 XmlParser
- 文件: `src/services/xml_parser.py`
- `parse_status(xml_string)` → `List[SvnStatus]`
- `parse_log(xml_string)` → `List[SvnLogEntry]`
- `parse_info(xml_string)` → `RepoInfo`
- 使用 `xml.etree.ElementTree`
- 实现 `_parse_svn_date()` 将 ISO 8601 日期格式化为可读格式
- **产出:** `xml_parser.py`
- **对应验收:** CHK-018 ~ CHK-020

### T2.6 实现 WorkerThread
- 文件: `src/services/worker_thread.py`
- 继承 `QThread`，接受可调用对象 `fn` + `*args` + `**kwargs`
- 定义 `finished = Signal(object)` 和 `error = Signal(str)`
- `run()` 中调用 `fn(*args, **kwargs)`，try/except 处理异常
- **产出:** `worker_thread.py`
- **对应验收:** CHK-021, CHK-022

---

## Phase 3: 数据模型层

### T3.1 实现 SvnStatus 模型
- 文件: `src/models/svn_status.py`
- 定义 `SvnItemStatus` 枚举
- 定义 `SvnStatus` dataclass
- **产出:** `svn_status.py`
- **对应验收:** CHK-023, CHK-027

### T3.2 实现 SvnLogEntry 模型
- 文件: `src/models/svn_log.py`
- 定义 `SvnChangedPath` dataclass
- 定义 `SvnLogEntry` dataclass
- **产出:** `svn_log.py`
- **对应验收:** CHK-024, CHK-025

### T3.3 实现 RepoInfo 模型
- 文件: `src/models/repo_info.py`
- 定义 `RepoInfo` dataclass
- **产出:** `repo_info.py`
- **对应验收:** CHK-026

---

## Phase 4: 核心 UI 组件

### T4.1 实现 MainWindow 框架
- 文件: `src/ui/main_window.py`
- 继承 `QMainWindow`
- 创建菜单栏（文件/SVN操作/视图/帮助），含快捷键
- 创建工具栏（检出/更新/提交/日志/还原/刷新）
- 创建状态栏（显示路径/版本号/状态）
- 中央区域使用 `QSplitter` 水平分割（左侧 RepoBrowser / 右侧 StatusWidget）
- 窗口标题 `MacSvnTool`
- 默认大小 1200×800，最小 800×600
- **产出:** `main_window.py`
- **对应验收:** CHK-028 ~ CHK-031

### T4.2 实现"打开工作副本"功能
- "文件 → 打开工作副本" 或工具栏按钮触发
- `QFileDialog.getExistingDirectory()` 选择目录
- 在 WorkerThread 中调用 `SvnService.info()` 验证是否为工作副本
- 验证通过后加载数据（status + info）
- **产出:** 打开工作副本完整流程
- **对应验收:** CHK-032, CHK-033, CHK-065

### T4.3 实现 RepoBrowser
- 文件: `src/ui/repo_browser.py`
- 继承 `QWidget`，包含 `QTreeView` + `QFileSystemModel`
- 自定义 Model 在 `data(Qt.DecorationRole)` 中返回状态图标
- 实现 `load_working_copy(path, status_list)` 方法
- 实现右键菜单（`contextMenuEvent`）
- 实现双击打开功能
- 状态图标 v1.0 使用 `QColor` 绘制 Unicode 字符
- **产出:** `repo_browser.py`
- **对应验收:** CHK-034 ~ CHK-036

### T4.4 实现 StatusWidget
- 文件: `src/ui/status_widget.py`
- 继承 `QWidget`，包含 `QTreeView` + 自定义 `QStandardItemModel`
- 列：文件名（带图标）、状态文本、版本号、修改者、修改时间
- 实现 `load_status(status_list)` 方法
- 支持多选（`SelectionMode.ExtendedSelection`）
- 支持排序（`setSortingEnabled(True)`）
- 双击行信号触发 DiffViewer
- **产出:** `status_widget.py`
- **对应验收:** CHK-037 ~ CHK-040

### T4.5 实现 CheckoutDialog
- 文件: `src/ui/checkout_dialog.py`
- 继承 `QDialog`
- URL 输入 + 路径选择 + 版本选择
- 实现表单验证
- 检出操作在 WorkerThread 中执行
- 检出成功后通过信号通知主窗口打开工作副本
- **产出:** `checkout_dialog.py`
- **对应验收:** CHK-041 ~ CHK-043

---

## Phase 5: 进阶 UI 组件

### T5.1 实现 LogViewer
- 文件: `src/ui/log_viewer.py`
- 继承 `QDialog`
- 上半部分 `QTableView`，列：版本号/作者/日期/信息
- 下半部分 `QTextEdit`（只读）显示详情
- 实现分页加载（初始 50 条，"加载更多"按钮）
- "差异对比"按钮 → 打开 DiffViewer
- 日志数据在 WorkerThread 中加载
- **产出:** `log_viewer.py`
- **对应验收:** CHK-044 ~ CHK-047

### T5.2 实现 CommitDialog
- 文件: `src/ui/commit_dialog.py`
- 继承 `QDialog`
- `QListWidget` 显示变更文件（复选框 + 状态图标 + 文件名 + 状态文本）
- `QPlainTextEdit` 输入提交信息
- `QCheckBox` "提交后更新到最新"
- 表单验证：至少勾选一个文件、信息非空
- 提交在 WorkerThread 中执行
- 成功后 `QMessageBox.information` 显示版本号
- **产出:** `commit_dialog.py`
- **对应验收:** CHK-048 ~ CHK-051

### T5.3 实现 DiffViewer
- 文件: `src/ui/diff_viewer.py`
- 继承 `QDialog`
- 版本选择器：两个 `QComboBox`（BASE/WORKING/HEAD/自定义）
- `QSplitter` 左右分栏 + 两个 `QPlainTextEdit`（只读）
- 实现 `_apply_diff_highlight()` 方法解析 unified diff 并着色
  - `+` 开头行 → 绿色背景
  - `-` 开头行 → 红色背景
- diff 数据在 WorkerThread 中加载
- **产出:** `diff_viewer.py`
- **对应验收:** CHK-052 ~ CHK-054

---

## Phase 6: 集成与打包

### T6.1 串联 UI 组件到 MainWindow
- 工具栏按钮连接对应操作
  - 检出 → `CheckoutDialog`
  - 更新 → `SvnService.update()` in WorkerThread
  - 提交 → `CommitDialog`
  - 日志 → `LogViewer`
  - 还原 → `SvnService.revert()` + 确认对话框
  - 刷新 → 重新加载 status
- 菜单项连接对应操作（同工具栏 + 快捷键）
- 未打开工作副本时禁用 SVN 操作按钮/菜单
- **产出:** 完整的 MainWindow 交互
- **对应验收:** CHK-055 ~ CHK-057

### T6.2 实现操作状态反馈
- 所有 WorkerThread 开始前状态栏显示"正在执行..."
- WorkerThread