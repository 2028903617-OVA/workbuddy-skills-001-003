# Search Mentions CLI

本文定义客户尽调报告中 `sharecrm intelligence market search-mentions` 的复杂参数调用说明。它不是独立业务流程文档，只补充 `enterprise-cli-map.md` 中公开动态/舆情提及这一行 CLI 的参数校验、字段映射和降级边界；业务取数顺序、证据消费和报告裁剪仍以主流程、输出契约和数据模型为准。

## Command

使用：

```bash
sharecrm intelligence market search-mentions --data '{"keyword":"<普通搜索词>"}'
```

该命令用于补充公开动态和舆情提及，可与新闻类 CLI 结果共同进入动态候选池；最终输出前按 `report-data-model.md` 的动态去重规则合并。

## Core Rules

1. `keyword` 必填，发送给智慧星光时映射为 `must_kw`。
2. `keyword` 只支持普通搜索词，长度不超过 100 字符；不支持高级表达式、`should_kw` 或 `not_kw`。
3. 默认平台为 `zhihuixingguang`。
4. 默认时间窗为最近不超过 7 天；显式时间跨度超过 7 天时，按 `endTime - 7 天` 截断 `startTime`。
5. `time_filter` 固定为 `ctime`。
6. 当前实现不启用 `wildcard`、`sort_after` 或高级搜索表达式。
7. 空值参数不要传；列表参数传入前先去空、去重。
8. CLI 报错、返回空或字段不足时，继续使用公开 web 来源补查；不得把空结果写成公开世界中不存在相关动态。
9. `search-mentions` 结果可与新闻类 CLI、上市公告、公开 web 来源并行采集；同一事件只在最终报告中展示一次。
10. 即使当前后端接受超过 7 天的时间窗，调用方也必须按本文件主动截断，不依赖后端容错。
11. 返回字段以实际响应为准；实测记录可能返回 `gtime`、`replyCount`、`visitCount` 等字段，而不是严格的 `ctime`、`reply_count` 下划线形态。
12. 返回 `total` 不一定代表全库命中总量；消费时优先以 `articles.length` 作为本次返回条数，覆盖范围另写入 `meta.retrievalCoverage`。

## Parameters

| 参数 | 规则 | 智慧星光映射/说明 |
|:---|:---|:---|
| `keyword` | 必填；普通搜索词；长度不超过 100 字符；不支持高级表达式、`should_kw`、`not_kw` | `must_kw` |
| `source` | 可选；缺省全量；显式传入只允许 `news,pingmei,app,forum,blog,weibo,weixin,video,insvideo,tv`；去空、去重 | 来源类型 |
| `startTime` / `endTime` | 可选；必须是 10 位秒级时间戳；若传入必须满足 `startTime < endTime`；缺省最近不超过 7 天；跨度超过 7 天时截断 | 时间范围，`time_filter=ctime` |
| `page` | 可选；缺省或 `<1` 按 `1`；最大 `30`，超过按 `30` 发送 | 页码 |
| `size` | 可选；缺省或 `<1` 使用配置默认值；最大 `100`，超过按 `100` 发送 | 每页条数 |
| `platform` | 可选；缺省 `zhihuixingguang` | 平台 |
| `sortField` | 可选；默认 `ctime`；只允许 `ctime,reply_count,repost_count,like_count,gather.gtime,gather.stime` | 排序字段 |
| `sortOrder` | 可选；默认 `desc`；只允许 `asc,desc` | 排序方向 |
| `matchFields` | 可选；缺省 `title,content,retweeted.title,retweeted.content`；显式值只允许 `title,content,retweeted.title,retweeted.content,translation.content,ocr,place` | 匹配字段 |
| `sentiments` | 可选；只允许 `1,2,0,9,-1,-2,-5,-6` | 情感筛选 |
| `siteDomain` | 可选；最多 50 个；空值忽略、重复值去重；精准 input 匹配 | `gather.site_domain` |
| `siteName` | 可选；去首尾空格；精准 input 匹配 | `gather.site_name` |
| `userName` | 可选；去首尾空格；精准 input 匹配 | `user.name` |
| `userProvince` / `userCity` / `userDistrict` | 可选 | 地域来源字段为 `user` |
| `analysisPlaceProvince` / `analysisPlaceCity` / `analysisPlaceDistrict` | 可选 | 地域来源字段为 `analysis.place` |
| `findAddressProvince` / `findAddressCity` / `findAddressDistrict` | 可选 | 地域来源字段为 `analysis.find_address` |
| `ipProvince` / `ipCity` / `ipDistrict` | 可选 | 地域来源字段为 `analysis.user.analysis_ip_region` |

## Region Rules

智慧星光只有一个共享 `region.location`。多个地域来源同时传入时，省、市、区必须表示同一地点。

处理规则：

1. 只传入一个地域来源时，按该来源映射 `region.location`。
2. 传入多个地域来源时，先比较省、市、区是否一致。
3. 多个地域来源一致时，只发送一个共享地域条件。
4. 多个地域来源冲突时，不调用 CLI，返回 400 风格错误，提示用户地域筛选冲突。

示例：

- `userProvince=广东省` 与 `ipProvince=广东省` 可合并。
- `userCity=深圳市` 与 `analysisPlaceCity=广州市` 冲突，应返回 400。

## Recommended Usage

默认客户尽调报告可使用：

```json
{
  "keyword": "<工商全称>",
  "platform": "zhihuixingguang",
  "sortField": "ctime",
  "sortOrder": "desc",
  "page": 1
}
```

## Time Window Algorithm

单次调用前先归一化时间窗：

1. 如果用户未给时间范围，设置 `endTime=当前秒级时间戳`，`startTime=endTime - 7天 + 1秒`。
2. 如果用户给了 `startTime/endTime`，先校验二者都是 10 位秒级时间戳，且 `startTime < endTime`。
3. 如果 `endTime - startTime` 超过 7 天，单次调用按 `startTime = endTime - 7天 + 1秒` 截断后发送。
4. 如果业务问题需要覆盖更长口径，不要发送超过 7 天的大窗口；从 `endTime` 向前拆成多个不超过 7 天的窗口逐段查询。
5. 每段查询都应记录实际发送的 `startTime/endTime/page/size/sortField/sortOrder`，并将返回量写入 `meta.retrievalCoverage`。

按场景调整：

- 近期经营动态：使用默认来源和默认 7 天窗口；如报告需要更长口径，分段查询或补充新闻类 CLI、上市公告、公开 web 来源，不把单次 CLI 默认窗口当作 6-12 个月全量覆盖。
- 负面舆情/风险线索：传入允许的负向 `sentiments`，并结合风险 CLI、监管、法院或新闻来源补证。
- 指定媒体或站点：优先用 `source`、`siteDomain` 或 `siteName` 精准筛选。
- 指定地域：只在用户明确要求地域口径或报告问题依赖地域时传入地域参数。

## Evidence Handling

进入报告的数据必须保留：

- 查询关键词。
- 时间窗和排序口径。
- 来源类型或站点。
- 标题、发布时间、来源、链接或可追溯标识。
- 该条动态支撑的报告判断。

字段归一化建议：

- 标题：优先 `title`。
- 正文/摘要：优先 `content`；过长时只抽取与客户判断相关的摘要，不把长正文整段放入报告。
- 链接：优先 `url`。
- 来源：优先 `siteName`、`channel`、`publisher.siteName`。
- 域名：优先 `siteDomain`。
- 发布时间：优先 `ctime`；如果只有 `gtime`，只能标注为采集时间或内部时间，不要伪装成发布时间。
- 互动量：兼容 `reply_count/repost_count/like_count` 和 `replyCount/repostCount/likeCount/visitCount`。
- 账号：优先 `user.name`、`publisher.name`、`user.nickname`。
- 情感：使用 `sentiment`，按原始值保留，必要时再映射为正/中/负/争议。

内部可记录完整 CLI 路径和参数；最终报告只展示业务可读来源，不展示技术参数、平台内部字段或原始查询 JSON。

## Empty Result Handling

空结果可能返回完整分页结构，也可能只返回：

```json
{"articles":[]}
```

处理规则：

1. 将 `articles` 为空视为本次窗口无候选记录，不视为该客户不存在公开动态。
2. 如果用户问题需要更长口径，继续按 7 天窗口向前分段查询，或补充新闻类 CLI、上市公告、招投标、风险动态、公开 web 来源。
3. 分段查询应记录每段 `startTime/endTime` 和返回量，写入 `meta.retrievalCoverage`。
4. 所有分段和多来源结果进入动态候选池，最终按 `report-data-model.md` 去重后再输出。
5. 多来源仍无证据时，该动态类信息默认不输出，不编造“没有相关动态”。

## Merge With Other Dynamic Sources

将 `search-mentions` 返回记录先放入动态候选池，不直接渲染到报告。候选池可同时包含：

- `sharecrm intelligence market get-news` 等新闻动态 CLI。
- `sharecrm intelligence listed action-listed-company-announcement` 等公告 CLI。
- 公开 web 来源补查结果。
- 招投标或风险 CLI 中与近期动态直接相关的记录。

最终进入 `operationDynamics` 和 `evidence` 前，按 `report-data-model.md` 的动态去重规则合并。合并后优先保留更权威、更近、更完整的来源字段；被合并来源写入同一条证据的内部追溯或补充来源，不重复生成报告条目。
