# 客户声音记忆模板

## 用途

本模板用于沉淀周期性客户声音洞察，不是 CRM 记录备份，也不是单客户360档案。只记录来自销售记录（`ActiveRecordObj`）、会议记录（`AIMeetingObj`）、会议记录明细（`AIMeetingChunkObj`）的高价值客户声音。

推荐路径：

```text
memory/customer_voice/[YYYY-MM]/[scope].md
```

推荐命名：

- `[YYYY-MM]_customer_voice_snapshot.md`：月度客户声音快照。
- `[YYYY-WW]_customer_voice_weekly.md`：周度客户声音快照。
- `[YYYY-MM-DD]_high_risk_voice.md`：高风险客户声音事件。
- `[YYYY-MM-DD]_emerging_signal.md`：新兴客户声音信号。
- `[YYYY-MM-DD]_voice_closed_loop.md`：客户声音闭环记录。

## 模板 1：周期客户声音快照

```markdown
# 客户声音快照 — {YYYY-MM 或 YYYY-WW}

## 记录元信息
- 分析视角：CEO/管理层/销售管理者/部门负责人/AE/会议记录（AIMeetingObj）/销售记录（ActiveRecordObj）
- 覆盖范围：
- 时间范围：
- 记录人：
- 样本量：销售记录（ActiveRecordObj）数 / 会议记录（AIMeetingObj）数 / 会议记录明细（AIMeetingChunkObj）数 / 声音数
- 信息完整度：完整/部分/不足
- 数据来源：销售记录（ActiveRecordObj）/会议记录（AIMeetingObj）/会议记录明细（AIMeetingChunkObj）/Memory/推断

## 结论摘要
- 一句话结论：
- 高频声音：
- 上升趋势：
- 主要风险：
- 主要机会：
- 重点来源/人群：
- 最大信息缺口：

## 高频声音主题
| 主题 | 声音数 | 涉及销售记录（ActiveRecordObj）/会议记录（AIMeetingObj） | 情绪倾向 | 强度 | 业务影响 | 置信度 |
| --- | --- | --- | --- | --- | --- | --- |
|  |  |  | 正/中/负/混合 | 高/中/低 |  | 确认/推断/未知 |

## 趋势变化
| 主题 | 当前周期 | 对比周期 | 趋势 | 判断 |
| --- | --- | --- | --- | --- |
|  |  |  | 上升/下降/稳定/新出现/消失/未知 |  |

## 角色/部门/人员归因
| 维度 | 样本 | 高频主题 | 风险等级 | 解读 |
| --- | --- | --- | --- | --- |
| 负责人/部门/会议发起人/内部参与人/业务类型 |  |  | 高/中/低/未知 |  |

## 代表性客户原文
| 来源 | 时间 | 主题 | 原文/高保真摘要 | 强度 | 为什么重要 |
| --- | --- | --- | --- | --- | --- |
| 销售记录（ActiveRecordObj）/会议记录（AIMeetingObj）/会议记录明细（AIMeetingChunkObj） |  |  |  | 高/中/低 |  |

## 风险与机会
| 类型 | 内容 | 影响来源 | 业务影响 | 建议责任方 | 状态 |
| --- | --- | --- | --- | --- | --- |
| 风险/机会 |  |  |  | AE/销售管理者/产品/交付/服务/数据负责人 | 待处理/处理中/已闭环 |

## 记录质量
- AI 分析失败会议：
- 缺少原文的会议记录明细（AIMeetingChunkObj）：
- ActiveRecordObj.active_record_content 不足：
- ActiveRecordObj.interactive_content 不足：
- 样本偏差：

## 建议动作
| 优先级 | 动作 | 目的 | 责任角色 | 截止/时机 | 状态 |
| --- | --- | --- | --- | --- | --- |
| 高/中/低 |  |  |  |  | 待处理/处理中/已完成 |

## 开放问题与样本偏差
- 
```

## 模板 2：高风险客户声音事件

高风险客户声音指可能影响关键推进、客户关系、上线验收、经营判断，或出现强烈负面、升级、竞品替代、预算冻结、记录质量异常的客户反馈。

```markdown
# 高风险客户声音 — {主题/来源} — {YYYY-MM-DD}

## 事件摘要
- 来源对象：销售记录（ActiveRecordObj）/会议记录（AIMeetingObj）/会议记录明细（AIMeetingChunkObj）
- 来源记录 ID：
- meeting_id：
- active_record_type：
- interactive_types：
- interaction_channels：
- related_object：
- account_id：
- leads_id：
- new_opportunity_id：
- object_api_name：
- original_id：
- 负责人/部门：
- 会议发起人：
- 内部参与人：
- 声音类型：产品/交付/服务/价格/预算/审批/竞品/使用效果/记录质量/其他
- 风险等级：高/中/低/未知
- 信息来源：会议记录明细（AIMeetingChunkObj）原文/会议记录明细（AIMeetingChunkObj）摘要/会议记录（AIMeetingObj）备注/ActiveRecordObj.active_record_content/ActiveRecordObj.interactive_content/销售观察/Memory
- 证据等级：E1/E2/E3/E4
- 置信度：确认/推断/未知

## 客户声音
- 原文/高保真摘要：
- 发生场景：
- 情绪与强度：

## 业务影响
- 对关键推进：
- 对客户关系：
- 对产品/交付/服务：
- 对记录质量：

## 归因判断
- 直接原因：
- 可能深层原因：
- 仍需核对：

## 闭环动作
| 动作 | 目的 | 责任角色 | 截止/时机 | 状态 |
| --- | --- | --- | --- | --- |
|  |  |  |  | 待处理/处理中/已完成 |
```

## 模板 3：新兴声音信号

```markdown
# 新兴客户声音信号 — {主题} — {YYYY-MM-DD}

## 信号摘要
- 主题：
- 首次明显出现时间：
- 涉及来源：销售记录（ActiveRecordObj）数 / 会议记录（AIMeetingObj）数 / 会议记录明细（AIMeetingChunkObj）数
- 涉及负责人/部门/参与人：
- 声音数量：
- 趋势：新出现/上升/未知
- 置信度：确认/推断/未知

## 代表性声音
| 来源 | 时间 | 声音摘要 | 证据等级 | 强度 |
| --- | --- | --- | --- | --- |
|  |  |  | E1/E2/E3/E4 | 高/中/低 |

## 为什么重要
- 对产品：
- 对销售：
- 对交付/服务：
- 对经营：
- 对记录质量：

## 后续验证
- 需要验证的问题：
- 建议核对来源：
- 责任角色：
```

## 模板 4：客户声音闭环记录

```markdown
# 客户声音闭环 — {主题/来源} — {YYYY-MM-DD}

## 声音来源
- 关联快照/事件：
- 来源对象：
- 来源记录 ID：
- meeting_id：
- 原始声音：
- 风险或机会：

## 处理过程
| 日期 | 动作 | 责任方 | 结果 |
| --- | --- | --- | --- |
|  |  |  |  |

## 闭环结果
- 状态：已解决/部分解决/未解决/转长期跟进
- 后续记录反馈：
- 对关键推进/满意度/记录质量影响：
- 可复用经验：

## 仍需关注
- 
```

## 更新规则

- 周/月度客户声音快照只记录高价值结论，不备份所有明细。
- 高风险客户声音应当天记录，并标注责任角色和闭环状态。
- 新兴信号至少有 E1/E2 或多个来源记录重复出现时再沉淀。
- 客户声音被产品、交付、服务、销售或数据负责人闭环后，应补充闭环记录。
- 信息不确定时写“推断”或“未知”，不要补成事实。
- 与销售记录（ActiveRecordObj）或会议记录（AIMeetingObj）冲突时，在 memory 中标注“需核对”。
