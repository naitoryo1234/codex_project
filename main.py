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


# ページ設定 (wide レイアウト + モバイル最適化)
st.set_page_config(
    page_title="設定推定ツール",
    page_icon="🎰",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# モバイル向けの余白・フォント調整、安全領域を確保
st.markdown(
    """
    <style>
      .block-container { padding-top: calc(1.2rem + env(safe-area-inset-top)); padding-bottom: 2rem; max-width: 980px; }
      h1 { font-size: 1.6rem !important; }
      label, .stMarkdown p { font-size: 0.95rem; }
      .stNumberInput input { font-size: 1rem; }
      .micro-row { margin-top: 0.25rem; }
      .micro-row [data-testid="stHorizontalBlock"] { display: flex !important; flex-wrap: nowrap !important; }
      .micro-row [data-testid="column"] { width: 50% !important; padding-right: 0.25rem; }
      .micro-row [data-testid="column"]:last-child { padding-right: 0; padding-left: 0.25rem; }
      .micro-row .stButton > button { padding: 0.14rem 0.46rem; font-size: 0.82rem; min-width: 60px; }
      .copy-share-container { margin: 0.6rem 0 0.8rem; }
      .copy-share-container button { padding: 0.5rem 0.9rem; background-color: #2F80ED; border: none; border-radius: 0.5rem; color: #ffffff; font-size: 0.95rem; cursor: pointer; }
      .copy-share-container button:hover { background-color: #1C5FC4; }
      .reliability-caption { font-size: 0.85rem; color: #5f6368; margin-bottom: 0.4rem; }
      .reliability-comment { font-size: 0.9rem; color: #424242; margin: 0.2rem 0 0.8rem; line-height: 1.45; }
      div[data-testid="stMetricValue"] { white-space: normal !important; overflow: visible !important; text-overflow: clip !important; line-height: 1.2; }
      @media (max-width: 420px) {
        .block-container { padding-left: 0.6rem; padding-right: 0.6rem; }
        label, .stMarkdown p { font-size: 0.9rem; }
        .micro-row .stButton > button { min-width: 56px; }
        div[data-testid="stMetricValue"] { font-size: 1rem !important; }
      }
    </style>
    """
,
    unsafe_allow_html=True,
)

# iPhone Safari での横並びを強制
st.markdown(
    """
    <style>
    @media (max-width: 640px) {
      div[data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: nowrap !important; }
      div[data-testid="stHorizontalBlock"] > div { width: 50% !important; min-width: 0 !important; flex: 0 0 50% !important; }
      div[data-testid="column"] { width: 50% !important; min-width: 0 !important; flex: 0 0 50% !important; }
      div[data-testid="stNumberInput"] { min-width: 0 !important; }
    }
    </style>
    """
,
    unsafe_allow_html=True,
)

st.title("モンキーターンV判別ツール")

# セッション保存用の初期値
if "n" not in st.session_state:
    st.session_state.n = 1000
if "k" not in st.session_state:
    st.session_state.k = 20

with st.form("inputs", clear_on_submit=False):
    st.subheader("入力")

    # N と k を横並びで配置。インクリメントボタンは小さめに配置。
    col_n, col_k = st.columns(2, gap="small")
    with col_n:
        n = st.number_input("総回転数 N", min_value=0, value=int(st.session_state.n), step=10, key="n_input")
        st.markdown('<div class="micro-row">', unsafe_allow_html=True)
        n_col1, n_col2 = st.columns(2)
        with n_col1:
            if st.form_submit_button("N -50", key="n_minus"):
                st.session_state.n = max(0, int(n) - 50)
                st.rerun()
        with n_col2:
            if st.form_submit_button("N +50", key="n_plus"):
                st.session_state.n = int(n) + 50
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col_k:
        k = st.number_input("小役回数 k", min_value=0, value=int(st.session_state.k), step=1, key="k_input")
        st.markdown('<div class="micro-row">', unsafe_allow_html=True)
        k_col1, k_col2 = st.columns(2)
        with k_col1:
            if st.form_submit_button("k -10", key="k_minus"):
                st.session_state.k = max(0, int(k) - 10)
                st.rerun()
        with k_col2:
            if st.form_submit_button("k +10", key="k_plus"):
                st.session_state.k = int(k) + 10
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # 事前確率はフォーム送信時に自動正規化
    st.markdown("事前確率は合計値に応じて自動で正規化されます。")
    prior_mode = st.radio("事前の設定", ["均等", "カスタム"], horizontal=True, index=0)

    default_uniform = 100.0 / len(SETTING_KEYS)
    prior_inputs: Dict[str, float] = {k: default_uniform for k in SETTING_KEYS}

    if prior_mode == "カスタム":
        with st.expander("事前確率を細かく入力する", expanded=True):
            cols = st.columns(len(SETTING_KEYS))
            for idx, key in enumerate(SETTING_KEYS):
                with cols[idx]:
                    prior_inputs[key] = st.number_input(
                        f"設定{key}",
                        min_value=0.0,
                        value=float(f"{default_uniform:.1f}"),
                        step=0.1,
                        key=f"prior_{key}",
                    )

    submitted = st.form_submit_button("計算する", use_container_width=True)

if submitted:
    st.session_state.n = int(n)
    st.session_state.k = int(k)

    if st.session_state.k > st.session_state.n:
        st.error("入力エラー: 0 <= 小役回数 <= 回転数 を満たしてください。")
        st.stop()

    priors = prior_inputs
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
    ci_range_text = f"{ci_low * 100:.2f}% - {ci_high * 100:.2f}%"




    expected_top = SETTINGS[top_key]
    expected_top_percent = format_percent(expected_top)

    distance_sigma = (
        abs(hit_prob - expected_top)
        / math.sqrt(expected_top * (1.0 - expected_top) / st.session_state.n)
        if st.session_state.n > 0
        else 0.0
    )

    star_labels = {
        5: "かなり安心",
        4: "やや安心",
        3: "五分五分",
        2: "慎重",
        1: "厳しい",
    }

    thresholds_456 = [
        (5, {"min_n": 280, "min_goal": 0.78, "min_diff": 0.35, "min_ratio": 4.0}),
        (4, {"min_n": 200, "min_goal": 0.68, "min_diff": 0.25, "min_ratio": 3.0}),
        (3, {"min_n": 130, "min_goal": 0.55, "min_diff": 0.15, "min_ratio": 2.1}),
        (2, {"min_n": 90, "min_goal": 0.45, "min_diff": 0.05, "min_ratio": 1.2}),
    ]
    thresholds_56 = [
        (5, {"min_n": 260, "min_goal": 0.55, "min_diff": 0.22, "min_ratio": 3.0}),
        (4, {"min_n": 180, "min_goal": 0.45, "min_diff": 0.16, "min_ratio": 2.4}),
        (3, {"min_n": 120, "min_goal": 0.35, "min_diff": 0.08, "min_ratio": 1.6}),
        (2, {"min_n": 80, "min_goal": 0.28, "min_diff": 0.03, "min_ratio": 1.1}),
    ]

    def evaluate_goal(goal_code: str, goal_prob: float, alt_prob: float, thresholds):
        sample_n = st.session_state.n
        ratio = goal_prob / alt_prob if alt_prob > 0 else float("inf")
        diff = goal_prob - alt_prob
        diff_pct = diff * 100.0

        star = 1
        thresholds_dict = {star_key: cond for star_key, cond in thresholds}
        for star_candidate, cond in thresholds:
            cond_ratio = cond.get("min_ratio", 0.0)
            cond_diff = cond.get("min_diff", 0.0)
            cond_goal = cond.get("min_goal", 0.0)
            cond_n = cond.get("min_n", 0)
            if (
                sample_n >= cond_n
                and goal_prob >= cond_goal
                and diff >= cond_diff
                and ratio >= cond_ratio
            ):
                star = star_candidate
                break

        stars_text = "★" * star + "☆" * (5 - star)
        ratio_text = "∞" if math.isinf(ratio) else f"{ratio:.1f}x"
        min_sample_for_consideration = thresholds[-1][1].get("min_n", 0)
        insufficient_sample = sample_n < max(min_sample_for_consideration, 60)

        base_comments = {
            "456": {
                5: "456狙いでも安心して粘れるデータです。",
                4: "456寄りが濃厚です。少し回せば確信が持てそうです。",
                3: "456の芽はありますが、追加サンプルで傾向を再確認したいラインです。",
                2: "456狙いにはデータがやや不足しています。慎重に様子を見ましょう。",
                1: "現状は低設定寄りで、456狙いは厳しい展開です。",
            },
            "56": {
                5: "設定5・6本命で戦える濃さです。勝負どころと言えます。",
                4: "設定5・6がかなり有力です。追加で押し切るならチャンスです。",
                3: "設定5・6の芽はありますが設定4との競り合いです。追加サンプルで見極めを。",
                2: "設定5・6を狙うには裏付けが不足しています。設定4ラインも視野に入れて慎重に。",
                1: "設定5・6はかなり薄い状況です。無理に56狙いに固執しない方が賢明です。",
            },
        }

        shortage_comments = {
            "456": "サンプルが少ないため456の判断はまだ揺らぎが大きいです。まずはデータを集めましょう。",
            "56": "サンプル不足のため56の信頼度は評価しきれません。追加で回転数を確保して様子を見ましょう。",
        }

        if insufficient_sample and star <= 3:
            comment = shortage_comments[goal_code]
        else:
            comment = base_comments[goal_code][star]

        comment += f" (差 {diff_pct:.1f}pt / 比 {ratio_text})"

        next_needed = 0
        for higher_star in sorted(thresholds_dict.keys()):
            if higher_star > star:
                min_n = thresholds_dict[higher_star].get("min_n", sample_n)
                if sample_n < min_n:
                    next_needed = min_n - sample_n
                    comment += f" 目安としてあと約{next_needed}G回すと★{higher_star}を狙えます。"
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
        }


    rating_456 = evaluate_goal("456", high_prob, low_prob, thresholds_456)
    rating_56 = evaluate_goal("56", grp56, grp124, thresholds_56)

    if rating_456["stars"] >= 4 and rating_56["stars"] <= 2:
        rating_456["comment"] += " 一方で設定5・6まで絞るには、もう少し上振れを待った方が安心です。"
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
        <div class=\"copy-share-container\">
          <button id=\"__BUTTON_ID__\">判別結果をコピー</button>
        </div>
        <script>
          const btn = document.getElementById('__BUTTON_ID__');
          const textToCopy = __COPY_TEXT__;
          if (btn) {
            btn.addEventListener('click', async () => {
              try {
                await navigator.clipboard.writeText(textToCopy);
                window.alert('判別結果をコピー\u3057\u307e\u3057\u305f\u3002');
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
