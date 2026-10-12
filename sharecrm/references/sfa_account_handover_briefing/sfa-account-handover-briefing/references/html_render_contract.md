# 团队交接简报 HTML 渲染契约

生成团队交接简报 HTML 时读取本文件。HTML 必须由 `scripts/render_handover_briefing.py` 渲染，不得由 agent 手写整份 HTML、重新设计 DOM，或把正式模板只当作视觉参考。

## 执行顺序

1. 按 R01-R09 生成 Markdown 使用的结构化事实。
2. 将同一组事实写入 `handover_facts_bundle.json`。
3. 执行：

```bash
python3 scripts/render_handover_briefing.py \
  --input <handover_facts_bundle.json> \
  --output <客户名称>_团队交接简报_<日期>.html
```

渲染器会读取 `assets/templates/handover.html`、自动内联 `assets/styles/handover.css`，并调用 `scripts/validate_handover_briefing.py`。校验失败时不得交付 HTML。需要拦截旧客户残留时，可重复传入 `--forbid-text "<旧内容>"`。

移动端顶部信息栏必须使用自适应高度：客户名称、商机状态、金额和交接判断均允许自然换行，不得互相挤压成单字竖排。顶部信息栏不固定吸顶，分页标签独立吸顶，避免长内容改变头部高度后产生遮挡。

## 顶层结构

```json
{
  "metadata": {},
  "alert": {},
  "quality_signals": {},
  "executive_summary": {},
  "sections": {},
  "data_coverage": {},
  "references": {}
}
```

## metadata

| 字段 | 含义 |
| --- | --- |
| `customer_name` | 客户名称，必填 |
| `mode` | `standard` 或 `full`，默认 `standard` |
| `handover_date` | 交接日期 |
| `data_updated_at` | CRM 和外部情报的数据截止时间 |
| `original_owner` | 原负责人，未知时明确写未知 |
| `new_owner` | 接手人，未知时明确写未知 |
| `handover_status` | 待交接、交接中、已交接、未知 |
| `handover_reason` | 交接原因 |
| `handover_urgency` | 高、中、低、未知 |
| `memory_status` | 内部判断字段，完整、部分、不足或未知；不得渲染到 HTML |
| `customer_state` | 当前客户状态 |
| `opportunity_status` | 当前主要商机或合作状态 |
| `opportunity_amount` | 已确认金额；不可估算 |
| `industry_or_segment` | 行业、赛道或规模 |
| `coach_summary` | 内部支持者或关键关系摘要 |
| `handover_score_label` | 定性交接状态，不得填写无计算规则的数字分 |

## alert 与 quality_signals

```json
{
  "alert": {
    "title": "第一条交接提醒",
    "body": "提醒所依据的事实和影响",
    "action": "接手人第一动作"
  },
  "quality_signals": {
    "information": {"status": "完整|部分|不足|未知", "note": "证据说明"},
    "relationship": {"status": "升温|稳定|降温|未知", "note": "证据说明"},
    "competition": {"status": "高|中|低|未知", "note": "证据说明"}
  }
}
```

三个质量信号只展示定性状态，不接受任意百分制。关系温度如有证据，可在 `sections.relationship.overall_temperature` 使用 R04 定义的 `-5` 到 `+5`；无证据时保持未知。

## executive_summary

```json
{
  "executive_summary": {
    "one_sentence_conclusion": "客户当前状态 + 最大历史包袱 + 接手优先级",
    "items": [
      {"label": "当前客户状态", "value": "结论", "confidence": "确认|推断|未知"}
    ]
  }
}
```

摘要最多 6 项，建议覆盖当前状态、交接原因、最大风险、最关键关系、待兑现承诺和第一周重点。

## sections

```json
{
  "sections": {
    "handover_context": [
      {"label": "交接背景", "value": "已确认事实"}
    ],
    "account_profile": [
      {"label": "行业", "value": "制造业", "full_width": false}
    ],
    "relationship": {
      "overall_label": "信任 / 中立 / 冷淡 / 未知",
      "overall_temperature": 3,
      "key_people": [
        {
          "name": "姓名",
          "title": "职务",
          "role": "EB|TB|UX|Coach|Gatekeeper|Influencer|Unknown",
          "temperature": 3,
          "attitude": "支持|中立|反对|未知",
          "contact_note": "联络注意",
          "confidence": "确认|推断|未知"
        }
      ]
    },
    "commitments": [
      {
        "title": "承诺内容",
        "party": "我方|客户|内部协同",
        "due_date": "日期或未知",
        "status": "未开始|进行中|已兑现|部分兑现|逾期|未知",
        "action": "接手处理",
        "confidence": "确认|推断|未知"
      }
    ],
    "timeline": [
      {"date": "日期", "title": "事件", "description": "过程", "impact": "交接影响", "confidence": "确认|推断|未知"}
    ],
    "competition": {
      "status_label": "竞争状态",
      "note": "接手提醒",
      "items": [
        {"name": "竞品", "entered_at": "时间", "stage": "阶段", "strategy": "应对", "result": "结果", "confidence": "确认|推断|未知"}
      ]
    },
    "risks": [
      {"severity": "高|中|低|未知", "title": "风险", "description": "事实与影响", "action": "接手处理", "confidence": "确认|推断|未知"}
    ],
    "first_week_actions": [
      {"priority": "高|中|低", "action": "动作", "why": "原因", "owner": "负责人", "completion_standard": "完成标准"}
    ],
    "handover_gaps": [
      {"title": "缺口", "impact": "影响", "action": "补齐方式"}
    ],
    "handover_notes": [
      {"label": "备注标题", "content": "接手人必须知道的内容"}
    ],
    "financial_health": {
      "scope_label": "完整财务口径",
      "items": [
        {"label": "应收金额", "value": "金额或未知", "note": "接手含义"}
      ]
    }
  }
}
```

`standard` 不展示历史合作、财务与客户健康卡片；重大回款、交付或流失风险仍须进入摘要和风险。`full` 才展示 `financial_health`。

桌面与移动端使用相同的 `account_profile`、`relationship.key_people`、`timeline` 和 `competition.items`，不得分别生成两套事实。

页签固定为“概览、历程与竞争、交接备注、数据质量”。数据质量作为独立最后页签承载数据覆盖、参考来源、置信度说明和数据截止，不在每个业务页签重复展示；业务结论本身仍保留必要的单条置信度。

## data_coverage

使用中文业务标签作为 key，只允许：`已读取 / 无数据 / 权限不足 / 未触发查询 / 查询失败`。

默认覆盖：客户、商机、联系人、跟进记录、待办/任务、需求/问题、会议、竞品明细、合同/订单/回款、外部情报。内部记忆读取状态不得进入用户可见区域；用户可见区域也不得出现对象 apiName、字段 apiName、CLI 命令或 query plan。

## references

```json
{
  "references": {
    "sources": ["CRM 客户、商机、联系人和跟进记录", "原负责人交接信息", "必要外部情报"],
    "confidence_note": "确认：有直接证据；推断：有行为证据；未知：当前证据不足。"
  }
}
```

来源只展示中文业务类别，不展示内部记忆能力或读取状态。渲染器会将意外出现的对象 apiName 替换为中文标签，校验器仍会对最终可见文本进行二次拦截。
