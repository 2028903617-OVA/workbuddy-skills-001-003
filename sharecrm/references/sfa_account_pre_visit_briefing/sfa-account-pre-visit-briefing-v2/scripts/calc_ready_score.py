#!/usr/bin/env python3
"""根据结构化 CRM 摘要计算见客就绪度。

输入：通过标准输入传入 JSON，或通过命令行参数传入 JSON 文件路径。
输出：包含分项分、综合就绪度、等级和缺失字段的 JSON。

输入格式刻意使用简单布尔值和枚举，便于 Agent 从不完整 CRM 数据中组装，
不需要完整复刻 CRM 对象结构。
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime
from typing import Any


GRADE_READY = [
    (80, "green", "就绪"),
    (60, "yellow", "准备中"),
    (40, "orange", "不足"),
    (0, "red", "危险"),
]

GRADE_COMPETITION = [
    (71, "red", "高风险"),
    (51, "orange", "中高风险"),
    (26, "yellow", "中低风险"),
    (0, "green", "低风险"),
]


def load_input() -> dict[str, Any]:
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            return json.load(f)
    text = sys.stdin.read()
    if not text.strip():
        raise SystemExit(
            "用法：calc_ready_score.py input.json\n"
            "  或：cat input.json | calc_ready_score.py"
        )
    return json.loads(text)


def parse_date(value: Any) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    text = str(value)
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        return None


def freshness_factor(last_updated: Any) -> float:
    updated = parse_date(last_updated)
    if not updated:
        return 0.5
    days = (date.today() - updated).days
    if days <= 30:
        return 1.0
    if days <= 90:
        return 0.8
    if days <= 180:
        return 0.5
    return 0.2


def grade(score: float, table: list[tuple[int, str, str]]) -> dict[str, str]:
    rounded = max(0, min(100, round(score)))
    for threshold, color, label in table:
        if rounded >= threshold:
            return {"color": color, "label": label}
    return {"color": "red", "label": "危险"}


def score_information(data: dict[str, Any]) -> tuple[float, list[str]]:
    weights = {
        "basic_info": 10,
        "decision_chain": 25,
        "recent_interactions": 25,
        "business_pain": 20,
        "financial_or_strategy_signal": 20,
    }
    missing: list[str] = []
    raw = 0.0
    for key, weight in weights.items():
        if data.get(key):
            raw += weight
        else:
            missing.append(key)
    return raw * freshness_factor(data.get("last_updated")), missing


def score_pain_match(data: dict[str, Any]) -> tuple[float, list[str]]:
    pains = data.get("pain_points") or []
    if not pains:
        return 0.0, ["pain_points"]

    product_fit = {"P1": 1.0, "P2": 0.7, "P3": 0.4, "P0": 0.0}
    evidence = {"E1": 1.0, "E2": 0.8, "E3": 0.6, "E4": 0.3}

    scores: list[float] = []
    missing: list[str] = []
    for index, pain in enumerate(pains, start=1):
        fit = product_fit.get(str(pain.get("product_fit", "")).upper())
        ev = evidence.get(str(pain.get("evidence", "")).upper())
        if fit is None:
            missing.append(f"pain_points[{index}].product_fit")
            fit = 0.0
        if ev is None:
            missing.append(f"pain_points[{index}].evidence")
            ev = 0.0
        scores.append(100 * fit * ev * freshness_factor(pain.get("last_mentioned")))

    return sum(scores) / len(scores), missing


def infer_competitor_signal_status(data: dict[str, Any]) -> str:
    explicit = str(data.get("competitor_signal_status", "")).strip().lower()
    if explicit in {"none", "unknown", "confirmed"}:
        return explicit

    stage = str(data.get("competitor_stage", "")).upper()
    if stage in {"C2", "C3", "C4"} or data.get("competitors"):
        return "confirmed"
    if stage == "C1":
        return "unknown"
    return "none"


def score_competition(data: dict[str, Any]) -> tuple[float, list[str], str]:
    stage_risk_map = {"C1": 35, "C2": 55, "C3": 72, "C4": 85}
    differentiation_map = {"D1": -20, "D2": -10, "D3": 5, "D4": 20}
    readiness_credits = {
        "comparison_doc": -15,
        "talk_track": -10,
        "pricing_known": -5,
    }

    missing: list[str] = []
    signal_status = infer_competitor_signal_status(data)

    if signal_status == "none":
        return 10.0, missing, signal_status

    if signal_status == "unknown":
        return 45.0, ["competitor_evidence"], signal_status

    stage = str(data.get("competitor_stage", "")).upper()
    if "competitor_stage" not in data:
        missing.append("competitor_stage")
    risk = float(stage_risk_map.get(stage, 55))

    ratio = data.get("relationship_ratio")
    if ratio is None:
        missing.append("relationship_ratio")
    else:
        ratio = float(ratio)
        if ratio > 1.5:
            risk -= 20
        elif ratio < 0.5:
            risk += 30
        elif ratio < 0.8:
            risk += 15

    diff = str(data.get("differentiation", "")).upper()
    if not diff:
        diff = "D3"
    risk += differentiation_map.get(diff, 10)
    if "differentiation" not in data:
        missing.append("differentiation")

    prep = data.get("competition_preparation") or {}
    for key, credit in readiness_credits.items():
        if prep.get(key):
            risk += credit

    return max(0, min(100, risk)), missing, signal_status


def probability_adjustment(probability: Any) -> int:
    if probability is None:
        return 0
    value = float(probability)
    if value >= 70:
        return 5
    if value >= 40:
        return 0
    if value >= 20:
        return -5
    return -10


def main() -> None:
    data = load_input()
    info_score, info_missing = score_information(data)
    pain_score, pain_missing = score_pain_match(data)
    competition_risk, competition_missing, competition_signal_status = score_competition(data)
    adjustment = probability_adjustment(data.get("crm_probability"))

    readiness = (
        info_score * 0.35
        + pain_score * 0.35
        + (100 - competition_risk) * 0.30
        + adjustment
    )
    readiness = max(0, min(100, readiness))

    result = {
        "information_completeness": round(info_score),
        "pain_point_match": round(pain_score),
        "competitive_risk": round(competition_risk),
        "competitor_signal_status": competition_signal_status,
        "crm_probability_adjustment": adjustment,
        "readiness": round(readiness),
        "readiness_grade": grade(readiness, GRADE_READY),
        "competitive_grade": grade(competition_risk, GRADE_COMPETITION),
        "missing_fields": info_missing + pain_missing + competition_missing,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
