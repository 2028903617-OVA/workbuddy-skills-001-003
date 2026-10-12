# R01 声音范围识别

## 目标

把用户的自然语言请求转换为可查询、可分析的客户声音范围，包括分析视角、对象范围、时间范围、三对象过滤条件、输出深度，以及用户意图类型和交互模式。

## 触发条件

用户请求客户声音、客户反馈、VOC、客户痛点趋势、某部门/某销售/某角色视角的客户声音时始终执行。

用户询问 VOC 方法论/理论/知识时也同样触发，包括"什么是 VOC""介绍一下 VOC""讲讲华为 VOC""VOC 五步闭环是什么""$APPEALS 是什么""VOC 方法论""客户声音方法论"等。

## 输入来源

- 用户输入。
- 当前上下文中的日期、人员、部门、会议记录（`AIMeetingObj`）或销售记录（`ActiveRecordObj`）范围。
- 销售记录（`ActiveRecordObj`）、会议记录（`AIMeetingObj`）、会议记录明细（`AIMeetingChunkObj`）。

## 视角类型

| 视角 | 典型请求 | 输出重点 |
| --- | --- | --- |
| CEO | “CEO 看客户声音”“老板想知道客户都在反馈什么” | 经营风险、战略信号、跨部门共性问题、高强度声音、客户分层、管理动作 |
| 销售管理者 | “销售团队客户声音”“本月客户反馈” | 高频主题、人员/部门差异、销售记录（ActiveRecordObj）/会议记录（AIMeetingObj）质量、管理动作 |
| 部门负责人 | “销售一部客户声音” | 本部门销售记录（ActiveRecordObj）和会议记录（AIMeetingObj）中的反馈、重点人员、部门风险 |
| AE | “张三名下客户声音”“我负责的会议里客户都在问什么” | 本人负责/创建/参与记录中的高优先级声音 |
| 会议视角 | “上周会议客户声音”“AI 会议记录里客户反馈” | 会议记录（AIMeetingObj）主题、会议记录明细（AIMeetingChunkObj）原文、会议 AI 状态、参与人归因 |
| 销售记录视角 | “销售记录里的客户声音” | 销售记录（ActiveRecordObj）正文、负责人、创建人、业务类型归因 |
| 单记录补充 | “这条会议记录的客户声音” | 只提取该会议或销售记录声音，不生成客户360 |

## 默认值

- 未指定视角：默认 `CEO`。
- 未指定时间范围：默认最近 30 天。
- 未指定对象范围：默认同时纳入销售记录（`ActiveRecordObj`）、会议记录（`AIMeetingObj`）和会议记录明细（`AIMeetingChunkObj`）。
- 未指定排序：按风险强度、频次、记录来源完整度和跨部门重复程度综合排序。
- 用户提到“上周/月/季度”时，按当前日期解析自然时间。

## 输出契约

```yaml
r01_scope:
  view_type: CEO|sales_manager|department_leader|ae|meeting|sales_record|single_record|unknown
  scope_label:
  source_objects:
    include_sales_records: true|false
    include_meetings: true|false
    include_meeting_chunks: true|false
  time_range:
    start_date:
    end_date:
    time_field: create_time|start_time|end_time|last_modified_time
    compare_range:
      start_date:
      end_date:
  filters:
    owners:
      - name:
        id:
    owner_departments:
      - name:
        id:
    data_own_departments:
      - name:
        id:
    created_by:
      - name:
        id:
    initiators:
      - name:
        id:
    inner_participants:
      - name:
        id:
    record_types:
      - value:
    ai_status:
      - value:
    chunk_status:
      - value:
    meeting_ids:
      - id:
    original_refs:
      - object_api_name:
        original_id:
  full_mode: true|false
  output_depth: summary|standard|full
  intent_type: report|qa|exploration|mixed|voc_theory|unknown
  interaction_mode: report|qa|report_with_qa|unknown
  report_template: voc_5step|classic_6chapter
  output_format: markdown|html
  detected_user_dimension: 痛点|期望|不满|认可|竞品|趋势|none
  data_gaps:
    - gap
```

## 分析规则

- 先识别"谁要看"，再识别"看哪些销售记录（ActiveRecordObj）/会议记录（AIMeetingObj）"，最后识别"看多久"。
- 范围识别完成后，执行意图识别子步骤：根据用户输入关键词判断意图类型（报告/问答/探索/混合）和交互模式。意图识别规则引用 R09。
- 识别用户是否提到了六维关键词（痛点/期望/不满/认可/竞品/趋势），记录到 detected_user_dimension 字段。
- 识别用户是否指定了报告模板。关键词"VOC五步"/"五步闭环"/"闭环"→ voc_5step；关键词"经典六章"/"六章"/"传统格式"→ classic_6chapter；未指定→默认 voc_5step。
  - **评审版说明**：`voc_5step` 已调整为评审后的精简结构，默认只输出 `听见客户声音（Hear）`、`理解客户声音（Understand）`、`持续变革（Transform）` 三章；不再输出独立的 `采取行动（Act）`、`反馈闭环（Feedback)` 和 `附录`。
- 识别用户是否要求 HTML 输出格式。关键词"HTML"/"html"/"网页"/"页面"→ output_format=html；未指定→默认 markdown。
- 识别用户是否在询问 VOC 方法论/理论/知识。关键词"什么是 VOC""介绍一下 VOC""讲讲华为 VOC""VOC 五步闭环是什么""$APPEALS 是什么""VOC 方法论""客户声音方法论"→ intent_type=voc_theory。
  - **当 intent_type=voc_theory 时**：
    1. 跳过所有 CRM 数据查询、范围识别、声音抽取步骤
    2. 不输出下方的「声音范围与样本」Markdown 表格
    3. 直接由 SKILL.md「前置意图判断」接管，读取 `references/voc_methodology.md` 输出
    4. R01 的输出契约中 intent_type 字段标记为 `voc_theory`，其余字段可留空
- 如果用户未指定角色，也按全局经营视角处理，不默认收窄到某个人员范围。
- 如果用户说"CEO"，不要默认只看 CEO 本人相关记录，而是看全局经营视角。
- 如果用户说"某销售"，优先匹配 `owner`、`created_by`、`initiator`、`inner_participants`。
- 如果用户说"部门"，优先匹配 `owner_department` 和 `data_own_department`。
- 如果用户说"会议"，优先查询 `AIMeetingObj` 和 `AIMeetingChunkObj`，并通过 `meeting_id` 关联。
- 如果用户说"销售记录"，优先查询销售记录（`ActiveRecordObj`）；会议记录明细（`AIMeetingChunkObj`）仅在 `object_api_name/original_id` 指向销售记录（`ActiveRecordObj`）时作为补充。
- 如果用户只给单条会议或记录 ID，输出单记录声音摘要，不扩展成标准客户简报。
- 多个候选部门、人员、会议或记录重名时，需要让用户选择。
- 时间范围必须进入最终报告顶部，不允许省略。
- 比较区间默认取上一等长周期；如果数据不足，写"无可靠对比基线"。
- `--full` 只扩大三对象历史窗口和明细展示，不查询其他业务对象。

## Markdown 输出

```markdown
## 1. 🔎 声音范围与样本

| 维度 | 内容 |
| --- | --- |
| 分析视角 | CEO/管理层/销售管理者/部门负责人/AE/会议记录（AIMeetingObj）/销售记录（ActiveRecordObj）/单记录 |
| 数据对象 | 销售记录（ActiveRecordObj）/ 会议记录（AIMeetingObj）/ 会议记录明细（AIMeetingChunkObj） |
| 覆盖范围 |  |
| 时间范围 |  |
| 对比周期 |  |
| 过滤条件 |  |
| 输出深度 | summary/standard/full |

### 范围说明
- {本次分析纳入和排除的销售记录（ActiveRecordObj）、会议记录（AIMeetingObj）和会议记录明细（AIMeetingChunkObj）范围}

### 范围缺口
- {缺少的部门、人员、会议、记录、时间或字段信息}
```
