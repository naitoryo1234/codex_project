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


# ページ設定（モバイル最適化）
st.set_page_config(page_title="設定推定 (ベイズ)", page_icon="🎰", layout="centered", initial_sidebar_state="collapsed")

# 余白やフォントをモバイル向けに調整
st.markdown(
    """
    <style>
      /* 全体の左右余白をやや詰める */
      .block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: 860px; }
      /* インプットやラベルの行間を詰める */
      label, .stMarkdown p { font-size: 0.95rem; }
      .stNumberInput input { font-size: 1rem; }
      /* 小さめ画面での余白調整 */
      @media (max-width: 420px) {
        .block-container { padding-left: 0.6rem; padding-right: 0.6rem; }
        label, .stMarkdown p { font-size: 0.9rem; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("設定推定ツール (ベイズ更新)")

# セッション状態（クイック操作用）
if "n" not in st.session_state:
    st.session_state.n = 1000
if "k" not in st.session_state:
    st.session_state.k = 20

with st.form("inputs", clear_on_submit=False):
    st.subheader("入力")

    # 数値入力（モバイルで縦積み）
    n = st.number_input("総回転数 N", min_value=0, value=int(st.session_state.n), step=10, key="n_input")
    k = st.number_input("小役回数 k", min_value=0, value=int(st.session_state.k), step=1, key="k_input")

    # クイック操作ボタン（横並び）
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
    with c1:
        if st.form_submit_button("N -50"):
            st.session_state.n = max(0, int(n) - 50)
            st.rerun()
    with c2:
        if st.form_submit_button("N +50"):
            st.session_state.n = int(n) + 50
            st.rerun()
    with c3:
        if st.form_submit_button("k -10"):
            st.session_state.k = max(0, int(k) - 10)
            st.rerun()
    with c4:
        if st.form_submit_button("k +10"):
            st.session_state.k = int(k) + 10
            st.rerun()

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

    # 表示テーブル（モバイルで見やすい列順）
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

    # 棒グラフ（ツールチップ付き、モバイルでタップしやすいサイズ）
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

else:
    st.info("フォームに入力して『計算する』を押してください。事前確率はデフォルトで均等配分です。")
