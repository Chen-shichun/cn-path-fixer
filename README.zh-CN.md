# cn-path-fixer

> 诊断并修复 Windows 用户名含中文（非 ASCII 字符）导致的开发工具异常。

[English](README.md) | 简体中文

## 简介

在 Windows 上，如果账户名包含非 ASCII 字符（例如 `C:\Users\张三\`），一大堆开发工具会默认把数据目录放在这个路径下：npm 的全局包和缓存、conda 的虚拟环境与包缓存，以及 cmake、MSVC、node-gyp 等原生构建工具链，也常常从这个路径下被调用。

有些工具能正常处理，有些不能。这类故障特别迷惑人，因为报错几乎不会直接告诉你"你的用户名是中文"——你看到的往往是 `path contains non-ASCII characters`、安装前缀变乱码、虚拟环境创建失败，或者构建在第三方脚本深处因编码问题崩掉。

**cn-path-fixer** 是一个零依赖的小工具，只做三件事：

1. **诊断** —— 读取 npm、conda、git 以及当前构建目录的配置，逐一报告哪些路径含有非 ASCII 字符。
2. **修复** —— 把有问题的目录迁移到纯英文路径（默认 `C:\tools`），并提供 DryRun 预览模式，改之前先看清每一处变动。
3. **校验** —— 改完后回读工具的实际配置，确认真的生效才报成功，而不是想当然。

设计上保持克制：默认只读、先预览、拒绝不安全输入、完全可回滚。

## 效果对比

**修复前**，诊断会标出问题路径：

```
===== CN-PATH DIAGNOSTIC REPORT =====

USERPROFILE : C:\Users\张三  [NON-ASCII!]

--- npm ---
prefix : C:\Users\张三\AppData\Roaming\npm  [NON-ASCII!]
cache  : C:\Users\张三\AppData\Local\npm-cache  [NON-ASCII!]
```

**修复后**，同一个诊断：

```
--- npm ---
prefix : C:\tools\npm  [ascii ok]
cache  : C:\tools\npm-cache  [ascii ok]
```

## 环境要求

- Windows（本工具解决的问题是 Windows 特有的）
- Python 3.8 或更高版本 —— **仅用标准库**，无需安装任何第三方包
- `npm` 和/或 `conda` 在 PATH 中（可选；未安装的工具会自动跳过）

## 安装

把整个 skill 文件夹放到 WorkBuddy 用户级 skills 目录：

```
~/.workbuddy/skills/cn-path-fixer/
```

无需编译，无需安装依赖。

## 使用

### 第 1 步 — 诊断（只读，随时可跑）

```bash
python scripts/diagnose.py
```

不会修改任何东西。它按工具逐个打印相关路径是否含非 ASCII 字符。

### 第 2 步 — 预览改动（DryRun）

```bash
python scripts/fix.py -Tool npm -Base C:\tools -DryRun
```

输出：

```
===== CN-PATH FIX (Base: C:\tools, Tool: npm, DryRun: True) =====
[DRYRUN] create dir: C:\tools\npm
[DRYRUN] create dir: C:\tools\npm-cache
[DRYRUN] npm config set prefix C:\tools\npm
[DRYRUN] npm config set cache C:\tools\npm-cache
===== DONE =====
```

### 第 3 步 — 执行

```bash
python scripts/fix.py -Tool npm -Base C:\tools
```

脚本会写入配置，然后回读一次，只有工具确实返回新路径才打印 `[verified]`：

```
npm prefix -> C:\tools\npm  [verified]
npm cache  -> C:\tools\npm-cache  [verified]
```

如需同时把新的全局命令目录加入用户 PATH：

```bash
python scripts/fix.py -Tool npm -Base C:\tools -AddToPath
```

### 第 4 步 — 验证

```bash
python scripts/diagnose.py
npm config get prefix
npm root -g
```

PATH 改动需要**新开一个终端**才生效。

## 参数

| 参数 | 取值 | 默认值 | 说明 |
|---|---|---|---|
| `-Tool` | `npm`、`conda`、`all` | `all` | 修复哪个工具；未安装的工具自动跳过。 |
| `-Base` | 任意纯英文路径 | `C:\tools` | 迁移目标根目录；含非 ASCII 字符会被拒绝并报错退出。 |
| `-DryRun` | 开关 | 关 | 只打印将要执行的动作，不做任何修改。 |
| `-AddToPath` | 开关 | 关 | 把 `<BASE>\npm` 追加到用户 PATH，使全局安装的命令行工具可直接调用。 |

## 实际做了哪些改动

没有任何隐藏操作。所有写操作仅限于以下几条：

**npm**（写入你的 `~/.npmrc`）

```bash
npm config set prefix "<BASE>\npm"
npm config set cache  "<BASE>\npm-cache"
```

**conda**（写入你的 `~/.condarc`）

```bash
conda config --add envs_dirs "<BASE>\conda-envs"
conda config --add pkgs_dirs "<BASE>\conda-pkgs"
```

**PATH**（仅在使用 `-AddToPath` 时）

把 `<BASE>\npm` 追加到注册表中当前用户的 `Path`。比较时使用归一化后的路径，因此重复执行不会产生重复条目。

它**不会**卸载任何东西，不会改动 Node.js 或 Python 本体，也不会删除你的旧目录。已安装的包保持原位，只有**以后**的全局安装会落到新位置。

## 安全性

- **先预览。** `-DryRun` 会在写入前打印每一条命令。
- **拒绝不安全输入。** 非 ASCII 的 `-Base` 会被立即拒绝并以非 0 退出码退出。
- **校验而非假设。** 每处配置写入后都会回读确认；失败如实打印 `ERROR`，绝不会静默报成功。
- **幂等。** 重复执行安全，PATH 条目会去重。
- **完全可回滚。**

### 如何回滚

`~/.npmrc` 就是一个纯文本文件。可以直接编辑，也可以执行：

```bash
npm config set prefix "<你原来的 prefix>"
npm config set cache  "<你原来的 cache>"
```

conda 则删掉 `~/.condarc` 中新增的那两行即可。

## 目录结构

```
cn-path-fixer/
├── README.md                       # 英文说明
├── README.zh-CN.md                 # 本文件（中文说明）
├── SKILL.md                        # Skill 清单（frontmatter + 工作流）
├── LICENSE                         # MIT
├── .gitignore
├── scripts/
│   ├── diagnose.py                 # 只读诊断
│   └── fix.py                      # 带 DryRun 的参数化修复
└── references/
    └── troubleshooting.md          # 各工具典型报错与成因对照
```

## 注意事项（踩过的坑）

- **`npm config set` 是本地写文件。** 它不走网络。看到 `EPERM` 那是权限或沙箱问题，不是网络问题。
- **中文路径请优先用 Bash + Python 调用，别用 PowerShell。** 在某些环境下，含中文的路径参数经 PowerShell 传递时会在进程启动层被编码破坏。用 Bash 配合托管 Python 解释器调用脚本可完全规避。
- **Windows 工具的输出常是 GBK 编码。** 脚本以字节捕获子进程输出，并按 `utf-8 → gbk → latin-1` 兜底解码，因此含中文的路径能被正确读出，不会抛 `UnicodeDecodeError`。
- **`USERPROFILE` 本身改不了** —— 它由 Windows 账户名决定。本工具的思路是把工具的数据目录迁走，这才是真正起作用的部分。
- **源码和构建目录仍建议放在纯英文路径**（如 `C:\dev`）。诊断会把非 ASCII 的当前工作目录标记为构建风险。

## 许可证

MIT —— 详见 [LICENSE](LICENSE)。
