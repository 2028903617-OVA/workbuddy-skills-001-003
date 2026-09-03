# 对象字段 API 速查（纷享销客）

> 三份字段定义导出文件（本机 D 盘）为权威来源；本册内嵌最常用字段，脱离原机也能回答核心问题。
> ⚠️ 金额类字段不止一种，生产函数中回款金额用过 `PaymentObj.amount`、订单金额用过 `SalesOrderObj.field_7QA6l__c`——**以用户当次明确指定为准，勿硬编码**。

## 一、核心对象链路

```
销售线索(LeadsObj) ──转换──▶ 客户(Account) ──▶ 销售订单(SalesOrderObj) ──▶ 回款(PaymentObj)
                                     ▲
              高级外勤(follow_up_record__c) 挂在 线索/客户 下
              合同变更 / 退款 关联 销售订单 / 回款
```

- **客户是枢纽对象**：除合同变更单外，所有对象都建在客户下；客户信息变动影响全部子对象。
- 提交后客户**姓名/电话/地址不可改**，新增只能在「联系人 / 客户地址」。
- 金蝶(ERP)只同步**首次**客户信息。

## 二、常用字段速查表

### 销售订单 SalesOrderObj（225 字段，21-sheet 导出）
| 用途 | API | 类型/备注 |
|---|---|---|
| 创建时间 | `create_time` | 日期时间, epoch 毫秒 |
| 确认(审批通过)时间 | `confirm_time` | 日期时间 |
| 带单类型 | `UDSSel2__c` | 单选（集团联单过滤用） |
| 公司 | `UDSSel7__c` | 单选 |
| 业务类型 | `record_type` | — |
| 生命状态 | `life_status` | 单选（normal=正常） |
| 首回款时间 | `first_repayment_time__c` | date，**无自动反写**，需计划任务/CSV 刷新 |
| 订单金额 | `field_7QA6l__c` / `order_amount` 等 | ⚠️ 多个候选，以用户指定为准 |

⚠️ `SalesOrderObj` 经 fs-server `data_record_update` **被禁用**（报"当前对象不支持执行该操作:编辑"）→ 刷新订单字段只能走计划任务自定义函数或后台 CSV 导入(更新模式)。

### 回款 PaymentObj
| 用途 | API | 备注 |
|---|---|---|
| 回款类型 | `field_274Al__c` | 标签「回款类型」，选项 定金/销售收款。**存 code 非中文**：销售收款=`8b4we3s9C`（定金 code 待补） |
| 回款金额 | `amount` | ⚠️ 以用户指定为准 |
| 关联订单 | `order_id` | 存订单 `_id`（非订单编号文本） |
| 回款日期 | `payment_time` | 首回款日期取其最小值（仅 `life_status='normal'`） |
| 个人销售收款判断 | `field_DapeV__c>0` | 团队判断用 `field_274Al__c='8b4we3s9C'` |

⚠️ 回款明细(OrderPaymentObj)上的 `field_rr5cJ__c` 是**引用字段**，fs-server 读不到取值——过滤回款类型读 `PaymentObj.field_274Al__c`，不要用明细引用字段。

### 人员 PersonnelObj
| 用途 | API | 备注 |
|---|---|---|
| 系统名（昵称） | `name` | 必填，识别人认这个；`full_name` 姓名可能为空 |
| 主属部门 | `main_department` | 部门类型，组织归属 |
| 负责人所在部门 | `owner_department` | 单行文本，动态 |
| 主属公司/事业部 | `field_v2M9H__c` | 单选；欣暖家=`6p1Rxc395` |
| 月度销售指标 | `amount__c` | 数字，2026-07-28 用户新建，**不在 21-sheet 导出内** |

⚠️ 「唯一性ID（必填）」=`_id`、「员工ID（必填）」=`user_id`：老记录二者常相同，新记录 `_id` 是 ObjectId 长串、`user_id` 是短号，勿混。
⚠️ `QueryRecordsBySQL` 按可见范围权限过滤，可能查不到全员。

### 高级外勤 follow_up_record__c（21-sheet 导出**没有**，在补充导出里）
| 用途 | API |
|---|---|
| 客户关联 | `related_customer__c`（查找关联→客户） |
| 销售记录关联 | `related_sales_record__c` |
| 线索关联 | `related_lead__c` |
| 负责人 | `owner`（人员, 必填） |
| 创建/修改时间 | `create_time` / `last_modified_time` |

### 绩效月度 object_oEmfu__c（西门子/欣暖家反写目标）
| 用途 | API |
|---|---|
| 第一成交率奖金 | `first_deal_bonus__c` |
| ABC总量奖金 | `abc_count_bonus__c` |
| ABC转化奖金 | `abc_conversion_bonus__c` |
| 业绩达成奖金 | `target_achieve_bonus__c` |
| 合计（计算字段） | `total_assessment_bonus__c`（公式自动求和） |
| 员工 | `person_name__c`（人员） |
| 年 / 月 | `year__c` / `month__c`（数字） |
| 品牌 | `brand_name__c`（单选，选项=大金;方太;西门子;泽锋;乾鑫;圆策;欣暖家;启欣;民森匠心;芯猫;鸿格;集团职能;智管家电;其他） |
| 生命状态 | `life_status`（**无 `__c` 后缀**，选项=未生效;审核中;正常;变更中;作废） |
| 目标类 | `sales_target__c` / `collection_target_amount__c` / `order_amount_target__c` / `lead_target_count__c` 均为计算字段 |

### 积分规则引擎
- 父：`object_incentiveRule__c`（`rule_type__c`=自动计算/手动录入/其他、`life_status`、`incentive_rule_code__c` 自增编号）
- 明细：`object_rule_details__c`（经 `field_incentive_rule__c` 主从关系挂父，`lock_rule`）
- 每日积分：`object_incentive_points__c`；积分明细：`object_points_details__c` / `process_points_details__c`

### 提成核算 16 对象（第三份导出，2026-08-04）
核心：计提基数表 `commission_base_table__c`、计提基数明细 `provision_base_details__c`、提成汇总表 `commission_summary_table__c`（**每月每人一条**，含达成系数与 `commissionAmount__c` 提成金额）、提成明细 `commission_details__c`、计提规则等。

`commission_base_table__c` 关键口径 [已验证·2026-08-04 实测]：
- `actual_sales_amount__c`(计算,=订单含变更) = `order_amount__c`(统计)+`changed_amount__c`(统计)
- `actual_collection_amount__c`(计算,=回款已扣退款) = `recovery_amount__c`(统计)−`refund_amount__c`(统计)；**退款仅作回款减项，无独立指标**
- 部门：`data_own_department`（数组存 deptId，**创建时冻结、调店不变**，函数口径用这个）vs `owner_department`（动态，日常「所在部门」用这个）
- 计提周期：`field_6WkL4__c`(开始)/`field_fi91b__c`(结束)=计提周期月；`assigned_month_date__c`=所属月首日
- `provision_status__c`(单选=未计提;已计提;其他)、`provision_commission__c`(单选=是;否;其他，'是'=方太厨电顾问基数，函数有意排除)
- 明细 `calc_type__c`（单选=当月计算;跨月计算;其他）→ **一笔单可跨月拆多条基数**

## 三、三份字段定义导出文件（本机权威来源）

| 文件 | 覆盖 | 读法 |
|---|---|---|
| `D:/Backup/Downloads/N_202607_24_7b79918c157c4566bc7eccf498773f0d.xlsx.xlsx` | 21 sheet：对象及字段API + 20 对象（SalesOrderObj 225 字段） | **必须 `load_workbook(read_only=False)`**（read_only=True 每 sheet 只报 1 行）；列：col0=序号, col1=显示名, col2=API名, col3=类型, col4=必填 |
| `D:/Backup/Downloads/对象及字段API.xlsx` | 9 sheet：主表 + 8 对象（**含高级外勤**、绩效积分全套） | 主表字段级扁平表：`对象名称|对象Api|字段名称|字段Api|类型|必填|选项值` |
| `D:/Backup/Downloads/对象及字段API (1).xlsx` | 17 sheet：主表 + 16 提成/计提对象（完整提成体系） | 对象 sheet：row4=表头，row5+=字段 |

读取环境：venv Python（`.workbuddy/binaries/python/envs/default/` 下，含 openpyxl 3.1.5）。

## 四、字段现场确认法

不确定的字段 API / 选项 code：用 fs-server `data_describe_get` 现场确认，或查上表三份导出文件。**禁止凭记忆编造 API 名或选项值。**
