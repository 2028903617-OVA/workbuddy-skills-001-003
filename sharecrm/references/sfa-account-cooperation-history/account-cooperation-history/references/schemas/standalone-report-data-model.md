# 客户合作历史分析独立报告数据模型

本文定义 `account-cooperation-history` 独立调用时生成完整合作历史分析结果所使用的数据模型。它必须沿用客户尽调主报告的数据模型骨架和公共子结构，只在 `cooperationContext` 与 `cooperationHistory` 内补充合作专题独立输出需要的扩展字段。

编排调用模式的返回结构见 `references/schemas/insight-data-model.md`。

## 顶层结构

```jsonc
{
  "meta": {},
  "crmContext": {},
  "cooperationContext": {},
  "cooperationHistory": [],
  "sellerRelevantSignals": [],
  "gaps": [],
  "evidence": []
}
```

## 同构原则

- 本模型是客户尽调主报告 `report-data-model.md` 的合作专题子集，不另起一套顶层字段体系。
- 顶层只保留合作专题独立报告需要的主报告公共入口：`meta`、`crmContext`、`cooperationContext`、`cooperationHistory`、`sellerRelevantSignals`、`gaps`、`evidence`。
- 客户身份、用户场景、卖方画像、覆盖情况统一放入 `meta`。
- CRM 内部锚定、内部接触、合同订单回款等摘要统一放入 `crmContext`。
- 合作摘要、供应商/竞品信号、内部历史摘要和合作影响统一放入 `cooperationContext`。
- 公开合作、招投标、采购、中标、官网案例等事件统一放入 `cooperationHistory`。
- 所有重要判断通过 `evidenceRefs` 回链顶层 `evidence`。
- 独立报告比编排调用结果更完整，但仍只围绕目标客户展开，不输出投标策略、采购推进、触达路径、销售话术、跟进节奏或作战计划。

## 共享子结构

### gap

```jsonc
{
  "topic": "cooperation | crm | enterprise | seller_context | other",
  "question": "",
  "whyItMatters": "",
  "suggestedVerification": "",
  "blocking": false
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
    "publicCooperationData": "available | partial | missing",
    "sellerContext": "available | partial | missing"
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
  "contacts": [],
  "opportunities": [],
  "contracts": [],
  "orders": [],
  "payments": [],
  "activities": [],
  "downgradeReason": "",
  "evidenceRefs": []
}
```

字段说明：

- `crmContext` 尽量沿用主报告口径，避免合作专题单独发明新的内部记录字段体系。
- 联系人、商机、合同、订单、回款、活动只保留能解释合作关系、合作深度、失败经历、项目阶段或履约背景的业务摘要。
- 正文不得展示对象 API 名、字段 API 名、内部记录 ID、敏感金额原值或不适合外显的内部备注。

## cooperationContext

```jsonc
{
  "summary": "",
  "timeWindow": "",
  "cooperationCoverage": "complete | partial | limited",
  "partnerIndustryDistribution": [],
  "partnerMarketDistribution": [],
  "supplierAndCompetitorSignals": [],
  "internalHistory": [],
  "businessImplications": [],
  "gaps": [],
  "evidenceRefs": []
}
```

字段说明：

- `summary`、`supplierAndCompetitorSignals`、`internalHistory`、`businessImplications`、`gaps`、`evidenceRefs` 与主报告 `cooperationContext` 保持同名同义。
- `timeWindow` 和 `cooperationCoverage` 是合作专题独立报告扩展，用于解释时间范围和公开证据覆盖度。
- `partnerIndustryDistribution` 是可选扩展字段，用于在结构化信息充分时表达合作对象行业分布。
- `partnerMarketDistribution` 是可选扩展字段，用于在结构化信息充分时表达合作对象区域 / 市场分布。
- 没有证据的供应商/竞品判断不进入正式信号字段，进入 `gaps`。

## cooperationHistory

```jsonc
[
  {
    "date": "",
    "partner": "",
    "partnerType": "customer | supplier | ecosystem | project_party | related_company | competitor | internal_record | unknown",
    "cooperationType": "strategic_cooperation | project | bidding | procurement | winning_bid | case | contract | internal_contact | other",
    "content": "",
    "businessArea": "",
    "relationStrength": "high | medium | low | unknown",
    "confidence": "high | medium | low",
    "businessImplication": "",
    "evidenceRefs": []
  }
]
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
    "id": "H-S1",
    "sourceType": "crm_record | company_official | public_web | public_news | tender | annual_report | exchange_announcement | model_inference",
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
- `cooperationContext.summary` 对应独立报告“合作历史情报结论”的主体说明。
- `cooperationHistory` 对应“合作时间线”“合作对象分类分析”“合作业务领域分布”的基础事实层。
- `supplierAndCompetitorSignals`、`internalHistory`、`businessImplications` 对应供应商关系、内部历史和业务含义章节。
- 与发问方业务相关的客户侧合作信号写入 `sellerRelevantSignals`，不直接展示卖方画像原文。
- 证据不足、角色不清、来源冲突或时间窗过旧的内容写入 `cooperationContext.gaps` 或顶层 `gaps`。
