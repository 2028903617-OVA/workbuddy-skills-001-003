# 01 环境与执行基线

## 1.1 本机画像（001 · Windows · 弱机）

| 项 | 值 |
|---|---|
| 内存/CPU | 16GB / 奔腾 G6405 / 无独显 |
| 禁忌 | **禁跑本地大模型、禁大图 OCR**（OCR 优先直接读图） |
| Python（唯一） | `C:/Users/Administrator/.workbuddy/binaries/python/envs/default/Scripts/python.exe` |
| Node | `C:/Users/Administrator/.workbuddy/binaries/node/versions/22.12.0/node.exe` |
| 协同 | 003 为强机，双机带记忆与 skill 同步 |

## 1.2 Bash shim 缺失命令（A01）

**现象**：`rm` `dirname` `cd` `head` `tail` `grep` `ls` 报 `command not found` 或 Exit 127。

**根因**：WorkBuddy 的 bash 是 shim，部分命令未实现。

**正确做法**：文件删除、目录切换、文本检索、取头部——**一律走 Python**。不要重试同一条 bash 命令。

```python
# 代替 ls / find
import os; print(os.listdir(r'D:\path'))
# 代替 rm
os.remove(p)            # 文件
shutil.rmtree(p)        # 目录（仅限项目内，禁用于个人目录）
# 代替 head
print(open(p, encoding='utf-8').read()[:2000])
```

⚠️ 个人目录（Desktop/Downloads/Documents）**禁止递归删除**，扫描一律只读。

## 1.3 ★ 反引号被命令替换吞掉（A02 · 最隐蔽）

**现象**：往文件里写 `` `SomeApiName` ``、`` `某台账.xlsx` `` 这类带反引号的内容，写进去后**反引号及其内容全部消失**，文件还被截断。

**根因**：bash 对双引号内的反引号做**命令替换**，把内容当命令执行（找不到就输出空）。

**正确做法**：
1. 写含反引号/`$`/`!` 的内容 → **用 Write / Edit 工具，或 Python 脚本**，不要在 `bash -c "python -c '...'"` 里内联。
2. Python 脚本本身用 `'''...'''` 三引号，并确保脚本文件由 Write 工具落盘。

**举一反三**：凡是"内容里含 shell 元字符"，都不走 shell 通道。

## 1.4 Read 长行截断（A03）

Read 工具单行超 2000 字符会截断 → 长行先切分再读。

## 1.5 Glob 不认 D 盘（A04）

用 Python `os.listdir` 列目录，结果写临时文件再 Read。

## 1.6 Windows 权限类（A06 · 静默失败最危险）

### 非管理员静默失败
写 `C:\Program Files\`、改 `HKLM\SOFTWARE\`、改 hosts **不生效但不报错**（UAC 默默拦截，不像 Linux 直接 PermissionError）。

✅ 脚本开头自检：
```powershell
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) { Write-Error "需要管理员权限"; exit 1 }
```
**绝不静默继续。**

### ExecutionPolicy（A07）
跑 `.ps1` 报"禁止运行脚本"。用 `Set-ExecutionPolicy -Scope Process Bypass`（仅当前进程），**不要全局 Unrestricted**。

### 改完 PATH 不生效（A08）
环境变量是进程启动时**一次性读入**的缓存。新开终端，或重拼：
```powershell
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
```
程序要生效必须**重启该程序**。

### TrustedInstaller 层
管理员改 system32 下 hosts 仍"拒绝访问" → 该文件归 `NT SERVICE\TrustedInstaller`。
```cmd
takeown /f C:\Windows\System32\drivers\etc\hosts
icacls C:\Windows\System32\drivers\etc\hosts /grant administrators:F
```
**不要用 `echo >` 重定向写 hosts**（编码易乱），用记事本/VSCode。

### 改完必须读回
写盘成功 ≠ 生效。用 `reg query` / `Get-Service` / `powercfg -q` / 重读文件**对比预期**。

## 1.7 计划任务不触发（排查四因）

1. 触发器条件（电源/网络/空闲）不满足
2. 勾了"仅在用户登录时运行"但机器锁屏
3. 没勾"使用最高权限运行"
4. 触发器账户 ≠ 运行账户

✅ 用 `schtasks /Query /FO LIST /V` 查真实配置（比 GUI 准）。
结果码：`0x0` 成功 / `0x1` 失败 / `0x41301` 仍在运行 / `0x800710E0` 被拒。

**排程要落在开机窗口内**：先查 `powercfg -query SCHEME_CURRENT SUB_SLEEP`，排程留 **30 分钟余量**，优先"开机后 N 分钟"而非固定时刻。

## 1.8 服务账户选择（最小特权）

| 账户 | 用途 |
|---|---|
| `NT AUTHORITY\LocalService` | **默认**，最小权限、匿名 |
| `NT AUTHORITY\NetworkService` | 需网络出站身份 |
| `LocalSystem` | 机器级高权，最后手段 |

```cmd
sc config <name> obj= "NT AUTHORITY\LocalService" password= ""
sc qc <name>
```
注意 `obj=` 后**有空格**。

## 1.9 其他（A09 / A10）

- **Git Bash 的 tar 解不了 zip** → Python `zipfile`
- **`pip install -U pip` 被自我保护拒绝** → `python -m pip install ...`
- **HF_ENDPOINT 镜像**与 `huggingface_hub` snapshot 校验不兼容 → 直连官方
- **git `-C /c/...` 报 No such file** → 先 `cd` 进目录再执行
- **`&&` 链静默失败**（如 commit 未提交）→ 分开执行并检查返回码
- **Groovy**：用 `java -jar groovy.jar 脚本`（manifest Class-Path 引同级 jar），勿用 `-cp ... GroovyMain`；块注释内不能出现字面量 `*/`
