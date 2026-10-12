# -*- coding: utf-8 -*-
"""
线索转换校验脚本
用法: python verify.py <leads_id>
"""
import json
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

def get_config_values():
    """
    调用 CLI 工具 LeadsTransferConfigGet，返回配置值字典

    各配置 key 含义：
    - "40": 转换关联已有客户权限。值为 "0" 表示无权限，其他值表示有权限。
            该配置控制线索转换时是否允许关联已有客户（AccountObj 的 TransferExist）。
    - "41": 旧版全局必须转换配置。值为逗号分隔的 4 位字符串，格式为
            "cusMust,conMust,oppMust,newOppMust"（每位为 0 或 1）。
            例如 "1,0,0,0" 表示客户必须转换，联系人/老商机/新商机非必须。
            当 must_transfer_by_type 未配置时，使用此全局配置。
    - "config_newopportunity_open": 新商机（商机2.0）功能开关。
            值为 "open" 表示开启，其他值表示关闭。
            开启后，转换页面可同时展示老商机和新商机供选择。
    - "must_transfer_by_type": 按线索类型（record_type）配置的必须转换规则。
            值为 JSON 字符串，格式如 {"default_leads_type": "1,1,0,1"}。
            优先级高于 "41"，可按不同线索业务类型设置差异化的必转规则。
    - "put_crm_feed_select_mode": 销售线索动态（Feed）带入模式。
            1 = 走缓存（按用户上次选择），2 = 强制带入，3 = 不允许带入。
    - "put_teams_select_mode": 相关团队带入模式。
            1 = 走缓存（按用户上次选择），2 = 强制带入，3 = 不允许带入。
    """
    arg = {
        "isAllConfig": False,
        "keys": [
            "40",
            "41",
            "config_newopportunity_open",
            "must_transfer_by_type",
            "put_crm_feed_select_mode",
            "put_teams_select_mode"
        ]
    }

    path = shutil.which("sharecrm")
    result = subprocess.run([path, "sales", "lead", "leads-transfer-config-get", "-d", json.dumps(arg)], capture_output=True, text=True, encoding='utf-8')
    if result.returncode != 0:
        raise RuntimeError(f"CLI命令：sharecrm sales lead leads-transfer-config-get 执行失败，错误原因：{result.stderr}")
    res = json.loads(result.stdout)

    config = {}
    for item in res["values"]:
        config[item["key"]] = item.get("value", "")

    # 解析 "41" 为 must_transform 字典
    must_transform = {
        "AccountObj": False,
        "ContactObj": False,
        "OpportunityObj": False,
        "NewOpportunityObj": False,
    }
    raw_41 = config.get("41", "")
    if raw_41:
        parts = raw_41.split(",")
        keys = ["AccountObj", "ContactObj", "OpportunityObj", "NewOpportunityObj"]
        for i, k in enumerate(keys):
            if i < len(parts):
                must_transform[k] = parts[i].strip() == "1"

    # 解析 must_transfer_by_type（如存在则覆盖 "41"）
    raw_by_type = config.get("must_transfer_by_type", "")
    if raw_by_type:
        try:
            by_type = json.loads(raw_by_type)
            # 前端以当前线索的 record_type 取对应值，此处仅保留原始字典供调用方使用
            config["_must_transfer_by_type_parsed"] = by_type
        except json.JSONDecodeError:
            pass

    config["_must_transform"] = must_transform
    config["_exist_account_rights"] = config.get("40", "") != "0"
    config["_is_new_opportunity_open"] = config.get("config_newopportunity_open", "") == "open"

    # ---------- 简洁输出 ----------
    print("[线索转换配置]")

    # 全局必转规则

    # 按线索类型必转规则（若存在则解析并展示）
    if raw_by_type:
        print("  按业务类型必转规则:")
        try:
            by_type = json.loads(raw_by_type)
            type_obj_names = ["客户", "联系人", "商机(老)", "商机(新)"]
            for ltype, val in by_type.items():
                parts = val.split(",")
                musts = []
                for i, name in enumerate(type_obj_names):
                    if i < len(parts) and parts[i].strip() == "1":
                        musts.append(name)
                print(f"    {ltype}: {', '.join(musts) if musts else '无'}")
        except json.JSONDecodeError:
            print(f"    (解析失败) {raw_by_type}")
    else:
        must_objects = []
        for obj_key in ["AccountObj", "ContactObj", "OpportunityObj", "NewOpportunityObj"]:
            if must_transform[obj_key]:
                must_objects.append(obj_key)
        print(f"  全局必转对象: {', '.join(must_objects) if must_objects else '无'}")

    # 新商机开关
    print(f"  新商机功能: {'开启' if config['_is_new_opportunity_open'] else '关闭'}")

    # 动态/团队带入模式（转译为可读文字）
    mode_desc = {"1": "走缓存", "2": "强制带入", "3": "不允许带入"}
    feed_mode = config.get("put_crm_feed_select_mode", "")
    teams_mode = config.get("put_teams_select_mode", "")
    print(f"  销售记录动态带入模式:{feed_mode}（{mode_desc.get(feed_mode, feed_mode)}）")
    print(f"  销售线索的相关团队带入模式:{teams_mode}（{mode_desc.get(teams_mode, teams_mode)}）")

    return config


def batch_object_action_codes_privilege_check(config: dict):
    """
    调用 CLI 工具 leads-transfer-privilege-batch-check，校验转换目标对象权限

    校验逻辑（对齐前端）：
    1. 客户（AccountObj）始终必须转换，因此必须有 TransferAdd 权限。
    2. AccountObj 的 TransferExist（关联已有客户）权限不由 actionRights 决定，
       而是由配置 "40" 控制（_exist_account_rights）。
    3. 对于 mustTransform（必转）的对象，必须至少拥有一个权限：
       TransferAdd（转换新建）或 TransferExist（转换关联已有）。
    4. OpportunityObj（老商机）和 NewOpportunityObj（新商机）均需校验。
    """
    arg = {
        "apiName2ActionCodes": {
            "AccountObj": ["TransferAdd", "TransferExist"],
            "ContactObj": ["TransferAdd", "TransferExist"],
            "OpportunityObj": ["TransferAdd", "TransferExist"],
            "NewOpportunityObj": ["TransferAdd", "TransferExist"]
        }
    }

    path = shutil.which("sharecrm")
    result = subprocess.run([path, "sales", "lead", "leads-transfer-privilege-batch-check", "-d", json.dumps(arg)], capture_output=True, text=True, encoding='utf-8')
    if result.returncode != 0:
        raise RuntimeError(f"CLI命令：sharecrm sales lead leads-transfer-privilege-batch-check 执行失败，错误原因：{result.stderr}")
    rights = json.loads(result.stdout)
    account_exist = config['_exist_account_rights']

    print("[线索转换权限]")
    if not rights['AccountObj']['TransferAdd']:
        if not account_exist:
            print("客户(AccountObj)无转换新建权限，无法执行线索转换")
            return False
    print(f"  客户(AccountObj): 转换关联已有{account_exist}, 转换新增{rights['AccountObj']['TransferAdd']}")
    print(f"  联系人(ContactObj): 转换关联已有{rights['ContactObj']['TransferExist']}, 转换新增{rights['ContactObj']['TransferAdd']}")
    print(f"  商机(NewOpportunityObj): 转换关联已有{rights['NewOpportunityObj']['TransferExist']}, 转换新增{rights['NewOpportunityObj']['TransferAdd']}")
    print(f"  老商机(OpportunityObj):不允许通过skill转换！如果用户需要转换，就终止转换流程，并提示用户去CRM中手动操作。")
    # 权限全通过，不输出任何信息
    return True


def get_record_type():
    """
    调用 CLI 工具 bulkFindValidRecordTypeList，获取可用业务类型
    """
    arg = {
        "objectApiNameList": ["AccountObj", "ContactObj", "NewOpportunityObj"]
    }

    path = shutil.which("sharecrm")
    result = subprocess.run([path, "sales", "lead", "action-leads-bulk-find-valid-record-type-list", "-d", json.dumps(arg)], capture_output=True, text=True, encoding='utf-8')
    if result.returncode != 0:
        raise RuntimeError(f"CLI命令：sharecrm sales lead action-leads-bulk-find-valid-record-type-list 执行失败，错误原因：{result.stderr}")
    res = json.loads(result.stdout)
    record_type_list = res["recordTypeList"]

    print("[可用业务类型 多条业务类型提示用户选择]")
    for api_name in record_type_list:
        record_type = record_type_list[api_name]
        for record in record_type:
            if record["is_active"]:
                print(f"  ({api_name}业务类型) \t api_name:{record['api_name']},\t label:{record['label']}")

    return True

def get_target_object_data(leads_id: str, object_api_name: str):
    cli_command = "leads-transfer-account-get"
    if "ContactObj" == object_api_name:
        cli_command = "leads-transfer-contact-get"
    elif "NewOpportunityObj" == object_api_name:
        cli_command = "leads-transfer-newopportunity-get"
    elif "OpportunityObj" == object_api_name:
        print("  OpportunityObj老商机不允许通过skill转换！终止转换流程，提示用户去CRM中手动操作。")
        return False

    arg = {
        "objectDataId": leads_id
    }

    path = shutil.which("sharecrm")
    result = subprocess.run([path, "sales", "lead", cli_command, "-d", json.dumps(arg)], capture_output=True, text=True, encoding='utf-8')
    if result.returncode != 0:
        raise RuntimeError(f"CLI命令：sharecrm sales lead {cli_command} 执行失败，错误原因：{result.stderr}")
    res = json.loads(result.stdout)
    data = res["objectData"]

    # 使用leads-transfer-search查是否有重复用户
    object_transfer_search(leads_id, data)
    return True

# todo 需重新配置
def object_transfer_search(leads_id: str, object_data: object):
    data_name = "account_data"
    if "ContactObj" == object_data['object_describe_api_name']:
        data_name = "contact_data"
    elif "NewOpportunityObj" == object_data['object_describe_api_name']:
        data_name = "newOpportunity_data"

    arg = {
        "page_size": 20,
        "page_number": 1,
        data_name: object_data,
        "leads_id": leads_id,
        "is_unique_search": False,
        "is_need_duplicate": True
    }

    path = shutil.which("sharecrm")
    result = subprocess.run([path, "sales", "lead", "leads-transfer-search", "-d", json.dumps(arg)], capture_output=True, text=True, encoding='utf-8')
    if result.returncode != 0:
        raise RuntimeError(f"CLI命令：sharecrm sales lead leads-transfer-search 执行失败，错误原因：{result.stderr}")
    res = json.loads(result.stdout)
    res_list = json.loads(res["data"]["data"])

    if len(res_list["values"]) == 0:
        print(f"  {object_data['object_describe_api_name']}没有可关联的数据，推荐直接新建")
        return True
    data_list = res_list["values"][0]["data_list"]
    if len(data_list) == 0:
        print(f"  {object_data['object_describe_api_name']}没有可关联的数据，推荐直接新建")
    else:
        for o in data_list:
            print(f"  {object_data['object_describe_api_name']}存在可关联数据：ID：{o['_id']} name:{o['name']}")
    return True

def main():
    if len(sys.argv) < 2:
        print("用法: python verify.py <leads_id>")
        sys.exit(1)

    leads_id = sys.argv[1]

    try:
        # 1. 获取线索转换配置
        config = get_config_values()

        # 2.校验转换目标对象权限
        if not batch_object_action_codes_privilege_check(config):
            return
        # 3.获取可用业务类型
        get_record_type()

        # 4.查找是否可以直接关联
        # print("[关联检查]")
        # for api_name in ["AccountObj","ContactObj","NewOpportunityObj"]:
        #     get_target_object_data(leads_id, api_name)

        print("前置校验通过，请和用户确认是否需要关联、是否需要更换业务类型。")
    except:
        print("前置校验出错，请勿继续尝试，立即终止线索转换任务，并向用户报告，请勿绕过本脚本。")


if __name__ == "__main__":
    main()
