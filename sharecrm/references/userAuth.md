---
name: sharecrm-auth
version: 2.0.0
description: "sharecrm 认证与会话管理：配置初始化、OAuth 设备码登录（auth login）、授权状态查看（auth status）、本地授权清理（auth logout）、Token 自动刷新、认证错误处理、安全规则。当用户需要配置 sharecrm、登录授权、遇到认证/权限错误时触发。"
---

# sharecrm 认证与会话管理

本技能指导你如何通过 sharecrm 完成认证、管理会话，以及处理各类认证相关问题。

## 配置初始化

首次使用需运行 `sharecrm auth login` 发起 OAuth 设备码登录。CLI 会输出授权链接和用户码，将链接发给用户，用户打开链接完成授权后，CLI 自动保存会话并输出登录结果。

如果是在执行其他 `sharecrm` 远程命令时遇到“未登录 / 登录失效 / 设备码过期 / 授权被拒绝”等认证中断，**必须先保存被中断的原始命令**，然后自动执行 `sharecrm auth login`。只有在授权成功后，才继续执行后续操作，并**自动重试原命令**；不要要求用户再次重复原始任务。

```bash
# 发起登录（阻塞直到用户授权完成或超时）
sharecrm auth login
```

登录成功后 CLI 输出：

```json
{
  "success": true,
  "userId": "...",
  "appId": "...",
  "scope": ["..."]
}
```

## 认证方式

当前仅支持 **OAuth 设备码（Device Flow）** 登录，用户身份认证。

### 登录流程

1. CLI 请求设备码 → 输出授权链接和用户码
2. 用户在浏览器中打开链接，输入用户码完成授权
3. CLI 轮询授权状态，成功后保存会话到本地

### 设备码状态码

| 错误码 | 含义 | 处理方式 |
|---|---|---|
| `40001` | `authorization_pending` — 用户尚未完成授权 | 继续轮询 |
| `40002` | `slow_down` — 轮询过快 | 自动增大轮询间隔 |
| `40003` | 设备码已过期 | 重新执行 `sharecrm auth login` |
| `40004` | 用户拒绝授权 | 重新执行 `sharecrm auth login` |

## 认证命令

### auth login

```bash
sharecrm auth login
```

- 发起 OAuth 设备码登录，无参数/选项
- 阻塞直到用户完成授权或设备码过期
- 授权链接中包含 `apiUrl` 时会自动写入本地会话

### auth status

```bash
sharecrm auth status
```

输出当前会话状态 JSON：

```json
{
  "appId": "...",
  "expiresAt": "2026-04-20T12:00:00.000Z",
  "grantedAt": "2026-04-20T10:00:00.000Z",
  "identity": "user",
  "scope": "calendar:calendar:readonly crm:customer:readonly",
  "tokenStatus": "normal",
  "userName": "...",
  "userId": "...",
  "cliVersion": "0.1.5"
}
```

- `tokenStatus`: `normal` 表示 Token 有效，`needs_refresh` 表示已过期或即将过期
- `scope`: 以空格分隔的已授权权限列表，无则为空字符串

### auth logout

```bash
sharecrm auth logout
```

- 删除本地 `session.json` 文件
- 输出: `Logged out locally.`

## 认证中断自动恢复（MUST）

当任意 `sharecrm` 远程命令因为认证问题失败时，必须严格按下面流程处理：

1. 记录被中断的原始命令（包含子命令、参数、JSON 数据）
2. 自动执行 `sharecrm auth login`
3. 将授权链接和用户码展示给用户，并等待命令返回成功结果
4. 登录成功后，自动重新执行刚才被中断的原始命令，无需用户再次发起请求
5. 如果登录失败、超时、设备码过期或用户拒绝授权，则告知用户失败原因，并停止重试

执行要求：

- 在 `sharecrm auth login` 完成前，不要继续执行任何依赖认证的远程命令
- 恢复执行时，必须复用原始命令和原始参数，不能擅自改写用户意图
- 只有登录成功后才能恢复原任务；如果登录未成功，不要假装任务已继续
- 不要把“请重新执行原命令”交给用户，应该由 agent 自动续跑

## Token 自动刷新

CLI 在执行远程命令时自动处理 Token 过期：

1. 发送请求，服务端返回 `AUTH_FAIL`
2. 如果本地有 `refreshToken` 和 `appId`，自动调用 Token 刷新接口
3. 刷新成功后保存新会话，并**重试一次**原请求
4. 刷新失败（无 refreshToken / appId、刷新接口报错、返回相同 accessToken）→ 进入“认证中断自动恢复”流程，自动执行 `sharecrm auth login`

```text
提示：---------------------
登录状态已失效，请重新登录授权。
执行命令：sharecrm auth login
```

> Token 过期前 60 秒也会触发预刷新（`shouldRefresh` 逻辑）。
> 如果自动刷新最终仍失败，agent 必须等待重新授权成功后，再继续被中断的原任务。

## 权限不足处理

远程命令返回权限错误时，响应中包含：

| 字段 | 说明 |
|---|---|
| `permission_violations` | 缺失的权限 scope 列表 |
| `console_url` | 纷享 CRM 开发者后台的权限配置链接 |
| `hint` | 建议的修复命令 |

**处理方式**：将 `console_url` 提供给用户，引导去后台开通对应的 scope。

## 认证错误处理

### 未登录执行远程命令

```
You must login before executing remote commands.
sharecrm auth login
```

处理：进入“认证中断自动恢复”流程，自动执行 `sharecrm auth login`，等待授权成功后自动重试原命令。

### 登录状态已失效

```
提示：---------------------
登录状态已失效，请重新登录授权。
执行命令：sharecrm auth login
```

处理：进入“认证中断自动恢复”流程，自动执行 `sharecrm auth login`，等待授权成功后自动重试原命令。

### 设备码过期

```
Device code expired. Please run auth login again.
```

处理：当前登录流程已失效。重新执行 `sharecrm auth login`，并继续等待新的授权结果；登录成功后自动恢复原命令。

### 授权被拒绝

```
Authorization was denied. Please try again after granting access.
```

处理：用户在授权页面拒绝了授权。若用户决定继续，则重新执行 `sharecrm auth login` 并等待授权成功；成功后自动恢复原命令，否则停止任务并告知用户。

### 缺少认证环境变量

```
FS_CLI_AUTH_BASE_URL is required for auth API requests.
```

处理：配置 `FS_CLI_AUTH_BASE_URL` 环境变量。

## 安全规则

- **禁止输出密钥**（accessToken、refreshToken）到终端明文
- **写入/删除操作前必须确认用户意图**
- 本地会话文件 (`session.json`) 存储在 `~/.sharecrm/`，注意目录权限
