# MacSvnTool v1.0 — Checklist

## 项目骨架
- [x] 目录结构完整：`main.py`、`requirements.txt`、`build.py`、`src/models/`、`src/services/`、`src/ui/`、`resources/icons/`
- [x] `requirements.txt` 包含 `PySide6>=6.5` 和 `pyinstaller>=5.0`
- [x] `python main.py` 可启动并显示空窗口
- [x] 启动时检测 svn 命令，未安装时弹窗提示

## 数据模型
- [x] `SvnItemStatus` 枚举定义完整（8 种状态）
- [x] `SvnStatus` dataclass 字段：path, status, revision, last_author, last_date
- [x] `SvnLogEntry` dataclass 字段：revision, author, date, message, changed_paths
- [x] `SvnChangedPath` dataclass 字段：path, action, copy_from_path, copy_from_rev
- [x] `RepoInfo` dataclass 字段：url, root, uuid, revision, last_changed_rev, last_changed_date, last_changed_author

## SVN 服务层
- [x] `SvnError` 异常类包含 message, command, stderr
- [x] `XmlParser.parse_status()` 正确解析 `svn status --xml` 输出
- [x] `XmlParser.parse_log()` 正确解析 `svn log --xml` 输出，包含 changed_paths
- [x] `XmlParser.parse_info()` 正确解析 `svn info --xml` 输出
- [x] `SvnService.is_available()` 正确检测 svn 命令
- [x] `SvnService.checkout()` 正确执行检出
- [x] `SvnService.update()` 正确执行更新
- [x] `SvnService.commit()` 正确执行提交
- [x] `SvnService.status()` 正确返回状态列表
- [x] `SvnService.log()` 正确返回日志列表
- [x] `SvnService.diff()` 正确返回差异文本
- [x] `SvnService.info()` 正确返回仓库信息
- [x] `SvnService.revert()` 正确执行还原
- [x] `SvnService.add()` 正确执行添加
- [x] `SvnService.cleanup()` 正确执行清理
- [x] 60 秒超时机制生效
- [x] 操作失败时抛出 `SvnError`

## 后台线程
- [x] `WorkerThread(QThread)` 接受函数和参数
- [x] `finished` 信号正确 emit 成功结果
- [x] `error` 信号正确 emit 错误消息
- [x] 长时间操作不阻塞 UI

## 主窗口
- [x] 菜单栏包含"文件""SVN操作""视图""帮助"
- [x] 工具栏包含 [检出] [更新] [提交] [日志] [还原] [刷新]
- [x] 状态栏显示路径、版本号、状态
- [x] 左右分栏布局（QSplitter）
- [x] 空状态显示提示文字
- [x] 菜单项和工具栏按钮功能正确映射

## RepoBrowser
- [x] 树形结构展示工作副本文件/目录
- [x] 状态图标区分 modified/added/deleted/conflicted/unversioned/missing/normal
- [x] 右键菜单包含全部选项（更新、提交、比较差异、查看日志、还原、添加、在访达中显示）
- [x] 双击文件在系统默认编辑器中打开

## StatusWidget
- [x] 非 normal 状态的文件正确显示
- [x] 列：文件名(图标)、状态文本、版本号、最后修改者、最后修改时间
- [x] 支持多选
- [x] 支持按列排序
- [x] 双击文件行打开 DiffViewer

## CheckoutDialog
- [x] URL 输入框和路径选择器
- [x] 版本选择（HEAD / 指定版本号）
- [x] URL 为空时阻止操作
- [x] 目标路径为空时阻止操作
- [x] 检出成功自动打开工作副本

## CommitDialog
- [x] 文件列表带复选框和状态图标
- [x] 默认勾选非 unversioned 文件
- [x] 提交信息输入框
- [x] "提交后更新"复选框
- [x] 提交信息为空时阻止操作
- [x] 未勾选任何文件时阻止操作
- [x] 提交成功后显示版本号并刷新

## LogViewer
- [x] 表格显示版本号、作者、日期、提交信息
- [x] 详情面板显示完整信息和变更文件列表
- [x] "加载更多"按钮功能正确
- [x] "差异对比"按钮功能正确

## DiffViewer
- [x] 左右分栏对比 BASE 和 WORKING 版本
- [x] 新增行绿色背景
- [x] 删除行红色背景
- [x] 版本选择器（BASE / WORKING / HEAD / 指定版本号）

## 集成
- [x] 打开工作副本完整流程（选择→验证→加载）走通
- [x] 工具栏按钮状态随工作副本打开/关闭正确切换
- [x] 提交后自动刷新状态
- [x] 检出后自动打开工作副本

## 打包
- [x] PyInstaller 打包成功
- [x] 打包产物可在无 Python 环境运行
