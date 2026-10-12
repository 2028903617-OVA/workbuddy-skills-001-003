# R03 痛点识别与优先级

## 目标

提取并排序客户个性化痛点，把最高优先级痛点转化为可在会议现场验证的问题或场景。本规则产出见客就绪度所需的 `business_pain` 和 `pain_points` 字段。

## 触发条件

只要存在跟进记录、商机备注、会议上下文、memory 或公开线索，就执行。若没有客户个性化痛点，返回低置信度假设和验证问题。

## 证据等级

| 等级 | 含义 | 用法 |
| --- | --- | --- |
| E1 | 客户直接表达，有原话或明确记录 | 可作为主切入点 |
| E2 | 从客户行为推断 | 作为假设，需现场验证 |
| E3 | 从公开/财务线索推断 | 谨慎提及，先验证 |
| E4 | 只有行业通用假设 | 不得作为主切入点 |

## 产品匹配度

| 等级 | 含义 |
| --- | --- |
| P1 | 纷享销客核心能力可直接解决 |
| P2 | 可部分解决，或需要组合方案 |
| P3 | 间接相关，只适合用于探需 |
| P0 | 不属于纷享销客适配痛点，不要强行关联 |

## 提取契约

先返回以下结构化内容：

```yaml
r03_pain_points:
  business_pain: true|false
  top_pain:
    pain:
    evidence_level: E1|E2|E3|E4
    product_fit: P1|P2|P3|P0
    source:
    last_mentioned:
    customer_words:
    concrete_scene:
    validation_question:
    success_standard:
  pain_points:
    - pain:
      evidence: E1|E2|E3|E4
      product_fit: P1|P2|P3|P0
      last_mentioned:
      source:
      trend: active|weakening|resolved|unknown
      priority_reason:
  must_have:
    known: true|false
    items:
      - requirement:
        source:
        can_we_meet: yes|no|unknown
  missing_fields:
    - field_name
  risks:
    - risk:
      source:
      severity: fatal|major|minor
```

## 排序规则

按以下顺序排序痛点：

1. 证据强度：E1 > E2 > E3 > E4。
2. 时效性：30 天内 > 31-90 天 > 91-180 天 > 更早。
3. 产品匹配度：P1 > P2 > P3 > P0。
4. 今日参会人：由今日参会人负责或关心的痛点优先。

## 具体场景要求

最高优先级痛点必须包含：

- CRM 或客户原话里的具体业务场景，或
- 明确标注的假设，以及可现场验证的问题。

错误示例：

```markdown
客户痛点是提升服务效率。
```

正确示例：

```markdown
推断：服务工程师外出后，总部看不到工单进度。
验证问题：您现在最想知道的是工程师到了没有、修到哪一步，还是客户是否确认完成？
```

## Markdown 摘要

```markdown
### 痛点
- 首选痛点：{top_pain} | 证据：{E-level/source}
- 具体场景：{scene_or_hypothesis}
- 今天验证问题：{validation_question}
- 必选条件：{must_have_or_unknown}
```

如果全部痛点都只是 E3/E4，今天会议目标应偏向探需，而不是讲方案。
