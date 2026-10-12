#!/usr/bin/env python3
"""
线索转商机资格验证 — CRM数据准入脚本

用法：
    python verify.py <leads_id>

功能：
    1. 从CRM拉取线索完整数据
    2. 执行准入判断（硬性门禁）
    3. 输出结构化JSON供后续评分环节使用
"""

# -*- coding: utf-8 -*-
import json
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')


def run_sharecrm(args_str):
    path = shutil.which("sharecrm")
    cmd = [path, "data", "record", "get-by-id", "-d", args_str]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        print(json.dumps({"error": f"sharecrm调用失败: {result.stderr.strip()}"}, ensure_ascii=False))
        sys.exit(1)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(json.dumps({"error": f"sharecrm返回非JSON: {result.stdout[:500]}"}, ensure_ascii=False))
        sys.exit(1)


# get-by-id 返回的中文标签到 api_name 的映射
LABEL_TO_API = {
    "姓名": "name", "公司": "company", "手机": "mobile", "电话": "tel",
    "邮箱": "email", "职务": "job_title", "部门": "department",
    "状态": "biz_status", "锁定状态": "lock_status", "生命状态": "life_status",
    "线索阶段": "leads_stage", "销售线索详情": "remark",
    "下次跟进时间": "next_followed_time", "最后跟进时间": "last_follow_time",
    "创建时间": "create_time", "是否超时": "is_overtime",
    "转换概率": "conversion_probability", "洞察分数": "insight_score",
    "加分项": "pros_tags", "减分项": "cons_tags",
    "下次跟进要点": "next_followed_remark",
}


def normalize_record(raw):
    """将 get-by-id 返回的中文标签记录转为 api_name 键的字典。"""
    record = raw.get("record", raw)
    result = {}
    for key, value in record.items():
        api = LABEL_TO_API.get(key, key)
        result[api] = value
    return result


def get_field(data, field, default=None):
    return data.get(field, default)


# ── 准入判断 ──

def entry_check(lead):
    items = []
    passed = True

    biz_status = get_field(lead, "biz_status", "")
    life_status = get_field(lead, "life_status", "")

    if biz_status in ("已转换", "无效") or life_status == "作废":
        items.append({"check": "线索状态", "pass": False, "detail": f"biz_status={biz_status}, life_status={life_status}"})
        passed = False
    else:
        items.append({"check": "线索状态", "pass": True, "detail": f"biz_status={biz_status}"})

    lock_status = get_field(lead, "lock_status", "")
    if lock_status == "锁定":
        items.append({"check": "锁定状态", "pass": False, "detail": "线索已锁定"})
        passed = False
    else:
        items.append({"check": "锁定状态", "pass": True, "detail": f"lock_status={lock_status}"})

    if biz_status == "未分配":
        items.append({"check": "分配状态", "pass": False, "detail": "线索未分配"})
        passed = False
    else:
        items.append({"check": "分配状态", "pass": True, "detail": f"biz_status={biz_status}"})

    name = get_field(lead, "name", "")
    company = get_field(lead, "company", "")
    if not name and not company:
        items.append({"check": "基本信息", "pass": False, "detail": "姓名和公司均为空"})
        passed = False
    else:
        items.append({"check": "基本信息", "pass": True, "detail": f"name={name}, company={company}"})

    return {"passed": passed, "items": items}


# ── 主流程 ──

def main():
    if len(sys.argv) < 2:
        print("用法: python verify.py <leads_id>", file=sys.stderr)
        sys.exit(1)

    leads_id = sys.argv[1]
    raw = run_sharecrm(json.dumps({
        "object_api_name": "LeadsObj",
        "id": leads_id,
    }))

    if not raw or (isinstance(raw, dict) and raw.get("code") is not None and raw.get("code") != 0):
        print(json.dumps({"error": "获取线索数据失败", "raw": raw}, ensure_ascii=False))
        sys.exit(1)

    lead = normalize_record(raw)

    entry = entry_check(lead)

    result = {
        "leads_id": leads_id,
        "leads_name": get_field(lead, "name", ""),
        "leads_company": get_field(lead, "company", ""),
        "entry_check": entry,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 准入不通过时给明确提示
    if not entry["passed"]:
        failed = [i["check"] for i in entry["items"] if not i["pass"]]
        print(f"\n[准入不通过] 以下条件未满足: {', '.join(failed)}", file=sys.stderr)


if __name__ == "__main__":
    main()
