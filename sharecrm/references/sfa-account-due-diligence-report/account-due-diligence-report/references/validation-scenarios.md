# 客户尽调报告回归验证场景

本文用于修改或验收 `account-due-diligence-report` 时做内部回归检查，不作为报告正文输出。

## 1. 简称误命中

输入：

- 用户输入某公司简称，工商基础信息命中一个名称相近但行业明显不符的非目标主体；上下文同时提到上市身份、股票代码、官网或主营业务关键词。

期望：

- 不直接采用工商基础信息中名称相近但锚点冲突的主体。
- 继续使用上市公司简介、股票代码、行业/业务关键词、官网或公开来源确认目标上市主体或真实签约主体。
- `meta.targetCompany.entityResolution` 记录候选冲突和最终选择依据。

## 2. 上市财务年份参数

输入：

- 目标主体为上市公司，用户要求看最近一年经营财务。

期望：

- 先调用上市公司简介确认股票代码和上市主体。
- 利润表、资产负债表、现金流量表默认只传 `companyName`。
- 从第一页返回列表中按 `reportYear/endDate/reportDateType/isAudit` 筛选最近年度和必要的最近季度。
- 如果用户指定年份未在第一页覆盖，必须记录覆盖不足并转公开年报、公告或交易所来源补证，不得断言该年份没有财报。
- 当前 CLI 1.1.8 未验证修复前，不传 `reportYear/pageNum/pageSize`；如误传后出现 schema 校验错误，只记录一次降级，不在 `--data`、显式 flag、字符串/数字年份之间反复试错。

## 3. search-mentions 空结果

输入：

- 用户要求查询近 30 天公开动态。

期望：

- 不发送超过 7 天的大窗口。
- 按不超过 7 天的窗口分段查询；每段记录 `startTime/endTime/page/size` 和返回量。
- 空结果只表示该窗口未命中，不写成公开世界不存在相关动态。
- 必要时补充新闻 CLI、上市公告、公开 web 来源。

## 4. 专题 Skill 编排

输入：

- 用户要求完整客户尽调报告或客户详情页报告。

期望：

- 默认编排调用行业分析、产业链分析、合作历史三个专题 Skill。
- 主报告在专题编排前先读取 `references/skill-composition.md`。
- 三个专题 Skill 均读取各自 `minimumReferenceSet` 中适用 reference，且均包含各自的 `references/enterprise-cli-map.md`；行业分析还必须读取 `_router.md` 命中的行业模板。
- `topicInsights.industry.referenceReadStatus`、`topicInsights.chain.referenceReadStatus`、`topicInsights.cooperation.referenceReadStatus` 均记录 `required/read/missing/status/downgradeReason`。
- 如果执行日志显示某专题只读取了 `SKILL.md`，该专题必须为 `loadStatus=partial` 且 `referenceReadStatus.status=partial`；最终质量自检不得写成专题编排全部通过。
- 未调用或无有效结果时，写入 `topicInsights.<topic>.loadStatus` 和 `meta.retrievalCoverage`，不得静默跳过。

## 5. HTML 展示

输入：

- 需要生成正式 HTML 报告。

期望：

- 目录为悬浮目录，目录项只包含实际渲染章节。
- 封面与正文 section 明显区分，允许深色/品牌色/渐变背景、白字标题、subtitle、meta chips。
- 结构化信息充足时，至少生成 2-4 个可视化模块；不要只生成一个保守柱状图或饼图。
- 允许使用热力图、Sankey、关系网络图、组合图、矩阵图等复杂图表。
- 允许使用 emoji / Unicode 图标强化摘要块、业务卡片和风险/机会信号。
- ECharts 不可用时，仍有 CSS 时间轴、关系卡片、矩阵、财务期间表或表格增强降级。
- 没有空白图表容器；模型归纳型图表必须标注归纳口径，不把归纳等级伪装成原始统计值。

## 6. 摘要卡片响应式布局

输入：

- 需要生成正式 HTML 报告，概览摘要包含 4 张结论卡：“客户是谁 / 客户做什么 / 当前业务重点 / CRM 或合作状态”。

期望：

- 桌面端或常见 CRM iframe 宽度下使用两列网格，形成 2x2；不出现第一行 3 张、第二行 1 张。
- 窄屏或移动端自动单列。
- 不固定卡片高度；长文本通过内容摘要控制长度，不靠固定高度裁切或制造大空白。
- KPI 短数字卡可继续使用自适应多列，但不能把结论卡和 KPI 卡混用同一套会产生 3+1 的 `auto-fit` 规则。

## 7. 区域分布地图

输入：

- 目标企业有分支机构、子公司、项目或客户的省份/城市字段，需要展示区域分布。

期望：

- 优先使用 ECharts 中国地图、省级地图或地理分布图的区域着色表达地理覆盖；同时保留省份排行、区域分组或表格 fallback。
- 如使用 ECharts 地图，HTML 中必须加载可信开源/开放 GeoJSON、平台内置地图数据或内嵌合法 GeoJSON/SVG，并在设置图表前调用 `echarts.registerMap`；`series.map` 与注册的 `mapName` 一致。外部开源/开放 GeoJSON 地址应记录到 `mapConfig.mapDataUrl`，不得把 GeoJSON 全文写入文档。
- `visuals.chartType` 使用 `china_map`、`province_distribution_map` 或 `geo_distribution`，并填写 `mapConfig.mapName`、`mapDataSource`、`mapDataUrl`、`primaryRenderMode`、`requiresChoropleth`、`regionNameField`、`regionNameNormalization` 和 `fallbackRequired`。
- 区域分布地图必须包含 `series.type='map'` 的区域着色层；`scatter` / `effectScatter` 只能叠加展示总部、工厂或项目城市，不能单独替代区域着色图。
- 如果源数据是城市列表，必须先归一到地图数据使用的省级/直辖市/自治区/特别行政区完整名称；例如普通省份、直辖市、自治区和特别行政区均应与 GeoJSON/SVG 的地区名称一致。
- 地图自检必须确认业务数据地区已命中并着色；只有灰色底图、空 canvas、地图轮廓或圆点图层时，不得判定为区域分布地图成功。
- 地图数据不可用、地图注册失败、ECharts 依赖不可用或地区名称无法匹配时，不保留空白地图容器，改用省份排行、区域卡片或 fallback table。
- 如果区域分布只来自首批分页数据，必须在 `coverageNote` 说明覆盖范围，不把首批样本写成全量地理分布。
- Treemap 只能作为构成占比图，不作为“区域分布”的默认表达。
