# 线索诊断流程

本文件负责诊断生成阶段的流程编排与内部分析视角。对象边界、评分前置、评分驱动诊断、风险分级、Markdown 输出等硬约束由 `SKILL.md` 定义，本文件不放宽；远端 knowhow 调用命令与 HTML 保存链路以 `SKILL.md` 的 `ToolsList` 和 `Workflow` 为准。

## 内部分析视角

三个连续视角，非互斥、不三选一，默认按序执行：

1. **视角A 洞察诊断**：以 `Scoring_Result` 维度结果为主骨架，形成整体判断与完整输出骨架。
2. **视角B 线索画像**：收敛当前状态、关键背景、核心短板与主要风险，强化概要、全局诊断、风险识别的可读性。
3. **视角C 下一步推进**：把已识别短板转成跟进策略与行动建议，明确“下一步怎么跟”。

## 执行步骤

1. 读取 `references/global-diagnosis-criteria.md`。该文件已按 `output_template.md` 章节顺序内聚全局诊断、关键缺失项、跟进策略、风险识别与行动建议标准；无需再分别加载风险识别或阶段动作拆分文件。
2. 视角A：先查询 `get_profile_score --objectApiName LeadsObj`；CLI 失败、为空、无评分信息或对象不匹配时回退 `sfa-leads-score`。再根据线索主数据与销售记录直接生成 `AI_Stage`，结合选定的 `Scoring_Result`、内部生成的 `AI_Stage`、线索事实与销售记录形成全局诊断；全局诊断维度必须严格沿用选定评分来源的名称和顺序，每个维度的判断必须区分「事实 / 判断 / 待确认问题」，并记录评分来源。
3. 视角B：收敛线索画像（当前状态、关键背景、核心短板、主要风险）。
4. 从全局短板、阶段不达标项与销售管理风险中识别 `P0 / P1 / P2` 关键缺失项和风险。
5. 视角C：基于内部生成的 `AI_Stage` 生成跟进策略与行动建议；生成时应用 `references/global-diagnosis-criteria.md` 中的「跟进策略」与「跟进建议」标准；阶段证据不足时只输出保守推进动作，不给高置信阶段结论。
6. 按 `references/output_template.md` 的结构组织诊断内容；最终 Markdown / HTML 输出由 `SKILL.md` Workflow 第 7~8 步执行。
