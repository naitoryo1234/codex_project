import html
import math
from typing import Dict, List

import altair as alt
import pandas as pd
import streamlit as st

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
      .copy-share-container { margin-top: 1.5rem; }
      .copy-share-container button { padding: 0.5rem 0.9rem; background-color: #2F80ED; border: none; border-radius: 0.5rem; color: #ffffff; font-size: 0.95rem; cursor: pointer; }
      .copy-share-container button:hover { background-color: #1C5FC4; }
      div[data-testid="stMetricValue"] { white-space: normal !important; overflow: visible !important; text-overflow: clip !important; line-height: 1.2; }
      @media (max-width: 420px) {
        .block-container { padding-left: 0.6rem; padding-right: 0.6rem; }
        label, .stMarkdown p { font-size: 0.9rem; }
        .micro-row .stButton > button { min-width: 56px; }
        div[data-testid="stMetricValue"] { font-size: 1rem !important; }
      }
    </style>
    """,
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
    """,
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

    # 最も確率が高い設定を強調
    top_key = max(posteriors, key=posteriors.get)
    top_prob = posteriors[top_key] * 100.0

    c1, c2 = st.columns(2)
    with c1:
        st.metric(label="最有力の設定", value=f"設定{top_key}", delta=f"{top_prob:.2f}%")
    with c2:
        low_prob = sum(posteriors.get(key, 0.0) for key in ["1", "2"]) * 100.0
        high_prob = sum(posteriors.get(key, 0.0) for key in ["4", "5", "6"]) * 100.0
        st.metric(label="低設定(1,2) / 高設定(4,5,6)", value=f"{low_prob:.2f}% / {high_prob:.2f}%")
        grp124 = (posteriors.get("1", 0.0) + posteriors.get("2", 0.0) + posteriors.get("4", 0.0)) * 100.0
        grp56 = (posteriors.get("5", 0.0) + posteriors.get("6", 0.0)) * 100.0
        st.metric(label="(1,2,4) / (5,6)", value=f"{grp124:.2f}% / {grp56:.2f}%")

    # 棒グラフ (最有力の設定を赤でハイライト)
    chart_data = pd.DataFrame({
        "設定": SETTING_KEYS,
        "事後確率(%)": [posteriors[key] * 100.0 for key in SETTING_KEYS],
    })
    chart = (
        alt.Chart(chart_data)
        .mark_bar(size=36, cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("設定:N", sort=SETTING_KEYS, axis=alt.Axis(title=None)),
            y=alt.Y("事後確率(%):Q", axis=alt.Axis(title=None)),
            color=alt.condition(
                alt.datum.設定 == top_key,
                alt.value("#E74C3C"),  # 最有力の設定を赤で表示
                alt.value("#2F80ED"),
            ),
            tooltip=[alt.Tooltip("設定:N"), alt.Tooltip("事後確率(%):Q", format=".2f")],
        )
        .properties(height=260)
    )
    st.altair_chart(chart, use_container_width=True)

    # 表形式で各設定の事前・事後を表示
    rows = []
    for key in SETTING_KEYS:
        p = SETTINGS[key]
        rows.append(
            {
                "設定": key,
                "確率(1/x)": round(1.0 / p, 2),
                "事前(%)": round(priors_norm[key] * 100.0, 2),
                "事後(%)": round(posteriors[key] * 100.0, 2),
            }
        )
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # 共有用テキストとコピー用ボタン
    summary_lines = [
        "モンキーターンV 判別結果",
        f"総回転数: {st.session_state.n}G",
        f"小役回数: {st.session_state.k}回",
        f"最有力設定: 設定{top_key} ({top_prob:.2f}%)",
        f"低設定(1・2): {low_prob:.2f}%",
        f"高設定(4・5・6): {high_prob:.2f}%",
        "各設定の事後確率:",
    ]
    for key in SETTING_KEYS:
        summary_lines.append(
            f"  設定{key}: {posteriors[key] * 100.0:.2f}% (事前 {priors_norm[key] * 100.0:.2f}%)"
        )
    copy_text = "\n".join(summary_lines)

    st.text_area("共有用テキスト", value=copy_text, height=220)

    escaped_text = html.escape(copy_text)
    st.markdown(
        f"""
        <div class="copy-share-container">
          <textarea id="share-text" style="position: absolute; left: -9999px; top: -9999px;" aria-hidden="true">{escaped_text}</textarea>
          <button onclick="navigator.clipboard.writeText(document.getElementById('share-text').value).then(() => window.alert('判別結果をコピーしました。')).catch(() => window.alert('コピーに失敗しました。'));">
            判別結果をコピー
          </button>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.info("フォームに入力し「計算する」を押してください。事前確率は未設定でも自動で均等化されます。")
