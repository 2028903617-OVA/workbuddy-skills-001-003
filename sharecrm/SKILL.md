---
name: sharecrm
description: Use when the user needs to query, create, or manage ShareCRM data, knowledge, solutions, approvals, files, schedules, or other ShareCRM product capabilities through the `sharecrm` CLI.
license: MIT
metadata:
  agentSupport: true
  author: "zengww9500@fxiaoke.com"
  version: "1.1.0"
  requires:
    bins: ["sharecrm"]
  cliHelp: "sharecrm -h"
---

# 纷享销客全产品 Skill

通过 `sharecrm` 命令管理纷享产品能力。

## 严格禁止 (NEVER DO)
- 不要使用 sharecrm 命令以外的方式操作（禁止 curl、HTTP API、浏览器）
- 不要编造 UUID、ID 等标识符，必须从命令返回中提取
- 不要猜测字段名/参数值，操作前必须先查询确认

## 严格要求 (MUST DO)
- 危险操作必须先向用户确认，用户同意后才加 `--yes` 执行
- 单次批量操作不超过 30 条记录
- 所有命令必须**严格遵循**对应产品参考文档里面规定的参数格式（如：如果有参数值，则参数和参数值之间至少用一个空格隔开）

## 前置条件
- 已安装 `sharecrm`，可通过 `sharecrm -V` 确认是否安装，如果未安装 MUST 请先用 Read 工具读取 [`references/shareCrmInstall.md`](references/shareCrmInstall.md)内容，并完成sharecrm安装
- 已通过 `sharecrm auth login` 完成登录授权
- **CRITICAL — 开始前 MUST 先用 Read 工具读取 [`references/userAuth.md`](references/userAuth.md)，其中包含登录授权、身份认证**
- 登录用户具有对应数据操作的权限 scope

> **注意：** 产品命令的使用方法可以通过 `sharecrm <product> -h` 查看，命令帮助信息可以通过 `sharecrm <product> <command> -h` 查看,命令帮助信息中会列出所有参数。

## 产品总览

| 产品             | 用途                                      | 命令帮助信息查                     | 参考文档                                     |
|----------------|-----------------------------------------|-----------------------------|------------------------------------------|
| `knowledge`    | 知识与检索：                                  | `sharecrm  knowledge -h`    |                                          |
| `solution`     | 内容与方案：                                  | `sharecrm  solution -h`     |                                          |
| `enterprise`   | 企业与行业：                                  | `sharecrm  enterprise -h`   |                                          |
| `sales`        | CRM与销售：                                 | `sharecrm  sales -h`        |                                          |
| `marketing`    | 营销与增长：                                  | `sharecrm  marketing -h`    |                                          |
| `service`      | 服务与工单：                                  | `sharecrm  service -h`      |                                          |
| `visit`        | 外勤与拜访：外勤/外勤记录/外勤审批/外勤审批表单               | `sharecrm  visit -h`        |                                          |
| `bi`           | BI分析：                                   | `sharecrm  bi -h`           |
| `approval`     | 审批：审批工单，审批工单查询，审批工单创建，审批工单修改，审批工单删除     | `sharecrm  approval -h`     |                                          |
| `bpm`          | BPM：                                    | `sharecrm  bpm -h`          |                                          |
| `flow`         | 流程：流程创建，流程查询，流程修改，流程删除                  | `sharecrm  flow -h`         |                                          |
| `data`         | 对象与数据：CRM通用对象数据操作，包括查询，新建，编辑，根据SQL查询等   | `sharecrm  data -h`         | [data.md](./references/products/data.md) |
| `describe`     | 对象描述：CRM对象描述的基本操作，包括查询对象ApiName，查询对象描述等 | `sharecrm  contact -h`      |                                          |
| `file`         | 文件：对象文件上传                                  | `sharecrm  file -h`         | [fileUpload.md](./references/fileUpload.md)                                         |
| `utility`      | 通用函数：                                   | `sharecrm  utility -h`      |                                          |
| `work`         | 日程任务：                                   | `sharecrm  work -h`         |                                          |
| `tag`          | 标签：                                     | `sharecrm  tag -h`          |                                          |
| `usergroup`    | 用户组：                                    | `sharecrm  usergroup -h`    |                                          |
| `stage`        | 阶段：                                     | `sharecrm  stage -h`        |                                          |
| `notice`       | 通知：                                     | `sharecrm  notice -h`       |                                          |
| `mail`         | 邮件：                                     | `sharecrm  mail -h`         |                                          |
| `channel`      | 渠道协同：                                   | `sharecrm  channel -h`      |                                          |
| `conversation` | 群组与会话：                                  | `sharecrm  conversation -h` |                                          |

## 意图判断决策树

- 用户提到"知识/知识库/知识检索/知识库检索/知识查询/知识搜索" → `knowledge`
- 用户提到"解决方案/方案/内容/内容方案/方案检索/方案搜索" → `solution`
- 用户提到"企业信息/行业信息/行业检索/行业查询/行业搜索" → `enterprise`
- 用户提到"销售/CRM" → `sales`
- 用户提到"营销/增长/推广/推广渠道/推广渠道管理/推广渠道分析/推广渠道效果/推广渠道效果分析" → `marketing`
- 用户提到"售后/售后服务/售后支持/售后处理/服务工单/售后工单" → `service`
- 用户提到"外勤/外勤记录/外勤审批/外勤审批表单/拜访/拜访记录/拜访审批/拜访审批表单" → `visit`
- 用户提到"BI/BI报表/数据分析/数据可视化/数据统计/数据统计分析/数据统计效果/数据统计效果分析/数据可视化/数据可视化分析" → `bi`
- 用户提到"审批/审批表单/审批流程/审批工单" → `approval`
- 用户提到"BPM/业务流程/BPM流程/BPM流程定义/BPM流程实例/BPM流程任务/BPM流程任务节点" → `bpm`
- 用户提到"对象/对象数据/对象数据查询/对象数据检索/对象数据创建/对象数据修改/对象数据删除" → `data`
- 用户提到"文件/网盘/文件管理/文件检索/文件查询/文件上传/文件下载/文件分享/文件收藏/文件收藏夹/文件收藏夹创建/文件收藏夹删除" → `file`
- 用户提到"函数/APL函数/通用函数/通用函数定义/通用函数实例/通用函数任务/通用函数任务节点" → `utility`
- 用户提到"日程/日程任务/日程任务节点/日程任务实例/日程任务定义" → `work`
- 用户提到"标签/标签管理/标签创建/标签删除" → `tag`
- 用户提到"用户组/用户组管理/用户组创建/用户组删除" → `usergroup`
- 用户提到"阶段/阶段管理/阶段创建/阶段删除" → `stage`
- 用户提到"通知/通知查看/通知检索/通知管理/通知创建/通知删除" → `notice`
- 用户提到"邮件/邮件管理/邮件创建/邮件删除" → `mail`
- 用户提到"渠道/渠道协同/渠道管理/渠道创建/渠道删除" → `channel`
- 用户提到"群组/群组管理/群组创建/群组删除" → `conversation`

> 

## 危险操作确认

以下操作为不可逆或高影响操作，执行前**必须先向用户展示操作摘要并获得明确同意**，同意后才加 `--yes` 执行。

| 产品 | 命令                     | 说明             |
|------|------------------------|----------------|
| `data` | `data CreateRecords`   | 创建对象数据         |

### 确认流程
```
Step 1 → 展示操作摘要（操作类型 + 目标对象 + 影响范围）
Step 2 → 用户明确回复确认（如 "确认" / "好的"）
Step 3 → 加 --yes 执行命令
```

## 核心流程
作为一个智能助手，你的首要任务是**理解用户的真实、完整的意图**，而不是简单地执行命令。在选择 `sharecrm` 的产品命令前，必须严格遵循以下四步流程：

1. 意图分类：首先，判断用户指令的核心 动词/动作 属于哪一类。这比关注名词更重要。
2. 歧义处理与信息追问：如果用户指令模糊或包含多个产品的关键字，严禁猜测。必须主动向用户追问以澄清意图。这是你作为智能助手而非命令执行器的核心价值。
3. 精准产品映射：在完成前两步，意图已经清晰后，参考产品总览和意图判断决策树 来选择产品。
4. 充分阅读产品参考文件，通过编写代码或直接调用指令实现用户意图。

## 错误处理
1. 遇到错误，加 `--debug` 重试一次
2. 仍然失败，报告完整错误信息给用户，禁止自行尝试替代方案
3. 认证失败时，参考 [userAuth](references/userAuth.md) 中的认证章节处理


## 子技能索引

当用户意图匹配下表场景时，**MUST** 先用 Read 工具读取对应子技能的 `SKILL.md`，并严格按其指令执行。

### 知识与检索

| 子技能 | 用途 | 参考文档 |
|--------|------|----------|
| `agentic-rag` | CRM 知识检索强制入口：产品功能/配置/故障/政策/文档问答 | [`agentic-rag`](references/agentic_rag/agentic-rag/SKILL.md) |

### 数据读写

| 子技能 | 用途 | 参考文档 |
|--------|------|----------|
| `semantic-interpreter` | 自然语言 CRM 数据查询/检索/聚合/分析的唯一入口 | [`semantic-interpreter`](references/semantic_interpreter/semantic-interpreter/SKILL.md) |
| `data-read` | `sharecrm data` 只读兜底：对象识别、描述、关系与记录读取 | [`data-read`](references/data-read/data-read/SKILL.md) |
| `data-add` | 自然语言创建/录入 CRM 主对象数据记录 | [`data-add`](references/data_add/data-add/SKILL.md) |
| `data-edit` | 自然语言编辑/更新 CRM 主对象已有记录字段 | [`data-edit`](references/data_edit/data-edit/SKILL.md) |

### 流程运行时

| 子技能 | 用途 | 参考文档 |
|--------|------|----------|
| `flow-tasks-query` | 查询审批流/业务流/阶段推进器待办任务 | [`flow-tasks-query`](references/flow_tasks_query/flow-tasks-query/SKILL.md) |
| `flow-runtime-handler-skill` | 处理审批流/业务流/阶段推进器运行时任务 | [`flow-runtime-handler-skill`](references/flow-runtime-handler-skill/flow-runtime-handler-skill/SKILL.md) |
| `approval-runtime-skill` | 查询或处理审批实例与审批任务 | [`approval-runtime-skill`](references/approval_runtime_skill/approval-runtime-skill/SKILL.md) |
| `bpm-runtime-skill` | 查询或处理业务流实例与业务流任务 | [`bpm-runtime-skill`](references/bpm_runtime_skill/bpm-runtime-skill/SKILL.md) |
| `stage-runtime-skill` | 查询或处理阶段推进器实例、阶段与任务 | [`stage-runtime-skill`](references/stage_runtime_skill/stage-runtime-skill/SKILL.md) |

### 客服 CSM

| 子技能 | 用途 | 参考文档 |
|--------|------|----------|
| `agent-kb-qa` | 客服侧知识库问答，生成解答与回复参考 | [`agent-kb-qa`](references/csm_agent_knowledge_base_qa/agent-kb-qa/SKILL.md) |
| `create-case` | 从会话上下文提取信息并创建案例 | [`create-case`](references/csm_create_case/create-case/SKILL.md) |
| `smart-handoff-to-human-agent` | 智能转接人工客服 | [`smart-handoff-to-human-agent`](references/csm_handoff_to_human_agent/smart-handoff-to-human-agent/SKILL.md) |
| `knowledge-capture` | 从会话提炼知识并创建问答对/知识文章 | [`knowledge-capture`](references/csm_knowledge_capture/knowledge-capture/SKILL.md) |
| `next-best-action` | 生成客服下一步行动建议 | [`next-best-action`](references/csm_next_best_action/next-best-action/SKILL.md) |
| `query-case` | 按访客/客户信息查询匹配案例 | [`query-case`](references/csm_query_case/query-case/SKILL.md) |
| `response-recommendation` | 生成多种风格客服话术推荐 | [`response-recommendation`](references/csm_response_recommendation/response-recommendation/SKILL.md) |
| `knowledge-base-qa` | 机器人知识库问答（带来源引用） | [`knowledge-base-qa`](references/csm_robot_knowledge_qa/knowledge-base-qa/SKILL.md) |
| `robot-session-summary` | 总结前序智能客服会话与待跟进事项 | [`robot-session-summary`](references/csm_robot_session_summary/robot-session-summary/SKILL.md) |
| `self-service-appointment` | 客户自助预约并创建服务请求 | [`self-service-appointment`](references/csm_self_service_appointment/self-service-appointment/SKILL.md) |
| `intent-recognition` | 识别客户主诉求并分流服务路径 | [`intent-recognition`](references/csm_service_process/intent-recognition/SKILL.md) |
| `service-progress-query` | 按单号/电话查询服务进度 | [`service-progress-query`](references/csm_service_progress_query/service-progress-query/SKILL.md) |
| `customer-profile-insight` | 生成访客画像洞察报告 | [`customer-profile-insight`](references/csm_visitor_profile_insight/customer-profile-insight/SKILL.md) |

### SFA 销售

| 子技能 | 用途 | 参考文档 |
|--------|------|----------|
| `leads-convert-validate` | 线索转商机前资格验证 | [`leads-convert-validate`](references/leads_convert_validate/leads-convert-validate/SKILL.md) |
| `account-chain-analysis` | 客户产业链位置、上下游与生态关系分析 | [`account-chain-analysis`](references/sfa-account-chain-analysis/account-chain-analysis/SKILL.md) |
| `account-cooperation-history` | 客户历史合作与供应商关系分析 | [`account-cooperation-history`](references/sfa-account-cooperation-history/account-cooperation-history/SKILL.md) |
| `account-due-diligence-report` | 客户情报/尽调报告（含舆情检索） | [`account-due-diligence-report`](references/sfa-account-due-diligence-report/account-due-diligence-report/SKILL.md) |
| `account-industry-analysis` | 客户所处行业环境与趋势分析 | [`account-industry-analysis`](references/sfa-account-industry-analysis/account-industry-analysis/SKILL.md) |
| `sfa-customer-voice` | 基于销售/会议记录的客户之声（VOC）分析 | [`sfa-customer-voice`](references/sfa-customer-voice/sfa-customer-voice/SKILL.md) |
| `sfa-account-diagnosis` | 客户经营诊断与下一步经营建议 | [`sfa-account-diagnosis`](references/sfa_account_diagnosis/sfa-account-diagnosis/SKILL.md) |
| `sfa-account-handover-briefing` | 客户团队交接简报 | [`sfa-account-handover-briefing`](references/sfa_account_handover_briefing/sfa-account-handover-briefing/SKILL.md) |
| `sfa-account-pre-visit-briefing-v2` | 见客前/拜访前客户简报 | [`sfa-account-pre-visit-briefing-v2`](references/sfa_account_pre_visit_briefing/sfa-account-pre-visit-briefing-v2/SKILL.md) |
| `sfa-account-score` | 客户评分与健康度评估 | [`sfa-account-score`](references/sfa_account_score/sfa-account-score/SKILL.md) |
| `sfa-account-standard-briefing` | 客户 360 标准档案简报 | [`sfa-account-standard-briefing`](references/sfa_account_standard_briefing/sfa-account-standard-briefing/SKILL.md) |
| `sfa-data-convert` | SFA 单据转换（报价/合同/订单等） | [`sfa-data-convert`](references/sfa_data_convert/sfa-data-convert/SKILL.md) |
| `sfa-decision-chain-diagnosis` | 商机决策链诊断 | [`sfa-decision-chain-diagnosis`](references/sfa_decision_chain_diagnosis/sfa-decision-chain-diagnosis/SKILL.md) |
| `sfa-journal-personal-report` | 销售个人日报/周报/月报 | [`sfa-journal-personal-report`](references/sfa_journal_personal_report/sfa-journal-personal-report/SKILL.md) |
| `sfa-journal-team-report` | 销售团队日报/周报/月报 | [`sfa-journal-team-report`](references/sfa_journal_team_report/sfa-journal-team-report/SKILL.md) |
| `sfa-leads-convert` | 线索转化为客户/联系人/商机 | [`sfa-leads-convert`](references/sfa_leads_convert/sfa-leads-convert/SKILL.md) |
| `sfa-leads-diagnosis` | 线索诊断、画像与跟进建议 | [`sfa-leads-diagnosis`](references/sfa_leads_diagnosis/sfa-leads-diagnosis/SKILL.md) |
| `sfa-leads-score` | 线索评分与质量评估 | [`sfa-leads-score`](references/sfa_leads_score/sfa-leads-score/SKILL.md) |
| `sfa-opportunity-competitive-analysis` | 商机竞争分析与竞品对比 | [`sfa-opportunity-competitive-analysis`](references/sfa_opportunity_competitive_analysis/sfa-opportunity-competitive-analysis/SKILL.md) |
| `sfa-opportunity-diagnosis` | 商机诊断、风险识别与赢单建议 | [`sfa-opportunity-diagnosis`](references/sfa_opportunity_diagnosis/sfa-opportunity-diagnosis/SKILL.md) |
| `sfa-opportunity-score` | 商机评分与赢率评估 | [`sfa-opportunity-score`](references/sfa_opportunity_score/sfa-opportunity-score/SKILL.md) |
| `sfa-opportunity-stage` | 商机阶段查询与变更 | [`sfa-opportunity-stage`](references/sfa_opportunity_stage/sfa-opportunity-stage/SKILL.md) |
| `sfa-price-tool` | 询价/价目表/最优价格查询 | [`sfa-price-tool`](references/sfa_price_tool/sfa-price-tool/SKILL.md) |
| `sfa-product-attribute-tool` | 产品关联属性查询/关联/解除 | [`sfa-product-attribute-tool`](references/sfa_product_attribute_tool/sfa-product-attribute-tool/SKILL.md) |

## 详细参考 (按需读取)
- [sharecrm程序安装](references/shareCrmInstall.md) — sharecrm程序安装
- [sharecrm授权登录](references/userAuth.md) — 全局标志、认证、输出格式
- [纷享CRM对象清单](references/objectApiNames.md) — 各数据对象 API 名称
