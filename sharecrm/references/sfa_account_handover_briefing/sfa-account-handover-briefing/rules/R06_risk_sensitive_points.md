# R06 风险与敏感点

## 目标

整理接手人必须知道的风险、敏感点和不能踩的坑。该规则关注“接手后如何不断档、不误伤关系、不重复历史错误”。

## 触发条件

完成 R01-R05 后始终执行。即使没有明确风险，也必须输出“暂无明确高风险记录”并列出需要核对的风险项。

## 输入来源

- R01 交接背景中的交接紧急度和客户记忆状态。
- R03 博弈编年中的转折点、未兑现承诺、交付/回款/投诉事件。
- R04 关系温度与关键人地图。
- R05 承诺台账。
- CRM `ActiveRecordObj`、`CompetitiveLinesObj`、合同、订单、回款、CSM 预警、流失原因。
- Memory 中的风险与敏感点、关键人关系卡、关键博弈事件。
- `references/industry_benchmarks.md`，仅用于形成待核对风险假设。

## 风险类型

| 类型 | 说明 |
| --- | --- |
| relationship | 关系风险，如 Coach 降温、Gatekeeper 阻碍、EB 未触达 |
| commitment | 承诺风险，如我方逾期、客户承诺未兑现 |
| competitor | 竞品风险，如竞品 POC、报价、历史输单 |
| budget | 预算/审批风险 |
| delivery | 交付/实施/服务风险 |
| payment | 回款/应收风险 |
| churn | 流失/不续约风险 |
| political | 客户内部政治风险 |
| compliance | 合规/安全/审计风险 |
| data_gap | 交接信息缺口导致的风险 |

## 输出契约

```yaml
r06_risk_sensitive_points:
  risks:
    - risk_id:
      type: relationship|commitment|competitor|budget|delivery|payment|churn|political|compliance|data_gap
      risk:
      severity: high|medium|low|unknown
      evidence:
      source:
      affected_people:
        - name:
      business_impact:
      receiver_do:
      receiver_do_not:
      needs_original_ae_explanation: true|false|unknown
      confidence: confirmed|inferred|unknown
  sensitive_points:
    - point:
      why_sensitive:
      do_not:
      safer_wording_or_path:
      confidence: confirmed|inferred|unknown
  first_week_watchlist:
    - item:
      reason:
      suggested_owner:
  data_gaps:
    - gap
```

## 分级规则

| 严重度 | 判断标准 |
| --- | --- |
| high | 可能导致客户流失、商机失败、关系破裂、投诉升级、合同/回款风险 |
| medium | 会影响推进节奏、接手信任、关键人关系或交付体验 |
| low | 需要注意但短期不会改变项目结果 |
| unknown | 信息不足，需原 AE 或相关角色补充 |

## 分析规则

- 风险必须有证据；行业假设只能进入 `first_week_watchlist` 或 `data_gaps`。
- 每个高风险必须写清楚接手人“应该做”和“不要做”。
- 客户内部政治不能凭职位脑补，必须有 Memory、CRM 或用户明确输入支撑。
- 交付、回款、CSM 预警和流失原因要如实写，不要为了交接好看而弱化。
- 风险和敏感点要服务接手人，不写泛泛的销售建议。
- 不输出“今天必须守住”“今日行动”等见客前语言。

## 结构化文本输出

```markdown
## 6. 风险与敏感点

### 高风险项
| 风险 | 类型 | 严重度 | 证据 | 影响 | 接手人应该做 | 绝对不要 |
| --- | --- | --- | --- | --- | --- | --- |
|  | 关系/承诺/竞品/预算/交付/回款/流失/内部政治/合规/信息缺口 | 高/中/低/未知 |  |  |  |  |

### 敏感点
| 敏感点 | 为什么敏感 | 不能做 | 更稳妥的路径 |
| --- | --- | --- | --- |
|  |  |  |  |

### 接手第一周观察清单
| 事项 | 为什么要看 | 建议负责人 |
| --- | --- | --- |
|  |  | 原AE/接手人/CSM/售前/实施/财务 |

### 风险缺口
- {缺少原 AE 解释、客户健康、回款、竞品、预算审批或关系证据等信息}
```
