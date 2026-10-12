# 线索（LeadsObj）数据查询配置 — Data_Query_Config

线索诊断需读取的数据及查询方式。统一走 `sharecrm` CLI，复杂参数用 `--data '<json>'`，中文确保 UTF-8。字段不确定先用对象描述确认口径，不要编造字段名。具体工具清单与命令模板以 `SKILL.md` 的 `ToolsList` 为准，本文件只定义对象级查询范围、字段集与配置解释规则。

## 1. 对象定位（仅当未给 object_id 时）

sharecrm data record query-id-by-name --data '{"query":"<线索名称或公司名>","apiNames":["LeadsObj"]}'

未命中时按 `name` 模糊兜底（候选 >= 2 时展示 `_id` / `name` / `company` 供选择，不自动选第一条）：

sharecrm data record query-by-name --data '{"object_api_names":["LeadsObj"],"name":"<线索名称或公司关键词>"}'

## 2. 线索主数据（字段 + 特征）

已知 `lead_id` 时优先用 `get-by-id` 获取主记录详情；需要字段裁剪时用 `query-by-fields` 按 `_id` 取定字段：

sharecrm data record get-by-id --object_api_name LeadsObj --id <lead_id>

sharecrm data record query-by-fields --data '{"object_api_name":"LeadsObj","select_fields":["_id","name","company","leads_stage","leads_stage__r","biz_status","biz_status__r","leads_status","leads_status__r","source","source__r","owner","owner__r","industry","industry__r","level","level__r","intention","remark","create_time","last_modified_time","last_followed_time"],"filters":[{"field_api_name":"_id","operator":"EQ","values":["<lead_id>"]}],"limit":1}'

> **敏感字段最小化**：`contact_phone`、`email` 等联系人个人信息默认**不查询、不输出**；仅当用户明确要求联系动作且业务必要时才查询，且只做存在性提示（如“已有联系电话”），不在输出正文回显具体号码/邮箱，字段不可见时不得模型补齐。

## 3. 销售记录 / 跟进记录

查询关联到该线索的销售记录（对象 API 以实际环境为准，常见 `ActiveRecordObj`）：

sharecrm data record query-by-fields --data '{"object_api_name":"ActiveRecordObj","select_fields":["_id","active_record_content","active_record_type","related_object_id","create_time","created_by__r"],"filters":[{"field_api_name":"related_object_id","operator":"EQ","values":["<lead_id>"]}],"orders":[{"field_api_name":"create_time","is_asc":false}],"limit":10}'

## 4. 按意图的最小查询范围

| 意图 | 需查询 |
| --- | --- |
| 生成画像 | 第 1、2 节（主数据 + 特征） |
| 下一步怎么跟 | 第 1 节定位 + 第 2、3 节主数据与销售记录 |
| 洞察（默认） | 第 1、2、3 节全部 + 评分 |

> `Scoring_Result`（必需）优先来自 `get_profile_score --objectApiName LeadsObj`；仅当 CLI 失败、为空、无可用评分信息或对象不匹配时，才回退上游 `sfa-leads-score`。`AI_Stage` 不由其他 skill 提供，调用方必须根据本次查询到的线索阶段、状态、主数据与销售记录，按 `SKILL.md` Workflow 第 4 步直接判断。

## 5. 卖方行业配置（SELLER_INDUSTRY）

读取卖方主营行业配置，得到 `SELLER_INDUSTRY`，用于增强远端 knowhow 检索主题：

sharecrm sales get-config-by-key --data '{"key":"service_models"}'

返回结果中如存在明确行业名称，则记为 `SELLER_INDUSTRY`。

- 若返回为空、不可用或无法判断行业：`SELLER_INDUSTRY` 置空。
- `SELLER_INDUSTRY` 为空时，后续远端 knowhow 查询不拼接行业，并在诊断输出中标注“缺少卖方行业信息”。
- 不得由模型猜测行业，不得用客户行业字段替代卖方行业。
