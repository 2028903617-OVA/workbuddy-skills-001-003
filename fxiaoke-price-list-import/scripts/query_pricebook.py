#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
query_pricebook.py —— 价目表明细「实时查 → 落地」一体化（技能 v1.9.0 新主流程）

★ 取代旧「快照驱动」流程：**不再读两份 xlsx 导出快照**，改为通过连接器实时查系统。

两阶段（先查后写，符合铁律 1：先说明、后执行）：

  阶段 1（默认，纯只读）—— 查到「哪些要新建 / 哪些要更新」，报给用户等确认：
      python query_pricebook.py --source <源表.xlsx> --org 乾鑫

  阶段 2（用户确认后）—— 整理价格/品牌/品类/品项并直写：
      python query_pricebook.py --source <源表.xlsx> --org 乾鑫 --apply

查询通道：sharecrm CLI `data record query-by-fields`（底层 = 连接器服务 fs-mcpserver）
写入通道：OpenAPI（openapi_client.py 的 create / update；`--apply` 才真提交）

铁律：
  - 产品只能在金蝶新建后同步；系统查不到 → **回报用户，绝不自行建 ProductObj**
  - 写前必须查重（`product_id` + `pricebook_id` 双条件，结果不得截断）
  - `pricebook_sellingprice` 是默认值表达式，**必须显式传**
  - select_one 字段传**码值**，不传 label（码值表自动查 + 本地缓存）
"""
import argparse
import json
import os
import subprocess
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_import as bi  # noqa: E402

# ---------------------------------------------------------------- 环境

TOOLS_DIR = r"C:/Users/Administrator/WorkBuddy/纷享销客后台开发空间/工具/sharecrm-tools"
CRED_FILE = r"C:/Users/Administrator/.workbuddy/fxiaoke-app-003.json"
NODE_CANDIDATES = [
    r"C:/Users/Administrator/.workbuddy/binaries/node/versions/22.22.2-6/node.exe",
    r"C:/Users/Administrator/.workbuddy/binaries/node/versions/22.12.0/node.exe",
]
CLI_JS = (r"C:/Users/Administrator/.workbuddy/binaries/node/workspace/"
          r"node_modules/@share-crm/sharecrm-cli/dist/index.js")
CODE_CACHE = os.path.join(HERE, ".cache", "select_one_codes.json")

# 价目表明细：源表语义 → 系统字段 API 名
PB_FIELDS = {
    "cost": "field_pFit1__c",           # 成本价
    "settle": "field_108w9__c",         # 销售结算价
    "limit": "field_11k97__c",          # 品牌负责人审核价
    "price": "pricebook_sellingprice",  # 价目表售价（★默认值表达式，必须显式传）
    "brand": "field_xv1Bw__c",          # 品牌（text）
    "pclass": "field_yy0j1__c",         # 产品大类（select_one → 码值）
    "pitem": "product_item__c",         # 产品品项（select_one → 码值）
}


def _node():
    for p in NODE_CANDIDATES:
        if os.path.isfile(p):
            return p
    raise SystemExit("找不到 node.exe，请更新 NODE_CANDIDATES")


# ---------------------------------------------------------------- 连接器查询（只读）

class CliError(RuntimeError):
    pass


CLI_RETRIES = 4          # CLI 会话不稳（"fetch failed" 偶发）→ 必须重试
CLI_BACKOFF = 1.5        # 秒，线性退避


def _run_cli(args, tries=CLI_RETRIES):
    """跑 CLI 并返回 stdout；对偶发失败（fetch failed / 空输出）自动重试。

    ★ 实测坑（2026-10-13）：sharecrm CLI 偶发返回 `fetch failed`（同一条命令第 2 次就成功），
      不重试会把偶发网络抖动误判成「对象/记录不存在」。必须串行 + 重试。
    """
    last = ""
    for i in range(tries):
        p = subprocess.run([_node(), CLI_JS] + args,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        out = (p.stdout or "").strip()
        err = (p.stderr or "").strip()
        if out and not out.startswith("fetch failed"):
            return out
        last = ("fetch failed" if "fetch failed" in out + err else (err or out))[:200]
        if i < tries - 1:
            import time
            time.sleep(CLI_BACKOFF * (i + 1))
    raise CliError("CLI 连续 %d 次失败：%s" % (tries, last))


# ★★ 服务端硬上限（2026-10-13 服务端原话）：
#   「请求的 limit 100 超过最大值 50，查询未执行。请使用不超过 50 的 limit 和相同 offset 重试当前页；
#     仅在本次查询成功后，下一页 offset 才应为当前 offset 加 applied limit。不要重复使用同一个 offset」
#   → limit > 50 会**不执行查询**并在某些封装下表现成「0 条」，极易被误读成「记录不存在」→ 重复建。
MAX_LIMIT = 50
BLOCKING_NOTICES = ("LIMIT_EXCEEDED", "PERMISSION_DENIED", "INVALID_ARGUMENT",
                    "FIELDS_NOT_EXISTS", "OBJECT_NOT_EXISTS")


def cli_query(object_api_name, filters, select_fields, limit=50, offset=0):
    """调 sharecrm CLI 查记录，返回记录列表；**无命中返回 []**。

    ★ 实测坑 1（2026-10-13）：CLI 的 `recordResult` 有**两种结构**——
        · 有命中 → `recordResult` 是 **list**
        · 无命中 → `recordResult` 是 **dict**：`{totalNumber, records:[], searchTemplateQuery}`（伴 `EMPTY_RESULT` notice）
      直接 `hits[0]` 会在无命中时抛 `KeyError: 0`。此处统一归一化成 list。

    ★★ 实测坑 2（2026-10-13，**最危险**）：`search_template_query.limit` **上限 50**。
      limit=51/100/200 时服务端返回 notice **`LIMIT_EXCEEDED`**（`status=NOT_EXECUTED`，查询根本没跑），
      而 `recordResult` 退化成 `{totalNumber: 0, records: []}` —— **不报错、静默返回 0 条**！
      若不知情，会把「查重没命中」当成「明细不存在」→ **重复建明细**。
      故：① limit 自动夹到 MAX_LIMIT；② 一旦 notices 出现阻断码，**直接抛 CliError**，绝不返回空。
    """
    lim = int(limit) if limit else MAX_LIMIT
    if lim > MAX_LIMIT:
        lim = MAX_LIMIT                       # 夹紧，不让服务端静默清零
    data = {
        "object_api_name": object_api_name,
        "need_count": True,
        "select_fields": select_fields,
        "filters": filters,
        "search_template_query": {"limit": lim, "offset": int(offset or 0)},
    }
    out = _run_cli(["data", "record", "query-by-fields",
                    "--data", json.dumps(data, ensure_ascii=False)])
    try:
        d = json.loads(out)
    except Exception as e:
        raise CliError("CLI 输出非 JSON：%s | %s" % (e, out[:300]))
    if not isinstance(d, dict):
        return d if isinstance(d, list) else []
    notices = [n.get("code") for n in ((d.get("queryMeta") or {}).get("notices") or [])]
    bad = [c for c in notices if c in BLOCKING_NOTICES]
    if bad:
        raise CliError("CLI 返回阻断性 notice %s（结果不可信，已拒绝采信）：%s"
                       % (bad, json.dumps(d, ensure_ascii=False)[:400]))
    if "recordResult" not in d:
        # 形如 {"errorCode":..,"errorMessage":..} 的错误响应 → 明确抛出，不静默吞
        em = d.get("errorMessage") or d.get("message") or d.get("error")
        if em:
            raise CliError("CLI 报错：%s" % json.dumps(d, ensure_ascii=False)[:400])
        return []
    rr = d["recordResult"]
    if isinstance(rr, dict):            # 无命中形态
        return rr.get("records") or []
    return rr or []


def cli_query_all(object_api_name, filters, select_fields, page=MAX_LIMIT, max_records=20000):
    """翻页取**全部**命中（结果可 >100 条时用）。★ 查重/统计必须走这个，不得只看首页。

    检索口径与 cli_query 一致；`page` 上限 MAX_LIMIT。
    """
    page = min(int(page or MAX_LIMIT), MAX_LIMIT)
    got, offset = [], 0
    while len(got) < max_records:
        chunk = cli_query(object_api_name, filters, select_fields, limit=page, offset=offset)
        if not chunk:
            break
        got.extend(chunk)
        if len(chunk) < page:
            break
        offset += page
    return got


def find_pricebook(name):
    """按名称找价目表（精确 → 模糊），返回 dict 或 None。"""
    hits = cli_query("PriceBookObj", [{"field_name": "name", "field_values": [name], "operator": "eq"}],
                     ["_id", "name"], limit=5)
    if not hits:
        hits = cli_query("PriceBookObj", [{"field_name": "name", "field_values": [name], "operator": "like"}],
                         ["_id", "name"], limit=5)
    if not hits:
        return None
    for h in hits:
        if str(h.get("价目表名称") or h.get("name") or "").strip() == name:
            return h
    return hits[0]


def _brand_gate(model, cand_name):
    """★ 更严的品牌闸：两边都能识别出品牌且不同 → 拒。

    为什么不能只靠 `bi.fuzzy_ok` 的内置品牌闸：它用 `bi.brand_words()`（词表 `BRAND_WORDS`
    仅 31 词），而品牌词总表 `BRAND_KEYWORDS` 明显更大（含 林内 / 樱花 / 大松 …）。
    未收录的品牌在 `brand_words()` 里返回空集 → 判据 `if bs and bc and not (bs & bc)` 直接跳过
    → **不同品牌静默放行**。实战：源表 `美的电热水器JSQ27-M12 MAX` 会命中
    `林内燃气热水器JSQ27-M12 Max`（型号码相同）→ 价格挂到别家产品上。

    这里改用 `guess_brand_from_model`（走全量 BRAND_KEYWORDS），把该漏洞补上。
    两侧只有一边识别得出品牌时**不拦**（源表常只写型号码，不能因此拒掉正确命中）。
    """
    bm = bi.guess_brand_from_model(str(model))
    bc = bi.guess_brand_from_model(str(cand_name))
    if bm and bc and bm != bc:
        return False, "%s ≠ %s" % (bm, bc)
    return True, ""


def _product_candidates(query):
    """按一个关键词 like 搜产品，返回 [(产品名, id, 分类路径)]（去重保序）。

    ★ 带出 `category`：品牌识别第 ① 级的数据源（**分类路径首段即品牌**，
      见 `bi.brand_from_category`）。label 兼容「分类」/`category` 两种返回。
    """
    hits = cli_query("ProductObj",
                     [{"field_name": "name", "field_values": [query], "operator": "like"}],
                     ["_id", "name", "category"], limit=50)
    out = []
    for h in hits:
        nm = str(h.get("产品名称") or h.get("name") or "").strip()
        pid = h.get("_id")
        cat = str(h.get("分类") or h.get("category") or "").strip()
        if nm and pid and (nm, pid, cat) not in out:
            out.append((nm, pid, cat))
    return out


def find_product(model, name_hint=None):
    """按型号/名称查产品。返回 (系统产品名, 产品id, 分类路径) 或 (None, None, None)。

    ★ 查不到的**主因不是「系统没有」，而是「整串 like 命中不了」**：源表常写完整名称
      （`美的电热水器JSQ27-M12 MAX`），系统名却是另一套品类词 + 大小写
      （`美的燃气热水器JSQ27-M12 Max`）→ 整串 like 必然查不到。
      故按 **完整串 → 型号码 token** 的顺序逐级放宽候选生成，**再用两道闸把关**。

    两道闸（`bi.fuzzy_ok`）：① 型号码边界完整；② 品牌一致。
    都过不了 → 返回 (None, None, None)，由调用方标「产品未同步」交用户判定 —— **宁可漏报不误配**。
    """
    queries = []
    for q in (name_hint, model):
        if q and str(q).strip() and q not in queries:
            queries.append(str(q).strip())
    # 型号码 token 兜底（长的优先，命中面更精确）
    for t in sorted(bi.model_tokens(model), key=len, reverse=True):
        if t not in queries:
            queries.append(t)

    fallback = []            # 过不了闸但命中的候选，留作最后「整串包含」兜底
    for q in queries:
        cands = _product_candidates(q)
        if not cands:
            continue
        # ★ fuzzy_ok 返回 (ok, reason) 元组，元组恒为真 → 必须取 [0]，否则闸门失效
        # ★ 再叠一道更严的品牌闸 _brand_gate（fuzzy_ok 内置的品牌闸词表不全）
        good = [c for c in cands if bi.fuzzy_ok(model, c[0])[0] and _brand_gate(model, c[0])[0]]
        if good:
            good.sort(key=lambda c: (abs(len(c[0]) - len(model)), c[0]))
            return good[0]
        for c in cands:
            if c not in fallback:
                fallback.append(c)

    # 最后兜底：候选名**逐字包含**源表整串（品牌词差异时仍可能命中）
    core = str(model).strip()
    fb = [c for c in fallback if core.lower() in c[0].lower() and _brand_gate(model, c[0])[0]]
    if fb:
        fb.sort(key=lambda c: (abs(len(c[0]) - len(model)), c[0]))
        return fb[0]
    return None, None, None


def find_detail(product_id, pricebook_id):
    """双条件查重：返回明细 dict 或 None。★ 结果不得截断。"""
    hits = cli_query("PriceBookProductObj",
                     [{"field_name": "product_id", "field_values": [product_id], "operator": "eq"},
                      {"field_name": "pricebook_id", "field_values": [pricebook_id], "operator": "eq"}],
                     ["_id", "name", "product_name", "pricebook_sellingprice",
                      "field_11k97__c", "field_108w9__c", "field_pFit1__c",
                      "field_xv1Bw__c", "field_yy0j1__c", "product_item__c"], limit=20)
    return hits[0] if hits else None


# ---------------------------------------------------------------- select_one 码值

_code_cache = None


def _load_codes():
    global _code_cache
    if _code_cache is None:
        if os.path.isfile(CODE_CACHE):
            with open(CODE_CACHE, encoding="utf-8") as f:
                _code_cache = json.load(f)
        else:
            _code_cache = {}
    return _code_cache


def fetch_field_options(field_api_name, object_api_name="PriceBookProductObj"):
    """经 sharecrm CLI 取某字段的选项，返回 {label: value}。

    ★ 用 CLI `data describe get` 而不是 sharedev 通道 —— 少一条依赖链、
      不再需要 `.sharedev/settings.json`（CLI 的 `--data` 走同一服务端，返回同源数据）。
    ★ 过滤 `not_usable: true`（已停用选项）—— 停用选项提交会被拒。
    """
    data = {"object_api_name": object_api_name, "field_api_names": [field_api_name]}
    try:
        out = _run_cli(["data", "describe", "get",
                        "--data", json.dumps(data, ensure_ascii=False)])
    except CliError:
        return {}
    try:
        d = json.loads(out)
    except Exception:
        return {}
    f = (d.get("fields") or {}).get(field_api_name) or {}
    m = {}
    for opt in f.get("options") or []:
        if opt.get("not_usable"):
            continue
        lbl = opt.get("label")
        val = opt.get("value")
        if lbl and val not in (None, ""):
            m[str(lbl).strip()] = val
    return m


def field_codes(field_api_name):
    """返回 {label: value} 映射（带本地缓存，避免重复请求）。"""
    cache = _load_codes()
    if field_api_name in cache and cache[field_api_name]:
        return cache[field_api_name]
    m = fetch_field_options(field_api_name)
    if m:
        cache[field_api_name] = m
        os.makedirs(os.path.dirname(CODE_CACHE), exist_ok=True)
        with open(CODE_CACHE, "w", encoding="utf-8") as fh:
            json.dump(cache, fh, ensure_ascii=False, indent=2)
    return m


def to_code(field_api_name, label):
    """label → 码值；找不到原样返回并标记。"""
    if not label:
        return None, False
    m = field_codes(field_api_name)
    if label in m:
        return m[label], True
    return label, False


# ---------------------------------------------------------------- 组装

def build_plan(src, org=None, brand_hint=None):
    """解析源表 + 实时查询，产出逐行计划。"""
    # 显式给了 --org 就先校验，别读了源表才发现组织不认识（快速失败）
    if org and org not in bi.ORG_PRICEBOOKS:
        raise SystemExit("组织「%s」不在组织→价目表映射表里，请确认组织名" % org)
    rows, brand, fmt, sheet, idx = bi.load_source_rows(src, brand_hint)
    org = org or brand
    pb_name = bi.ORG_PRICEBOOKS.get(org)
    if not pb_name:
        raise SystemExit("组织「%s」不在组织→价目表映射表里，请确认组织名" % org)
    pb = find_pricebook(pb_name)
    if not pb:
        raise SystemExit("系统里找不到价目表「%s」" % pb_name)
    pb_id = pb.get("_id")

    plans = []
    for r in rows:
        model = r["model"]
        prod_name, prod_id, prod_cat = find_product(model, r.get("src_brand") and model)
        item = {
            "model": model,
            "price": r["price"], "limit": r["limit"], "settle": r["settle"], "cost": r["cost"],
            "src_brand": r.get("src_brand"), "src_pclass": r.get("src_pclass"), "src_pitem": r.get("src_pitem"),
            "product_name": prod_name, "product_id": prod_id,
            "detail": None, "action": None, "notes": [],
        }
        if not prod_id:
            item["action"] = "产品未同步"
            item["notes"].append("系统里查不到该产品 → 先在金蝶新建并同步，绝不自行建产品")
            plans.append(item)
            continue
        # 品牌：① 系统产品分类首段 → ② 产品名(词表) → ③ 源表品牌列（2026-10-14 三级兜底）
        b_from_cat = bi.brand_from_category(prod_cat)
        b_from_name = bi.guess_brand_from_model(prod_name or model)
        b_src = bi._src_brand_norm(r.get("src_brand"))
        item["brand"] = bi.resolve_brand(r.get("src_brand"), prod_name or model, prod_cat)
        item["brand_src"] = ("产品分类" if b_from_cat else
                             ("产品名称" if b_from_name else
                              ("源表品牌列" if b_src else "未识别")))
        if item["brand"] and b_src and item["brand"] != b_src:
            item["notes"].append("品牌冲突·已按%s为准（源表写「%s」）" % (item["brand_src"], b_src))
        # 大类/品项：按组织规则
        pclass, pitem, ok = bi.classify(model, org, r.get("src_pclass"), r.get("src_pitem"))
        item["pclass"], item["pitem"] = pclass, pitem
        item["class_matched"] = ok
        if not ok:
            item["notes"].append("分类未匹配关键词表 → 大类/品项留空（需你确认是否补填）")
        elif not (pclass or pitem):
            item["notes"].append("该品类在关键词表里定义为留空（大类/品项都不填），按组织规则")
        elif not (pclass and pitem):
            item["notes"].append("分类只填到一半（大类=%s / 品项=%s），按组织规则如此"
                                 % (pclass or "空", pitem or "空"))
        # 查重（★ 双条件；结果不得截断）
        det = find_detail(prod_id, pb_id)
        item["detail"] = det
        item["action"] = "更新" if det else "新建"
        plans.append(item)

    return {
        "org": org, "pricebook": pb, "pricebook_name": pb_name, "pricebook_id": pb_id,
        "sheet": sheet, "fmt": fmt, "plans": plans,
    }


def fmt_plan(res):
    """精简文本输出（省 token）。"""
    L = []
    L.append("%s → %s   id=%s" % (res["org"], res["pricebook_name"], res["pricebook_id"]))
    n_new = n_upd = n_miss = 0
    for i, p in enumerate(res["plans"], 1):
        if p["action"] == "新建":
            n_new += 1
        elif p["action"] == "更新":
            n_upd += 1
        else:
            n_miss += 1
        L.append("")
        L.append("%d. %s" % (i, p["model"]))
        if p["product_id"]:
            L.append("   产品  已存在  %s  (%s)" % (p["product_name"], p["product_id"]))
        else:
            L.append("   产品  **未同步**（系统查无）")
        if p["detail"]:
            d = p["detail"]
            L.append("   明细  已有 %s (%s) → 【%s】"
                     % (d.get("价目表明细编号") or d.get("name"), d.get("_id"), p["action"]))
        elif p["product_id"]:
            L.append("   明细  未建 → 【新建】")
        # ★ 更新时逐项对比「现值 → 新值」，让人一眼看出改了什么（铁律 1：先说明改什么）
        cur = p["detail"] or {}
        pairs = [("售价", p.get("price"), cur.get("价目表售价") or cur.get("pricebook_sellingprice"), PB_FIELDS["price"]),
                 ("审核", p.get("limit"), cur.get("品牌负责人审核价") or cur.get(PB_FIELDS["limit"]), PB_FIELDS["limit"]),
                 ("结算", p.get("settle"), cur.get("销售结算价") or cur.get(PB_FIELDS["settle"]), PB_FIELDS["settle"]),
                 ("成本", p.get("cost"), cur.get("成本价") or cur.get(PB_FIELDS["cost"]), PB_FIELDS["cost"])]
        if p["detail"]:
            show = []
            for label, new, old, _f in pairs:
                if new is None:
                    continue
                if old is None or old == "":
                    show.append("%s (空)→%s" % (label, new))
                elif str(old).rstrip("0").rstrip(".") == str(new).rstrip("0").rstrip("."):
                    show.append("%s %s(不变)" % (label, new))
                else:
                    show.append("%s %s→%s" % (label, old, new))
            if show:
                L.append("   改    %s" % " ".join(show))
            old_brand = cur.get("品牌") or cur.get(PB_FIELDS["brand"])
            if p.get("brand"):
                if old_brand and old_brand != p["brand"]:
                    L.append("   改    品牌 %s→%s" % (old_brand, p["brand"]))
                elif not old_brand:
                    L.append("   改    品牌 (空)→%s" % p["brand"])
            old_pc = cur.get("产品大类") or cur.get(PB_FIELDS["pclass"])
            old_pi = cur.get("产品品项") or cur.get(PB_FIELDS["pitem"])
            if (p.get("pclass") or p.get("pitem")) and (
                    (p.get("pclass") and p.get("pclass") != old_pc)
                    or (p.get("pitem") and p.get("pitem") != old_pi)):
                L.append("   改    分类 %s/%s → %s/%s"
                         % (old_pc or "空", old_pi or "空", p.get("pclass") or "空", p.get("pitem") or "空"))
        else:
            vals = []
            for label, new, _old, _f in pairs:
                if new is not None:
                    vals.append("%s%s" % (label, new))
            if vals:
                L.append("   值    %s" % " ".join(vals))
        extra = [x for x in [p.get("brand"), p.get("pclass"), p.get("pitem")] if x]
        if extra:
            L.append("   分类  %s" % " | ".join(extra))
        for n in p["notes"]:
            L.append("   ! %s" % n)
    L.append("")
    L.append("汇总：新建 %d / 更新 %d / 产品未同步 %d" % (n_new, n_upd, n_miss))
    return "\n".join(L)


# ---------------------------------------------------------------- 写入（阶段 2）

def _client():
    sys.path.insert(0, TOOLS_DIR)
    import openapi_client as oc
    ns = types.SimpleNamespace(cred_file=CRED_FILE, domain=None, app_id=None, app_secret=None,
                               permanent_code=None, open_user_id=None, user_id=None,
                               token=None, ea=None)
    return oc.build_client(ns)


def apply_plan(res, dry_run=True):
    """按计划直写。dry_run=True 只打印报文。"""
    c = _client()
    results = []
    for p in res["plans"]:
        if p["action"] not in ("新建", "更新"):
            results.append((p["model"], p["action"], "跳过"))
            continue
        codes = {}
        for key, field in (("pclass", PB_FIELDS["pclass"]), ("pitem", PB_FIELDS["pitem"])):
            code, found = to_code(field, p.get(key))
            if code:
                codes[key] = code
                if not found:
                    p["notes"].append("%s「%s」未在系统选项里找到，原样提交（可能被拒）" % (key, p.get(key)))
        payload = {
            PB_FIELDS["price"]: p.get("price"),
            PB_FIELDS["limit"]: p.get("limit"),
            PB_FIELDS["settle"]: p.get("settle"),
            PB_FIELDS["cost"]: p.get("cost"),
        }
        if p.get("brand"):
            payload[PB_FIELDS["brand"]] = p["brand"]
        if codes.get("pclass"):
            payload[PB_FIELDS["pclass"]] = codes["pclass"]
        if codes.get("pitem"):
            payload[PB_FIELDS["pitem"]] = codes["pitem"]
        payload = {k: v for k, v in payload.items() if v is not None}

        if p["action"] == "新建":
            payload.update({"pricebook_id": res["pricebook_id"], "product_id": p["product_id"],
                            "record_type": "default__c"})
            r = c.create("PriceBookProductObj", payload, execute=not dry_run)
        else:
            payload["_id"] = p["detail"]["_id"]
            r = c.update("PriceBookProductObj", payload, execute=not dry_run)
        results.append((p["model"], p["action"], "DRY" if dry_run else json.dumps(
            r[1] if isinstance(r, (list, tuple)) else r, ensure_ascii=False)[:160]))
    return results


def main():
    ap = argparse.ArgumentParser(description="价目表明细实时查+落地（快照已弃用）")
    ap.add_argument("--source", required=True, help="源表 xlsx")
    ap.add_argument("--org", help="组织（决定价目表）；不传则从源表识别")
    ap.add_argument("--brand", help="组织别名（等价 --org，兼容旧参数）")
    ap.add_argument("--apply", action="store_true", help="用户确认后才加：真正写入")
    ap.add_argument("--json", action="store_true", help="输出 JSON 而非精简文本")
    a = ap.parse_args()

    res = build_plan(a.source, org=a.org or a.brand)
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=2, default=str))
        return
    print(fmt_plan(res))
    if a.apply:
        print("\n=== 执行写入 ===")
        for model, action, out in apply_plan(res, dry_run=False):
            print("  %-28s %-6s %s" % (model, action, out))
    else:
        print("\n[只读] 未写入。确认后加 --apply 落地。")


if __name__ == "__main__":
    main()
