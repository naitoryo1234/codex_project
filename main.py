import math
from typing import Dict, List

import streamlit as st
import pandas as pd
import altair as alt

# 設定ごとの理論値（出現確率）
SETTINGS: Dict[str, float] = {
    "1": 1 / 38.15,
    "2": 1 / 36.86,
    "4": 1 / 30.27,
    "5": 1 / 24.51,
    "6": 1 / 22.53,
}
SETTING_KEYS: List[str] = list(SETTINGS.keys())


def calculate_likelihood(num_spins: int, num_hits: int, p: float) -> float:
    """二項分布の尤度 P(K=k | N=n, p)。大きな数でも安定するよう対数を使う。"""
    if p <= 0.0 or p >= 1.0 or num_spins <= 0 or num_hits < 0 or num_hits > num_spins:
        return 0.0
    log_nCk = (
        math.lgamma(num_spins + 1)
        - math.lgamma(num_hits + 1)
        - math.lgamma(num_spins - num_hits + 1)
    )
    log_likelihood = log_nCk + num_hits * math.log(p) + (num_spins - num_hits) * math.log(1.0 - p)
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
    for k in SETTING_KEYS:
        p = SETTINGS[k]
        prior = priors.get(k, 0.0)
        likelihood = calculate_likelihood(num_spins, num_hits, p) if prior > 0.0 else 0.0
        numerator = likelihood * prior
        posterior_numerators[k] = numerator
        marginal_likelihood += numerator
    if marginal_likelihood > 0.0:
        return {k: posterior_numerators[k] / marginal_likelihood for k in SETTING_KEYS}
    return priors


# ページ設定（wide + モバイル最適化）
st.set_page_config(page_title="設定推定ツール", page_icon="🎰", layout="wide", initial_sidebar_state="collapsed")

# 余白やフォントをモバイル向けに調整（上部切れ対策: safe-area 分も確保）
st.markdown(
    """
    <style>
      .block-container { padding-top: calc(1.2rem + env(safe-area-inset-top)); padding-bottom: 2rem; max-width: 980px; }
      label, .stMarkdown p { font-size: 0.95rem; }
      .stNumberInput input { font-size: 1rem; }
      /* マイクロボタン行: 2列で横並び、小さめボタン */
      .micro-row { margin-top: 0.25rem; }
      .micro-row [data-testid="stHorizontalBlock"] { display: flex !important; flex-wrap: nowrap !important; }
      .micro-row [data-testid="column"] { width: 50% !important; padding-right: 0.25rem; }
      .micro-row [data-testid="column"]:last-child { padding-right: 0; padding-left: 0.25rem; }
      .micro-row .stButton > button { padding: 0.14rem 0.46rem; font-size: 0.82rem; min-width: 60px; }
      /* metricの値を省略せず折り返し可にする */
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

# iPhone Safari での強制横並び（より強い指定）
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

# セッション状態
if "n" not in st.session_state:
    st.session_state.n = 1000
if "k" not in st.session_state:
    st.session_state.k = 20

with st.form("inputs", clear_on_submit=False):
    st.subheader("入力")

    # N と k を横並び（2カラム・小さめギャップ）
    colN, colK = st.columns(2, gap="small")
    with colN:
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

    with colK:
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

    # 事前確率の設定モード
    st.markdown("事前確率（合計は自動正規化）")
    prior_mode = st.radio("事前の設定", ["均等", "カスタム"], horizontal=True, index=0)

    default_uniform = 100.0 / len(SETTING_KEYS)
    prior_inputs: Dict[str, float] = {k: default_uniform for k in SETTING_KEYS}

    if prior_mode == "カスタム":
        with st.expander("事前確率を細かく指定", expanded=True):
            cols = st.columns(len(SETTING_KEYS))
            for idx, key in enumerate(SETTING_KEYS):
                with cols[idx]:
                    prior_inputs[key] = st.number_input(
                        f"設定 {key}", min_value=0.0, value=float(f"{default_uniform:.1f}"), step=0.1, key=f"prior_{key}"
                    )

    submitted = st.form_submit_button("計算する", use_container_width=True)

if submitted:
    st.session_state.n = int(n)
    st.session_state.k = int(k)

    if st.session_state.k > st.session_state.n:
        st.error("入力エラー: 0 <= 小役回数 <= 回転数 を満たしてください。")
        st.stop()

    priors = prior_inputs  # 比率/百分率でOK（内部で正規化）
    posteriors = compute_posteriors(int(st.session_state.n), int(st.session_state.k), priors)
    priors_norm = normalize(priors)

    # トップ設定の強調表示
    top_key = max(posteriors, key=posteriors.get)
    top_prob = posteriors[top_key] * 100.0

    c1, c2 = st.columns(2)
    with c1:
        st.metric(label="最有力の設定", value=f"設定 {top_key}", delta=f"{top_prob:.2f}%")
    with c2:
        low_prob = sum(posteriors.get(k, 0.0) for k in ["1", "2"]) * 100.0
        high_prob = sum(posteriors.get(k, 0.0) for k in ["4", "5", "6"]) * 100.0
        st.metric(label="低(1,2) / 高(4,5,6)", value=f"{low_prob:.2f}% / {high_prob:.2f}%")
        grp124 = (posteriors.get("1", 0.0) + posteriors.get("2", 0.0) + posteriors.get("4", 0.0)) * 100.0
        grp56 = (posteriors.get("5", 0.0) + posteriors.get("6", 0.0)) * 100.0
        st.metric(label="(1,2,4) / (5,6)", value=f"{grp124:.2f}% / {grp56:.2f}%")

    # 棒グラフ（先に表示）
    chart_data = pd.DataFrame({
        "設定": SETTING_KEYS,
        "事後(%)": [posteriors[k] * 100.0 for k in SETTING_KEYS],
    })
    chart = (
        alt.Chart(chart_data)
        .mark_bar(size=36, cornerRadiusTopLeft=3, cornerRadiusTopRight=3, color="#2F80ED")
        .encode(
            x=alt.X("設定:N", sort=SETTING_KEYS, axis=alt.Axis(title=None)),
            y=alt.Y("事後(%):Q", axis=alt.Axis(title=None)),
            tooltip=[alt.Tooltip("設定:N"), alt.Tooltip("事後(%):Q", format=".2f")],
        )
        .properties(height=260)
    )
    st.altair_chart(chart, use_container_width=True)

    # 表（後に表示）
    rows = []
    for key in SETTING_KEYS:
        p = SETTINGS[key]
        rows.append(
            {
                "設定": key,
                "理論(1/x)": round(1.0 / p, 2),
                "事前(%)": round(priors_norm[key] * 100.0, 2),
                "事後(%)": round(posteriors[key] * 100.0, 2),
            }
        )
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

else:
    st.info("フォームに入力して『計算する』を押してください。事前確率はデフォルトで均等配分です。")
