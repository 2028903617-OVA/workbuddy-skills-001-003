# 客户产业链分析编排调用数据模型

本文定义 `account-chain-analysis` 在编排调用模式下返回给主报告 Skill 的结构化数据。独立输出模板仍以 `references/output-contract.md` 为准；本模型只服务主报告编排消费。

## 顶层结构

```jsonc
{
  "loadStatus": "available | partial | missing",
  "sourceSkill": "account-chain-analysis",
  "referenceReadStatus": {
    "status": "complete | partial | failed | not_applicable",
    "required": [],
    "read": [],
    "missing": [],
    "downgradeReason": ""
  },
  "targetCustomer": {},
  "summary": "",
  "chainPosition": "",
  "valueRole": "",
  "relations": [],
  "groupCapital": [],
  "keyDependencies": [],
  "businessImplications": [],
  "sellerRelevantSignals": [],
  "evidence": [],
  "gaps": []
}
```

## 字段说明

- `loadStatus`
  标识本次是否形成可被主报告消费的产业链结果。
- `sourceSkill`
  固定为 `account-chain-analysis`，用于主报告写入 `topicInsights.chain.sourceSkill`。
- `referenceReadStatus`
  记录编排调用模式下本专题 required/read/missing references。只读取 `SKILL.md` 时必须为 `partial`，不能标记为完整可用。
- `targetCustomer`
  记录目标客户主体锚点，至少包含客户名称；有工商全称、统一社会信用代码或 CRM 记录 ID 时一并保留。
- `summary`
  面向目标客户的产业链摘要，不是完整产业链图谱说明。
- `chainPosition`
  客户在产业链中的主位置，例如上游、中游、下游、平台、渠道、服务商、集成商等。
- `valueRole`
  客户在价值流中的角色，例如生产方、集成方、渠道方、交付方、运营方等。
- `relations`
  上游、下游、渠道、生态等关系摘要。
- `groupCapital`
  会影响控制、采购归口、区域覆盖或组织复杂度的集团/资本关系。
- `keyDependencies`
  客户对供应、渠道、客户、技术、资质、平台、区域资源等的关键依赖。
- `businessImplications`
  产业链关系对客户经营、需求、风险或相关情报信号的影响。
- `sellerRelevantSignals`
  与发问方业务相关的客户侧产业链信号；不得展示卖方画像原文。
- `evidence`
  支撑关键结论的证据列表。
- `gaps`
  会影响链位、依赖或关系判断的待核实事项。

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

## relation

```jsonc
{
  "relationType": "upstream | downstream | channel | ecosystem | group_capital | unknown",
  "objectName": "",
  "objectRole": "",
  "relationNature": "",
  "sourceFact": "",
  "businessImplication": "",
  "confidence": "high | medium | low",
  "evidenceRefs": []
}
```

## keyDependency

```jsonc
{
  "dependencyType": "supply | customer | channel | platform | technology | qualification | region | capital | other",
  "dependencyFact": "",
  "impact": "",
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
    "id": "C-E1",
    "sourceType": "structured_enterprise_data | crm_record | company_official | public_web | public_news | annual_report | model_inference",
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
  "topic": "chain",
  "question": "",
  "whyItMatters": "",
  "suggestedVerification": "",
  "blocking": false
}
```

## 写入主报告规则

- 本模型整体写入 `topicInsights.chain`。
- `summary` 写入 `chainContext.summary`。
- `chainPosition` 写入 `chainContext.chainPosition`。
- `valueRole` 写入 `chainContext.valueRole`。
- `relations` 按 `relationType` 拆入 `chainContext.upstream`、`chainContext.downstream`、`chainContext.channels`、`chainContext.ecosystem`。
- `groupCapital` 写入 `chainContext.groupCapitalRelations`；涉及控制、采购归口、区域覆盖或组织复杂度时，同步进入 `ownership.businessImplications`。
- `keyDependencies` 写入 `chainContext.keyDependencies`。
- `businessImplications` 写入 `chainContext.businessImplications`；与发问方相关的部分再写入 `sellerRelevantSignals`。
- `evidence` 归并到主报告顶层 `evidence`，并用 `evidenceRefs` 回链。

## 约束

- 不返回拓客对象清单、二跳扩展、候选池、CRM 查重结果或 P0/P1/P2 定档。
- 不返回线索创建、客户挂接、销售动作建议。
- 集团/资本关系不能自动等同于上下游供应链关系；没有证据时只能进入 `gaps`。
