---
name: "leads-convert-validate"
description: "线索转商机前的资格验证。对线索进行CRM准入判断，调用 sfa-leads-score 获取评分报告，输出 yes/no 结论。当用户表达\\\"验证这条线索能否转商机\\\"、\\\"线索转商机前检查\\\"、\\\"评估线索是否满足升级条件\\\"、\\\"线索准入判断\\\"、\\\"线索资格审查\\\"、\\\"这个线索能不能升级\\\"、\\\"帮我看看这条线索够不够转商机\\\"等意图时触发。"
apiName: "leads_convert_validate"
---
# leads-convert-validate

> **版本**: v2.0
> **LTC阶段**: L阶段 → M阶段（线索培育 → 商机挖掘）
> **来源**: 销售管理Knowhow v1.3
> **最后更新**: 2026-06-08

---

## 定位

当销售认为某条线索已经"差不多可以立项/升级成商机"时，调用此Skill。

本Skill解决的是：
- 这条线索能不能升商机（yes / no）
- 不依赖交互式提问，基于 CRM 数据和 `sfa-leads-score` 评分报告做判定

---

## 核心功能

1. **准入判断**：线索是否满足升级为商机的最低条件（CRM数据层面）
2. **评分获取**：调用 `sfa-leads-score` 输出线索评分报告
3. **结论输出**：yes（可升级）或 no（不可升级）

---

## Trigger

**适合这些表达：**

- 验证这条线索能否转商机
- 线索转商机前检查
- 评估线索是否满足升级条件
- 线索准入判断
- 线索资格审查
- 这个线索能不能升级
- 帮我看看这条线索够不够转商机

**不适合这些表达：**

- 需要评分明细和分析 → 走 `sfa-leads-score`
- 需要诊断、风险、行动建议 → 走 `sfa-leads-diagnosis`
- 需要执行线索转换 → 走线索转换流程

---

## Inputs

| 输入 | 作用 | 必填 |
|:---|:---|:---|
| `object_id` | 直接定位线索对象 | 是（与"线索名称"二选一） |
| 线索名称 | 通过名称定位线索 | 是（与 `object_id` 二选一） |

---

## Workflow

### 第 1 步：获取线索ID

**场景 A — 用户提供了线索ID**：直接使用。

**场景 B — 用户提供了线索名称**：
```bash
sharecrm data record query-by-fields -d '{"object_api_name":"LeadsObj","select_fields":["_id","name","company","mobile","biz_status","lock_status","leads_stage"],"search_template_query":{"limit":20,"filters":[{"field_name":"name","operator":"LIKE","field_values":["<线索名称>"]}],"orders":[{"fieldName":"last_modified_time","isAsc":false}]}}'
```

### 第 2 步：准入判断

获取线索详情后，检查硬性门禁（详见 [references/qualification-rules.md](references/qualification-rules.md)）：

- `biz_status` 不为"已转换"或"无效"，`life_status` 为"正常"
- `lock_status` 不为"锁定"
- `biz_status` 不为"未分配"
- `name` 和 `company` 至少一项非空

**任一项不通过 → 直接返回 no，附不通过原因，终止流程。**

准入判断可调用辅助脚本：
```bash
python scripts/verify.py <leads_id>
```

### 第 3 步：调用 sfa-leads-score 获取评分报告

准入通过后，将线索 ID 传入 `sfa-leads-score`，获取完整评分报告（总分、评级、四维度得分、评分依据）。

本 skill 不重复执行评分逻辑，只消费评分报告的结果。

### 第 4 步：输出验证结论

基于评分报告中的**评级**判定：

| 评分评级 | 结论 | 说明 |
|:---|:---:|:---|
| A（≥70） | **yes** | 高质量线索，可升级为商机 |
| B（50-69） | **yes** | 有潜力但信息不完整，可转商机后在商机阶段继续补齐 |
| C（30-49） | **no** | 培育线索，需继续培育后复评 |
| D（<30） | **no** | 低价值或无效线索，不建议升级 |

按 [templates/线索转商机报告模板.md](templates/线索转商机报告模板.md) 格式输出验证结果。

---

## Outputs

每次输出必须包含：
1. 准入判断结果（含 4 项门禁检查明细）
2. 评分报告摘要（引用 `sfa-leads-score` 输出：总分、评级、四维度得分）
3. 验证结论：**yes** 或 **no**
4. 结论说明

---

## Boundaries

- **只读不写**：本 skill 只分析评估，不执行任何数据修改或转换操作
- **不交互提问**：不再向销售逐项确认红线，全部判定基于 CRM 数据 + 评分报告
- **不替代转换 skill**：验证结果为 yes 后，引导用户使用线索转换流程
- **不替代评分 skill**：评分逻辑由 `sfa-leads-score` 承担，本 skill 只消费其输出
- **不输出诊断/建议/动作**：不输出缺失项清单、谁补什么时候补、下一步推荐路径等

---

## Dependencies

- `sfa-leads-score`：线索评分 skill，本 skill 的第 3 步依赖其输出

---

## 完整对话示例

```
用户：帮我看看"张三公司"这条线索能不能转商机

SKILL：
1. 查询线索详情
   ID：69ef28eff5c5f300079a268e，姓名：张三，公司：张三科技，状态：跟进中

2. 准入判断
   - [通过] 线索状态：biz_status=跟进中
   - [通过] 锁定状态：lock_status=未锁定
   - [通过] 分配状态：已分配
   - [通过] 基本信息：name=张三, company=张三科技
   → 准入通过

3. 调用 sfa-leads-score 评分
   - 线索总分：72/100
   - 评级：A
   - 七问验证：51/70
   - 三要素评估：24/30
   - CRM行为和跟进信号：11/15
   - 匹配度和风险：8/10

4. 验证结论：yes
   评级 A（72/100），高质量线索，可升级为商机。
   是否现在执行线索转换？
```
