#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""query_pricebook.py 的离线回归测试。

全部走桩，**不联网、不读真实系统、不写任何数据**。
覆盖点（都是踩过的坑）：
  1. cli_query 的 recordResult 两种结构归一化（有命中 list / 无命中 dict）—— 曾致 KeyError: 0
  2. 无命中 → []，find_detail 返回 None（决定「新建」还是「更新」）
  3. find_product 的两道闸：品牌不一致拒绝、括号变体拒绝
  4. to_code 的 label → 码值转换与「转不出」标记；停用选项必须过滤
  5. apply_plan：新建带 pricebook_id/product_id/record_type；更新带 _id；价字段全显式
  6. 产品未同步的行不写入
  7. build_plan 的 新建/更新 判定与未知组织停止

★ 桩必须**用完还原**（`_PatchBase`）——否则前面用例打的桩会污染后面的用例，
  表现为「明明改了 cli_query，find_detail 却还返回 None」，极易误判成产品代码有 bug。
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import query_pricebook as q  # noqa: E402
import build_import as bi  # noqa: E402


class _PatchBase(unittest.TestCase):
    """打桩前快照模块属性，tearDown 时逐一还原，避免跨用例污染。"""

    PATCH_ATTRS = ("cli_query", "field_codes", "find_product", "find_detail",
                   "find_pricebook", "_client", "CLI_RETRIES", "CLI_BACKOFF",
                   "_run_cli")

    def setUp(self):
        self._saved = {k: getattr(q, k, None) for k in self.PATCH_ATTRS}
        self._saved_src = bi.load_source_rows
        self._saved_run = q.subprocess.run

    def tearDown(self):
        for k, v in self._saved.items():
            setattr(q, k, v)
        bi.load_source_rows = self._saved_src
        q.subprocess.run = self._saved_run


class TestCliQueryNormalize(_PatchBase):
    """CLI 的 recordResult 有两种结构，必须归一化成 list。"""

    def _run_with_fake_stdout(self, payload):
        class R:
            returncode = 0
            stderr = ""
            stdout = json.dumps(payload, ensure_ascii=False)
        q.subprocess.run = lambda *a, **k: R()
        return q.cli_query("XObj", [], ["_id"])

    def test_hit_shape_is_list(self):
        """有命中 → recordResult 是 list。"""
        got = self._run_with_fake_stdout({"recordResult": [{"_id": "a"}, {"_id": "b"}]})
        self.assertEqual([r["_id"] for r in got], ["a", "b"])

    def test_empty_shape_is_dict_with_records(self):
        """★ 无命中 → recordResult 是 dict{totalNumber,records,searchTemplateQuery}，必须返回 []。"""
        got = self._run_with_fake_stdout(
            {"recordResult": {"totalNumber": 0, "records": [], "searchTemplateQuery": "{}"}})
        self.assertEqual(got, [])

    def test_dict_shape_with_records_returns_them(self):
        got = self._run_with_fake_stdout(
            {"recordResult": {"totalNumber": 2, "records": [{"_id": "x"}, {"_id": "y"}]}})
        self.assertEqual([r["_id"] for r in got], ["x", "y"])

    def test_error_response_raises(self):
        with self.assertRaises(q.CliError):
            self._run_with_fake_stdout({"errorCode": 10006, "errorMessage": "apiName not exists"})

    def test_missing_recordResult_returns_empty(self):
        self.assertEqual(self._run_with_fake_stdout({"queryMeta": {}}), [])

    def test_transient_fetch_failed_is_retried(self):
        """★ CLI 偶发 'fetch failed' 必须重试，不能误判成「记录不存在」。"""
        seq = ["fetch failed",
               json.dumps({"recordResult": [{"_id": "ok1"}]}, ensure_ascii=False)]

        class R:
            returncode = 0
            stderr = ""

            def __init__(self, s):
                self.stdout = s

        calls = []

        def fake_run(*a, **k):
            calls.append(1)
            return R(seq[min(len(calls) - 1, len(seq) - 1)])

        q.subprocess.run = fake_run
        q.CLI_BACKOFF = 0            # 测试不真等待
        got = q.cli_query("XObj", [], ["_id"])
        self.assertEqual([r["_id"] for r in got], ["ok1"])
        self.assertEqual(len(calls), 2, "第一次失败、第二次成功，共调 2 次")

    def test_limit_exceeded_raises_not_silent_zero(self):
        """★★ limit>100 服务端报 LIMIT_EXCEEDED 并静默返回 0 条 —— 必须抛错，绝不返回空。
        否则「查重没命中」会被当成「明细不存在」→ 重复建明细。"""
        payload = {"queryMode": "RECORD",
                   "queryMeta": {"notices": [{"code": "LIMIT_EXCEEDED"}],
                                 "page": {"returnedCount": 0}},
                   "recordResult": {"totalNumber": 0, "records": []}}
        with self.assertRaises(q.CliError):
            self._run_with_fake_stdout(payload)

    def test_limit_is_clamped_to_max(self):
        """limit 传 200 时必须被夹到 MAX_LIMIT，不能原样发给服务端。"""
        seen = {}

        class R:
            returncode = 0
            stderr = ""
            stdout = json.dumps({"recordResult": []})

        def spy(args, **k):
            seen["data"] = json.loads(args[args.index("--data") + 1])
            return R.stdout

        q.subprocess.run = lambda *a, **k: R()
        q._run_cli = lambda args, **k: spy(args)
        q.cli_query("XObj", [], ["_id"], limit=200)
        self.assertEqual(seen["data"]["search_template_query"]["limit"], q.MAX_LIMIT)

    def test_persistent_failure_raises(self):
        class R:
            returncode = 0
            stderr = ""
            stdout = "fetch failed"

        q.subprocess.run = lambda *a, **k: R()
        q.CLI_BACKOFF = 0
        q.CLI_RETRIES = 2
        try:
            with self.assertRaises(q.CliError):
                q.cli_query("XObj", [], ["_id"])
        finally:
            q.CLI_RETRIES = 4


class TestFindDetail(_PatchBase):
    """双条件查重：命中→dict，未命中→None。"""

    def test_no_hit_returns_none(self):
        q.cli_query = lambda *a, **k: []
        self.assertIsNone(q.find_detail("pid", "pbid"))

    def test_hit_returns_first(self):
        q.cli_query = lambda *a, **k: [{"_id": "d1", "价目表售价": "540.00"}]
        got = q.find_detail("pid", "pbid")
        self.assertIsNotNone(got)
        self.assertEqual(got["_id"], "d1")

    def test_filters_are_two_conditions(self):
        seen = {}

        def spy(obj, filters, fields, limit=200):
            seen["obj"] = obj
            seen["filters"] = filters
            return []

        q.cli_query = spy
        q.find_detail("PID", "PBID")
        self.assertEqual(seen["obj"], "PriceBookProductObj")
        pairs = {(f["field_name"], tuple(f["field_values"])) for f in seen["filters"]}
        self.assertIn(("product_id", ("PID",)), pairs)
        self.assertIn(("pricebook_id", ("PBID",)), pairs)


class TestFindProductGates(_PatchBase):
    """find_product 的两道闸必须真的生效。"""

    def test_brand_mismatch_rejected(self):
        """源表型号推得出品牌 A，候选名推得出品牌 B → 拒绝。"""
        q.cli_query = lambda *a, **k: [{"产品名称": "美的电热水器X100", "_id": "p1"}]
        name, pid, cat = q.find_product("格力电热水器X100")
        self.assertIsNone(pid, "品牌不一致不该命中")

    def test_bracket_variant_rejected(self):
        """源表带括号变体 (HE)、候选没有 → 是不同产品，拒绝。"""
        q.cli_query = lambda *a, **k: [{"产品名称": "美的电热水器F60-33Q7Pro", "_id": "p1"}]
        name, pid, cat = q.find_product("美的电热水器F60-33Q7Pro(HE)")
        self.assertIsNone(pid, "括号变体不同不该命中")

    def test_good_hit(self):
        q.cli_query = lambda *a, **k: [{"产品名称": "格力电饭煲GDCF-40X22Ca", "_id": "p9"}]
        name, pid, cat = q.find_product("GDCF-40X22Ca")
        self.assertEqual(pid, "p9")
        self.assertEqual(name, "格力电饭煲GDCF-40X22Ca")

    def test_no_candidate_returns_none(self):
        q.cli_query = lambda *a, **k: []
        self.assertEqual(q.find_product("不存在的型号ZZZ"), (None, None, None))

    def test_token_fallback_finds_differently_named_product(self):
        """★ 整串 like 查不到时，必须用型号码 token 兜底。
        实战：源表 `美的电热水器JSQ27-M12 MAX` vs 系统 `美的燃气热水器JSQ27-M12 Max`。"""
        seen = []

        def spy(obj, filters, fields, limit=50, offset=0):
            kw = filters[0]["field_values"][0]
            seen.append(kw)
            if kw == "JSQ27-M12":            # 只有型号码 token 能命中
                return [{"产品名称": "美的燃气热水器JSQ27-M12 Max", "_id": "pX"}]
            return []

        q.cli_query = spy
        name, pid, cat = q.find_product("美的电热水器JSQ27-M12 MAX")
        self.assertEqual(pid, "pX")
        self.assertEqual(name, "美的燃气热水器JSQ27-M12 Max")
        self.assertIn("JSQ27-M12", seen, "必须回退到型号码 token 查询")

    def test_token_fallback_respects_gates(self):
        """token 兜底命中的候选同样要过两道闸（品牌不一致 → 拒）。"""
        q.cli_query = lambda obj, filters, fields, limit=50, offset=0: [
            {"产品名称": "林内燃气热水器JSQ27-M12 Max", "_id": "pY"}]
        name, pid, cat = q.find_product("美的电热水器JSQ27-M12 MAX")
        self.assertIsNone(pid, "品牌不一致，token 兜底也不能放行")


class TestCodeMapping(_PatchBase):
    def test_to_code_hit(self):
        q.field_codes = lambda f: {"生活电器": "7"}
        self.assertEqual(q.to_code("field_yy0j1__c", "生活电器"), ("7", True))

    def test_to_code_miss_marks_unfound(self):
        q.field_codes = lambda f: {"生活电器": "7"}
        code, found = q.to_code("field_yy0j1__c", "未知品类")
        self.assertEqual(code, "未知品类")
        self.assertFalse(found, "转不出必须标记，便于进核对清单")

    def test_to_code_empty(self):
        self.assertEqual(q.to_code("f", ""), (None, False))

    def test_fetch_field_options_filters_disabled(self):
        """fetch_field_options 抽 label→value，且过滤 not_usable（停用选项提交会被拒）。"""
        class R:
            returncode = 0
            stderr = ""
            stdout = json.dumps({"fields": {"f_a": {"options": [
                {"label": "在用的", "value": "1", "not_usable": False},
                {"label": "停用的", "value": "2", "not_usable": True},
            ]}}}, ensure_ascii=False)

        q.subprocess.run = lambda *a, **k: R()
        self.assertEqual(q.fetch_field_options("f_a"), {"在用的": "1"})

    def test_fetch_field_options_bad_json_returns_empty(self):
        class R:
            returncode = 0
            stderr = ""
            stdout = "not json"

        q.subprocess.run = lambda *a, **k: R()
        self.assertEqual(q.fetch_field_options("f_a"), {})


class TestApplyPlan(_PatchBase):
    """报文构造：新建 / 更新分别要带什么。"""

    def setUp(self):
        super().setUp()
        self.sent = []
        outer = self

        class Stub:
            def create(self, obj, payload, execute=False):
                outer.sent.append(("create", obj, payload, execute))
                return ("CREATE", '{"errorCode":0}')

            def update(self, obj, payload, execute=False):
                outer.sent.append(("update", obj, payload, execute))
                return ("UPDATE", '{"errorCode":0}')

        q._client = lambda: Stub()
        q.field_codes = lambda f: {"生活电器": "7", "格力生活电器": "option_gree_living_appliances__c"}

    def _res(self, action, extra=None):
        item = {"model": "M1", "price": 438.0, "limit": 372.0, "settle": 372.0, "cost": 335.0,
                "brand": "格力", "pclass": "生活电器", "pitem": "格力生活电器",
                "product_name": "P", "product_id": "PID", "action": action,
                "detail": ({"_id": "DID"} if action == "更新" else None), "notes": []}
        if extra:
            item.update(extra)
        return {"org": "乾鑫", "pricebook_name": "PB", "pricebook_id": "PBID", "plans": [item]}

    def test_create_payload(self):
        q.apply_plan(self._res("新建"), dry_run=False)
        kind, obj, payload, execute = self.sent[0]
        self.assertEqual(kind, "create")
        self.assertEqual(obj, "PriceBookProductObj")
        self.assertTrue(execute)
        self.assertEqual(payload["pricebook_id"], "PBID")
        self.assertEqual(payload["product_id"], "PID")
        self.assertEqual(payload["record_type"], "default__c")
        # 4 个价字段必须显式传（pricebook_sellingprice 是默认值表达式，API 不自动算）
        for k in ("pricebook_sellingprice", "field_11k97__c", "field_108w9__c", "field_pFit1__c"):
            self.assertIn(k, payload)
            self.assertIsNotNone(payload[k])
        # select_one 必须是码值
        self.assertEqual(payload["field_yy0j1__c"], "7")
        self.assertEqual(payload["product_item__c"], "option_gree_living_appliances__c")
        self.assertNotIn("_id", payload)

    def test_update_payload_has_id(self):
        q.apply_plan(self._res("更新"), dry_run=False)
        kind, obj, payload, execute = self.sent[0]
        self.assertEqual(kind, "update")
        self.assertEqual(payload["_id"], "DID")
        self.assertNotIn("pricebook_id", payload)
        self.assertNotIn("product_id", payload)

    def test_unsynced_product_skipped(self):
        """产品未同步的行必须跳过，不得写入。"""
        res = self._res("产品未同步", {"product_id": None, "detail": None})
        out = q.apply_plan(res, dry_run=False)
        self.assertEqual(self.sent, [], "产品未同步绝不能写入")
        self.assertEqual(out[0][2], "跳过")

    def test_price_field_is_always_explicit(self):
        """价格为 None 的字段不进 payload（避免覆盖），但售价必须始终在。"""
        res = self._res("新建", {"cost": None})
        q.apply_plan(res, dry_run=False)
        payload = self.sent[0][1] if False else self.sent[0][2]
        self.assertIn("pricebook_sellingprice", payload)
        self.assertNotIn("field_pFit1__c", payload)

    def test_missing_code_gets_flagged(self):
        """label 转不出码值 → 原样提交 + 记 notes。"""
        q.field_codes = lambda f: {}
        res = self._res("新建")
        q.apply_plan(res, dry_run=False)
        self.assertTrue(any("未在系统选项里找到" in n for n in res["plans"][0]["notes"]))


class TestBuildPlanOffline(_PatchBase):
    """build_plan 端到端（全桩）。"""

    ROWS = [
        {"model": "GDCF-40X22Ca", "price": 438, "limit": 372, "settle": 372, "cost": 335,
         "note": None, "src_brand": "格力", "src_pclass": "生活电器", "src_pitem": "格力生活电器"},
        {"model": "F60-A20MD1(HI)", "price": 574, "limit": 488, "settle": 488, "cost": 439,
         "note": None, "src_brand": "美的", "src_pclass": "生活电器", "src_pitem": "格力生活电器"},
    ]

    def _stub_common(self, rows):
        bi.load_source_rows = lambda src, bh=None: (rows, "乾鑫", "A", "Sheet1", {})
        q.find_pricebook = lambda name: {"_id": "PBID", "价目表名称": name}

    def test_plan_marks_new_and_update(self):
        self._stub_common(self.ROWS)
        q.find_product = lambda model, hint=None: (
            ("格力电饭煲GDCF-40X22Ca", "PID1", "") if "GDCF" in model else ("美的电热水器F60-A20MD1(HI)", "PID2", ""))
        q.find_detail = lambda pid, pbid: ({"_id": "D1"} if pid == "PID2" else None)

        res = q.build_plan("dummy.xlsx", org="乾鑫")
        self.assertEqual([(p["model"], p["action"]) for p in res["plans"]],
                         [("GDCF-40X22Ca", "新建"), ("F60-A20MD1(HI)", "更新")])
        self.assertEqual(res["pricebook_id"], "PBID")

    def test_unsynced_product_action(self):
        self._stub_common([dict(self.ROWS[0], model="新型号ZZ")])
        q.find_product = lambda model, hint=None: (None, None, None)
        q.find_detail = lambda pid, pbid: None
        res = q.build_plan("dummy.xlsx", org="乾鑫")
        self.assertEqual(res["plans"][0]["action"], "产品未同步")
        self.assertTrue(any("绝不自行建产品" in n for n in res["plans"][0]["notes"]))

    def test_unknown_org_stops(self):
        with self.assertRaises(SystemExit):
            q.build_plan("dummy.xlsx", org="不存在的组织XYZ")

    def test_fmt_plan_summary(self):
        self._stub_common([self.ROWS[0]])
        q.find_product = lambda model, hint=None: ("格力电饭煲GDCF-40X22Ca", "PID1", "")
        q.find_detail = lambda pid, pbid: None
        txt = q.fmt_plan(q.build_plan("dummy.xlsx", org="乾鑫"))
        self.assertIn("汇总：新建 1 / 更新 0 / 产品未同步 0", txt)
        self.assertIn("已存在", txt)

    def test_brand_from_product_name_wins(self):
        """品牌以产品名称为准；源表写的「格力」与产品名的「大松」冲突 → 取大松并记 notes。"""
        self._stub_common([dict(self.ROWS[0], model="大松电风扇FSZ-S23Bg781",
                                src_brand="格力")])
        q.find_product = lambda model, hint=None: ("大松电风扇FSZ-S23Bg781", "PIDX", "")
        q.find_detail = lambda pid, pbid: None
        res = q.build_plan("dummy.xlsx", org="乾鑫")
        self.assertEqual(res["plans"][0]["brand"], "大松")
        self.assertTrue(any("品牌冲突" in n for n in res["plans"][0]["notes"]))


class TestBrandFromCategory(unittest.TestCase):
    """★ 2026-10-14 新增：品牌识别第 ① 级 —— 系统产品分类首段。"""

    def test_dash_prefix(self):
        self.assertEqual(bi.brand_from_category("K-追觅/K-追觅小家电/K-追觅扫地机器人"), "追觅")

    def test_underscore_prefix(self):
        self.assertEqual(bi.brand_from_category("K_大金/K_大金空调/K_大金挂机"), "大金")

    def test_no_prefix(self):
        self.assertEqual(bi.brand_from_category("美的/空调"), "美的")

    def test_single_segment(self):
        self.assertEqual(bi.brand_from_category("K-东芝"), "东芝")

    def test_lowercase_prefix(self):
        self.assertEqual(bi.brand_from_category("k-海尔/冰箱"), "海尔")

    def test_category_with_category_word_strips_to_brand(self):
        """实测坑：`K-东芝坐便器` 首段带品类词 → 必须得到「东芝」而非「东芝坐便器」。"""
        self.assertEqual(bi.brand_from_category("K-东芝坐便器"), "东芝")

    def test_long_brand_wins_in_category(self):
        self.assertEqual(bi.brand_from_category("K-AO史密斯热水器"), "AO史密斯")

    def test_empty_inputs(self):
        for v in (None, "", "   ", "/x/y"):
            self.assertEqual(bi.brand_from_category(v), "")


class TestResolveBrandPriority(unittest.TestCase):
    """三级兜底优先级：① 产品分类 → ② 产品名词表 → ③ 源表品牌列。"""

    def test_category_wins_over_all(self):
        # 分类说追觅、产品名也含追觅、源表写美的 → 取分类
        self.assertEqual(
            bi.resolve_brand("美的", "追觅扫地机器人X60PRO", "K-追觅/K-追觅小家电"), "追觅")

    def test_category_beats_model_table(self):
        # 分类给出词表里没有的品牌 → 仍采信分类（这正是修「追觅」漏识别的手段）
        self.assertEqual(bi.resolve_brand("", "扫地机器人X60PRO", "K-追觅/小家电"), "追觅")

    def test_model_table_when_no_category(self):
        self.assertEqual(bi.resolve_brand("", "大金挂机衡境FTXE135AC-H1", ""), "大金")

    def test_src_brand_is_last_resort(self):
        self.assertEqual(bi.resolve_brand("Ronshen/容声", "未知型号ZZZ", None), "容声")

    def test_nothing_recognized(self):
        self.assertEqual(bi.resolve_brand("", "未知型号ZZZ", ""), "")

    def test_category_none_backward_compatible(self):
        # 能力 2/3 快照通道不传 category → 行为同旧版
        self.assertEqual(bi.resolve_brand("格力", "大松电风扇FSZ-S23Bg781", None), "大松")


class TestBuildPlanBrandFromCategory(unittest.TestCase):
    """build_plan 端到端：产品分类首段直接决定品牌，并记 brand_src。"""

    def setUp(self):
        self.old = {}
        for a in ("find_pricebook", "find_product", "find_detail"):
            self.old[a] = getattr(q, a, None)
        self.old_lsr = bi.load_source_rows

    def tearDown(self):
        for a, v in self.old.items():
            if v is None:
                delattr(q, a)
            else:
                setattr(q, a, v)
        bi.load_source_rows = self.old_lsr

    def test_brand_taken_from_category(self):
        rows = [{"model": "追觅扫地机器人X60PRO智能上下水", "price": 6405, "limit": 4744,
                 "settle": 4270, "cost": 4270, "src_brand": "", "src_pclass": None,
                 "src_pitem": None}]
        bi.load_source_rows = lambda src, bh=None: (rows, "欣暖家", "A", "Sheet1", {})
        q.find_pricebook = lambda name: {"_id": "PB1"}
        q.find_product = lambda model, hint=None: (
            "追觅扫地机器人X60PRO智能上下水", "P1", "K-追觅/K-追觅小家电/K-追觅扫地机器人")
        q.find_detail = lambda pid, pbid: None

        res = q.build_plan("dummy.xlsx", org="欣暖家")
        p = res["plans"][0]
        self.assertEqual(p["brand"], "追觅")
        self.assertEqual(p["brand_src"], "产品分类")

    def test_brand_falls_back_to_model_table(self):
        rows = [{"model": "大金挂机衡境FTXE135AC-H1", "price": 6500, "limit": 5368,
                 "settle": 5368, "cost": 5100, "src_brand": "", "src_pclass": None,
                 "src_pitem": None}]
        bi.load_source_rows = lambda src, bh=None: (rows, "大金", "A", "Sheet1", {})
        q.find_pricebook = lambda name: {"_id": "PB2"}
        q.find_product = lambda model, hint=None: ("大金1.5匹变频挂机FTXE135AC-H1", "P2", "")
        q.find_detail = lambda pid, pbid: None

        res = q.build_plan("dummy.xlsx", org="大金")
        p = res["plans"][0]
        self.assertEqual(p["brand"], "大金")
        self.assertEqual(p["brand_src"], "产品名称")


if __name__ == "__main__":
    unittest.main(verbosity=2)
