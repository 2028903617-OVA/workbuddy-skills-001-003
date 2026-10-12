# 线索（LeadsObj）评分数据查询

用于线索质量、准入、转商机价值等 knowhow 评分。只查询支撑评分所需的业务事实。

## 1. 对象定位

sharecrm data record query-id-by-name --data '{"query":"<线索名称或公司名>","apiNames":["LeadsObj"]}'

未命中时模糊兜底（候选 ≥2 时展示 `_id` / `name` / `company` / `owner__r` 供选择，不自动选第一条）：

sharecrm data record query-by-name --data '{"object_api_names":["LeadsObj"],"name":"<线索名称或关键词>"}'

## 2. 线索主数据（字段 + 特征）

`get-by-id` 使用扁平参数 `--object_api_name LeadsObj --id <lead_id> --raw`，**不支持指定返回字段**，返回整条记录。需要限定字段时改用 `query-by-fields`。

sharecrm data record get-by-id --object_api_name LeadsObj --id <lead_id> --raw

如只需部分字段（控制返回体量），用 `query-by-fields`：

sharecrm data record query-by-fields --object_api_name LeadsObj --select_fields "_id,name,company,leads_stage,leads_stage__r,biz_status,biz_status__r,leads_status,leads_status__r,source,source__r,owner,owner__r,industry,industry__r,level,level__r,intention,remark,create_time,last_modified_time,last_follow_time,last_followed_time" --_id-eq "<lead_id>" --limit 1 --raw

sharecrm data describe get --object_api_name LeadsObj --simple_describe true

字段口径以 `describe get` 为准：`leads_stage` / `biz_status` / `leads_status`、`last_follow_time` / `last_followed_time` 在不同环境可能不一致，若环境字段不同，按实际 `describe` 返回调整，不要编造字段名。

> **敏感字段最小化**：`contact_phone`、`email` 等联系人个人信息默认不查询、不输出；仅当评分明确需要判断“是否已有关键联系人且联系方式完整”时，才允许校验字段是否存在，并且最终评分输出只写“已有联系方式”或“联系方式未体现”，不回显具体号码或邮箱。

## 3. 关联数据（评分所需）

### 3.1 销售记录 / 跟进记录（必须读取数据）

Timeline、Sponsor、深度互动、CRM 行为、预算/采购线索、当前需求与下一步动作，优先从销售记录中取证。线索侧通常通过 `ActiveRecordObj.related_object_id` 关联；如环境字段不同，先 `describe` 再调整。

sharecrm data record query-by-fields --object_api_name ActiveRecordObj --select_fields "_id,active_record_content,active_record_type,related_object_id,related_object_data,related_api_names,create_time,created_by__r" --related_object_id-eq "<lead_id>" --limit 20 --sort create_time:desc --raw

sharecrm data describe get --object_api_name ActiveRecordObj --simple_describe true

结果级校验：只采纳 `related_object_id == <lead_id>`，或 `related_object_data` 中存在 `id == <lead_id>` 且对象口径指向 `LeadsObj` 的记录；不满足条件的记录必须丢弃，不得作为评分证据。

### 3.2 转化 / 重复 / 无效风险信号（条件关注）

重复、无效、纯调研、已转化、被竞品锁定等信号，优先从线索主字段与销售记录中取证，不额外假设专门关系对象。

重点关注：
- `leads_stage` / `biz_status` / `leads_status` 等状态字段
- `remark` 中是否存在“已转商机 / 已转客户 / 无效 / 重复 / 调研 / 竞品锁定”等事实
- 销售记录中是否明确出现转化动作、无效原因、竞品替换、当前 CRM 使用情况、预算/采购路径等线索

若记录中已明确显示“已转化”或“无效”，评分需按保守规则处理；若只有模糊暗示，不得把推测写成已确认事实。

## 4. 评分证据映射

| 评分维度 | 主要证据来源 |
| --- | --- |
| 七问验证 | `LeadsObj` 主字段、`remark`、最近销售记录 |
| Timeline | `remark`、销售记录中的时间表达、下一步动作、最后跟进时间 |
| Sponsor | 联系人/决策人相关字段（若环境存在）、销售记录中的发起人/业务 owner 线索 |
| 深度互动 | 销售记录的次数、类型、内容；是否有多角色沟通、现场拜访、深度会议 |
| CRM 行为和跟进信号 | 状态字段、负责人、最后跟进时间、活跃记录最近性 |
| 预算 / 采购 / 当前 CRM | `remark` 与销售记录中的预算、采购流程、当前系统使用、替换动机线索 |
| 匹配度和风险 | 行业、来源、等级、意向、状态字段，以及无效/重复/竞品/纯调研等风险信号 |

记录未体现 ≠ 事实不存在。缺少证据时只能按评分标准保守给分，并在评分依据中明确写“当前记录暂未体现”。

## 评分使用

- 线索主字段、备注、销售记录共同构成评分事实来源；没有证据的维度不得主观补齐。
- 七问验证、Timeline、Sponsor、深度互动等结论，必须能回溯到字段事实或销售记录内容。
- 字段不存在、记录为空、或环境字段与示例不同，都不代表能力失效；先以 `describe get` 校验真实口径，再按可见事实评分。
- 最终评分输出不回显联系人手机号、邮箱等敏感信息，只保留对评分有用的存在性或角色性描述。
