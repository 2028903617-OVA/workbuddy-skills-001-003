# 客户行业分析编排调用数据模型

本文定义 `account-industry-analysis` 在编排调用模式下返回给主报告 Skill 的结构化数据。独立输出模板仍以 `references/output-contract.md` 为准；本模型只服务主报告编排消费。

## 顶层结构

```jsonc
{
  "loadStatus": "available | partial | missing",
  "sourceSkill": "account-industry-analysis",
  "referenceReadStatus": {
    "status": "complete | partial | failed | not_applicable",
    "required": [],
    "read": [],
    "missing": [],
    "downgradeReason": ""
  },
  "targetCustomer": {},
  "summary": "",
  "industryStage": "",
  "industryStageBasis": "",
  "customerPosition": {},
  "judgments": [],
  "businessImplications": [],
  "sellerRelevantSignals": [],
  "evidence": [],
  "gaps": []
}
```

## 字段说明

- `loadStatus`
  标识本次是否形成可被主报告消费的行业结果。
- `sourceSkill`
  固定为 `account-industry-analysis`，用于主报告写入 `topicInsights.industry.sourceSkill`。
- `referenceReadStatus`
  记录编排调用模式下本专题 required/read/missing references。只读取 `SKILL.md` 时必须为 `partial`，不能标记为完整可用。
- `targetCustomer`
  记录目标客户主体锚点，至少包含客户名称；有工商全称、统一社会信用代码或 CRM 记录 ID 时一并保留。
- `summary`
  面向目标客户的行业摘要，不是完整行业研究导语。
- `industryStage`
  行业阶段或行业状态，只保留一个主判断。
- `industryStageBasis`
  支撑行业阶段判断的简短依据。
- `customerPosition`
  客户在行业中的位置、类型、角色或分层。
- `judgments`
  趋势、政策、竞争格局、行业痛点、客户位置等关键判断。
- `businessImplications`
  行业变化对客户经营、需求、风险或相关情报信号的影响。
- `sellerRelevantSignals`
  与发问方业务相关的客户侧行业信号；不得展示卖方画像原文。
- `evidence`
  支撑关键结论的证据列表。
- `gaps`
  会影响关键判断的待核实事项。

## targetCustomer

```jsonc
{
  "inputName": "",
  "legalName": "",
  "creditCode": "",
  "crmRecordId": "",
  "industryAnchor": "",
  "anchorSource": "crm | enterprise_data | public_source | user_input | inferred"
}
```

## customerPosition

```jsonc
{
  "description": "",
  "positionType": "",
  "segment": "",
  "basis": "",
  "businessImplication": "",
  "confidence": "high | medium | low",
  "evidenceRefs": []
}
```

## judgment

```jsonc
{
  "type": "trend | policy | competition | pain_point | position | other",
  "title": "",
  "fact": "",
  "judgment": "",
  "businessImplication": "",
  "confidence": "high | medium | low",
  "evidenceRefs": []
}
```

## businessImplication

```jsonc
{
  "type": "operation | demand | risk | relevance | other",
  "customerFact": "",
  "implication": "",
  "confidence": "high | medium | low",
  "evidenceRefs": []
}
```

## sellerRelevantSignal

```jsonc
{
  "signalType": "opportunity | risk | relationship | other",
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
    "id": "I-E1",
    "sourceType": "crm_record | company_official | public_web | public_news | policy | annual_report | industry_report | model_inference",
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
  "topic": "industry",
  "question": "",
  "whyItMatters": "",
  "suggestedVerification": "",
  "blocking": false
}
```

## 写入主报告规则

- 本模型整体写入 `topicInsights.industry`。
- `summary` 写入 `industryContext.summary`。
- `industryStage` 写入 `industryContext.industryStage`。
- `industryStageBasis` 写入 `industryContext.industryStageBasis`。
- `customerPosition` 写入 `industryContext.customerPosition`。
- `judgments` 按 `type` 拆入 `industryContext.trends`、`industryContext.policies`、`industryContext.majorPlayers`、`industryContext.commonPainPoints` 或 `industryContext.judgments`。
- `businessImplications` 写入 `industryContext.businessImplications`；与发问方相关的部分再写入 `sellerRelevantSignals`。
- `evidence` 归并到主报告顶层 `evidence`，并用 `evidenceRefs` 回链。

## 约束

- 不返回完整行业研究报告、市场容量测算或宏观综述。
- 不返回触达动作、销售话术、跟进节奏、资源投入建议。
- 没有证据的内容不得进入 `summary`、`industryStage`、`customerPosition` 或 `judgments`，只能进入 `gaps`。
