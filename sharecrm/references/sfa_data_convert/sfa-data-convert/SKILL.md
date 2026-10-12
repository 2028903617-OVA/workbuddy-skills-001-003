---
name: "sfa-data-convert"
description: "用于转换，禁止用于创建、新建、保存、更新、下单操作以及线索的操作。仅支持商机转报价单、报价单转销售合同、报价单转销售订单、销售合同转销售订单四个固定场景。禁止用于线索转换（线索转客户、联系人、商机）"
apiName: "sfa_data_convert"
---
# SFA单据转换处理流程
禁止用于线索转客户、联系人、商机，请使用`sfa-leads-convert`SKILL。

## Goal

处理以下 4 个固定转换场景：

| 场景 | 上游主对象 | 上游明细对象 | 下游主对象 | 下游明细对象 |
| --- | --- | --- | --- | --- |
| 商机转报价单 | `NewOpportunityObj` | `NewOpportunityLinesObj` | `QuoteObj` | `QuoteLinesObj` |
| 报价单转销售合同 | `QuoteObj` | `QuoteLinesObj` | `SaleContractObj` | `SaleContractLineObj` |
| 报价单转销售订单 | `QuoteObj` | `QuoteLinesObj` | `SalesOrderObj` | `SalesOrderProductObj` |
| 销售合同转销售订单 | `SaleContractObj` | `SaleContractLineObj` | `SalesOrderObj` | `SalesOrderProductObj` |


## WhenToUse

适合这些表达：

- 把这条商机转成报价单
- 商机转报价单
- 把这张报价单转成合同
- 报价单转销售合同
- 报价单转订单
- 用这张报价单转成销售订单
- 把这个合同转成订单
- 销售合同转销售订单

不适合这些表达：

- 创建全新报价单、合同或订单，但与现有源单据无关
- 只查询商机、报价单、合同详情但不转换
- 修改已有商机、报价单、合同或订单
- 商机转合同
- 商机转订单
- 合同转报价单
- 未在本 skill 中声明的其他转换方向

当不符合4个固定场景，明确提示用户当前只支持的这4个场景，禁止继续执行。

## 固定转换路由

只能支持以下固定路由，不允许臆造新路由：

- `NewOpportunityObj -> QuoteObj`
- `QuoteObj -> SaleContractObj`
- `QuoteObj -> SalesOrderObj`
- `SaleContractObj -> SalesOrderObj`

明细映射固定为：

- `NewOpportunityLinesObj -> QuoteLinesObj`
- `QuoteLinesObj -> SaleContractLineObj`
- `QuoteLinesObj -> SalesOrderProductObj`
- `SaleContractLineObj -> SalesOrderProductObj`

如果用户表达的转换方向不在上述 4 个固定场景内，必须直接说明当前 skill 不支持，禁止继续推断执行。

## 场景识别规则

优先同时识别两个维度：

- 源对象：商机 / 报价单 / 销售合同
- 目标对象：报价单 / 销售合同 / 销售订单

路由判断规则：

- 源对象是商机，目标对象是报价单：走“商机转报价单”
- 源对象是报价单，目标对象是销售合同：走“报价单转销售合同”
- 源对象是报价单，目标对象是销售订单：走“报价单转销售订单”
- 源对象是销售合同，目标对象是销售订单：走“销售合同转销售订单”

如果用户只说“转一下”“继续往下转”而未说清源对象或目标对象，必须先补问，不要猜。

## Required Inputs

- 源记录信息：ID、名称、编号或其他足以唯一定位源记录的信息
- 转换方向：必须能唯一确定为 4 个固定场景之一

当缺少必要输入，必须提示用户补充信息，未补充明确信息前，禁止继续执行。

可选输入：

- 用户在目标单据上明确指定的补充字段
- 需要同步回写源单据的要求
- 备注、日期、负责人等后续创建时需要的字段


## Tools & Commands

### queryIdByName
sharecrm data record query-id-by-name --data '{"query":"<数据名称或标题>","apiNames":["<对象名称，比如QuoteObj、NewOpportunityObj>"]}'


### queryByName
sharecrm data record query-by-name --data '{"name":"<数据名称或标题>","object_api_names":["<对象名称，比如QuoteObj、NewOpportunityObj>"]}'

### recordList
sharecrm data describe record-list -d '{"object_api_name":"<目标对象的 object_api_name>"}'

### opptConvertQuote
sharecrm sales opportunity oppt-convert-quote --data '{"objectDataId":"<商机ID>"}'

### quoteConvertContract
sharecrm sales quote quote-convert-contract --data '{"objectDataId":"<报价单ID>"}'

### quoteConvertOrder
sharecrm sales quote quote-convert-order --data '{"objectDataId":"<报价单ID>"}'

### contractConvertOrder
sharecrm sales contract contract-convert-order --data '{"objectDataId":"<合同ID>"}'

### createData
sharecrm data record create --data '{"object_api_name": "<apiName>", "object_data": <已构造的 object_data>, "details": <已构造的 details>}'

## Workflow
### Step1 解析并定位源记录
1. 解析用户输入，提取源对象候选信息
2. 当用户直接给出 ID 时，优先使用该 ID，通过`queryById`命令查询数据的有效性，如果查询结果为空，进入Step1 的第3小步
3. 当用户给名称、编号或口语化描述时，通过 `queryByName`命令查询数据，如果还查询不到数据，必须提示用户重新提供信息，如果找到数据，则进入Step1的第4、第5步
4. 如果命中多条候选记录，必须让用户确认具体记录
5. 只有在源记录唯一确定后，才允许继续

### Step2 场景识别及上游数据校验

按场景读取对应源对象及明细：

- 商机转报价单：读取 `NewOpportunityObj` / `NewOpportunityLinesObj`
- 报价单转销售合同：读取 `QuoteObj` / `QuoteLinesObj`
- 报价单转销售订单：读取 `QuoteObj` / `QuoteLinesObj`
- 销售合同转销售订单：读取 `SaleContractObj` / `SaleContractLineObj`

上游数据校验原则：

1. 上游数据必须存在
2. 上游数据必须处于可转换状态
3. 如果对象存在 `life_status` 字段且字段值不是 `normal`，必须提示禁止继续
4. 如果后端返回明确的状态限制、审批限制或业务限制，以后端限制为准，禁止绕过

### Step3 调用转换接口获取预填数据
按场景执行对应的转换接口，选其一，如果不确定是哪个场景，询问用户，不猜测。

- 场景A 商机转报价单
执行`opptConvertQuote`命令

- 场景B 报价单转销售合同
执行`quoteConvertContract`命令

- 场景C 报价单转销售订单
执行`quoteConvertOrder`命令    

- 场景D 销售合同转销售订单
执行`contractConvertOrder`命令

### Step4 获取预填数据后处理逻辑
1.步骤一：将返回数据json里的所有__temp_data_id__删除
2.步骤二：检查返回数据json里的`objectData`.`record_type`是否为空，分支情况如下：
- 情况1: 业务类型为空，执行`recordList`命令，如果未返回业务类型，阻断转换；如果返回业务类型只有一条，则直接赋值给`objectData`.`record_type`，然后进入`保存数据`步骤；如果返回业务类型有多条，则让用户选择 业务类型，然后进入`保存数据`步骤；
- 情况2：业务类型不为空进入`保存数据`步骤

### Step5 保存数据
执行`createData`命令

### Step6 返回结果

调用 `create` 后，**先判断接口返回，只有记录确实创建成功时才用 `render_content` 输出**，且成功时不要再附加任何文字总结。

返回不是「创建成功」时（例如系统返回需要二次确认的状态——重复校验/防重提示等，或返回报错），**不要调用 `render_content`**，也不要凭空生成一张「已创建」的结果卡或成功话术：

- **需要二次确认**：把系统要求确认的内容如实转达给用户（用 `AskUserQuestion`），等用户确认后再按系统要求重新提交；只有最终真正创建成功，才走 `render_content`。
- **返回 `User declined to create or update this record.`**：用户已明确拒绝本次创建，**立即终止整个操作**——不重试、不换方式重新提交、不再追问、不渲染结果卡，如实告知用户本次创建已取消即可。
- **返回 `errorCode=EXECUTE_FAILED`（或类似"当前对象不支持执行该操作/无权限/操作被禁止"的错误）**：这类错误表示**操作本身不被允许或不被支持**，不是字段写法问题，**立即终止，绝对不要重试、不要换字段或换参数重新提交**。如实把错误信息告诉用户即可。
- **保存失败 / 报错**：把失败原因如实告诉用户，不要伪装成成功，也不要渲染结果卡。**不要自动反复重试、不要换着花样重复提交。** 仅当错误信息明确指出某个可修正的字段问题（如枚举提交值非法、关联 ID 写错、必填缺失）时，回到对应步骤修正后**至多重试一次**；若重试仍失败、或错误原因不明确/不可由你自行修正（如权限、流程校验、系统异常、`EXECUTE_FAILED`），立即停下来把错误如实告知用户并等待用户指示，禁止继续循环提交。


## Output

### 验收标准
未执行`保存数据`步骤，禁止输出`xxx已成功转为xxx`类似的提示信息

### 下一步操作推荐
保存成功后，根据转换结果，给出下一步建议：
1. 商机转报价单成功后，询问用户
- 是否将报价单转销售合同？
- 是否将报价单转销售订单？
2. 报价单转销售合同成功后，推荐用户
- 是否将销售合同转销售订单？