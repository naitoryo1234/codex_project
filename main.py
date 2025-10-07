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

# 設定ごとの5枚役当選確率
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
        st.info("小役カウンターのビルド結果が見つかりません。`npm run build` を実行してから再度お試しください。")
        return None
    return _koyaku_counter_component(**kwargs)


def calculate_likelihood(num_spins: int, num_hits: int, p: float) -> float:
    """二項分布の尤度 P(K=k | N=n, p)。大きな値でも安定するよう対数計算を用いる。"""
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
    5: "かなり安心",
    4: "やや安心",
    3: "五分五分",
    2: "慎重",
    1: "厳しい",
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
            "insufficient": "サンプルが少なく、456の判別にはまだ揺らぎが大きい状況です。まずはデータを集めましょう。",
            "very_low": "現状は低設定寄りのデータで456狙いは厳しい展開です。",
            "low": "456狙いにはまだ裏付けが不足しています。慎重に様子を見ましょう。",
            "mid": "456の芽はありますが、追加サンプルで傾向を再確認したいラインです。",
            "high": "456寄りが濃厚です。もう少し回せば確信が持てそうです。",
            "very_high": "456狙いでも安心して粘れるデータです。",
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
            "insufficient": "サンプルが少なく、設定5・6の判別にはまだ裏付けが足りません。追加で回転数を確保しましょう。",
            "very_low": "設定5・6はかなり薄い状況です。無理に56狙いに固執しない方が賢明です。",
            "low": "設定5・6を狙うには裏付けが不足しています。設定4ラインも視野に慎重に。",
            "mid": "設定5・6の可能性はありますが、設定4との競り合いです。追加サンプルで見極めを。",
            "high": "設定5・6がかなり有力です。押し切るならチャンスです。",
            "very_high": "設定5・6本命で勝負できる濃さです。大きなチャンスと言えます。",
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

    stars_text = "★" * star + "☆" * (5 - star)
    ratio_text = "∞" if math.isinf(ratio) else f"{ratio:.1f}x"

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
            comment += " 優位性ははっきりしています。"
        elif -diff_close <= diff_pct <= diff_close and star <= 3:
            comment += " 今は競り合いなので追加のデータで見極めましょう。"
        elif diff_pct < -diff_close:
            comment += " 現状は他設定の方が優勢です。"

    comment += f" (差 {diff_pct:.1f}pt / 比 {ratio_text})"

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
                comment += f" 目安としてあと約{needed}G回すと次の信頼度を狙えます。"

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




# Safari互換のため、@mediaをHTML実体参照に変換しGFMの命名正規表現生成を回避する
st.set_page_config(
    page_title="設定推定ツール",
    page_icon="🎰",
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
      .copy-share-container { margin: 0.5rem 0 0.7rem; }
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

st.title("モンキーターンV判別ツール")
if "n" not in st.session_state:
    st.session_state.n = 1000
if "k" not in st.session_state:
    st.session_state.k = 20

koyaku_payload = None
with st.expander("???????????????", expanded=False):
    st.caption("??????????????????????????????????????????????????????????????????")
    koyaku_payload = render_koyaku_counter(key="koyaku-counter-main")

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

with st.form("inputs", clear_on_submit=False):
    st.subheader("入力")

    col_n, col_k = st.columns(2, gap="small")
    with col_n:
        n_value = st.number_input(
            "総回転数 N",
            min_value=0,
            value=int(st.session_state.n),
            step=10,
            key="n_input",
        )

    with col_k:
        k_value = st.number_input(
            "小役回数 k",
            min_value=0,
            value=int(st.session_state.k),
            step=1,
            key="k_input",
        )

    render_plain_text("事前確率は合計値に応じて自動で正規化されます。", classes="helper-text")
    prior_mode = st.radio("事前の設定", ["均等", "カスタム"], horizontal=True, index=0)

    prior_inputs: Dict[str, float] = {key: 100.0 / len(SETTING_KEYS) for key in SETTING_KEYS}
    if prior_mode == "カスタム":
        with st.expander("事前確率を細かく入力する", expanded=True):
            cols = st.columns(len(SETTING_KEYS))
            for idx, key in enumerate(SETTING_KEYS):
                with cols[idx]:
                    prior_inputs[key] = st.number_input(
                        f"設定{key}",
                        min_value=0.0,
                        value=prior_inputs[key],
                        step=0.1,
                        key=f"prior_{key}",
                    )

    submitted = st.form_submit_button("計算する", use_container_width=True)

if submitted:
    st.session_state.n = int(n_value)
    st.session_state.k = int(k_value)

    if st.session_state.k > st.session_state.n:
        st.error("入力エラー: 0 <= 小役回数 <= 回転数 を満たしてください。")
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
            rating_456["comment"] += " ただし設定5・6まで絞るには、もう少し上振れが欲しい状況です。"
        if rating_56["stars"] >= 4 and rating_456["stars"] <= 3:
            rating_56["comment"] += " 456視点ではまだ確信しきれませんが、56勝負に切り替える価値があります。"
        elif rating_56["stars"] <= 2 and rating_456["stars"] >= 3:
            rating_56["comment"] += " 設定4までは射程圏ですが、56単体で見ると追加サンプルが欲しい状況です。"

    summary_lines = [
        "モンキーターンV 判別結果",
        f"総回転数: {st.session_state.n}G",
        f"小役回数: {st.session_state.k}回",
        f"実測小役確率: {format_one_over(hit_prob)} ({st.session_state.k}/{st.session_state.n})",
        f"最有力設定: 設定{top_key} ({format_percent(top_prob)})",
        f"低設定(1・2): {format_percent(low_prob)}",
        f"高設定(4・5・6): {format_percent(high_prob)}",
        f"456信頼度: {rating_456['stars_text']} ({rating_456['label']})",
        f"456コメント: {rating_456['comment']}",
        f"56信頼度: {rating_56['stars_text']} ({rating_56['label']})",
        f"56コメント: {rating_56['comment']}",
        f"実測小役率95%CI: {ci_range_text} (n={st.session_state.n})",
        "各設定の事後確率:",
    ]
    for key in SETTING_KEYS:
        summary_lines.append(
            f"  設定{key}: {format_percent(posteriors[key])} (事前 {format_percent(priors_norm[key])})"
        )

    copy_text = "\n".join(summary_lines)
    copy_json = json.dumps(copy_text, ensure_ascii=False)
    button_id = f"copy-btn-{uuid.uuid4().hex}"

    copy_html = """
        <div class="copy-share-container">
          <button id="__BUTTON_ID__">判別結果をコピー</button>
        </div>
        <script>
          const btn = document.getElementById('__BUTTON_ID__');
          const textToCopy = __COPY_TEXT__;
          if (btn) {
            btn.addEventListener('click', async () => {
              try {
                await navigator.clipboard.writeText(textToCopy);
                window.alert('判別結果をコピーしました。');
              } catch (error) {
                window.alert('コピーに失敗しました。');
              }
            });
          }
        </script>
    """

    copy_html = copy_html.replace("__BUTTON_ID__", button_id).replace("__COPY_TEXT__", copy_json)
    components.html(copy_html, height=70, scrolling=False)

    render_small_text(
        f"理論値との差: {distance_sigma:.2f}σ（期待 {expected_top_percent}）"
        if st.session_state.n > 0
        else "理論値との比較には回転数が必要です。",
        classes="reliability-caption",
    )

    st.session_state['share_text_display'] = copy_text
    with st.expander("コピー内容を確認する", expanded=False):
        st.text_area("共有用テキスト", value=copy_text, height=180, key="share_text_display")

    result_cards_html = f"""
    <div class="result-grid">
      <div class="result-card">
        <div class="result-label">最有力の設定</div>
        <div class="result-value">設定{top_key}</div>
        <div class="result-sub">{format_percent(top_prob)}</div>
      </div>
      <div class="result-card">
        <div class="result-label">実測小役確率</div>
        <div class="result-value">{format_one_over(hit_prob)}</div>
        <div class="result-sub">95%CI {ci_range_text}</div>
      </div>
      <div class="result-card">
        <div class="result-label">低設定(1・2) / 高設定(4・5・6)</div>
        <div class="result-value">{format_percent(low_prob)} / {format_percent(high_prob)}</div>
        <div class="result-sub">差 {prob_gap * 100:.1f}pt</div>
      </div>
      <div class="result-card">
        <div class="result-label">(1,2,4) / (5,6)</div>
        <div class="result-value">{format_percent(grp124)} / {format_percent(grp56)}</div>
        <div class="result-sub">比 {bayes_factor if math.isinf(bayes_factor) else f"{bayes_factor:.1f}x"}</div>
      </div>
    </div>
    """
    st.markdown(result_cards_html, unsafe_allow_html=True)

    reliability_html = f"""
    <div class="pair-grid">
      <div class="pair-card">
        <div class="pair-label">456信頼度</div>
        <div class="pair-main">{rating_456['stars_text']}</div>
        <div class="pair-delta">{rating_456['label']}</div>
      </div>
      <div class="pair-card">
        <div class="pair-label">56信頼度</div>
        <div class="pair-main">{rating_56['stars_text']}</div>
        <div class="pair-delta">{rating_56['label']}</div>
      </div>
    </div>
    """
    st.markdown(reliability_html, unsafe_allow_html=True)

    render_plain_text(f"456コメント: {rating_456['comment']}", classes="reliability-comment")
    render_plain_text(f"56コメント: {rating_56['comment']}", classes="reliability-comment")

    setting_cards = ["<div class='setting-list'>"]
    for key in SETTING_KEYS:
        p = SETTINGS[key]
        prior_pct = priors_norm[key] * 100.0
        posterior_pct = posteriors[key] * 100.0
        prob_inv = 1.0 / p
        setting_cards.append(
            f"<div class='setting-item'>"
            f"<div class='setting-title'>設定{key}</div>"
            f"<div class='setting-values'>"
            f"<span>確率(1/x): {prob_inv:.2f}</span>"
            f"<span>事前: {prior_pct:.2f}%</span>"
            f"<span>事後: {posterior_pct:.2f}%</span>"
            "</div></div>"
        )
    setting_cards.append("</div>")
    st.markdown("".join(setting_cards), unsafe_allow_html=True)
else:
    render_plain_text("フォームに入力し『計算する』を押してください。事前確率は未設定でも自動で均等化されます。", classes="info-box")
