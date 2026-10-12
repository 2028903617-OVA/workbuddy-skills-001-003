# 客户（AccountObj）评分数据查询

用于客户质量、客户价值、健康度等 knowhow 评分。只查询支撑评分所需的业务事实。

## 对象定位

sharecrm data record query-id-by-name --data '{"query":"<客户名称>","apiNames":["AccountObj"]}'

返回多条候选时，展示候选并等待确认；未命中时返回未找到记录。

未命中但名称较明确时，可用名称归一化兜底：

sharecrm data record query-by-name --data '{"object_api_names":["AccountObj"],"name":"<客户名称或关键词>"}'

## 主记录详情

sharecrm data record get-by-id --object_api_name AccountObj --id <account_id>

如果详情字段不足，先查询对象描述，再按字段可用性补查。

sharecrm data describe identify-with-describe --object_api_name AccountObj

字段元数据已确认且确实需要字段裁剪时，用 `query-by-fields` 补查：

sharecrm data record query-by-fields --data '{"object_api_name":"AccountObj","select_fields":["_id","name","account_level","account_level__r","industry","industry__r","owner","owner__r","customer_status","customer_status__r","biz_status","biz_status__r","deal_status","deal_status__r","life_status","life_status__r","lock_status","lock_status__r","region","total_amount","completed_field_quantity","last_followed_time","last_modified_time","create_time"],"filters":[{"field_api_name":"_id","operator":"EQ","values":["<account_id>"]}],"limit":1}'

## 关联事实

需要判断客户价值或推进活跃度时，可补充查询关联商机。

sharecrm data record query-by-fields --data '{"object_api_name":"NewOpportunityObj","select_fields":["_id","name","sales_stage","sales_stage__r","amount","probability","close_date","last_modified_time"],"filters":[{"field_api_name":"account_id","operator":"EQ","values":["<account_id>"]}],"orders":[{"field_api_name":"last_modified_time","is_asc":false}],"limit":20}'

## 评分使用

- 客户状态、成交状态、完整度、最近跟进、关联商机等事实参与评分。
- 字段不存在或记录未体现时，不猜测，按评分标准保守给分。
