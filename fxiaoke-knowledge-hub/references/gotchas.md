# 高频坑清单（fs-server / APL / Excel / 业务统计）

> 每条均来自生产实测翻车记录。执行前先扫一遍对应小节。

## 一、fs-server MCP 查询坑

1. **明细查询单页上限 20 条，超限静默截断**——查询前必须向用户确认过滤条件、预期数据量、翻页策略，等确认再查（西门子规则 >20 条，曾漏「线索录入」规则）。
2. **SSE 直连单查询 50 条硬上限**，需 offset 翻页（详见 `fxiaoke-sse-client` 技能）。
3. **`UpdateRecordsByData` 的 `_id` 类型坑**：`_id` 必须放 `object_data` 体内，但传输层会把体内**纯数字字符串**（如 `"2768"`）自动转 JSON 数字 → 报「字段唯一性ID _id的数据值2768类型不正确」。绕过：短数字 `_id` 的 legacy 记录改走批量导入/管理端（CSV 中 `_id` 为真实字符串）；或用 ObjectId 格式 `_id`。
4. **`SalesOrderObj` 禁止 `data_record_update`**（报"当前对象不支持执行该操作:编辑"）→ 订单字段刷新只能走计划任务自定义函数或后台 CSV 导入(更新模式)。2026-07 曾需刷新 1949 条订单的 `first_repayment_time__c`。
5. **`QueryRecordsBySQL` 按可见范围权限过滤**：先按条件检索再剔无权限记录，可能查不到全员 → 用导出文件匹配 `user_id`/`_id` 再更新。
6. **回款明细引用字段读不到值**：OrderPaymentObj 的 `field_rr5cJ__c` 是引用字段，fs-server 读不到 → 回款类型过滤读 `PaymentObj.field_274Al__c`。
7. **选项字段存 code 非中文**：如销售收款=`8b4we3s9C`（显示值在 `__r`）。拿中文当查询值会查空。

## 二、统计口径坑

8. **线索被无效 → owner 被清空**：按 owner 聚合漏掉被无效线索（案例：吴斌当月新建 31 条、1 条被无效，owner 口径只统计到 30）。积分/绩效考核必须含被无效线索，统计前先问用户按 owner 还是创建人。
9. **订单审批 ≠ 成交**：成交=首次回款单审批通过才反写。别把订单审批通过当成交统计。
10. **回款剔除定金**：绩效只统计「销售收款」类；定金回款不绑订单明细。
11. **A 指标口径勿套 B 指标**：曾把①（第一成交率金额）的「仅第一成交」误写到③（成交ABC顾客数）。各指标定义独立核对。
12. **术语**：后台自动化叫「审批流 / 工作流」，不叫「触发器」。

## 三、APL 自定义函数坑

13. **更新 API 第二参是 dataId 字符串**：`Fx.object.update("Obj", dataId, updateMap, ...)` —— 不是把 `_id` 塞进 map。
14. **人员字段是数组**：`owner`/`created_by` 均为 `["人员id"]` 数组，EQ("id串") 可匹配。
15. **日期**：`Date.of(longValue)`、`date.withDay(1)`、`firstDay + 1.months - 1.days`；写 date 字段直接传 Date（平台自动截断时间）。
16. **金额字段勿硬编码**：回款金额/订单金额有多个候选字段，以用户当次指定为准。
17. 完整 API 写法与两个可复用模板见 `fxiaoke-apl-function` 技能；粘进纷享前先过 `fxiaoke-apl-testground` 自查（D13/D14/D18 沙箱禁令）。

## 四、Excel / 环境坑

18. **openpyxl 读字段导出必须 `load_workbook(read_only=False)`**：read_only=True 每 sheet 只报 1 行。
19. **读取环境**：venv Python（`.workbuddy/binaries/python/envs/default/` 下，含 openpyxl 3.1.5、pypdf 6.11.0）；独立 3.13.12 Python 无这些包。
20. **WPS 占用锁（EBUSY）**：被 WPS 打开的 `.md`/文件无法直接 Edit → 用 Python 读后写新文件绕开。
21. **Chrome headless 生成 PDF 必须用绝对输出路径**：相对路径 + cd 会 FileNotFoundError。

## 五、网络与资源约定

22. **需翻墙下载的资源**（GitHub releases、Google 系等）：不得擅自用镜像源或开代理——只向用户说明「需开梯子才能下载」，停手等用户决定。
23. **图片转表格**：优先 AI 直接读图核对（通常优于 OCR 坐标重建）；OCR 只在量大时作交叉核对。原则：不花钱、不耗时、数据必须精准。
