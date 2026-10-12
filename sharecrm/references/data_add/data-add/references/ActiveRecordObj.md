# ActiveRecordObj

## `what_list_type` 赋值逻辑

当目标对象为 `ActiveRecordObj`，且需要填写或修改“关联业务模块”/`related_object`/`what_list` 类型字段时，不要写入 `related_object`，也不要使用 `{ObjectApiName: ["id"]}` 简写；必须同时写入 `related_object_data` 和 `related_api_names`。

- 先按主流程的关联对象字段规则解析每条关联记录，取得唯一的关联对象 `apiName`、记录 `id` 和记录 `name`。
- `related_object_data` 写数组；每个元素必须包含 `describe_api_name`、`id`、`name`。
- `related_api_names` 写数组；值来自 `related_object_data[].describe_api_name` 去重后的对象 apiName，保留首次出现顺序。
- 多条同对象记录可同时写入 `related_object_data`；`related_api_names` 中该对象 apiName 只保留一次。
- 新建记录时，任何关联记录未唯一确认前，不得构造、校验或保存这两个字段。
- 编辑记录时，若用户表达“追加/补充关联”，在原 `object_data.related_object_data` 基础上追加，并按 `describe_api_name + id` 去重后重算 `related_api_names`。
- 编辑记录时，若用户表达“改为/设为/替换关联”，用新解析出的关联记录替换原 `related_object_data`，并重算 `related_api_names`。
- 编辑记录时，任何关联记录未唯一确认前，不得构造、校验或保存这两个字段。

示例片断：
```json
{
  "related_object_data": [
    {
      "describe_api_name": "AccountObj",
      "id": "6a0697de42275d000745a6ba",
      "name": "抚州影视文化公司"
    },
    {
      "describe_api_name": "AccountObj",
      "id": "6a057a8844cdb1000740a08d",
      "name": "小鹏"
    }
  ],
  "related_api_names": [
    "AccountObj"
  ]
}
```

## `cc_range` 抄送范围

`cc_range` 代表分享的抄送/可见范围，使用部门和人员范围表达。创建时，后端会读取分享固定抄送设置；当设置中存在固定部门或人员时，后端以设置值覆盖本次传入的 `cc_range`，并清空兼容的 `notifyRange`。
因此：
- Agent 不得猜测、预计算或补齐固定抄送人员；
- 用户传入的 `cc_range` 不保证是最终生效范围；
- 创建完成后，应以服务端结果或后续查询结果说明实际可见/回执范围。

示例片断：
```json
{
  "cc_range": {
    "departments": ["<departmentId>"],
    "employees": ["<employeeId>"]
  }
}
```

## `active_record_content` 协同富文本字段转换
active_record_content是协同富文本字段可使用 Markdown 或 HTML。HTML 含字色、字号等 CSS 时，必须将原始 HTML 的 CSS 转成 HTML属性再提交，不能先转为 Markdown 或纯文本。

## 关联Feed

`ActiveRecordObj` 创建成功后产生关联Feed。后续Feed相关查询、回复、点赞、回执均使用服务端返回的 `feedId`，不能把对象 `dataId` 当作 `feedId` 使用。

可以通过 `sharecrm feeds get-by-object` 命令, 使用 `ActiveRecordObj + dataId` 定位 Feed 和 FeedId。