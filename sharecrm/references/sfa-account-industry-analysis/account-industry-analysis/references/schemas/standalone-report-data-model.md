# 客户行业分析独立报告数据模型

本文定义 `account-industry-analysis` 独立调用时生成完整行业分析结果所使用的数据模型。它必须沿用客户尽调主报告的数据模型骨架和公共子结构，只在 `industryContext` 内补充行业专题独立输出需要的扩展字段。

编排调用模式的返回结构见 `references/schemas/insight-data-model.md`。

## 顶层结构

```jsonc
{
  "meta": {},
  "crmContext": {},
  "industryContext": {},
  "sellerRelevantSignals": [],
  "gaps": [],
  "evidence": []
}
```

## 同构原则

- 本模型是客户尽调主报告 `report-data-model.md` 的行业专题子集，不另起一套独立字段体系。
- 顶层只保留行业专题独立报告需要的主报告公共入口：`meta`、`crmContext`、`industryContext`、`sellerRelevantSignals`、`gaps`、`evidence`。
- 客户身份、用户场景、卖方画像、覆盖情况统一放入 `meta`，不再新增 `targetCustomer`、`sellerContext` 等平行顶层字段。
- CRM 锚定、CRM 字段依据和内部样本统一放入 `crmContext`，不再新增 `crmAnchor` 顶层字段。
- 行业结论、客户行业位置、行业变化影响、行业背景、趋势事件和行业模板口径统一放入 `industryContext`，不再新增 `industryConclusion`、`customerPosition`、`industryImpact`、`trendAndEvents`、`industryBackground`、`industryTemplate` 顶层字段。
- `sellerRelevantSignals`、`gaps`、`evidence` 沿用主报告公共结构；所有重要判断通过 `evidenceRefs` 回链顶层 `evidence`。
- 独立报告比编排调用结果更完整，但仍只围绕目标客户展开，不输出销售动作、触达路径、销售话术、跟进节奏或作战计划。

## 共享子结构

以下子结构与客户尽调主报告保持一致。

### judgment

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

### gap

```jsonc
{
  "topic": "industry | crm | enterprise | seller_context | other",
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
    "externalIndustryData": "available | partial | missing",
    "sellerContext": "available | partial | missing",
    "industryTemplate": "matched | generic | missing"
  },
  "generatedAt": "ISO8601"
}
```

使用规则：

- `meta.targetCompany` 与主报告 `meta.targetCompany` 保持同构。
- `meta.sellerContext.summaryForInternalReasoning` 仅用于内部推理，不进入报告正文。
- 独立报告正文只能展示基于卖方画像推理出的客户侧行业信号，不能展示卖方画像原文。

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
  "industryAnchor": {
    "anchorStatus": "confirmed | inferred | user_provided | missing",
    "industryName": "",
    "industryLevel1": "",
    "industryLevel2": "",
    "track": "",
    "region": "",
    "customerTier": "",
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

- `account` 沿用主报告 `crmContext.account` 的业务摘要口径；报告正文不得展示对象 API 名、字段 API 名、内部记录 ID 或敏感字段原值。
- `industryAnchor` 是行业专题对 CRM 锚定结果的扩展，放在 `crmContext` 内，不作为独立顶层结构。
- `internalSamples` 只保留业务摘要，例如同行业成交样本、输单样本、相关商机摘要、客户声音摘要。
- CRM 快速检索未命中不等于 CRM 未覆盖，必须保留降级原因。

## industryContext

```jsonc
{
  "summary": "",
  "industryStage": "growth | stable | contraction | transformation | regulation_intensified | unknown",
  "industryStageLabel": "增长 | 稳定 | 收缩 | 转型 | 监管加强 | 未确认",
  "industryStageBasis": "",
  "oneSentenceImplication": "",
  "trends": [],
  "policies": [],
  "majorPlayers": [],
  "commonPainPoints": [],
  "customerPosition": {
    "description": "",
    "positionType": "",
    "segment": "",
    "basis": "",
    "businessImplication": "",
    "confidence": "high | medium | low",
    "evidenceRefs": []
  },
  "businessImplications": [],
  "trendAndEvents": {
    "trends": [],
    "events": []
  },
  "templateContext": {
    "templateStatus": "matched | generic",
    "templateName": "logistics | manufacturing | saas | government | generic",
    "routeBasis": [],
    "matchedDimensions": {
      "industry": "",
      "businessModel": "",
      "scale": "",
      "chainPosition": "",
      "region": ""
    },
    "downgradeReason": ""
  },
  "gaps": [],
  "evidenceRefs": []
}
```

字段说明：

- `summary`、`industryStage`、`industryStageBasis`、`trends`、`policies`、`majorPlayers`、`commonPainPoints`、`customerPosition`、`businessImplications`、`gaps`、`evidenceRefs` 与主报告 `industryContext` 保持同名同义。
- `oneSentenceImplication` 用于独立报告“行业情报结论”的一句话结论。
- `businessImplications` 是独立报告“行业变化对客户的影响”的核心数据，不再新增 `industryImpact` 顶层字段。
- `trendAndEvents` 是独立报告需要的行业趋势和事件明细，作为 `industryContext` 的专题扩展。
- `templateContext` 是行业模板路由口径，作为 `industryContext` 的专题扩展。
- 无证据的维度不进入 `businessImplications` 或判断字段，进入 `gaps`。

## businessImplication

```jsonc
{
  "type": "operation | demand | risk | relevance | other",
  "dimension": "growth | regulation | competition | cycle | operating_pressure | other",
  "customerFact": "",
  "industryChange": "",
  "implication": "",
  "factOrInference": "fact | inferred",
  "confidence": "high | medium | low",
  "evidenceRefs": []
}
```

使用规则：

- 每条必须回答“这对目标客户意味着什么”。
- 对客户无实质影响的维度可以保留一条 `type=other` 的简短判断，不强行展开。
- 没有证据或只能提出问题的内容写入 `gaps`。

## trendAndEvents

```jsonc
{
  "trends": [
    {
      "direction": "up | flat | down | turning | unknown",
      "timeWindow": "",
      "basis": "",
      "customerImpact": "",
      "factOrInference": "fact | inferred",
      "evidenceRefs": []
    }
  ],
  "events": [
    {
      "time": "",
      "event": "",
      "customerImpact": "",
      "source": "",
      "evidenceRefs": []
    }
  ]
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
    "id": "E1",
    "sourceType": "structured_enterprise_data | crm_record | crm_original_text | company_official | public_web | public_news | policy | annual_report | industry_report | regulator | topic_skill | model_inference",
    "displaySource": "",
    "sourceUrl": "",
    "date": "",
    "supports": "",
    "internalTrace": {
      "tool": "",
      "objectApiName": "",
      "recordId": "",
      "query": ""
    }
  }
]
```

## 独立报告渲染规则

- Markdown 和 HTML 只能消费本模型已有字段，不直接拼接原始 CLI 输出、网页文本或 CRM 记录。
- `行业情报结论` 消费 `industryContext.summary`、`industryContext.industryStage`、`industryContext.industryStageBasis`、`industryContext.oneSentenceImplication`、`crmContext.industryAnchor`、`industryContext.templateContext`。
- `客户行业位置` 消费 `industryContext.customerPosition`。
- `行业变化对客户的影响` 消费 `industryContext.businessImplications`。
- `行业背景摘要` 消费 `industryContext.trends`、`industryContext.policies`、`industryContext.majorPlayers`、`industryContext.commonPainPoints`、`industryContext.trendAndEvents`。
- `与发问方业务相关的行业信号` 消费 `sellerRelevantSignals`。
- `待核实事项` 优先消费 `industryContext.gaps`，必要时合并顶层 `gaps`。
- `证据来源` 消费顶层 `evidence`。
