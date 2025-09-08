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


st.set_page_config(page_title="設定推定 (ベイズ)", layout="centered")
st.title("設定推定ツール (ベイズ更新)")

with st.form("inputs"):
    st.subheader("入力")
    col1, col2 = st.columns(2)
    with col1:
        n = st.number_input("総回転数 N", min_value=0, value=1000, step=10)
    with col2:
        k = st.number_input("小役回数 k", min_value=0, value=20, step=1)

    st.markdown("事前確率（均等がデフォルト。合計は自動正規化）")
    prior_cols = st.columns(len(SETTING_KEYS))
    prior_inputs: Dict[str, float] = {}
    default_uniform = 100.0 / len(SETTING_KEYS)
    for idx, key in enumerate(SETTING_KEYS):
        with prior_cols[idx]:
            prior_inputs[key] = st.number_input(
                f"設定 {key}", min_value=0.0, value=float(f"{default_uniform:.1f}"), step=0.1, key=f"prior_{key}"
            )

    submitted = st.form_submit_button("計算する")

if submitted:
    priors = prior_inputs  # 値は正規化前（比率や%でOK）

    if n < 0 or k < 0 or k > n:
        st.error("入力エラー: 0 <= 小役回数 <= 回転数 を満たしてください。")
        st.stop()

    posteriors = compute_posteriors(int(n), int(k), priors)

    st.subheader("結果")

    df_rows = []
    for key in SETTING_KEYS:
        p = SETTINGS[key]
        df_rows.append(
            {
                "設定": key,
                "理論値(1/x)": round(1.0 / p, 2),
                "事前(%)": round(normalize(priors)[key] * 100.0, 2),
                "事後(%)": round(posteriors[key] * 100.0, 2),
            }
        )
    df = pd.DataFrame(df_rows)

    st.dataframe(df, use_container_width=True)

    chart_data = pd.DataFrame({
        "設定": SETTING_KEYS,
        "事後(%)": [posteriors[k] * 100.0 for k in SETTING_KEYS],
    })
    chart = (
        alt.Chart(chart_data)
        .mark_bar(color="#007bff")
        .encode(x=alt.X("設定:N", sort=SETTING_KEYS), y=alt.Y("事後(%):Q"))
        .properties(height=300)
    )
    st.altair_chart(chart, use_container_width=True)

    # 低設定/高設定のグループ表示（参考）
    low_keys = ["1", "2"]
    high_keys = ["4", "5", "6"]
    low_prob = sum(posteriors.get(k, 0.0) for k in low_keys) * 100.0
    high_prob = sum(posteriors.get(k, 0.0) for k in high_keys) * 100.0
    st.markdown(
        f"低設定 (1,2): **{low_prob:.2f}%**　｜　高設定 (4,5,6): **{high_prob:.2f}%**"
    )
else:
    st.info("フォームに入力して『計算する』を押してください。事前確率はデフォルトで均等配分です。")
