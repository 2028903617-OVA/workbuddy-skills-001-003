# R07 竞品历史

## 目标

整理客户历史和当前竞争态势，让接手人知道“客户为什么比较、过去怎么打、现在谁占优、哪些打法不要重复”。交接场景里，竞品历史不是进攻话术，而是客户决策背景和历史包袱。

## 触发条件

完成 R01-R06 后执行。只要 CRM、Memory、客户原话或用户输入出现竞品、自研、替换、招投标、POC、报价对比、历史输单，就必须输出竞品历史。

如果没有任何竞品证据，输出“暂无明确竞品记录”，并列出需要接手人向原 AE 核对的问题。

## 输入来源

- CRM `CompetitiveLinesObj`。
- CRM `NewOpportunityObj.competitors`、商机备注、输赢状态。
- CRM `ActiveRecordObj.active_record_content` 中的客户原话、竞品比较、报价、POC、招投标记录。
- Memory 中的关键博弈事件、历史输赢、客户偏好、关键人关系卡。
- 用户补充的原 AE 口头交代。
- `references/competitive_reference.md`，仅用于解释竞品阶段和通用强弱项。

## 竞品阶段

| 阶段 | 名称 | 判断标准 |
| --- | --- | --- |
| C0 | 未知 | 没有竞品信息 |
| C1 | 线索 | 客户提到竞品或同类系统，但没有明确比较动作 |
| C2 | 在场 | 客户明确比较竞品、索要对比或 CRM 有竞品明细 |
| C3 | 深度评估 | 竞品进入 POC、方案、报价、招投标或技术评审 |
| C4 | 已选择 | 客户已签竞品、历史输给竞品或流失原因明确为竞品替换 |

## 输出契约

```yaml
r07_competitive_history:
  competitors:
    - competitor_id:
      competitor_name:
      stage: C0|C1|C2|C3|C4
      current_or_historical: current|historical|both|unknown
      customer_comparison_reason:
      customer_quote:
      known_price:
      our_response_history:
      outcome: won|lost|ongoing|shelved|unknown
      key_people_influenced:
        - name:
          role:
          attitude:
      current_impact:
      receiver_verify:
      confidence: confirmed|inferred|unknown
  competitor_risks:
    - risk:
      evidence:
      receiver_do:
      receiver_do_not:
  data_gaps:
    - gap
```

## 判断规则

- 竞品必须有证据；行业常见玩家不能直接写成“当前竞品在场”。
- 自研系统、集团指定平台、原有系统续用，都按竞品处理。
- 有报价写“已知报价”；没有报价写“未知”，不要估算。
- 历史输给竞品时，必须写清楚输的原因，以及该原因是否仍影响当前关系。
- 竞品进入 C2 及以上时，必须进入最终交接简报。
- 通用竞品强弱项只能作为背景，不得覆盖客户实际评价。
- 接手建议写“需要核对什么”和“不要重复什么打法”，不写攻击竞品的话术。

## 结构化文本输出

```markdown
## 7. 竞品历史

### 竞品总览
| 竞品 | 阶段 | 当前/历史 | 客户比较原因 | 已知报价 | 历史结果 | 当前影响 | 置信度 |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  | C0/C1/C2/C3/C4 | 当前/历史/都有/未知 |  | 未知/金额 | 赢单/输单/进行中/搁置/未知 |  | 确认/推断/未知 |

### 历史打法与结果
| 竞品 | 我方历史应对 | 结果 | 接手人不要重复 | 接手人需核对 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

### 关键人影响
| 关键人 | 受哪个竞品影响 | 态度 | 证据 | 接手注意 |
| --- | --- | --- | --- | --- |
|  |  | 支持/中立/反对/未知 |  |  |

### 竞品信息缺口
- {缺少竞品名称、阶段、报价、客户比较原因、关键影响人或历史输赢原因等信息}
```
