# 客户合作历史分析编排调用数据模型

本文定义 `account-cooperation-history` 在编排调用模式下返回给主报告 Skill 的结构化数据。独立输出模板仍以 `references/output-contract.md` 为准；本模型只服务主报告编排消费。

## 顶层结构

```jsonc
{
  "loadStatus": "available | partial | missing",
  "sourceSkill": "account-cooperation-history",
  "referenceReadStatus": {
    "status": "complete | partial | failed | not_applicable",
    "required": [],
    "read": [],
    "missing": [],
    "downgradeReason": ""
  },
  "targetCustomer": {},
  "summary": "",
  "cooperationItems": [],
  "supplierAndCompetitorSignals": [],
  "internalHistory": [],
  "businessImplications": [],
  "sellerRelevantSignals": [],
  "evidence": [],
  "gaps": []
}
```

## 字段说明

- `loadStatus`
  标识本次是否形成可被主报告消费的合作历史结果。
- `sourceSkill`
  固定为 `account-cooperation-history`，用于主报告写入 `topicInsights.cooperation.sourceSkill`。
- `referenceReadStatus`
  记录编排调用模式下本专题 required/read/missing references。只读取 `SKILL.md` 时必须为 `partial`，不能标记为完整可用。
- `targetCustomer`
  记录目标客户主体锚点，至少包含客户名称；有工商全称、统一社会信用代码或 CRM 记录 ID 时一并保留。
- `summary`
  面向目标客户的合作历史摘要，不是完整合作报告导语。
- `cooperationItems`
  公开合作、招投标、采购、中标、项目参与、官网案例、公告合作等合作事项。
- `supplierAndCompetitorSignals`
  供应商、竞品、替代关系、合作偏好、进入壁垒等客户侧信号。
- `internalHistory`
  CRM 内部历史接触摘要，只保留业务含义，不暴露对象 API 名、内部记录 ID 或敏感字段原值。
- `businessImplications`
  合作事实对客户理解、进入壁垒、替换难度、合作窗口或风险判断的影响。
- `sellerRelevantSignals`
  与发问方业务相关的客户侧合作信号；不得展示卖方画像原文。
- `evidence`
  支撑关键结论的证据列表。
- `gaps`
  会影响长期供应商、竞品占位、关键合作或内部历史判断的待核实事项。

## targetCustomer

```jsonc
{
  "inputName": "",
  "legalName": "",
  "creditCode": "",
  "crmRecordId": "",
  "anchorSource": "crm | enterprise_data | public_source | user_input | inferred"
}
```

## cooperationItem

```jsonc
{
  "date": "",
  "partner": "",
  "partnerType": "customer | supplier | ecosystem | project_party | related_company | competitor | internal_record | unknown",
  "cooperationType": "strategic_cooperation | project | bidding | procurement | winning_bid | case | contract | internal_contact | other",
  "content": "",
  "businessArea": "",
  "relationStrength": "high | medium | low | unknown",
  "businessImplication": "",
  "confidence": "high | medium | low",
  "evidenceRefs": []
}
```

## supplierAndCompetitorSignal

```jsonc
{
  "signalType": "supplier | competitor | substitute | cooperation_preference | entry_barrier | project_signal | other",
  "relatedParty": "",
  "sourceFact": "",
  "judgment": "",
  "businessImplication": "",
  "confidence": "high | medium | low",
  "evidenceRefs": []
}
```

## internalHistoryItem

```jsonc
{
  "date": "",
  "recordType": "activity | opportunity | contract | order | payment | contact | failure_reason | other",
  "businessSummary": "",
  "result": "",
  "impactOnCurrentJudgment": "",
  "confidence": "high | medium | low",
  "evidenceRefs": []
}
```

## businessImplication

```jsonc
{
  "type": "operation | demand | risk | relationship | relevance | other",
  "customerFact": "",
  "implication": "",
  "confidence": "high | medium | low",
  "evidenceRefs": []
}
```

## sellerRelevantSignal

```jsonc
{
  "signalType": "opportunity | risk | relationship | supplier_competitor | other",
  "customerFact": "",
  "whyRelevant": "",
  "judgment": "",
  "confidence": "high | medium | low",
  "evidenceRefs": []
}
```

## evidence

```jsonc
[
  {
    "id": "H-E1",
    "sourceType": "crm_record | company_official | public_web | public_news | tender | annual_report | exchange_announcement | model_inference",
    "displaySource": "",
    "sourceUrl": "",
    "date": "",
    "supports": "",
    "internalTrace": {}
  }
]
```

## gap

```jsonc
{
  "topic": "cooperation",
  "question": "",
  "whyItMatters": "",
  "suggestedVerification": "",
  "blocking": false
}
```

## 写入主报告规则

- 本模型整体写入 `topicInsights.cooperation`。
- `summary` 写入 `cooperationContext.summary`。
- `cooperationItems` 写入 `cooperationHistory[]`。
- `supplierAndCompetitorSignals` 写入 `cooperationContext.supplierAndCompetitorSignals`；与发问方相关的部分再写入 `sellerRelevantSignals`。
- `internalHistory` 写入 `cooperationContext.internalHistory`，并按来源映射到 `crmContext.activities`、`crmContext.opportunities`、`crmContext.contracts`、`crmContext.orders` 或 `crmContext.payments` 的业务摘要。
- `businessImplications` 写入 `cooperationContext.businessImplications`，必要时同步到对应 `cooperationHistory[].businessImplication`。
- `evidence` 归并到主报告顶层 `evidence`，并用 `evidenceRefs` 回链。

## 约束

- 招投标、采购、中标和项目参与事件只作为合作历史证据域，不输出投标策略或采购推进方案。
- 不返回 CRM 写入建议、新建商机/线索/联系人建议。
- 不返回触达路径、销售话术、跟进节奏、作战计划或资源投入建议。
- 供应商和竞品关系必须有证据；仅凭名称无法判断时进入 `gaps`。
