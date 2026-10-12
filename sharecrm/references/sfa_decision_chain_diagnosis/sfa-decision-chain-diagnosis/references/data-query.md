# 商机决策链诊断数据查询配置 — Data_Query_Config

定义决策链诊断需要读取的 CRM 数据。主对象为 `NewOpportunityObj`；决策链事实主要来自商机主数据、关联客户、联系人、销售记录与可用的商机联系人关系对象。统一走 `sharecrm` CLI。按字段查询用 `query-by-fields`，以 `--object_api_name`、`--select_fields "f1,f2,..."`、`--<字段>-eq <值>`（模糊匹配用 `--<字段>-like`）、`--limit`、`--sort <字段>:desc|asc` 传参；`get-by-id` / `describe get` / `query-id-by-name` 等仍用 `--data '<json>'`，中文确保 UTF-8。字段不确定先用 `describe get` 确认口径，不要编造字段名。

## 0. 卖方行业配置

读取卖方主营行业配置，得到 `SELLER_INDUSTRY`：

```
sharecrm sales get-config-by-key --data '{"key":"service_models"}'
```

约定 `service_models` 存储卖方主营行业数据。返回格式为 `{"value":"逗号分隔字符串"}`，取其中代表卖方主营行业的值作为 `SELLER_INDUSTRY`（如 `"制造行业"`）。`service_models` 为空时，`SELLER_INDUSTRY` 留空；所有远端 knowhow 检索的 `coreTopics` 不拼接行业，并在输出标注“缺少卖方行业信息”。

## 1. 对象定位

```
sharecrm data record query-id-by-name --data '{"query":"<商机名称>","apiNames":["NewOpportunityObj"]}'
```

未命中时模糊兜底（候选 ≥2 时展示 `_id` / `name` / `account_id__r` 供选择）：

```
sharecrm data record query-by-fields --object_api_name NewOpportunityObj --select_fields "_id,name,account_id__r" --name-like "<关键词>" --limit 10 --sort last_modified_time:desc --raw
```

## 2. 商机主数据（字段 + 特征）

`get-by-id` 真实契约为 `--object_api_name <string> --id <string>`（或 `--data '{"object_api_name":...,"id":...}'`），**不支持指定返回字段**，返回整条记录。需要限定字段时改用 `query-by-fields`。

```
sharecrm data record get-by-id --data '{"object_api_name":"NewOpportunityObj","id":"<opportunity_id>"}' --raw
```

如只需部分字段（控制返回体量），用 `query-by-fields`：

```
sharecrm data record query-by-fields --object_api_name NewOpportunityObj --select_fields "_id,name,account_id,account_id__r,sales_stage,sales_stage__r,amount,win_rate,close_date,owner,owner__r,competitor,customer_budget,last_followed_time,last_modified_time,create_time" --_id-eq "<opportunity_id>" --limit 1 --raw
```

```
sharecrm data describe get --data '{"object_api_name":"NewOpportunityObj","simple_describe":true}'
```

## 3. 关联数据（诊断现状所需）

### 3.1 关联客户（AccountObj） (必须查询)

补足客户画像、状态、行业、价值背景；**行业字段必须查询**（含买方行业 `industry_level1` / `industry_level2`），不替代商机主数据。

```
sharecrm data record get-by-id --data '{"object_api_name":"AccountObj","id":"<account_id>"}' --raw
```

### 3.2 关联联系人 / 决策链 (必须查询)

决策链是核心维度之一，必须执行查询，支撑「决策链分析」。两层用途：

- **商机联系人**：识别“有哪些人”，提取姓名、职位、部门、角色、主联系人、互动状态，用于判断角色覆盖与触达层级。
- **商机联系人关系**：识别“谁影响谁、谁连接谁”，提取关系类型、影响方向、支持度、汇报关系、决策角色，用于判断真假决策者、Coach 候选、反对者与隐性权力中心。

商机关联联系人通过 `OpportunityContactObj`（商机-联系人关系对象）按 `new_opportunity_id` 反查，再取联系人详情；字段口径以 `describe get` 为准，字段不确定先 `describe`，不要编造。

先查商机关联联系人关系（角色、是否关键人、影响/汇报关系）：

```
sharecrm data record query-by-fields --object_api_name NewOpportunityContactsObj --select_fields "_id,new_opportunity_id,contact_id,contact_id__r,role,role__r,is_key_person,decision_role,decision_role__r,influence_direction,report_to,support_degree,last_modified_time" --new_opportunity_id-eq "<opportunity_id>" --limit 20 --sort last_modified_time:desc --raw
```

如需联系人职位/部门/决策角色详情，按上一步取得的 `contact_id` 取 `ContactObj`：

```
sharecrm data record get-by-id --data '{"object_api_name":"ContactObj","id":"<contact_id>"}' --raw
```

再查商机联系人关系（识别“谁影响谁、谁连接谁”），通过 `NewOpportunityContactRelationshipObj`（商机联系人关系对象）按 `new_opportunity_id` 反查，提取关系类型、影响方向、支持度、汇报关系、决策角色，用于真假决策者验证、Coach 候选识别与隐性权力中心判断：

```
sharecrm data record query-by-fields --object_api_name NewOpportunityContactRelationshipObj --select_fields "_id,name,new_opportunity_id,contact_id,contact_id__r,related_contact_id,related_contact_id__r,relationship_type,relationship_type__r,influence_direction,support_degree,support_degree__r,report_to,decision_role,decision_role__r,remark,last_modified_time" --new_opportunity_id-eq "<opportunity_id>" --limit 50 --sort last_modified_time:desc --raw
```

 关系对象 API 名与字段以实际环境 `describe get` 为准；`is_key_person` / `decision_role` / `influence_direction` / `report_to` / `support_degree` / `relationship_type` / `related_contact_id` 等字段若不存在，按 `describe` 返回的实际字段调整或归入 `ContactObj`，不要编造字段名；若该环境无 `OpportunityContactObj` 或 `NewOpportunityContactRelationshipObj`，按 `describe` 返回的实际关系对象调整 `objectApiName` 与关联字段，不要跳过决策链查询。多条关系汇聚到同一对象时关注其是否为隐性权力中心。无联系人记录不等于无决策链：查询为空时按「严重缺失」处理，角色统一写「未识别」，不得自动补全人物或立场。


### 3.3 销售记录（ActiveRecordObj） (必须读取数据)

```
sharecrm data record query-by-fields --object_api_name ActiveRecordObj --select_fields "_id,active_record_content,active_record_type,new_opportunity_id,create_time,created_by__r" --new_opportunity_id-eq "<opportunity_id>" --limit 10 --sort create_time:desc --raw
```


## 4. 使用规则

- 关键人角色、态度、影响力必须来自 CRM 记录、销售记录或用户输入，不能从职位名称硬推。
- 查询不到关系对象时，不阻断；标注“商机联系人关系数据缺失”，并基于联系人和销售记录降级判断。
