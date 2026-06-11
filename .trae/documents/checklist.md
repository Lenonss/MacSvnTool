# MacSvnTool — 验收清单 (Acceptance Checklist)

## Phase 1: 项目骨架与环境搭建

- [ ] CHK-001: `main.py` 可正常启动并显示空 PySide6 窗口
- [ ] CHK-002: `requirements.txt` 包含所有必需依赖（PySide6），`pip install -r requirements.txt` 可正常安装
- [ ] CHK-003: 项目目录结构符合 spec.md 第 2.3 节定义
- [ ] CHK-004: 启动时自动检测 `svn` 命令可用性，不可用时弹窗提示

## Phase 2: SVN 服务层

- [ ] CHK-005: `SvnService.is_available()` 在已安装 svn 的环境返回 `True`，未安装返回 `False`
- [ ] CHK-006: `SvnService.status(path)` 返回正确的 `List[SvnStatus]`，数据字段与 XML 输出一致
- [ ] CHK-007: `SvnService.log(path, limit=10)` 返回 10 条 `SvnLogEntry`，包含 changed_paths
- [ ] CHK-008: `SvnService.info(path)` 返回完整的 `RepoInfo`
- [ ] CHK-009: `SvnService.checkout(url, path)` 成功检出仓库并返回版本号
- [ ] CHK-010: `SvnService.update(path)` 成功更新并返回新版本号
- [ ] CHK-011: `SvnService.commit(paths, message)` 成功提交并返回新版本号
- [ ] CHK-012: `SvnService.diff(path)` 返回 unified diff 文本字符串
- [ ] CHK-013: `SvnService.revert(paths)` 成功还原文件
- [ ] CHK-014: `SvnService.add(paths)` 成功添加文件
- [ ] CHK-015: `SvnService.cleanup(path)` 成功清理工作副本
- [ ] CHK-016: 对非工作副本目录调用 status/log 等方法抛出 `SvnError`
- [ ] CHK-017: 执行超时（60秒）后抛出 `SvnError`
- [ ] CHK-018: `XmlParser.parse_status()` 正确解析 status XML，映射 item 到 `SvnItemStatus`
- [ ] CHK-019: `XmlParser.parse_log()` 正确解析 log XML，含 changed_paths
- [ ] CHK-020: `XmlParser.parse_info()` 正确解析 info XML
- [ ] CHK-021: `WorkerThread` 在后台线程执行，完成后通过 `finished` 信号返回结果
- [ ] CHK-022: `WorkerThread` 异常时通过 `error` 信号发送错误消息

## Phase 3: 数据模型层

- [ ] CHK-023: `SvnStatus` dataclass 字段完整（path, status, revision, last_author, last_date）
- [ ] CHK-024: `SvnLogEntry` dataclass 字段完整（revision, author, date, message, changed_paths）
- [ ] CHK-025: `SvnChangedPath` dataclass 字段完整（path, action, copy_from_path, copy_from_rev）
- [ ] CHK-026: `RepoInfo` dataclass 字段完整（url, root, uuid, revision, last_changed_*）
- [ ] CHK-027: `SvnItemStatus` 枚举覆盖所有状态（modified, added, deleted, conflicted, unversioned, missing, replaced, normal）

## Phase 4: 核心 UI 组件

- [ ] CHK-028: `MainWindow` 包含菜单栏（文件/SVN操作/视图/帮助）
- [ ] CHK-029: `MainWindow` 包含工具栏（检出/更新/提交/日志/还原/刷新）
- [ ] CHK-030: `MainWindow` 包含状态栏（路径/版本号/状态文本）
- [ ] CHK-031: `MainWindow` 窗口默认 1200×800，最小 800×600
- [ ] CHK-032: `MainWindow` 菜单"打开工作副本"触发 `QFileDialog` 选择目录
- [ ] CHK-033: 打开有效工作副本后 `RepoBrowser` 加载文件树
- [ ] CHK-034: `RepoBrowser` 文件/目录前显示 SVN 状态图标（Unicode 字符或图标）
- [ ] CHK-035: `RepoBrowser` 右键菜单显示（更新/提交/差异/日志/还原/添加/在访达中显示）
- [ ] CHK-036: `RepoBrowser` 双击文件在系统默认程序中打开
- [ ] CHK-037: `StatusWidget` 以表格形式展示所有非 normal 状态文件
- [ ] CHK-038: `StatusWidget` 列包含：文件名+图标、状态文本、版本号、修改者、修改时间
- [ ] CHK-039: `StatusWidget` 支持多选文件
- [ ] CHK-040: `StatusWidget` 双击文件行打开 DiffViewer
- [ ] CHK-041: `CheckoutDialog` 包含 URL 输入、路径选择、版本选择（HEAD/指定）
- [ ] CHK-042: `CheckoutDialog` 提交前验证：URL 和路径非空
- [ ] CHK-043: `CheckoutDialog` 检出成功后自动打开工作副本到主窗口

## Phase 5: 进阶 UI 组件

- [ ] CHK-044: `LogViewer` 以表格展示提交日志（版本/作者/日期/信息）
- [ ] CHK-045: `LogViewer` 下半部分显示选中条目详情（完整信息 + 变更文件列表）
- [ ] CHK-046: `LogViewer` 底部"差异对比"按钮打开 DiffViewer
- [ ] CHK-047: `LogViewer` 初始加载 50 条，支持"加载更多"
- [ ] CHK-048: `CommitDialog` 显示变更文件列表，每项带复选框 + 状态
- [ ] CHK-049: `CommitDialog` 提交信息 `QPlainTextEdit`，不可为空
- [ ] CHK-050: `CommitDialog` 提交前验证至少勾选一个文件、信息非空
- [ ] CHK-051: `CommitDialog` 提交成功后弹窗显示新版本号，刷新主窗口状态
- [ ] CHK-052: `DiffViewer` 左右双栏显示旧版/新版内容
- [ ] CHK-053: `DiffViewer` 版本选择器可选择 BASE/WORKING/HEAD/指定版本号
- [ ] CHK-054: `DiffViewer` 新增行绿色背景，删除行红色背景

## Phase 6: 集成与打包

- [ ] CHK-055: 工具栏按钮与菜单项联动，点击触发对应功能
- [ ] CHK-056: 在文件浏览器选中文件后，工具栏/菜单操作作用于选中文件
- [ ] CHK-057: 未打开工作副本时，SVN 操作菜单项/按钮置灰（不可用）
- [ ] CHK-058: 所有耗时操作通过 `WorkerThread` 在后台执行，不阻塞 UI
- [ ] CHK-059: 操作进行中状态栏显示进度信息
- [ ] CHK-060: `build.py` PyInstaller 打包脚本可正常执行
- [ ] CHK-061: 打包后 .exe 在无 Python 环境的 Windows 机器上可运行
- [ ] CHK-062: 打包后 .app 在 Mac 上可运行（`open MacSvnTool.app`）

## 边界场景

- [ ] CHK-063: 空工作副本（无修改文件）打开时，StatusWidget 显示空列表（非崩溃）
- [ ] CHK-064: 超大日志（100+ 条）正常分页加载，不卡顿
- [ ] CHK-065: 打开非 SVN 目录时给出友好提示而非崩溃
- [ ] CHK-066: 二进制文件 Diff 时给出提示"无法显示二进制文件差异"
- [ ] CHK-067: 网络断开时 SVN 操作给出友好提示
