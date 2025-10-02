import json
import math
import uuid
import html
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
        "min_sample_good": 200,
        "ci_warn": 18.0,
        "ci_good": 11.0,
        "goal_thresholds": {"high": 75.0, "mid": 65.0, "low": 48.0},
        "diff_thresholds": {"high": 15.0, "mid": 7.0},
        "negative_diff_thresholds": {"mid": -5.0, "high": -10.0},
        "ratio_thresholds": {"high": 2.0, "mid": 1.5},
        "strong_diff": 16.0,
        "strong_ratio": 2.2,
        "diff_close": 6.0,
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
    (5, {"min_n": 260, "min_goal": 0.80, "min_diff": 0.28, "min_ratio": 2.6}),
    (4, {"min_n": 200, "min_goal": 0.70, "min_diff": 0.20, "min_ratio": 2.1}),
    (3, {"min_n": 160, "min_goal": 0.60, "min_diff": 0.12, "min_ratio": 1.6}),
    (2, {"min_n": 120, "min_goal": 0.52, "min_diff": 0.05, "min_ratio": 1.2}),
]

thresholds_56 = [
    (5, {"min_n": 260, "min_goal": 0.58, "min_diff": 0.15, "min_ratio": 2.0}),
    (4, {"min_n": 210, "min_goal": 0.50, "min_diff": 0.10, "min_ratio": 1.6}),
    (3, {"min_n": 170, "min_goal": 0.42, "min_diff": 0.06, "min_ratio": 1.3}),
    (2, {"min_n": 140, "min_goal": 0.35, "min_diff": 0.02, "min_ratio": 1.1}),
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

        if score >= 6:
            star = 5
        elif score >= 4:
            star = 4
        elif score >= 2:
            star = 3
        elif score >= 0:
            star = 2
        else:
            star = 1

    stars_text = "★" * star + "☆" * (5 - star)
    ratio_text = "∞" if math.isinf(ratio) else f"{ratio:.1f}x"

    comments = config["comments"]
    if insufficient_sample:
        comment = comments["insufficient"]
    else:
        if star >= 5:
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
        elif -diff_close <= diff_pct <= diff_close:
            comment += " 今は競り合いなので追加のデータで見極めましょう。"
        elif diff_pct < -diff_close:
            comment += " 現状は他設定の方が優勢です。"

    comment += f" (差 {diff_pct:.1f}pt / 比 {ratio_text})"

    thresholds_dict = {star_key: cond for star_key, cond in thresholds}
    for higher_star in sorted(thresholds_dict.keys()):
        if higher_star > star:
            min_n_required = thresholds_dict[higher_star].get("min_n", sample_n)
            if sample_n < min_n_required:
                needed = min_n_required - sample_n
                comment += f" 目安としてあと約{needed}G回すと★{higher_star}を狙えます。"
            break

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



st.set_page_config(
    page_title="設定推定ツール",
    page_icon="🎰",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      .block-container { padding-top: calc(1.2rem + env(safe-area-inset-top)); padding-bottom: 2rem; max-width: 980px; }
      h1 { font-size: 1.6rem !important; }
      label, .stMarkdown p { font-size: 0.95rem; }
      .stNumberInput input { font-size: 1rem; }
      .copy-share-container { margin: 0.6rem 0 0.8rem; }
      .copy-share-container button { padding: 0.5rem 0.9rem; background-color: #2F80ED; border: none; border-radius: 0.5rem; color: #ffffff; font-size: 0.95rem; cursor: pointer; }
      .copy-share-container button:hover { background-color: #1C5FC4; }
      .reliability-caption { font-size: 0.85rem; color: #5f6368; margin-bottom: 0.4rem; }
      .reliability-comment { font-size: 0.9rem; color: #424242; margin: 0.2rem 0 0.8rem; line-height: 1.45; }
      div[data-testid="stMetricValue"] { white-space: normal !important; overflow: visible !important; text-overflow: clip !important; line-height: 1.2; }
      @media (max-width: 420px) {
        .block-container { padding-left: 0.6rem; padding-right: 0.6rem; }
        label, .stMarkdown p { font-size: 0.9rem; }
        .copy-share-container button { min-width: 56px; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    @media (max-width: 640px) {
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
        minus_n = st.form_submit_button("N -50", key="n_minus")
        if minus_n:
            st.session_state.n = max(0, int(n_value) - 50)
            st.experimental_rerun()
        plus_n = st.form_submit_button("N +50", key="n_plus")
        if plus_n:
            st.session_state.n = int(n_value) + 50
            st.experimental_rerun()

    with col_k:
        k_value = st.number_input(
            "小役回数 k",
            min_value=0,
            value=int(st.session_state.k),
            step=1,
            key="k_input",
        )
        minus_k = st.form_submit_button("k -10", key="k_minus")
        if minus_k:
            st.session_state.k = max(0, int(k_value) - 10)
            st.experimental_rerun()
        plus_k = st.form_submit_button("k +10", key="k_plus")
        if plus_k:
            st.session_state.k = int(k_value) + 10
            st.experimental_rerun()

    st.markdown("事前確率は合計値に応じて自動で正規化されます。")
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
        st.text_area("共有用テキスト", value=copy_text, height=220, key="share_text_display")

    c1, c2 = st.columns(2)
    with c1:
        st.metric(
            label="最有力の設定",
            value=f"設定{top_key} ({format_percent(top_prob)})",
        )
        st.metric(
            label="実測小役確率",
            value=f"{format_one_over(hit_prob)} ({st.session_state.k}/{st.session_state.n})",
            delta=f"95%CI {ci_range_text}",
        )
    with c2:
        st.metric(
            label="低設定(1,2) / 高設定(4,5,6)",
            value=f"{format_percent(low_prob)} / {format_percent(high_prob)}",
            delta=f"{rating_456['stars_text']} ({rating_456['label']})",
        )
        render_small_text(rating_456["comment"])
        st.metric(
            label="(1,2,4) / (5,6)",
            value=f"{format_percent(grp124)} / {format_percent(grp56)}",
            delta=f"{rating_56['stars_text']} ({rating_56['label']})",
        )
        render_small_text(rating_56["comment"])

    chart_data = pd.DataFrame(
        {
            "設定": SETTING_KEYS,
            "事後確率(%)": [posteriors[key] * 100.0 for key in SETTING_KEYS],
        }
    )
    chart = (
        alt.Chart(chart_data)
        .mark_bar(size=26, cornerRadiusTopLeft=3, cornerRadiusBottomLeft=3)
        .encode(
            y=alt.Y(
                "設定:N",
                sort=SETTING_KEYS,
                axis=alt.Axis(title=None, labelAngle=0),
            ),
            x=alt.X(
                "事後確率(%):Q",
                axis=alt.Axis(title="事後確率(%)", labelAngle=0),
                scale=alt.Scale(domainMin=0),
            ),
            color=alt.condition(
                alt.datum.設定 == top_key,
                alt.value("#E74C3C"),
                alt.value("#2F80ED"),
            ),
            tooltip=[alt.Tooltip("設定:N"), alt.Tooltip("事後確率(%):Q", format=".2f")],
        )
        .properties(height=260)
    )
    st.altair_chart(chart, use_container_width=True)

    rows = []
    for key in SETTING_KEYS:
        p = SETTINGS[key]
        rows.append(
            {
                "設定": key,
                "確率(1/x)": f"1/{(1.0 / p):.2f}",
                "事前(%)": f"{priors_norm[key] * 100.0:.2f}%",
                "事後(%)": f"{posteriors[key] * 100.0:.2f}%",
            }
        )
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("フォームに入力し「計算する」を押してください。事前確率は未設定でも自動で均等化されます。")
