---
name: "sfa-leads-convert"
description: "当用户表达将线索转换为客户、联系人或商机，或要求\\\"转化线索\\\"、\\\"线索转客户/联系人/商机\\\"时触发。"
apiName: "sfa_leads_convert"
---
# sfa-leads-convert

## Trigger

适合这些表达：

- 转化这条线索
- 把这个线索转成客户
- 线索转商机
- 线索转联系人
- 转换线索
- 线索转客户并转联系人
- 帮我转换线索

不适合这些表达：

- 查询线索详情
- 修改线索负责人
- 分配线索

## CLI 接口规范

### 通用查询 CLI
- 查询线索对象字段：`sharecrm data describe get -d '{"object_api_name":"LeadsObj","simple_describe":true}'`
- 按名称查询候选线索：`sharecrm data record query-by-fields -d '{"object_api_name":"LeadsObj","select_fields":["_id","name","company","mobile","biz_status","lock_status","record_type"],"search_template_query":{"limit":20,"filters":[{"field_name":"name","operator":"LIKE","field_values":["<线索名称>"]}],"orders":[{"fieldName":"last_modified_time","isAsc":false}]}}'`
- 按 ID 查询线索详情：`sharecrm data record get-by-id -d '{"object_api_name":"LeadsObj","id":"<leads_id>"}'`
- 查询目标对象描述时，按对象分别调用：`sharecrm data describe get -d '{"object_api_name":"AccountObj","simple_describe":true}'`、`sharecrm data describe get -d '{"object_api_name":"ContactObj","simple_describe":true}'`、`sharecrm data describe get -d '{"object_api_name":"NewOpportunityObj","simple_describe":true}'`

### 主业务动作 CLI
- 线索转换涉及这些业务动作：`leads-transfer-config-get`、`leads-transfer-privilege-batch-check`、`action_leads_bulkFindValidRecordTypeList`、`leads-transfer-account-get`、`leads-transfer-contact-get`、`leads-transfer-newopportunity-get`、`leads-transfer-search`、`leads-transfer`。
- 当前租户 `sharecrm help sales lead` 暂未暴露上述转换动作的业务 CLI；不要猜测 `sharecrm sales lead leads-transfer` 这类命令。
- 执行转换前，必须在租户后台 `Agent Studio -> Agent 操作库 -> 对应 action -> 详情 -> CLI` 复制真实 CLI 命令，然后只通过 `-d '{...}'` 传参。
- 获取配置示例（将 `<leads-transfer-config-get 的真实 CLI>` 替换为详情页复制到的命令）：`sharecrm <leads-transfer-config-get 的真实 CLI> -d '{"isAllConfig":false,"keys":["40","41","config_newopportunity_open","must_transfer_by_type","put_crm_feed_select_mode","put_teams_select_mode"]}'`
- 获取客户预转换数据示例：`sharecrm <leads-transfer-account-get 的真实 CLI> -d '{"objectDataId":"<leads_id>"}'`
- 执行转换示例：`sharecrm <leads-transfer 的真实 CLI> -d '{"dataList":{"AccountObj":{"fillMultiLang":true,"layoutInfoLog":true,"object_data":{"record_type":"default__c"}},"ContactObj":{"fillMultiLang":true,"layoutInfoLog":true,"object_data":{"record_type":"default__c"}}},"supportDetailObj":true,"putTeamMembersIntoCustomer":false,"combineCRMFeed":false,"leadsId":"<leads_id>"}'`

## 脚本清单

| 顺序 | 脚本 | 作用 |
|---|---|---|
| 1 | `scripts/verify.py` | 校验线索状态 + 转换配置 + 权限 + 获取预转换数据并查重 |
| 2 | `scripts/do_transfer.py` | 执行线索转换 |

### 脚本公共参数

```
python <script.py> <leads_id> [额外参数]
```

- `leads_id`：线索 ID

## 执行流程

注意！你操作的生产数据，不要自作主张的执行未经验证的修改操作。注意和用户友好的交互。
注意！严格按照下方流程执行！线索转换业务server校验条件很多，务必按照下面的步骤执行，遇到错误不要自己去尝试其他的方案。

### 第 1 步：获取线索 ID

**场景 A — 用户直接提供了线索 ID**
直接使用，跳过此步骤。

**场景 B — 用户只提供了线索名称（或其他模糊条件）**
使用 sharecrm的cli工具 `sharecrm data record query-by-template` 或 `sharecrm data record query-by-condition` 查询线索 ID，CLI 会指导具体用法。

- 从输出中提取 `_id`，让用户确认选择哪条线索
- 若输出为空，提示"未查询到该条线索"
- 多条输出询问用户转换哪一条

### 第 2 步：业务准入校验
调用 leads_convert_validate 这个skill，对线索转换这个业务进行准入校验。
线索转换操作涉及到用户的业务数据，当不满足准入条件时，不要自行绕过。立即报告给用户，并提醒该数据未达到准入条件。
如果用户决定绕过业务准入校验，需要二次提醒，得到用户二次确认后才能继续执行。

### 第 3 步：数据前置校验

从获取的对象数据中判断当前的数据状态，如果数据状态不符合要求就停止转换操作，并报告给用户
已转换，不可重复转换
已锁定，不可转换
未分配，需先领取或分配后才可以进行转换操作

然后再调用 `verify.py`：

```
python scripts/verify.py <leads_id>
```

**输出解析**：
- 包含 `[校验失败]` → 校验不通过，终止转换，向用户展示原因
- 包含 `前置校验通过，请和用户确认是否需要关联、是否需要更换业务类型。` → 通过，继续下一步
- `verify.py` 会同时获取预转换数据并检查可关联的已有记录，默认检查 `AccountObj`、`ContactObj`、`NewOpportunityObj`
- `verify.py` 会打印可用业务类型，格式为 `(<ObjectApiName>业务类型) api_name:<record_type>, label:<业务类型名称>`



### 第 4 步：确认转换方式和业务类型

```
AccountObj业务类型 api_name:default__c, label:默认业务类型
ContactObj业务类型 api_name:default__c, label:默认业务类型
NewOpportunityObj业务类型 api_name:default__c, label:默认业务类型
AccountObj没有可关联的数据，推荐直接新建
AccountObj存在可关联数据：ID：69ef3d13f5c5f300079aee4c name:已有客户名称
ContactObj没有可关联的数据，推荐直接新建
NewOpportunityObj没有可关联的数据，推荐直接新建
```

- `没有可关联的数据，推荐直接新建` → 该对象无重复，走新建流程
- `存在可关联数据：ID：xxx name:yyy` → 有重复记录，向用户推荐关联已有
- `api_name:<record_type>, label:<业务类型名称>` → 该对象可用业务类型，执行转换时必须传入对应 `record_type`

**与用户交互**：
1. 展示每个对象的查重结果
2. 有可关联数据的对象，优先推荐"关联已有"
3. 询问用户每个对象的选择（新建 / 关联已有 → 选哪个ID）
4. 展示每个对象的可用业务类型；如果某对象只有一个业务类型，默认使用该业务类型；如果有多个业务类型，必须让用户选择
5. 用户明确表态后，记录每个对象的 `transfer_type` 和 `record_type`：
   - 新建 → `Add`
   - 关联已有 → `已有记录ID`
   - 业务类型 → `verify.py` 输出中的 `api_name`

### 第 5 步：商机转换前准入判断
1. 当用户确认需要转商机时，做线索转商机前的资格验证，对线索进行准入判断、红线检查、升级建议和升级后推荐四层评估
2. 线索转商机的准入验证，调用skill：'leads-convert-validate'

### 第 6 步：执行转换

调用 `do_transfer.py`：

```
python scripts/do_transfer.py <leads_id> <transfer_arg> <record_type>
```

- `transfer_arg`：逗号分隔的 `ObjectName-transfer_type`，如：
  ```
  ContactObj-Add,AccountObj-69ef3d13f5c5f300079aee4c
  ```
- `record_type`：逗号分隔的 `ObjectName-record_type_api_name`，如：
  ```
  ContactObj-default__c,AccountObj-default__c,NewOpportunityObj-default__c
  ```
- `transfer_type` 取值：
  - `Add` → 新建
  - 已有记录 ID → 关联已有（如 `69ef3d13f5c5f300079aee4c`）
- **`transfer_arg` 和 `record_type` 都必须包含 `AccountObj`**
- `record_type` 只传本次转换涉及的对象，且对象集合必须与 `transfer_arg` 保持一致

**输出解析**：

脚本直接打印 `leads-transfer` 的完整返回 JSON：

```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

- `code == 0` → 转换成功
- 其他 → 转换失败，将返回内容展示给用户

### 第 6 步：返回结果

根据 `do_transfer.py` 的输出，向用户汇报（注意判断返回值中是否全部转换完成）：

- 转换成功 → 告知用户成功
- 转换失败 → 展示失败原因

## ⚠️ 硬性约束

- **客户不可跳过**：`AccountObj` 必须出现在 `transfer_arg` 和 `record_type` 中
- **业务类型必传**：调用 `do_transfer.py` 时必须传第五个参数 `record_type`，格式为 `ObjectApiName-record_type_api_name` 的逗号列表
- **对象集合一致**：`record_type` 中的对象必须与 `transfer_arg` 中的对象一致，不要多传未转换对象的业务类型
- **新老商机互斥**：`NewOpportunityObj` 和 `OpportunityObj` 不可同时转换；且 `OpportunityObj` 不允许通过 skill 转换
- **关联已有必须传有效 ID**：`transfer_type` 为已有 ID 时，`do_transfer.py` 会再次调用查重接口确认该 ID 存在

## 完整对话示例

```
用户：帮我转换"张三公司"这条线索

SKILL：
1. 使用 sharecrm data record query-by-template 或 sharecrm data record query-by-condition 查询"张三公司"
   输出：线索id：69ef28eff5c5f300079a268e  线索名称：张三  公司：张三公司
2. 确认线索ID为 69ef28eff5c5f300079a268e
3. 调用 verify.py 校验
   输出：
     AccountObj业务类型 api_name:default__c, label:默认业务类型
     ContactObj业务类型 api_name:default__c, label:默认业务类型
     NewOpportunityObj业务类型 api_name:default__c, label:默认业务类型
     AccountObj存在可关联数据：ID：69ef3d13f5c5f300079aee4c name:已有客户A
     ContactObj没有可关联的数据，推荐直接新建
     NewOpportunityObj没有可关联的数据，推荐直接新建
     前置校验通过，请和用户确认是否需要关联、是否需要更换业务类型。
4. 展示结果：
   - 客户：发现已有记录"已有客户A"，推荐关联已有
   - 联系人：无重复，新建
   - 商机：无重复，新建
   - 客户/联系人/商机均只有一个业务类型，使用 default__c
   用户确认：客户关联已有，联系人新建，商机新建，业务类型使用默认业务类型
5. 调用 do_transfer.py：
   python scripts/do_transfer.py 69ef28eff5c5f300079a268e AccountObj-69ef3d13f5c5f300079aee4c,ContactObj-Add,NewOpportunityObj-Add AccountObj-default__c,ContactObj-default__c,NewOpportunityObj-default__c
6. 展示转换结果
```

## 错误速查

| 输出关键词 | 含义 | 处理 |
|---|---|---|
| `[校验失败]` | 线索不可转换 | 终止，展示原因 |
| `不允许通过skill转换` | 老商机不支持 | 终止，提示去CRM |
| `AccountObj 客户对象必转` | 缺少客户对象 | 补充 `AccountObj` 重试 |
| `record_type参数说明` | 缺少业务类型参数或参数格式错误 | 按 `ObjectApiName-record_type_api_name` 补充第五个参数重试 |
| `前置校验出错` | `verify.py` 执行异常 | 终止 |
| `转换失败` | `do_transfer.py` 查重未命中 | 检查ID是否有效 |
| `关联查询数据失败` | 关联的已有记录不存在 | 检查ID是否有效 |

## 编码说明

所有脚本的输入和输出都使用了UTF-8编码，注意中文编码问题
