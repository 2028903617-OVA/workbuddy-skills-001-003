# 客户产业链分析独立报告数据模型

本文定义 `account-chain-analysis` 独立调用时生成完整产业链分析结果所使用的数据模型。它必须沿用客户尽调主报告的数据模型骨架和公共子结构，只在 `chainContext` 内补充产业链专题独立输出需要的扩展字段。

编排调用模式的返回结构见 `references/schemas/insight-data-model.md`。

## 顶层结构

```jsonc
{
  "meta": {},
  "crmContext": {},
  "chainContext": {},
  "sellerRelevantSignals": [],
  "gaps": [],
  "evidence": []
}
```

## 同构原则

- 本模型是客户尽调主报告 `report-data-model.md` 的产业链专题子集，不另起一套顶层字段体系。
- 顶层只保留产业链专题独立报告需要的主报告公共入口：`meta`、`crmContext`、`chainContext`、`sellerRelevantSignals`、`gaps`、`evidence`。
- 客户身份、用户场景、卖方画像、覆盖情况统一放入 `meta`。
- CRM 锚定、CRM 字段依据、内部覆盖和内部样本统一放入 `crmContext`。
- 链位、价值角色、结构、关系、关键依赖和业务含义统一放入 `chainContext`。
- 所有重要判断通过 `evidenceRefs` 回链顶层 `evidence`。
- 独立报告比编排调用结果更完整，但仍只围绕目标客户展开，不输出拓客动作、二跳扩展、触达路径、销售话术、跟进节奏或作战计划。

## 共享子结构

### gap

```jsonc
{
  "topic": "chain | crm | enterprise | seller_context | other",
  "question": "",
  "whyItMatters": "",
  "suggestedVerification": "",
  "blocking": false
}
```

### relation

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

## meta

```jsonc
{
  "reportMode": "standalone",
  "targetCompany": {
    "inputName": "",
    "legalName": "",
    "creditCode": "",
    "industry": "",
    "registrationStatus": ""
  },
  "userContext": {
    "role": "sales | manager | presales | customer_success | risk | unknown",
    "scenario": "",
    "focus": []
  },
  "sellerContext": {
    "loadStatus": "available | partial | missing",
    "mode": "config | user_input | crm_context | generic | missing",
    "source": "config_cli | user_input | crm_page_context | crm_product_summary | crm_won_deal_summary | unknown",
    "inferredKeywords": [],
    "relevanceRules": [],
    "confidence": "high | medium | low",
    "downgradeReason": "",
    "summaryForInternalReasoning": "内部推理摘要，不进入报告正文"
  },
  "retrievalCoverage": {
    "crm": "available | partial | missing | not_queried",
    "enterpriseData": "available | partial | missing",
    "publicChainData": "available | partial | missing",
    "industryTemplate": "matched | generic | missing"
  },
  "generatedAt": "ISO8601"
}
```

## crmContext

```jsonc
{
  "loadStatus": "available | partial | missing",
  "queryMode": "preset_objects | related_objects | user_requested_custom_object | not_queried",
  "objectDescribeDriven": true,
  "account": {
    "matched": true,
    "recordId": "",
    "businessSummary": "",
    "fieldBasis": []
  },
  "chainAnchor": {
    "anchorStatus": "confirmed | inferred | user_provided | missing",
    "customerRoleHint": "",
    "channelModeHint": "",
    "groupModeHint": "",
    "procurementModeHint": "",
    "fieldBasis": [],
    "downgradeReason": "",
    "evidenceRefs": []
  },
  "internalSamples": [],
  "downgradeReason": "",
  "evidenceRefs": []
}
```

字段说明：

- `account` 沿用主报告 `crmContext.account` 的业务摘要口径。
- `chainAnchor` 用于记录 CRM 内部可观察到的链路角色、渠道模式、集团化经营或采购归口线索，但不作为独立顶层结构。
- `internalSamples` 只保留业务摘要，例如涉及集团客户、渠道伙伴、区域子公司、项目交付模式的活动、商机、合同或订单摘要。
- 正文不得展示对象 API 名、字段 API 名、内部记录 ID 或敏感字段原值。

## chainContext

```jsonc
{
  "summary": "",
  "chainPosition": "",
  "valueRole": "",
  "chainStructure": {
    "methodology": "",
    "valueFlow": "",
    "upstreamSegment": "",
    "midstreamSegment": "",
    "downstreamSegment": "",
    "basis": "",
    "confidence": "high | medium | low",
    "evidenceRefs": []
  },
  "upstream": [],
  "downstream": [],
  "channels": [],
  "ecosystem": [],
  "groupCapitalRelations": [],
  "keyDependencies": [],
  "businessImplications": [],
  "gaps": [],
  "evidenceRefs": []
}
```

字段说明：

- `summary`、`chainPosition`、`valueRole`、`upstream`、`downstream`、`channels`、`ecosystem`、`groupCapitalRelations`、`keyDependencies`、`businessImplications`、`gaps`、`evidenceRefs` 与主报告 `chainContext` 保持同名同义。
- `chainStructure` 是独立报告需要的专题扩展，用于承载价值流向、方法论和上中下游结构概括。
- `groupCapitalRelations` 只记录会影响控制、采购归口、区域覆盖或组织复杂度的关系。
- 没有证据的维度不强行进入正式关系或依赖字段，进入 `gaps`。

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

## sellerRelevantSignals

```jsonc
[
  {
    "signalType": "opportunity | risk | relationship | supplier_competitor | other",
    "customerFact": "",
    "whyRelevant": "",
    "judgment": "",
    "evidenceRefs": []
  }
]
```

## evidence

```jsonc
[
  {
    "id": "C-S1",
    "sourceType": "structured_enterprise_data | crm_record | company_official | public_web | public_news | annual_report | exchange_announcement | model_inference",
    "displaySource": "",
    "sourceUrl": "",
    "date": "",
    "supports": "",
    "internalTrace": {}
  }
]
```

## 写入原则

- 先形成本数据模型，再按 `references/output-contract.md` 渲染独立文字或 HTML 结果。
- `chainContext.summary` 对应独立报告“产业链情报结论”的主体说明。
- `chainContext.chainStructure`、`chainPosition`、`valueRole` 对应独立报告“客户产业链位置”的基础骨架。
- `upstream`、`downstream`、`channels`、`ecosystem`、`groupCapitalRelations` 对应关系章节。
- `keyDependencies` 和 `businessImplications` 对应“关键依赖与业务含义”。
- 与发问方业务相关的客户侧信号写入 `sellerRelevantSignals`，不直接展示卖方画像原文。
- 证据不足、主体不清、来源冲突或关系方向不稳的内容写入 `chainContext.gaps` 或顶层 `gaps`。
