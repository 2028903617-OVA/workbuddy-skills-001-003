# 技能路由索引（9 个已沉淀纷享销客技能）

> 用户级技能目录：`~/.workbuddy/skills/<name>/`（每技能一个独立文件夹）
> 本册做「问题 → 技能」路由；各技能本身独立，可单独拷贝分发（配合品牌子集包）。

## 路由表

| 用户说/问 | 加载技能 | 品牌归属 | 说明 |
|---|---|---|---|
| 「写/改纷享销客自定义函数」「计划任务/流程后动作/前验证/范围规则」 | `fxiaoke-apl-function` | 通用 | APL(Groovy) 编写参考、Fx.object API 签名、本组织字段 code 表、两个可复用函数模板、11 条高频坑 |
| 「函数写好了想先自查」「模拟纷享验证」 | `fxiaoke-apl-testground` | 通用 | 本地标准 Groovy 复刻 APL 运行时（5 大命名空间），逻辑断言 + lint 预检（D13/D14/D18 沙箱禁令），粘进纷享前先自查 |
| 「做导入模板」「把目标导入人员表」「批量更新人员指标/状态」 | `fxiaoke-person-import-template` | 通用 | 人员对象导入模板（更新模式）：字段映射、金额单位换算、新旧口径合并、离职停用、必填核对 |
| 销售记录发布相关 | `fxiaoke-sales-record-publish` | 通用 | 销售记录发布流程 |
| 「fs-server 连不上」「SSE 直连」「查询被截断」 | `fxiaoke-sse-client` | 通用 | fs-server MCP 稳健 SSE 直连客户端 + 查询避坑（单查询 50 条硬上限 + offset） |
| 「生成/重新生成联单周报」「上周集团内部联单」 | `group-co-order-report` | 集团/多品牌 | 周报生成器：按公司归类主文件（品牌 Sheet、人员卡号、付款公司映射）+ 门店品牌子文件（部门小计）+ 部门带单费汇总 |
| 「考核口径确认表」 | `kpi-criteria-confirm-doc` | 通用(可定制) | 生成可打印 A4 考核口径确认表 |
| 「乾鑫 N 月考核金额表」 | `qianxin-kpi-amount` | 乾鑫 | 从三源文件（上月模板/本月基础表/本月人员表）生成乾鑫格力事业部月度考核金额表 |
| 「欣暖家 N 月奖金表/考核金额表」 | `xinnuanjia-kpi-amount` | 欣暖家 | 从基础绩效表 + 目标/人员模板生成欣暖家月度 KPI 奖金金额表 |

## 品牌子集包建议

| 收件人 | 建议包含 |
|---|---|
| 乾鑫会计 | `qianxin-kpi-amount` + `kpi-criteria-confirm-doc` + `fxiaoke-person-import-template` + 本知识库通用节/乾鑫节 |
| 欣暖家内勤 | `xinnuanjia-kpi-amount` + `kpi-criteria-confirm-doc` + `fxiaoke-person-import-template` + 本知识库通用节/欣暖家节 |
| 集团联单处理人 | `group-co-order-report` + `fxiaoke-sse-client` + 通用节 |

## 其他非纷享技能（001 机已装，非本知识库范围）

`excel-auto-zh`、`text-to-mindmap`、`video-editor-online`、`creator-video-cropper`、`wps-office-automation-skill`、`humanizer`、`self-improving`、`self-improving-agent`、`skill-vetter`、`talking-video-auto-edit` —— 仅列作全景，路由时勿误推荐。
