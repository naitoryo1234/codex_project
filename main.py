import json
import math
import uuid
import html
from pathlib import Path
from typing import Dict, List

import altair as alt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# 險ｭ螳壹＃縺ｨ縺ｮ5譫壼ｽｹ蠖馴∈遒ｺ邇・
SETTINGS: Dict[str, float] = {
    "1": 1 / 38.15,
    "2": 1 / 36.86,
    "4": 1 / 30.27,
    "5": 1 / 24.51,
    "6": 1 / 22.53,
}
SETTING_KEYS: List[str] = list(SETTINGS.keys())

KOYAKU_COMPONENT_BUILD_DIR = Path(__file__).parent / 'koyaku_counter_component' / 'build'
if KOYAKU_COMPONENT_BUILD_DIR.exists():
    _koyaku_counter_component = components.declare_component(
        'koyaku_counter',
        path=str(KOYAKU_COMPONENT_BUILD_DIR),
    )
else:
    _koyaku_counter_component = None


def render_koyaku_counter(**kwargs):
    if _koyaku_counter_component is None:
        st.info("Component assets not found. Please run `npm run build` in `koyaku_counter_component` and reload the app.")
        return None
    return _koyaku_counter_component(**kwargs)


def calculate_likelihood(num_spins: int, num_hits: int, p: float) -> float:
    """莠碁・・蟶・・蟆､蠎ｦ P(K=k | N=n, p)縲ょ､ｧ縺阪↑蛟､縺ｧ繧ょｮ牙ｮ壹☆繧九ｈ縺・ｯｾ謨ｰ險育ｮ励ｒ逕ｨ縺・ｋ縲・""
    if p <= 0.0 or p >= 1.0 or num_spins <= 0 or num_hits < 0 or num_hits > num_spins:
        return 0.0
    log_nCk = (
        math.lgamma(num_spins + 1)
        - math.lgamma(num_hits + 1)
        - math.lgamma(num_spins - num_hits + 1)
    )
    log_likelihood = (
        log_nCk
        + num_hits * math.log(p)
        + (num_spins - num_hits) * math.log(1.0 - p)
    )
    return math.exp(log_likelihood)


def normalize(priors: Dict[str, float]) -> Dict[str, float]:
    total = sum(max(0.0, priors.get(k, 0.0)) for k in SETTING_KEYS)
    if total <= 0.0:
        uniform = 1.0 / len(SETTING_KEYS)
        return {k: uniform for k in SETTING_KEYS}
    return {k: max(0.0, priors.get(k, 0.0)) / total for k in SETTING_KEYS}


def compute_posteriors(num_spins: int, num_hits: int, priors: Dict[str, float]) -> Dict[str, float]:
    priors = normalize(priors)
    posterior_numerators: Dict[str, float] = {}
    marginal_likelihood = 0.0
    for key in SETTING_KEYS:
        p = SETTINGS[key]
        prior = priors.get(key, 0.0)
        likelihood = calculate_likelihood(num_spins, num_hits, p) if prior > 0.0 else 0.0
        numerator = likelihood * prior
        posterior_numerators[key] = numerator
        marginal_likelihood += numerator
    if marginal_likelihood > 0.0:
        return {k: posterior_numerators[k] / marginal_likelihood for k in SETTING_KEYS}
    return priors


def format_one_over(prob: float) -> str:
    if prob <= 0.0:
        return "0"
    inv = 1.0 / prob
    if inv >= 1000:
        return f"1/{inv:,.0f}"
    if inv >= 100:
        return f"1/{inv:.1f}"
    return f"1/{inv:.2f}"


def format_percent(prob: float) -> str:
    return f"{prob * 100.0:.2f}%"




def render_plain_text(text: str, classes: str = "plain-text") -> None:
    escaped = html.escape(text).replace("\n", "<br />")
    st.markdown(
        f"<div class='{classes}'>{escaped}</div>",
        unsafe_allow_html=True,
    )

def render_small_text(text: str, classes: str = "reliability-comment") -> None:
    escaped = html.escape(text).replace("\n", "<br />")
    st.markdown(
        f"<div class='{classes}'>{escaped}</div>",
        unsafe_allow_html=True,
    )


star_labels = {
    5: "縺九↑繧雁ｮ牙ｿ・,
    4: "繧・ｄ螳牙ｿ・,
    3: "莠泌・莠泌・",
    2: "諷朱㍾",
    1: "蜴ｳ縺励＞",
}

GOAL_CONFIG = {
    "456": {
        "min_sample_warn": 120,
        "min_sample_good": 220,
        "ci_warn": 18.0,
        "ci_good": 10.5,
        "goal_thresholds": {"high": 75.0, "mid": 65.0, "low": 48.0},
        "diff_thresholds": {"high": 15.0, "mid": 7.0},
        "negative_diff_thresholds": {"mid": -5.0, "high": -10.0},
        "ratio_thresholds": {"high": 2.0, "mid": 1.5},
        "strong_diff": 16.0,
        "strong_ratio": 2.2,
        "diff_close": 6.0,
        "strict": {"goal": 78.0, "diff": 18.0, "ratio": 2.4, "sample": 240},
        "comments": {
            "insufficient": "繧ｵ繝ｳ繝励Ν縺悟ｰ代↑縺上・56縺ｮ蛻､蛻･縺ｫ縺ｯ縺ｾ縺謠ｺ繧峨℃縺悟､ｧ縺阪＞迥ｶ豕√〒縺吶ゅ∪縺壹・繝・・繧ｿ繧帝寔繧√∪縺励ｇ縺・・,
            "very_low": "迴ｾ迥ｶ縺ｯ菴手ｨｭ螳壼ｯ・ｊ縺ｮ繝・・繧ｿ縺ｧ456迢吶＞縺ｯ蜴ｳ縺励＞螻暮幕縺ｧ縺吶・,
            "low": "456迢吶＞縺ｫ縺ｯ縺ｾ縺陬丈ｻ倥￠縺御ｸ崎ｶｳ縺励※縺・∪縺吶よ・驥阪↓讒伜ｭ舌ｒ隕九∪縺励ｇ縺・・,
            "mid": "456縺ｮ闃ｽ縺ｯ縺ゅｊ縺ｾ縺吶′縲∬ｿｽ蜉繧ｵ繝ｳ繝励Ν縺ｧ蛯ｾ蜷代ｒ蜀咲｢ｺ隱阪＠縺溘＞繝ｩ繧､繝ｳ縺ｧ縺吶・,
            "high": "456蟇・ｊ縺梧ｿ・字縺ｧ縺吶ゅｂ縺・ｰ代＠蝗槭○縺ｰ遒ｺ菫｡縺梧戟縺ｦ縺昴≧縺ｧ縺吶・,
            "very_high": "456迢吶＞縺ｧ繧ょｮ牙ｿ・＠縺ｦ邊倥ｌ繧九ョ繝ｼ繧ｿ縺ｧ縺吶・,
        },
    },
    "56": {
        "min_sample_warn": 160,
        "min_sample_good": 240,
        "ci_warn": 12.0,
        "ci_good": 7.0,
        "goal_thresholds": {"high": 58.0, "mid": 50.0, "low": 35.0},
        "diff_thresholds": {"high": 8.0, "mid": 4.0},
        "negative_diff_thresholds": {"mid": -4.0, "high": -8.0},
        "ratio_thresholds": {"high": 1.8, "mid": 1.3},
        "strong_diff": 10.0,
        "strong_ratio": 1.7,
        "diff_close": 4.5,
        "strict": {"goal": 62.0, "diff": 12.0, "ratio": 1.9, "sample": 220},
        "comments": {
            "insufficient": "繧ｵ繝ｳ繝励Ν縺悟ｰ代↑縺上∬ｨｭ螳・繝ｻ6縺ｮ蛻､蛻･縺ｫ縺ｯ縺ｾ縺陬丈ｻ倥￠縺瑚ｶｳ繧翫∪縺帙ｓ縲りｿｽ蜉縺ｧ蝗櫁ｻ｢謨ｰ繧堤｢ｺ菫昴＠縺ｾ縺励ｇ縺・・,
            "very_low": "險ｭ螳・繝ｻ6縺ｯ縺九↑繧願埋縺・憾豕√〒縺吶ら┌逅・↓56迢吶＞縺ｫ蝗ｺ蝓ｷ縺励↑縺・婿縺瑚ｳ｢譏弱〒縺吶・,
            "low": "險ｭ螳・繝ｻ6繧堤漁縺・↓縺ｯ陬丈ｻ倥￠縺御ｸ崎ｶｳ縺励※縺・∪縺吶りｨｭ螳・繝ｩ繧､繝ｳ繧りｦ夜㍽縺ｫ諷朱㍾縺ｫ縲・,
            "mid": "險ｭ螳・繝ｻ6縺ｮ蜿ｯ閭ｽ諤ｧ縺ｯ縺ゅｊ縺ｾ縺吶′縲∬ｨｭ螳・縺ｨ縺ｮ遶ｶ繧雁粋縺・〒縺吶りｿｽ蜉繧ｵ繝ｳ繝励Ν縺ｧ隕区･ｵ繧√ｒ縲・,
            "high": "險ｭ螳・繝ｻ6縺後°縺ｪ繧頑怏蜉帙〒縺吶よ款縺怜・繧九↑繧峨メ繝｣繝ｳ繧ｹ縺ｧ縺吶・,
            "very_high": "險ｭ螳・繝ｻ6譛ｬ蜻ｽ縺ｧ蜍晁ｲ縺ｧ縺阪ｋ豼・＆縺ｧ縺吶ょ､ｧ縺阪↑繝√Ε繝ｳ繧ｹ縺ｨ險縺医∪縺吶・,
        },
    },
}

thresholds_456 = [
    (5, {"min_n": 280, "min_goal": 0.82, "min_diff": 0.32, "min_ratio": 2.6}),
    (4, {"min_n": 220, "min_goal": 0.74, "min_diff": 0.22, "min_ratio": 2.1}),
    (3, {"min_n": 180, "min_goal": 0.65, "min_diff": 0.12, "min_ratio": 1.6}),
    (2, {"min_n": 140, "min_goal": 0.54, "min_diff": 0.05, "min_ratio": 1.2}),
]

thresholds_56 = [
    (5, {"min_n": 260, "min_goal": 0.62, "min_diff": 0.15, "min_ratio": 2.0}),
    (4, {"min_n": 220, "min_goal": 0.54, "min_diff": 0.10, "min_ratio": 1.7}),
    (3, {"min_n": 180, "min_goal": 0.46, "min_diff": 0.06, "min_ratio": 1.4}),
    (2, {"min_n": 160, "min_goal": 0.38, "min_diff": 0.02, "min_ratio": 1.15}),
]



def evaluate_goal(goal_code: str, goal_prob: float, alt_prob: float, thresholds, ci_range_pct: float):
    config = GOAL_CONFIG[goal_code]
    sample_n = st.session_state.n

    alt_prob_safe = max(alt_prob, 1e-9)
    ratio = goal_prob / alt_prob_safe if alt_prob_safe > 0 else float("inf")
    diff = goal_prob - alt_prob
    diff_pct = diff * 100.0
    goal_prob_pct = goal_prob * 100.0

    insufficient_sample = (
        sample_n < config["min_sample_warn"]
        or ci_range_pct >= config["ci_warn"]
    )

    if (
        diff_pct >= config["strong_diff"]
        and ratio >= config["strong_ratio"]
        and goal_prob_pct >= config["goal_thresholds"]["mid"]
    ):
        insufficient_sample = False

    score = 0

    thresholds_goal = config["goal_thresholds"]
    if goal_prob_pct >= thresholds_goal["high"]:
        score += 2
    elif goal_prob_pct >= thresholds_goal["mid"]:
        score += 1
    elif goal_prob_pct <= thresholds_goal["low"]:
        score -= 1

    diff_thresholds = config["diff_thresholds"]
    neg_thresholds = config["negative_diff_thresholds"]
    if diff_pct >= diff_thresholds["high"]:
        score += 2
    elif diff_pct >= diff_thresholds["mid"]:
        score += 1
    elif diff_pct <= neg_thresholds["high"]:
        score -= 2
    elif diff_pct <= neg_thresholds["mid"]:
        score -= 1

    ratio_thresholds = config["ratio_thresholds"]
    if ratio >= ratio_thresholds["high"]:
        score += 2
    elif ratio >= ratio_thresholds["mid"]:
        score += 1
    elif ratio <= 1.0 / ratio_thresholds["high"]:
        score -= 2
    elif ratio <= 1.0 / ratio_thresholds["mid"]:
        score -= 1

    if ci_range_pct <= config["ci_good"]:
        score += 1
    elif ci_range_pct >= config["ci_warn"]:
        score -= 1

    if sample_n >= config["min_sample_good"]:
        score += 1
    elif sample_n < config["min_sample_warn"]:
        score -= 1

    if insufficient_sample:
        star = 2 if goal_prob_pct >= thresholds_goal["mid"] else 1
    else:
        if diff_pct < diff_thresholds["mid"]:
            score -= 1

        if score >= 7:
            star = 5
        elif score >= 4:
            star = 4
        elif score >= 1:
            star = 3
        elif score >= -1:
            star = 2
        else:
            star = 1

        if star == 5:
            strict = config.get("strict", {})
            strict_goal = strict.get("goal", thresholds_goal["high"])
            strict_diff = strict.get("diff", diff_thresholds["high"])
            strict_ratio = strict.get("ratio", ratio_thresholds["high"]) 
            strict_sample = strict.get("sample", config["min_sample_good"])
            if (
                goal_prob_pct < strict_goal
                or diff_pct < strict_diff
                or ratio < strict_ratio
                or sample_n < strict_sample
                or ci_range_pct > config["ci_good"]
            ):
                star = 4

    stars_text = "笘・ * star + "笘・ * (5 - star)
    ratio_text = "竏・ if math.isinf(ratio) else f"{ratio:.1f}x"

    comments = config["comments"]
    if insufficient_sample:
        comment = comments["insufficient"]
    else:
        if star == 5:
            comment = comments["very_high"]
        elif star == 4:
            comment = comments["high"]
        elif star == 3:
            comment = comments["mid"]
        elif star == 2:
            comment = comments["low"]
        else:
            comment = comments["very_low"]

        diff_close = config["diff_close"]
        if diff_pct >= diff_thresholds["high"] and ratio >= ratio_thresholds["high"]:
            comment += " 蜆ｪ菴肴ｧ縺ｯ縺ｯ縺｣縺阪ｊ縺励※縺・∪縺吶・
        elif -diff_close <= diff_pct <= diff_close and star <= 3:
            comment += " 莉翫・遶ｶ繧雁粋縺・↑縺ｮ縺ｧ霑ｽ蜉縺ｮ繝・・繧ｿ縺ｧ隕区･ｵ繧√∪縺励ｇ縺・・
        elif diff_pct < -diff_close:
            comment += " 迴ｾ迥ｶ縺ｯ莉冶ｨｭ螳壹・譁ｹ縺悟━蜍｢縺ｧ縺吶・

    comment += f" (蟾ｮ {diff_pct:.1f}pt / 豈・{ratio_text})"

    thresholds_dict = {star_key: cond for star_key, cond in thresholds}
    target_n = None
    if insufficient_sample:
        target_n = max(config["min_sample_warn"], config["min_sample_good"])
    else:
        for higher_star in sorted(thresholds_dict.keys()):
            if higher_star > star:
                target_n = thresholds_dict[higher_star].get("min_n", sample_n)
                break
        if target_n is None and star < 5:
            target_n = config["min_sample_good"]
        if target_n is not None and target_n < config["min_sample_warn"]:
            target_n = config["min_sample_warn"]

    if target_n is not None:
        needed = target_n - sample_n
        if needed > 0:
            needed = int(math.ceil(needed / 50.0) * 50)
            if needed >= 50:
                comment += f" 逶ｮ螳峨→縺励※縺ゅ→邏кneeded}G蝗槭☆縺ｨ谺｡縺ｮ菫｡鬆ｼ蠎ｦ繧堤漁縺医∪縺吶・

    return {
        "stars": star,
        "stars_text": stars_text,
        "label": star_labels[star],
        "comment": comment,
        "diff_pct": diff_pct,
        "ratio_text": ratio_text,
        "goal_prob": goal_prob,
        "alt_prob": alt_prob,
        "insufficient": insufficient_sample,
    }




# Safari莠呈鋤縺ｮ縺溘ａ縲　media繧辿TML螳滉ｽ灘盾辣ｧ縺ｫ螟画鋤縺宥FM縺ｮ蜻ｽ蜷肴ｭ｣隕剰｡ｨ迴ｾ逕滓・繧貞屓驕ｿ縺吶ｋ
st.set_page_config(
    page_title="險ｭ螳壽耳螳壹ヤ繝ｼ繝ｫ",
    page_icon="鴫",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      .block-container { padding-top: calc(1.1rem + env(safe-area-inset-top)); padding-bottom: 1.6rem; max-width: 960px; }
      h1 { font-size: 1.45rem !important; margin-bottom: 0.6rem; }
      label, .stMarkdown p { font-size: 0.9rem; }
      .stNumberInput input { font-size: 0.95rem; padding: 0.45rem 0.6rem; }
      .copy-share-container { margin: 0.2rem 0 0.3rem; }
      .copy-share-container button { padding: 0.45rem 0.85rem; background-color: #2F80ED; border: none; border-radius: 0.55rem; color: #ffffff; font-size: 0.92rem; cursor: pointer; }
      .copy-share-container button:hover { background-color: #1C5FC4; }
      .plain-text { font-size: 0.9rem; color: #303030; margin: 0.15rem 0 0.5rem; line-height: 1.5; }
      .helper-text { font-size: 0.88rem; color: #4a4a4a; margin-bottom: 0.5rem; }
      .info-box { background-color: #f1f3f5; border-radius: 0.6rem; padding: 0.85rem 0.95rem; font-size: 0.9rem; color: #2f3035; line-height: 1.45; }
      .result-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 0.6rem; margin: 0.7rem 0 0.8rem; }
      .result-card { background-color: #ffffff; border: 1px solid #e2e4e8; border-radius: 0.55rem; padding: 0.65rem 0.75rem; box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08); display: flex; flex-direction: column; gap: 0.3rem; min-height: 86px; }
      .result-label { font-size: 0.82rem; color: #4a4f57; letter-spacing: 0.01em; }
      .result-value { font-size: 1.05rem; font-weight: 600; color: #1f2329; font-variant-numeric: tabular-nums; }
      .result-sub { font-size: 0.9rem; color: #5b6269; }
      .pair-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 0.55rem; margin-top: 0.5rem; }
      .pair-card { background-color: #f8f9fb; border-radius: 0.55rem; padding: 0.65rem 0.75rem; display: flex; flex-direction: column; gap: 0.25rem; }
      .pair-label { font-size: 0.82rem; color: #4a4f57; }
      .pair-main { font-size: 1rem; font-weight: 600; color: #1f2329; font-variant-numeric: tabular-nums; }
      .pair-delta { font-size: 0.85rem; color: #5f6368; }
      .setting-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 0.55rem; margin-top: 0.6rem; }
      .setting-item { background-color: #ffffff; border: 1px solid #e0e2e6; border-radius: 0.55rem; padding: 0.6rem 0.75rem; display: flex; flex-direction: column; gap: 0.25rem; box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05); }
      .setting-title { font-size: 0.82rem; color: #57606a; }
      .setting-values { font-size: 0.9rem; color: #24292f; font-variant-numeric: tabular-nums; display: flex; flex-direction: column; gap: 0.2rem; }
      .reliability-caption { font-size: 0.82rem; color: #5f6368; margin-bottom: 0.4rem; }
      .reliability-comment { font-size: 0.88rem; color: #404650; margin: 0.2rem 0 0.7rem; line-height: 1.45; }
      .koyaku-caption { font-size: 0.78rem; color: #5c6570; margin-top: 0.35rem; }
      div[data-testid="stExpander"]:first-of-type > details summary span { font-size: 0.9rem; }

      &#64;media (max-width: 640px) {
        .block-container { padding-left: 0.55rem; padding-right: 0.55rem; }
        .result-card, .pair-card, .setting-item { padding: 0.55rem 0.65rem; }
        .result-value { font-size: 0.98rem; }
        .pair-main { font-size: 0.95rem; }
        h1 { font-size: 1.35rem !important; }
      }
      &#64;media (max-width: 420px) {
        .block-container { padding-left: 0.45rem; padding-right: 0.45rem; }
        .copy-share-container button { min-width: 54px; font-size: 0.88rem; }
        .plain-text { font-size: 0.85rem; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    &#64;media (max-width: 640px) {
      div[data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: nowrap !important; }
      div[data-testid="stHorizontalBlock"] > div { width: 50% !important; min-width: 0 !important; flex: 0 0 50% !important; }
      div[data-testid="stNumberInput"] { min-width: 0 !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "n" not in st.session_state:
    st.session_state.n = 300
if "k" not in st.session_state:
    st.session_state.k = 20

koyaku_payload = None
with st.expander("蟆丞ｽｹ繧ｫ繧ｦ繝ｳ繧ｿ繝ｼ・医Ο繝ｼ繧ｫ繝ｫ菫晏ｭ假ｼ・, expanded=False):
    koyaku_payload = render_koyaku_counter(key="koyaku-counter-main")
    st.markdown(
        "<p class='koyaku-caption'>譛荳頑ｮｵ縺ｯ蛻､蛻･繝輔か繝ｼ繝縺ｮ蟆丞ｽｹ蝗樊焚縺ｨ蜷梧悄縺励∪縺吶・/p>",
        unsafe_allow_html=True,
    )

if isinstance(koyaku_payload, dict):
    primary_count = koyaku_payload.get("primaryCount")
    if primary_count is None:
        counts_payload = koyaku_payload.get("counts")
        if isinstance(counts_payload, list) and counts_payload:
            primary_count = counts_payload[0]
    try:
        new_k_value = max(0, int(primary_count)) if primary_count is not None else None
    except (TypeError, ValueError):
        new_k_value = None
    if new_k_value is not None and st.session_state.k != new_k_value:
        st.session_state.k = new_k_value
        st.session_state["k_input"] = new_k_value

with st.form("inputs", clear_on_submit=False):
    col_n, col_k = st.columns(2, gap="small")
    with col_n:
        n_value = st.number_input(
            "邱丞屓霆｢謨ｰ N",
            min_value=0,
            value=int(st.session_state.n),
            step=10,
            key="n_input",
        )

    with col_k:
        k_value = st.number_input(
            "蟆丞ｽｹ蝗樊焚 k",
            min_value=0,
            value=int(st.session_state.k),
            step=1,
            key="k_input",
        )

    render_plain_text("莠句燕遒ｺ邇・・蜷郁ｨ亥､縺ｫ蠢懊§縺ｦ閾ｪ蜍輔〒豁｣隕丞喧縺輔ｌ縺ｾ縺吶・, classes="helper-text")
    prior_mode = st.radio("莠句燕縺ｮ險ｭ螳・, ["蝮・ｭ・, "繧ｫ繧ｹ繧ｿ繝"], horizontal=True, index=0)

    prior_inputs: Dict[str, float] = {key: 100.0 / len(SETTING_KEYS) for key in SETTING_KEYS}
    if prior_mode == "繧ｫ繧ｹ繧ｿ繝":
        with st.expander("莠句燕遒ｺ邇・ｒ邏ｰ縺九￥蜈･蜉帙☆繧・, expanded=True):
            cols = st.columns(len(SETTING_KEYS))
            for idx, key in enumerate(SETTING_KEYS):
                with cols[idx]:
                    prior_inputs[key] = st.number_input(
                        f"險ｭ螳嘴key}",
                        min_value=0.0,
                        value=prior_inputs[key],
                        step=0.1,
                        key=f"prior_{key}",
                    )

    submitted = st.form_submit_button("險育ｮ励☆繧・, use_container_width=True)

if submitted:
    st.session_state.n = int(n_value)
    st.session_state.k = int(k_value)

    if st.session_state.k > st.session_state.n:
        st.error("蜈･蜉帙お繝ｩ繝ｼ: 0 <= 蟆丞ｽｹ蝗樊焚 <= 蝗櫁ｻ｢謨ｰ 繧呈ｺ縺溘＠縺ｦ縺上□縺輔＞縲・)
        st.stop()

    priors = {key: prior_inputs[key] for key in SETTING_KEYS}
    posteriors = compute_posteriors(int(st.session_state.n), int(st.session_state.k), priors)
    priors_norm = normalize(priors)

    hit_prob = (st.session_state.k / st.session_state.n) if st.session_state.n > 0 else 0.0
    top_key = max(posteriors, key=posteriors.get)
    top_prob = posteriors[top_key]

    low_prob = sum(posteriors.get(key, 0.0) for key in ["1", "2"])
    high_prob = sum(posteriors.get(key, 0.0) for key in ["4", "5", "6"])
    grp124 = posteriors.get("1", 0.0) + posteriors.get("2", 0.0) + posteriors.get("4", 0.0)
    grp56 = posteriors.get("5", 0.0) + posteriors.get("6", 0.0)

    sorted_keys = sorted(SETTING_KEYS, key=lambda key: posteriors[key], reverse=True)
    second_key = sorted_keys[1] if len(sorted_keys) > 1 else top_key
    second_prob = posteriors.get(second_key, 0.0)
    prob_gap = max(0.0, top_prob - second_prob)
    bayes_factor = (top_prob / second_prob) if second_prob > 0 else float("inf")

    se = (
        math.sqrt(hit_prob * (1.0 - hit_prob) / st.session_state.n)
        if 0 < st.session_state.n and 0 < hit_prob < 1
        else 0.0
    )
    ci_low = max(0.0, hit_prob - 1.96 * se)
    ci_high = min(1.0, hit_prob + 1.96 * se)
    ci_range_pct = (ci_high - ci_low) * 100.0
    ci_range_text = f"{ci_low * 100:.2f}% - {ci_high * 100:.2f}%"

    expected_top = SETTINGS[top_key]
    if st.session_state.n > 0 and 0.0 < expected_top < 1.0:
        variance_top = expected_top * (1.0 - expected_top) / st.session_state.n
        distance_sigma = (
            abs(hit_prob - expected_top) / math.sqrt(variance_top)
            if variance_top > 0 else 0.0
        )
    else:
        distance_sigma = 0.0
    expected_top_percent = format_percent(expected_top)

    rating_456 = evaluate_goal("456", high_prob, low_prob, thresholds_456, ci_range_pct)
    rating_56 = evaluate_goal("56", grp56, grp124, thresholds_56, ci_range_pct)

    if not rating_456["insufficient"] and not rating_56["insufficient"]:
        if rating_456["stars"] >= 4 and rating_56["stars"] <= 2:
            rating_456["comment"] += " 縺溘□縺苓ｨｭ螳・繝ｻ6縺ｾ縺ｧ邨槭ｋ縺ｫ縺ｯ縲√ｂ縺・ｰ代＠荳頑険繧後′谺ｲ縺励＞迥ｶ豕√〒縺吶・
        if rating_56["stars"] >= 4 and rating_456["stars"] <= 3:
            rating_56["comment"] += " 456隕也せ縺ｧ縺ｯ縺ｾ縺遒ｺ菫｡縺励″繧後∪縺帙ｓ縺後・6蜍晁ｲ縺ｫ蛻・ｊ譖ｿ縺医ｋ萓｡蛟､縺後≠繧翫∪縺吶・
        elif rating_56["stars"] <= 2 and rating_456["stars"] >= 3:
            rating_56["comment"] += " 險ｭ螳・縺ｾ縺ｧ縺ｯ蟆・ｨ句恟縺ｧ縺吶′縲・6蜊倅ｽ薙〒隕九ｋ縺ｨ霑ｽ蜉繧ｵ繝ｳ繝励Ν縺梧ｬｲ縺励＞迥ｶ豕√〒縺吶・

    summary_lines = [
        "繝｢繝ｳ繧ｭ繝ｼ繧ｿ繝ｼ繝ｳV 蛻､蛻･邨先棡",
        f"邱丞屓霆｢謨ｰ: {st.session_state.n}G",
        f"蟆丞ｽｹ蝗樊焚: {st.session_state.k}蝗・,
        f"螳滓ｸｬ蟆丞ｽｹ遒ｺ邇・ {format_one_over(hit_prob)} ({st.session_state.k}/{st.session_state.n})",
        f"譛譛牙鴨險ｭ螳・ 險ｭ螳嘴top_key} ({format_percent(top_prob)})",
        f"菴手ｨｭ螳・1繝ｻ2): {format_percent(low_prob)}",
        f"鬮倩ｨｭ螳・4繝ｻ5繝ｻ6): {format_percent(high_prob)}",
        f"456菫｡鬆ｼ蠎ｦ: {rating_456['stars_text']} ({rating_456['label']})",
        f"456繧ｳ繝｡繝ｳ繝・ {rating_456['comment']}",
        f"56菫｡鬆ｼ蠎ｦ: {rating_56['stars_text']} ({rating_56['label']})",
        f"56繧ｳ繝｡繝ｳ繝・ {rating_56['comment']}",
        f"螳滓ｸｬ蟆丞ｽｹ邇・5%CI: {ci_range_text} (n={st.session_state.n})",
        "蜷・ｨｭ螳壹・莠句ｾ檎｢ｺ邇・",
    ]
    for key in SETTING_KEYS:
        summary_lines.append(
            f"  險ｭ螳嘴key}: {format_percent(posteriors[key])} (莠句燕 {format_percent(priors_norm[key])})"
        )

    copy_text = "\n".join(summary_lines)
    copy_json = json.dumps(copy_text, ensure_ascii=False)
    button_id = f"copy-btn-{uuid.uuid4().hex}"

    copy_html = """
        <div class="copy-share-container">
          <button id="__BUTTON_ID__">蛻､蛻･邨先棡繧偵さ繝斐・</button>
        </div>
        <script>
          const btn = document.getElementById('__BUTTON_ID__');
          const textToCopy = __COPY_TEXT__;
          if (btn) {
            btn.addEventListener('click', async () => {
              try {
                await navigator.clipboard.writeText(textToCopy);
                window.alert('蛻､蛻･邨先棡繧偵さ繝斐・縺励∪縺励◆縲・);
              } catch (error) {
                window.alert('繧ｳ繝斐・縺ｫ螟ｱ謨励＠縺ｾ縺励◆縲・);
              }
            });
          }
        </script>
    """

    copy_html = copy_html.replace("__BUTTON_ID__", button_id).replace("__COPY_TEXT__", copy_json)
    components.html(copy_html, height=44, scrolling=False)

    render_small_text(
        f"逅・ｫ門､縺ｨ縺ｮ蟾ｮ: {distance_sigma:.2f}ﾏ・ｼ域悄蠕・{expected_top_percent}・・
        if st.session_state.n > 0
        else "逅・ｫ門､縺ｨ縺ｮ豈碑ｼ・↓縺ｯ蝗櫁ｻ｢謨ｰ縺悟ｿ・ｦ√〒縺吶・,
        classes="reliability-caption",
    )

    st.session_state['share_text_display'] = copy_text
    with st.expander("繧ｳ繝斐・蜀・ｮｹ繧堤｢ｺ隱阪☆繧・, expanded=False):
        st.text_area("蜈ｱ譛臥畑繝・く繧ｹ繝・, value=copy_text, height=180, key="share_text_display")

    result_cards_html = f"""
    <div class="result-grid">
      <div class="result-card">
        <div class="result-label">譛譛牙鴨縺ｮ險ｭ螳・/div>
        <div class="result-value">險ｭ螳嘴top_key}</div>
        <div class="result-sub">{format_percent(top_prob)}</div>
      </div>
      <div class="result-card">
        <div class="result-label">螳滓ｸｬ蟆丞ｽｹ遒ｺ邇・/div>
        <div class="result-value">{format_one_over(hit_prob)}</div>
        <div class="result-sub">95%CI {ci_range_text}</div>
      </div>
      <div class="result-card">
        <div class="result-label">菴手ｨｭ螳・1繝ｻ2) / 鬮倩ｨｭ螳・4繝ｻ5繝ｻ6)</div>
        <div class="result-value">{format_percent(low_prob)} / {format_percent(high_prob)}</div>
        <div class="result-sub">蟾ｮ {prob_gap * 100:.1f}pt</div>
      </div>
      <div class="result-card">
        <div class="result-label">(1,2,4) / (5,6)</div>
        <div class="result-value">{format_percent(grp124)} / {format_percent(grp56)}</div>
        <div class="result-sub">豈・{bayes_factor if math.isinf(bayes_factor) else f"{bayes_factor:.1f}x"}</div>
      </div>
    </div>
    """
    st.markdown(result_cards_html, unsafe_allow_html=True)

    reliability_html = f"""
    <div class="pair-grid">
      <div class="pair-card">
        <div class="pair-label">456菫｡鬆ｼ蠎ｦ</div>
        <div class="pair-main">{rating_456['stars_text']}</div>
        <div class="pair-delta">{rating_456['label']}</div>
      </div>
      <div class="pair-card">
        <div class="pair-label">56菫｡鬆ｼ蠎ｦ</div>
        <div class="pair-main">{rating_56['stars_text']}</div>
        <div class="pair-delta">{rating_56['label']}</div>
      </div>
    </div>
    """
    st.markdown(reliability_html, unsafe_allow_html=True)

    render_plain_text(f"456繧ｳ繝｡繝ｳ繝・ {rating_456['comment']}", classes="reliability-comment")
    render_plain_text(f"56繧ｳ繝｡繝ｳ繝・ {rating_56['comment']}", classes="reliability-comment")

    setting_cards = ["<div class='setting-list'>"]
    for key in SETTING_KEYS:
        p = SETTINGS[key]
        prior_pct = priors_norm[key] * 100.0
        posterior_pct = posteriors[key] * 100.0
        prob_inv = 1.0 / p
        setting_cards.append(
            f"<div class='setting-item'>"
            f"<div class='setting-title'>險ｭ螳嘴key}</div>"
            f"<div class='setting-values'>"
            f"<span>遒ｺ邇・1/x): {prob_inv:.2f}</span>"
            f"<span>莠句燕: {prior_pct:.2f}%</span>"
            f"<span>莠句ｾ・ {posterior_pct:.2f}%</span>"
            "</div></div>"
        )
    setting_cards.append("</div>")
    st.markdown("".join(setting_cards), unsafe_allow_html=True)
else:
    render_plain_text("繝輔か繝ｼ繝縺ｫ蜈･蜉帙＠縲手ｨ育ｮ励☆繧九上ｒ謚ｼ縺励※縺上□縺輔＞縲ゆｺ句燕遒ｺ邇・・譛ｪ險ｭ螳壹〒繧り・蜍輔〒蝮・ｭ牙喧縺輔ｌ縺ｾ縺吶・, classes="info-box")

