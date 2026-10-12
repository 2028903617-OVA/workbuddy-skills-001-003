# 客户尽调报告中间数据模型

本文定义客户尽调报告的结构化中间数据模型。报告模板只消费本模型中的已有字段，不补写不存在的事实。

## 顶层结构

```jsonc
{
  "meta": {},
  "topicInsights": {},
  "basicProfile": {},
  "ownership": {},
  "businessModel": {},
  "ipProfile": {},
  "industryContext": {},
  "chainContext": {},
  "crmContext": {},
  "operationDynamics": [],
  "publicCompanyFinancials": {},
  "cooperationContext": {},
  "cooperationHistory": [],
  "riskProfile": [],
  "sellerRelevantSignals": [],
  "visuals": [],
  "evidence": []
}
```

## 设计原则

- 本模型是主报告的数据装配层，不是原始取数结果的完整转储。
- 企业情报 CLI、CRM、公开来源和专题 Skill 的结果先归入本模型，再由报告模板消费。
- `topicInsights` 保存专题 Skill 在编排调用模式下返回的结构化结果，用于追溯和调试。
- `industryContext`、`chainContext`、`cooperationContext` 保存主报告最终消费后的字段，用于正式报告渲染。
- 报告模板优先消费主报告上下文字段，不直接消费专题 Skill 的完整独立输出。
- 所有重要判断通过 `evidenceRefs` 回链顶层 `evidence`；不要在多个字段中重复粘贴完整证据文本。

## 共享子结构

以下子结构可在 `topicInsights` 和主报告上下文字段中复用。

### judgment

```jsonc
{
  "type": "trend | policy | competition | pain_point | position | dependency | relationship | supplier_competitor | internal_history | other",
  "title": "",
  "fact": "",
  "judgment": "",
  "businessImplication": "",
  "confidence": "high | medium | low",
  "evidenceRefs": []
}
```

### relation

```jsonc
{
  "relationType": "upstream | downstream | channel | ecosystem | group_capital | supplier | competitor | project_party | internal_record | unknown",
  "objectName": "",
  "objectRole": "",
  "relationNature": "",
  "sourceFact": "",
  "businessImplication": "",
  "confidence": "high | medium | low",
  "evidenceRefs": []
}
```

### gap

```jsonc
{
  "topic": "industry | chain | cooperation | crm | enterprise | risk | other",
  "question": "",
  "whyItMatters": "",
  "suggestedVerification": "",
  "blocking": false
}
```

## meta

```jsonc
{
  "targetCompany": {
    "inputName": "用户输入名称",
    "legalName": "工商全称",
    "creditCode": "统一社会信用代码",
    "aliases": [],
    "stockCode": "",
    "industry": "工商或公开资料行业",
    "registrationStatus": "登记状态",
    "listedStatus": "",
    "entityResolution": {
      "status": "confirmed | ambiguous | failed",
      "basis": "工商全称、信用代码、股票代码、官网、行业、城市等主体确认依据",
      "candidateCount": 0,
      "candidates": [
        {
          "legalName": "",
          "creditCode": "",
          "keyNo": "",
          "no": "",
          "stockCode": "",
          "industry": "",
          "registrationStatus": "",
          "listedStatus": "",
          "matchBasis": "",
          "conflictReason": ""
        }
      ],
      "selectedReason": "",
      "conflictNote": ""
    }
  },
  "userContext": {
    "role": "sales | manager | presales | customer_success | risk | unknown",
    "scenario": "用户业务场景"
  },
  "sellerContext": {
    "loadStatus": "available | partial | missing",
    "mode": "config | user_input | crm_context | generic | missing",
    "source": "config_cli | user_input | crm_page_context | crm_product_summary | crm_won_deal_summary | unknown",
    "configKeys": {
      "service_models": ""
    },
    "inferredKeywords": [],
    "relevanceRules": [],
    "confidence": "high | medium | low",
    "downgradeReason": "",
    "summaryForInternalReasoning": "内部推理摘要，不进入报告正文"
  },
  "retrievalCoverage": {
    "riskProfile": {
      "strategy": "time_window_first | targeted_followup | capped_scan | aggregate_only",
      "status": "sufficient | partial | unknown",
      "timeWindow": "近24-36个月 + 当前未结清记录",
      "sortOrFilter": "未结清、高金额、严重类型优先",
      "pageNum": 1,
      "pageSize": 10,
      "returned": 10,
      "total": 36,
      "hasMore": true,
      "followupReason": "风控场景下首批出现被执行记录，已按近年和未结清状态定向补查",
      "coverageNote": "本次风险判断优先覆盖近三年及当前未结清关键记录，非全部历史明细"
    },
    "crmOpportunities": {
      "strategy": "time_window_first",
      "status": "sufficient | partial | unknown",
      "timeWindow": "当前未关闭商机 + 近12-24个月历史商机/互动",
      "sortOrFilter": "当前推进、最近互动、金额较大、输赢状态明确",
      "returned": 0,
      "total": 0,
      "hasMore": false,
      "coverageNote": ""
    },
    "publicCompanyFinancials": {
      "strategy": "listed_intro_first | company_name_only_first_page | public_source_fallback | numeric_params_verified",
      "status": "sufficient | partial | unavailable | not_applicable",
      "listedEntity": "",
      "sameAsTargetCompany": true,
      "sentParams": {
        "companyName": "",
        "reportYear": "",
        "pageNum": "",
        "pageSize": ""
      },
      "returned": 0,
      "total": 0,
      "firstPageOnly": true,
      "selectedPeriods": [],
      "requestedYear": "",
      "requestedYearCovered": false,
      "downgradeReason": "",
      "coverageNote": ""
    }
  },
  "generatedAt": "ISO8601"
}
```

## topicInsights

`topicInsights` 保存专题 Skill 在编排调用模式下返回的结构化结果。它用于追溯“专题 Skill 返回了什么”，不是报告模板的主要渲染入口。

```jsonc
{
  "industry": {
    "loadStatus": "available | partial | missing | not_called",
    "sourceSkill": "account-industry-analysis",
    "referenceReadStatus": {
      "status": "complete | partial | failed | not_applicable",
      "required": [],
      "read": [],
      "missing": [],
      "downgradeReason": ""
    },
    "summary": "",
    "industryStage": "",
    "customerPosition": "",
    "judgments": [],
    "businessImplications": [],
    "evidenceRefs": [],
    "gaps": []
  },
  "chain": {
    "loadStatus": "available | partial | missing | not_called",
    "sourceSkill": "account-chain-analysis",
    "referenceReadStatus": {
      "status": "complete | partial | failed | not_applicable",
      "required": [],
      "read": [],
      "missing": [],
      "downgradeReason": ""
    },
    "summary": "",
    "chainPosition": "",
    "valueRole": "",
    "relations": [],
    "groupCapital": [],
    "keyDependencies": [],
    "businessImplications": [],
    "evidenceRefs": [],
    "gaps": []
  },
  "cooperation": {
    "loadStatus": "available | partial | missing | not_called",
    "sourceSkill": "account-cooperation-history",
    "referenceReadStatus": {
      "status": "complete | partial | failed | not_applicable",
      "required": [],
      "read": [],
      "missing": [],
      "downgradeReason": ""
    },
    "summary": "",
    "cooperationItems": [],
    "supplierAndCompetitorSignals": [],
    "internalHistory": [],
    "businessImplications": [],
    "evidenceRefs": [],
    "gaps": []
  }
}
```

使用规则：

- `loadStatus=not_called` 表示主报告本次未编排调用该专题 Skill。
- `loadStatus=missing` 表示已尝试调用或取数，但没有形成可消费结果。
- `referenceReadStatus.status=complete` 表示专题 `SKILL.md` 与 `skill-composition.md` 定义的适用最小 reference 集均已读取。
- `referenceReadStatus.status=partial` 表示已读取专题 `SKILL.md`，但存在必读 reference、命中模板或 workflow 步骤未读取/未执行；此时 `loadStatus` 不得标记为完整可用。
- `referenceReadStatus.status=failed` 表示专题不可用、关键 reference 缺失或工具失败，无法形成可消费专题结果。
- `referenceReadStatus.status=not_applicable` 仅用于按允许跳过规则未调用的专题，并必须在 `downgradeReason` 或 `meta.retrievalCoverage` 记录原因。
- `topicInsights` 中的 `evidenceRefs` 只引用顶层 `evidence.id`。
- 主报告生成时，应先把 `topicInsights` 中的结果归并到 `industryContext`、`chainContext`、`cooperationContext` 等正式消费字段，再渲染报告。

## crmContext

```jsonc
{
  "loadStatus": "available | partial | missing",
  "queryMode": "preset_objects | related_objects | user_requested_custom_object | not_queried",
  "objectDescribeDriven": true,
  "account": {
    "matched": true,
    "objectApiName": "AccountObj",
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
  "similarCases": [],
  "customObjects": [],
  "downgradeReason": "",
  "evidenceRefs": []
}
```

## basicProfile

```jsonc
{
  "companyName": "",
  "companyType": "",
  "industry": "",
  "foundedAt": "",
  "registeredCapital": "",
  "address": "",
  "businessScope": "",
  "listedStatus": "",
  "qualifications": []
}
```

## ownership

```jsonc
{
  "shareholders": [],
  "controllers": [],
  "branches": [],
  "investments": [],
  "relatedCompanies": [],
  "businessImplications": []
}
```

## businessModel

```jsonc
{
  "mainBusinesses": [],
  "productsOrServices": [],
  "targetCustomers": [],
  "salesModel": "",
  "deliveryModel": "",
  "operatingComplexity": [],
  "currentBusinessFocus": []
}
```

## ipProfile

```jsonc
{
  "summary": "",
  "patents": [],
  "softwareCopyrights": [],
  "standards": [],
  "trademarks": [],
  "icpRecords": [],
  "rdSignals": [],
  "businessRelevance": "",
  "riskNotes": [],
  "evidenceRefs": []
}
```

消费规则：

- `ipProfile` 用于判断研发能力、技术资产、产品支撑和线上经营痕迹，默认来自 `sharecrm intelligence ip conc` 的 `patentinfoinfo`、`copyrightsoftwareinfo`、`standardinformationinfo`、`trademarkinfo`、`tbicpbaseinfo`。
- 专利、软著、标准、商标和 ICP 需要与主营业务、产品、官网或公告交叉解释；只有数量但无法关联主营业务时，降低研发实力结论强度。
- 知识产权出质来自风险侧 `risk conc:intellectualinfo`，只进入融资、担保或风险补充，不直接写成研发实力。

## industryContext

```jsonc
{
  "summary": "",
  "industryStage": "",
  "industryStageBasis": "",
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
    "evidenceRefs": []
  },
  "judgments": [],
  "businessImplications": [],
  "gaps": [],
  "evidenceRefs": []
}
```

字段说明：

- `summary`：主报告第 5 章使用的客户相关行业摘要。
- `industryStage`：行业阶段或行业状态，只记录与目标客户判断相关的主阶段。
- `industryStageBasis`：支撑行业阶段判断的简短依据。
- `trends`、`policies`、`majorPlayers`、`commonPainPoints`：从行业专题结果拆分后的分类判断，元素可使用 `judgment` 子结构。
- `customerPosition`：客户在行业中的位置，不只记录行业标签。
- `businessImplications`：行业变化对客户经营、需求、风险或相关情报信号的影响。
- `gaps`：仅记录会影响关键判断的待核实事项。

## chainContext

```jsonc
{
  "summary": "",
  "chainPosition": "",
  "valueRole": "",
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

- `summary`：主报告第 6 章使用的产业链与生态关系摘要。
- `chainPosition`：客户在产业链中的主位置，例如上游、中游、下游、平台、渠道、服务商、集成商等。
- `valueRole`：客户在价值流中的角色，例如生产方、集成方、渠道方、交付方、运营方等。
- `upstream`、`downstream`、`channels`、`ecosystem`：按关系类型拆分后的关系列表，元素可使用 `relation` 子结构。
- `groupCapitalRelations`：只记录会影响控制、采购归口、区域覆盖或组织复杂度的集团/资本关系。
- `keyDependencies`：客户对供应、渠道、客户、技术、资质、平台、区域资源等的关键依赖。
- `businessImplications`：产业链关系对客户经营、需求、风险或相关情报信号的影响。
- `gaps`：仅记录会影响链位、关键依赖或关系判断的待核实事项。

## operationDynamics

```jsonc
[
  {
    "signal": "",
    "eventKey": "归一化去重键，内部使用，不展示",
    "title": "",
    "occurredAt": "",
    "sourceName": "",
    "sourceUrl": "",
    "sourceChannel": "news | pingmei | app | forum | blog | weibo | weixin | video | insvideo | tv | announcement | web | cli | other",
    "sourceTools": [
      "sharecrm intelligence market get-news",
      "sharecrm intelligence market search-mentions"
    ],
    "sourceFact": "",
    "businessExplanation": "",
    "impact": "",
    "evidenceRefs": []
  }
]
```

动态去重规则：

- 先把新闻类 CLI、`search-mentions`、上市公告、招投标、风险动态和公开 web 来源放入动态候选池，不直接渲染。
- 优先用规范化 URL 去重：去除协议差异、尾部斜杠、常见跟踪参数后相同，视为同一条。
- URL 缺失或不同但标题规范化后相同，且发布时间在 3 天内、来源名称相同或内容摘要高度相似，视为同一条。
- 标题不同但核心主体、事件类型、对象和时间一致，且内容摘要高度相似，视为同一事件。
- 合并时保留更权威、更近、更完整的 `sourceName/sourceUrl/date/content`；多个来源写入同一条 `evidence` 的 `internalTrace` 或补充来源，不重复生成 `operationDynamics` 条目。
- 同一事件既有结构化 CLI 又有公开网页证据时，报告展示优先使用业务可读、可追溯、可点击的来源；内部 CLI 路径只保留在 `internalTrace`。
- 只有同一事件去重，不合并同一客户在不同日期、不同项目、不同风险事项上的独立动态。

## publicCompanyFinancials

```jsonc
{
  "applicable": true,
  "listedIdentity": "",
  "sameAsTargetCompany": true,
  "stockCode": "",
  "queryMode": "listed_intro | company_name_only_first_page_financial_statements | public_source_fallback | numeric_params_verified",
  "periods": [],
  "revenueSummary": "",
  "profitSummary": "",
  "cashFlowSummary": "",
  "balanceSheetSummary": "",
  "statementCoverage": {
    "incomeStatement": {
      "status": "available | partial | unavailable",
      "selectedPeriod": "",
      "sourceListField": "incomeStatementList",
      "downgradeReason": ""
    },
    "balanceSheet": {
      "status": "available | partial | unavailable",
      "selectedPeriod": "",
      "sourceListField": "balanceSheetList",
      "downgradeReason": ""
    },
    "cashFlowStatement": {
      "status": "available | partial | unavailable",
      "selectedPeriod": "",
      "sourceListField": "cashflowStatementList",
      "downgradeReason": ""
    }
  },
  "keyMetrics": [],
  "businessImplications": [],
  "evidenceRefs": []
}
```

## cooperationContext

```jsonc
{
  "summary": "",
  "supplierAndCompetitorSignals": [],
  "internalHistory": [],
  "businessImplications": [],
  "gaps": [],
  "evidenceRefs": []
}
```

字段说明：

- `summary`：主报告第 9 章使用的合作历史与供应商关系摘要。
- `supplierAndCompetitorSignals`：供应商、竞品、替代关系、合作偏好和进入壁垒信号，元素可使用 `judgment` 或 `relation` 子结构。
- `internalHistory`：CRM 内部历史接触摘要，只保留业务含义，不暴露对象 API 名、内部记录 ID 或敏感字段原值。
- `businessImplications`：合作事实对客户理解、进入壁垒、替换难度、合作窗口、风险判断的影响。
- `gaps`：仅记录会影响长期供应商、竞品占位、关键合作或内部历史判断的待核实事项。

## cooperationHistory

```jsonc
[
  {
    "date": "",
    "partner": "",
    "partnerType": "customer | supplier | ecosystem | project_party | related_company | competitor | internal_record | unknown",
    "cooperationType": "",
    "content": "",
    "businessArea": "",
    "relationStrength": "high | medium | low | unknown",
    "confidence": "high | medium | low",
    "businessImplication": "",
    "evidenceRefs": []
  }
]
```

## riskProfile

```jsonc
[
  {
    "riskType": "",
    "riskFact": "",
    "businessImpact": "",
    "evidenceRefs": []
  }
]
```

## sellerRelevantSignals

```jsonc
[
  {
    "signalType": "opportunity | risk | relationship | supplier_competitor",
    "customerFact": "",
    "whyRelevant": "",
    "judgment": "",
    "evidenceRefs": []
  }
]
```

当前 CLI 1.1.8 兜底规则：

- 三表默认只传 `companyName`，不传 `reportYear/pageNum/pageSize`。
- 三表返回的 `total/pageNum/pageSize/isLastPage` 仅用于覆盖说明；在数值参数未验证修复前，不依赖这些字段继续翻页。
- 用户指定年份时，先在第一页列表中按 `reportYear` 筛选；如果未覆盖目标年份，设置 `requestedYearCovered=false`，在 `downgradeReason/coverageNote` 记录“内部 CLI 仅稳定返回第一页，目标年份未覆盖”，并使用公开年报、公告或交易所来源补证。
- 不得把第一页缺失写成该年份不存在财报。

## visuals

HTML 报告的可视化模块必须消费 `visuals` 或由本模型中已有结构化字段直接生成，不得为作图临时创造评分、占比、排序或趋势。

```jsonc
[
  {
    "id": "",
    "title": "",
    "chartType": "topic_coverage | ownership_bar | chain_relation_map | operation_timeline | cooperation_timeline | risk_distribution | financial_period_table | evidence_source_mix | product_scene_heatmap | customer_type_distribution | bidding_trend_combo | china_map | province_distribution_map | geo_distribution | sankey | relationship_graph | radar | treemap | funnel | qualitative_matrix | metric_cards | fallback_table",
    "question": "",
    "dataSourceFields": [],
    "data": [],
    "mapConfig": {
      "mapName": "",
      "mapDataSource": "inline_geojson | inline_svg | trusted_external_geojson | not_applicable",
      "mapDataUrl": "",
      "registeredBy": "echarts.registerMap",
      "primaryRenderMode": "choropleth_map | point_scatter | fallback",
      "requiresChoropleth": false,
      "pointLayerRole": "none | supplemental_city_points",
      "regionNameField": "province | city | district | custom",
      "regionNameNormalization": "省份名称与地图 GeoJSON properties.name 的匹配口径",
      "normalizationRules": [
        "河北 -> 河北省",
        "山西 -> 山西省",
        "辽宁 -> 辽宁省",
        "吉林 -> 吉林省",
        "黑龙江 -> 黑龙江省",
        "江苏 -> 江苏省",
        "浙江 -> 浙江省",
        "安徽 -> 安徽省",
        "福建 -> 福建省",
        "江西 -> 江西省",
        "山东 -> 山东省",
        "河南 -> 河南省",
        "湖北 -> 湖北省",
        "湖南 -> 湖南省",
        "广东 -> 广东省",
        "海南 -> 海南省",
        "四川 -> 四川省",
        "贵州 -> 贵州省",
        "云南 -> 云南省",
        "陕西 -> 陕西省",
        "甘肃 -> 甘肃省",
        "青海 -> 青海省",
        "北京 -> 北京市",
        "上海 -> 上海市",
        "天津 -> 天津市",
        "重庆 -> 重庆市",
        "广西 -> 广西壮族自治区",
        "内蒙古 -> 内蒙古自治区",
        "西藏 -> 西藏自治区",
        "宁夏 -> 宁夏回族自治区",
        "新疆 -> 新疆维吾尔自治区",
        "香港 -> 香港特别行政区",
        "澳门 -> 澳门特别行政区"
      ],
      "normalizedRegions": [],
      "matchedRegions": [],
      "unmatchedRegions": [],
      "renderCheck": {
        "mapRegistered": false,
        "seriesMapMatched": false,
        "hasCanvasOrSvg": false,
        "hasMatchedBusinessRegion": false,
        "hasChoroplethSeries": false
      },
      "downgradeReason": "",
      "fallbackRequired": true
    },
    "fallbackTable": [],
    "coverageNote": "",
    "derivedByModel": false,
    "derivationNote": "",
    "evidenceRefs": []
  }
]
```

使用规则：

- 每个可视化必须回答一个明确问题，例如“专题覆盖是否完整”“近年经营动态集中在哪些类型”“风险类型如何分布”。
- 数据优先来自本模型已有字段，如 `topicInsights`、`ownership`、`businessModel`、`industryContext`、`chainContext`、`operationDynamics`、`cooperationHistory`、`riskProfile`、`publicCompanyFinancials`、`sellerRelevantSignals`、`evidence`。
- `industryContext` 与 `businessModel.productsOrServices` 信息充足且存在清晰二维维度时，优先考虑 `product_scene_heatmap` 或 `qualitative_matrix`，表达产品/服务、应用场景、行业趋势和机会强弱之间的关系。热力图的行列标签必须可读；定性等级必须设置 `derivedByModel=true`、填写 `derivationNote`，并在图例或说明中展示等级含义，不得伪装成真实评分、排名或市场份额。
- `chainContext` 信息充足且存在方向性关系时，优先考虑 `sankey` 或 `chain_relation_map`，表达上游资源、客户能力、渠道和下游场景的流向。Sankey 节点和边必须来自已有字段、证据或明确模型归纳；真实 `value` 只能来自金额、次数、数量等证据，不要为了 Sankey 临时创造关系或流量数值。如果只有定性关系但需要布局值，必须说明数值仅用于布局，不代表金额、份额或真实流量；方向关系不足时使用分层关系卡、链路表或 `fallback_table`。
- `ownership.branches`、`ownership.investments`、`cooperationHistory` 或其他字段中存在省份/城市等地理字段时，区域分布优先考虑 `china_map`、`province_distribution_map` 或 `geo_distribution`，默认设置 `requiresChoropleth=true`、`primaryRenderMode=choropleth_map`。地图类图表必须填写 `mapConfig`，说明地图名、地图数据来源、地区名称匹配口径和 fallback；ECharts 5 不内置中国地图数据，生成 HTML 时必须先加载公司内部公网可访问地区边界 GeoJSON、平台内置地图数据或内嵌 GeoJSON/SVG，并 `echarts.registerMap`。公司内部地区边界地址记录到 `mapDataUrl`：`https://a9.fspage.com/FSR/weex/sfa/resource/map_boundary.json`；不得把 GeoJSON 全文写入数据模型或报告正文。
- 若区域分布表达对象是分支机构，地图 `data` 必须按省级行政区聚合分支机构数量；不得仅用 `1/0` 表示是否覆盖后再渲染成数量着色图。分支机构总量在 100 家以内时，应先分页取全量明细再聚合；无法取全时不要输出“首批地图”，应降级为表格并说明取数限制。对应章节还应同步提供分支机构明细表或 `fallbackTable`，至少保留名称、状态、成立时间和所在地区。
- 地图类图表的 `data` 应使用与地图数据口径一致的结构化地区数据，例如 `{ "name": "广东省", "value": 18, "items": [] }`，并通过 `series.type='map'` 渲染区域着色。`scatter` / `effectScatter` 只能作为总部、工厂或项目城市的补充点位层，`pointLayerRole` 应标为 `supplemental_city_points`；不得只输出圆点地图替代区域分布。如果源数据只有城市，应先映射到省级/直辖市/自治区/特别行政区，再填入 `normalizedRegions`、`matchedRegions` 和 `unmatchedRegions`；不得只用简称导致地图底图可见但业务区域不着色。常见归一示例保持少量即可，例如：`北京 -> 北京市`、`广东 -> 广东省`、`广西 -> 广西壮族自治区`。
- `industryContext`、`operationDynamics`、`evidence` 或相关结构化字段足以支撑行业事件类型、竞争格局、公开动态来源构成或行业影响判断时，行业章节至少生成一个行业图表，例如 `qualitative_matrix`、`product_scene_heatmap`、`radar`、`relationship_graph`、分组条形图或趋势组合图的 `fallback_table` 对应表达；不得因为整份报告已有其他图表而让行业章节长期缺少可视化。
- `treemap` 可用于构成占比或类别面积比较，但不作为地理区域分布的默认图表；区域分布无法稳定渲染地图时，使用省份排行、区域分组卡或 `fallback_table`。
- 允许基于已有字段生成定性归纳型可视化，例如强/中/弱覆盖、已证实/推断/待核实、机会/风险关注等级；此时必须设置 `derivedByModel=true` 并填写 `derivationNote`，说明归纳口径。
- 图表数据不足或类别边界不清时，使用 `fallback_table`、时间轴、关系卡片或摘要块，不输出空白图表。
- 每个图表必须有 `fallbackTable` 或文字结论，保证 ECharts 或脚本不可用时仍可读。
- 不展示 CLI 参数、CRM 对象 API 名、内部记录 ID 或 `internalTrace`。
- 不要把模型归纳等级伪装成真实统计值、市场份额、真实强度或客观评分；如 ECharts 需要数值编码，应在图例或说明中展示原始等级含义。

## evidence

```jsonc
[
  {
    "id": "E1",
    "sourceType": "structured_enterprise_data | crm_record | company_official | public_web | public_news | tender | annual_report | regulator | exchange_announcement | topic_skill | model_inference",
    "displaySource": "给报告读者看的来源名称，如工商基础信息、商机记录、企业官网、交易所公告",
    "sourceUrl": "公开来源 URL；内部结构化数据和 CRM 记录可为空",
    "date": "",
    "supports": "",
    "internalTrace": {
      "tool": "内部工具或 CLI 路径，仅内部追溯，不展示",
      "mergedTools": [],
      "mergedSourceIds": [],
      "objectApiName": "CRM 对象 API 名，仅内部追溯",
      "recordId": "CRM 记录 ID，仅内部追溯",
      "query": "查询主体或条件摘要，仅内部追溯"
    }
  }
]
```
