---
name: fxiaoke-sse-client
version: 1.0.0
description: 纷享销客 fs-server MCP 的稳健 SSE 直连客户端与查询避坑指南。覆盖「单查询 50 条硬上限 + offset
  翻页」「长 IN 列表静默漏数据 + 小批 IN」「SSE 流静默假死 + 自动重连客户端」。当需要用裸 Python 直连 fs-server
  拉取计提基数表/提成汇总表等大数据量对象时立即加载，避免取到截断数据或整批失败。
---

# 纷享销客 fs-server SSE 直连客户端与查询避坑

> 信息来源：本工作区 2026-08 实测（姜红计提基数表 84/92 条取数、7 月拆差）。fs-server 官方 MCP 通道同期报 `Expected object, received string`（参数双重字符串化 bug），不可用；裸 Python urllib 直连 SSE 是唯一可用通道，但有三大坑。

---

## 一、何时使用本技能

当需要从 fs-server 拉取**大数据量**对象（计提基数表 `commission_base_table__c`、明细 `provision_base_details__c`、提成汇总表 `commission_summary_table__c`、销售订单 `SalesOrderObj` 等），且官方 MCP 工具不可用/返回截断时，用本技能的 `fs_sse.py` 客户端 + 翻页/分批策略。

**三大致命坑（必记）：**

### 坑 1：单查询硬上限 50 条（最致命）
`data_record_query-by-sql` 无论写 `limit=50/100/200`，返回 `records` 永远最多 50 条，且 `data.queryMeta.limitReached=True` 表示还有更多。**任何"总数≤50"的查询结论都不可信。**
✅ 必须 `offset` 翻页，循环到 `len<50 or limitReached=False` 才算取全：
```python
off = 0
while True:
    recs, lr = m.query(f"select ... limit 50 offset {off}")
    if not recs: break
    all.extend(recs)
    if lr is False or len(recs) < 50: break
    off += 50
```

### 坑 2：长 `IN (...)` 列表静默漏数据
一次 `IN (35个_id)` 只返回 50 条明细（实际 105 条），导致主记录明细全漏、汇总被低估 40%。
✅ 单条 `=` 精确查询，或**分小批 IN（每批 ≤5 个值）**：
```python
for i in range(0, len(ids), 5):
    batch = ids[i:i+5]
    q = "select ... where provision_base__c in (%s)" % ",".join("'%s'"%x for x in batch)
```

### 坑 3：SSE 流「静默假死」→ 整批失败
服务端停止往 SSE 流推事件但**不关闭 TCP 连接**，`for raw in resp` 会一直阻塞在下一个 `recv()`。若 GET 超时设 240s，要等 240s 才重连，而查询 90s 先超时→流"活着"却永不重连→后续批次连锁失败（batch 1/12 整批挂、过阵自愈的根因）。
✅ 用本技能的 `fs_sse.py`：GET 超时降到 **30s**（静默假死最多 30s 重连）+ 自动重连 + 重新 handshake + 捕获 POST 内联结果 + `Event` 即时唤醒 + 指数退避。

---

## 二、客户端用法（fs_sse.py）

随本技能附带 `fs_sse.py`（同目录）。导入即用：

```python
import fs_sse
BASE = "https://open.fxiaoke.com/mcp/<租户路径>"
AUTH = "FSUTK_xxx"                       # 你的 token
HOST = "https://open.fxiaoke.com"
m = fs_sse.FsMCP(BASE, AUTH, HOST)        # 自动连接 + handshake，最多等 30s
recs, limitReached = m.query(
    "select _id,name,owner,recovery_amount__c from commission_base_table__c "
    "where owner='1748' limit 50 offset 0")
m.close()
```

### 关键方法
- `m.query(sql, tries=6, timeout=60)` → `(records, limitReached)`，内部含退避重试。
- `m.call(method, params, cid=None, timeout=60)` → 单条 JSON-RPC 调用（如 `tools/call`）。
- `m.close()` → 停止后台 SSE 线程。

### 客户端健壮性清单（已修复）
1. SSE 流断开**自动重连 + 重新 initialize/handshake**。
2. 捕获 POST 200 body 中的内联 JSON-RPC 结果（MCP Streamable HTTP 口径）。
3. `threading.Event` 替代忙轮询，响应到达即刻唤醒。
4. 指数退避 + 抖动，避免失败风暴。
5. 正确解析多行 `data:` 事件边界。
6. 请求串行 + 0.05s 轻微限速，降低服务端丢包。
7. GET 读超时 30s → 静默假死快速检测重连。

---

## 三、典型取数流程（计提基数表 7 月全量示例）

```python
import fs_sse, json
m = fs_sse.FsMCP(BASE, AUTH, HOST)
# 1) 翻页取某销售员 7 月主记录（按归属月 field_6WkL4__c）
JH='1748'; MS,ME=1782835200000,1785513599000   # 2026-07 范围(epoch ms)
main=[]; off=0
while True:
    q=(f"select _id,name,owner,provision_status__c,provision_commission__c,"
       f"recovery_amount__c,order_amount__c,field_6WkL4__c from commission_base_table__c "
       f"where owner='{JH}' and field_6WkL4__c>={MS} and field_6WkL4__c<={ME} limit 50 offset {off}")
    recs,lr=m.query(q)
    if not recs: break
    main.extend(recs)
    if lr is False or len(recs)<50: break
    off+=50
# 2) 逐条 = 精确查明细（避开 IN 批查）
for r in main:
    d,_=m.query(f"select _id,record_type,provision_base__c,recovery_date__c,order_date__c,"
                f"recovery_amount__c,order_amount__c from provision_base_details__c "
                f"where provision_base__c='{r['_id']}' limit 50")
    ...
m.close()
```

> 经验：前端列表视图常按 `provision_status__c` 过滤（如"已计提"子集）；姜红 7 月 `owner='1748'` 真实 92 条 = 84 已计提 + 8 未计提，前端"84"即已计提子集。主记录 Rollup 字段（`recovery_amount__c`/`order_amount__c`）是权威汇总值，做拆分时以它为准。
