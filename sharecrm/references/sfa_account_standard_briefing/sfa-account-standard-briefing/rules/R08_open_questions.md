# R08 开放问题与档案组装

## 目标

把前序规则中的未知项、推断项和冲突信息整理成“开放问题”，生成结论摘要，并组装最终客户360 Markdown 档案。

## 触发条件

完成 R01-R07 后始终执行。

## 输入来源

- R01-R07 的 `data_gaps`。
- 置信度为 `inferred` 或 `unknown` 的关键判断。
- CRM 与内部历史信息冲突项。
- 用户明确要求关注的问题。

## 输出契约

```yaml
r08_open_questions:
  information_completeness: complete|partial|insufficient
  executive_summary:
    one_sentence_conclusion:
    customer_status:
      conclusion:
      confidence: confirmed|inferred|unknown
    main_opportunity:
      conclusion:
      confidence: confirmed|inferred|unknown
    main_risk:
      conclusion:
      confidence: confirmed|inferred|unknown
    decision_chain:
      conclusion:
      confidence: confirmed|inferred|unknown
    relationship_temperature:
      conclusion:
      confidence: confirmed|inferred|unknown
    biggest_gap:
      conclusion:
      confidence: confirmed|inferred|unknown
    focus_points:
      - focus:
        reason:
  key_unknowns:
    - question:
      why_it_matters:
      source_rule:
      suggested_source: CRM|Memory|customer|public_info|internal_team
  risk_matrix:
    - risk:
      level: high|medium|low|unknown
      impact:
      trigger:
      mitigation_direction:
      confidence: confirmed|inferred|unknown
  data_health_alerts:
    - alert_type: discount|payment_cycle|receivable|external_risk|interaction|other
      signal:
      impact:
      suggested_check:
      confidence: confirmed|inferred|unknown
  conflicting_facts:
    - conflict:
      sources:
      resolution_needed:
  next_best_actions:
    - action:
      purpose:
      owner_or_role:
      timing:
      confidence: confirmed|inferred|unknown
  follow_up_focus:
    - focus:
      reason:
```

## 信息完整度判断

| 等级 | 判断标准 |
| --- | --- |
| 完整 | 客户基础信息、近 12 个月互动、至少 1 个进行中或历史商机、关键联系人、主要痛点和竞品状态都有证据 |
| 部分 | 基础信息和部分互动存在，但决策链、痛点、竞品或历史财务存在明显缺口 |
| 不足 | 只有客户名称或少量 CRM 字段，无法形成可靠客户认知 |

## 分析规则

- 结论摘要必须放在正文前，先给结论，再展开证据。
- 一句话结论要同时回答“客户当前状态、主要机会/风险、判断置信度”，不要写成口号。
- 摘要表只保留 6 个高价值判断：客户状态、主要机会、主要风险、决策链、关系温度、最大信息缺口。
- “优先关注”最多 3 条，只写客户认知或后续关注点，不写强行动指令。
- 风险矩阵必须汇总 R02-R07 的关键风险，按高/中/低分级，说明影响、触发条件和缓释方向。
- 风险等级不是情绪判断：高风险必须可能影响成交、续约、关键关系或项目时点；中风险影响局部推进；低风险需要关注但短期不改变判断。
- 如存在折扣异常、应收/回款周期、外部经营风险、法律诉讼、互动频率骤降或客户承诺反复延迟，必须放入“数据提示与健康预警”；没有证据时不输出猜测性预警。
- 外部风险只能作为预警或待核对事项，不得覆盖 CRM、Memory、合同、订单或回款事实。
- “数据提示与健康预警”服务风险判断，不新增独立“智能洞察”大章节，也不写成泛泛建议。
- Next Best Action 是标准版建议动作，不是见客前行动板；最多 5 条，围绕验证关键假设、补齐决策链、降低风险、推进项目里程碑。
- 建议动作要写“目的”和“时机”，不能只写任务名。
- 开放问题不是行动清单，而是客户认知缺口。
- 每个开放问题必须说明为什么重要。
- CRM 与内部历史信息冲突时，不直接选择一个版本；标注“需核对”。
- 内部事实与外部情报冲突时，不用外部情报覆盖内部事实；必须写入“事实冲突”或“关键信息缺口”，并标注“需核对”。
- 查询失败、权限不足、未触发查询导致的关键缺口必须进入“关键信息缺口”或“最大信息缺口”，避免被误读为客户不存在该信息。
- 最终 Markdown 必须保留置信度标注，避免把推断写成事实。
- 不输出见客前简报语言，包括“今日目标”“行动 P0/P1/P2”“底线”“确认出发”；P0/P1/P2 仅可用于使用规模优先级。
- 使用少量 emoji 强化章节扫读，默认用于一级章节标题，不用于每条记录。
- 不删减前序规则已产出的内容；没有数据时保留章节并写“未知/待补充/暂无记录”。
- 正文不逐条展示 `来源：...` 或 `依据：...`；证据类型统一放在最终档案末尾的 `📎 参考来源` 弱引用区。
- R03 和 R04 必须合并为同一个“决策圈图谱”一级章节；先展示关系温度，再展示决策链、人力地图、组织政治和覆盖分析。
- “博弈时间线”必须放在“决策圈图谱”之后。

## Markdown 输出

```markdown
## ❓ 开放问题

### 关键信息缺口
| 问题 | 为什么重要 | 建议核对来源 |
| --- | --- | --- |
|  |  | CRM/客户/公开信息/内部团队 |

### 事实冲突
- {冲突项}：{来源差异}；需核对：{核对方式}

### 风险矩阵
| 风险等级 | 风险 | 影响 | 触发条件 | 缓释方向 | 置信度 |
| --- | --- | --- | --- | --- | --- |
| 高/中/低 |  |  |  |  | 确认/推断/未知 |

## ✅ 后续建议动作

### 数据提示与健康预警
| 类型 | 信号 | 可能影响 | 建议核对 | 置信度 |
| --- | --- | --- | --- | --- |
| 折扣/回款/应收/外部风险/互动/其他 |  |  |  | 确认/推断/未知 |

### 建议动作
| 建议动作 | 目的 | 适合时机 | 责任角色 |
| --- | --- | --- | --- |
|  |  |  | AE/SE/CSM/销售管理者/未知 |

### 后续关注点
- {不强制行动，仅说明后续应持续关注的客户认知问题}
```

## 最终档案组装顺序

默认先在对话中直接输出 Markdown 正文，按以下结构组装，不包进代码块，也不要只给 `.md` 文件路径；随后读取 `references/html_render_contract.md` 和 `rules/R10_html_output.md`，把同一内容整理为 `briefing_facts_bundle.json`，调用 `scripts/render_standard_briefing.py` 生成并校验 HTML。不得手写 HTML 或重排正式模板；HTML 只做展示层，不改变事实、判断、置信度或信息缺口。

```markdown
# 客户360 — {客户名称}

> 数据更新时间：{date}
> 负责人：{owner，如未知写未知}
> 客户健康度：{score/100，如未知写未知}
> 信息完整度：完整/部分/不足
> 数据覆盖：客户 {已读取/无数据/权限不足/查询失败}；商机 {已读取/无数据/权限不足/未触发查询/查询失败}；联系人 {已读取/无数据/权限不足/未触发查询/查询失败}；销售记录 {已读取/无数据/权限不足/未触发查询/查询失败}；需求 {已读取/无数据/权限不足/未触发查询/查询失败}；互动问题 {已读取/无数据/权限不足/未触发查询/查询失败}；日程 {已读取/无数据/权限不足/未触发查询/查询失败}；会议 {已读取/无数据/权限不足/未触发查询/查询失败}；待办/任务 {已读取/无数据/权限不足/未触发查询/查询失败}；现场拜访 {已读取/无数据/权限不足/未触发查询/查询失败}；竞品明细 {已读取/无数据/权限不足/未触发查询/查询失败}；合同 {已读取/无数据/权限不足/未触发查询/查询失败}；订单/回款 {已读取/无数据/权限不足/未触发查询/查询失败}；外部情报 {已读取/无数据/权限不足/未触发查询/查询失败}。
> 置信度说明：确认 / 推断 / 未知
> 下次建议更新：{date/触发条件，如未知写“下次关键互动后”}

## 🧭 结论摘要

**一句话结论：** {客户当前处于什么状态；最大的机会或风险是什么；置信度是什么}

| 摘要项 | 结论 | 置信度 |
| --- | --- | --- |
| 客户状态 |  | 确认/推断/未知 |
| 主要机会 |  | 确认/推断/未知 |
| 主要风险 |  | 确认/推断/未知 |
| 决策链判断 |  | 确认/推断/未知 |
| 关系温度 |  | 确认/推断/未知 |
| 最大信息缺口 |  | 确认/推断/未知 |

**优先关注：**
- {最多 3 条，只写客户认知或后续关注点}

## 🪪 客户画像
## 👥 决策圈图谱
## 📅 博弈时间线
## 💼 项目背景与商机全貌
## 🎯 痛点地图
## ⚔️ 竞品全貌
## ❓ 开放问题
## ✅ 后续建议动作
## 🧾 历史合作、财务与客户健康（仅 --full）

> 📎 参考来源：CRM 客户/商机/联系人/互动记录、合同/订单/回款/CSM 记录、必要外部情报及行业/竞品参考。正文中的“推断/未知”仅用于客户认知梳理，需后续核对。
```
