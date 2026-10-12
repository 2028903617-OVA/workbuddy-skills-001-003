# -*- coding: utf-8 -*-
"""
线索转换
用法: python do_transfer.py <leads_id> <transfer_arg> <record_type>
"""
import json
import shutil
import subprocess
import sys
import time
import uuid

sys.stdout.reconfigure(encoding='utf-8')

accountId = ""
accountName = ""

def transfer(leads_id: str, object_list: object):

    arg = {
        "dataList": object_list,
        "supportDetailObj": True,
        "putTeamMembersIntoCustomer": False,
        "combineCRMFeed": False,
        "leadsId": leads_id,
    }

    path = shutil.which("sharecrm")
    result = subprocess.run([path, "sales", "lead", "leads-transfer", "-d", json.dumps(arg)], capture_output=True, text=True, encoding='utf-8')
    print(result)
    if result.returncode != 0:
        raise RuntimeError(f"CLI命令：sharecrm sales lead leads-transfer 执行失败，错误原因：{result.stderr}")


def get_transfer_arg(leads_id: str, object_name: str, transfer_type: str, record_type: str):
    target_object_data = get_target_object_data(leads_id, object_name, record_type)
    if "Add" == transfer_type:
        ret = {
            "fillMultiLang": True,
            "layoutInfoLog": True,
            "object_data": target_object_data
        }
        return ret
    else:
        data_name = "account_data"
        if "ContactObj" == object_name:
            data_name = "contact_data"
        elif "NewOpportunityObj" == object_name:
            data_name = "newOpportunity_data"

        arg = {
            "page_size": 20,
            "page_number": 1,
            data_name: target_object_data,
            "leads_id": leads_id,
            "is_unique_search": False,
            "is_need_duplicate": True
        }
        path = shutil.which("sharecrm")
        result = subprocess.run([path, "sales", "lead", "leads-transfer-search", "-d", json.dumps(arg)], capture_output=True, text=True, encoding='utf-8')
        if result.returncode != 0:
            raise RuntimeError(
                f"CLI命令：sharecrm sales lead leads-transfer-search 执行失败，错误原因：{result.stderr}")
        res_list = json.loads(result.stdout)["data"] # todo

        data_list = res_list["values"][0]["data_list"]

        for o in data_list:
            if o['_id'] == transfer_type:
                ret = {
                    "object_data": o
                }
                return ret

        print("转换失败")
        raise Exception("关联查询数据失败")


def get_target_object_data(leads_id: str, object_api_name: str, record_type: str):
    global accountId
    global accountName
    tool_name = "leads-transfer-account-get"
    if "ContactObj" == object_api_name:
        tool_name = "leads-transfer-contact-get"
    elif "NewOpportunityObj" == object_api_name:
        tool_name = "leads-transfer-newopportunity-get"
    elif "OpportunityObj" == object_api_name:
        print("不允许通过skill转换！终止转换流程，提示用户去CRM中手动操作。")
        return False

    arg = {
        "objectDataId": leads_id
    }

    path = shutil.which("sharecrm")
    result = subprocess.run([path, "sales", "lead", tool_name, "-d", json.dumps(arg)], capture_output=True, text=True, encoding='utf-8')
    if result.returncode != 0:
        raise RuntimeError(f"CLI命令：sharecrm sales lead {tool_name} 执行失败，错误原因：{result.stderr}")
    res = json.loads(result.stdout)
    data = res["objectData"]
    data["record_type"] = record_type

    if "AccountObj" == object_api_name:
        accountName = data["name"]
    #     data["_id"] = accountId
    if "NewOpportunityObj" == object_api_name:
        result = subprocess.run([path, "stage", "def", "list", "--enable", "1", "--entityId", "NewOpportunityObj"],
                                capture_output=True, text=True, encoding='utf-8')
        if result.returncode != 0:
            raise RuntimeError(f"CLI命令：sharecrm stage def list 执行失败，错误原因：{result.stderr}")
        res = json.loads(result.stdout)
        if len(res["data"]) == 0:
            print("商机阶段为空，无法转换为商机！")
            raise RuntimeError("商机阶段为空")
        work_id = res["data"][0]["sourceWorkflowId"]
        # data["account_id"] = accountId
        data["amount"] = "0.00"
        data["sales_process_id"] = work_id
        data["close_date"] = (time.time() + 7 * 24 * 3600) * 1000
        data["sales_stage"] = "1"
        data["name"] = accountName
    return data


def main():
    if len(sys.argv) < 4:
        print("用法: python do_transfer.py <leads_id> <transfer_arg> <record_type>")
        print("transfer_arg参数说明：传入对象apiName+类型，多个对象使用英文逗号分割，如客户关联已有，联系人新建： ContactObj-Add,AccountObj-客户数据id")
        print("record_type参数说明：传入对象apiName+record_type，如： ContactObj-default__c,AccountObj-default__c")
        sys.exit(1)

    leads_id = sys.argv[1]
    transfer_obj = sys.argv[2]
    record_type = sys.argv[3]

    if not ("AccountObj" in transfer_obj):
        print("AccountObj 客户对象必转！")
        return
    objects = transfer_obj.split(",")

    record_dict = {}
    parts = record_type.split(',')
    for part in parts:
        if '-' in part:
            key, value = part.split('-', 1)
            record_dict[key] = value

    global accountId
    if accountId == "":
        accountId = uuid.uuid4().hex[:24]

    try:
        dataList = {}
        for o_d in objects:
            arg = o_d.split("-")
            data = get_transfer_arg(leads_id, arg[0], arg[1], record_dict[arg[0]])
            dataList[arg[0]] = data
        transfer(leads_id, dataList)
        print("转换操作完成，但仍然需要检查是否真的转换成功（因转换操作后台不进行强事务校验，所以可能出现部分转换成功，但是返回值不报错的情况）")
    except:
        print("出错了！立即终止线索转换任务，因后续操作不可逆，可能造成数据错乱，请勿自动尝试。检查实际转换情况，立即向用户报告转换失败，并提示用户回到CRM中操作更便捷。"
              "如果用户想要绕过脚本继续操作，一定要再次警告用户绕过脚本操作大概率会导致CRM中数据混乱且无法修复，绕过脚本需要得到用户的二次确认。")


if __name__ == "__main__":
    main()
