import streamlit as st
import math

from src.constants import SETTING_KEYS, SETTINGS
from src.logic import compute_posteriors, normalize, evaluate_goal, format_percent, format_denominator
from src.styles import get_css
from src.components import (
    render_mobile_header,
    render_mobile_result_card,
    render_probability_bars_mobile,
    render_copy_button
)

# --- メインアプリ ---
def main():
    st.set_page_config(
        page_title="モンキーターンV 判別",
        page_icon="🚤",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    
    st.markdown(get_css(), unsafe_allow_html=True)
    
    # セッション初期化
    if "n" not in st.session_state: st.session_state.n = 0
    if "k" not in st.session_state: st.session_state.k = 0

    render_mobile_header()

    # --- 入力エリア ---
    with st.container():
        col_n, col_k = st.columns(2)
        
        with col_n:
            st.session_state.n = st.number_input("総回転数 (G)", value=st.session_state.n, step=10, key="num_n")

        with col_k:
            st.session_state.k = st.number_input("5枚役回数", value=st.session_state.k, step=1, key="num_k")

    # --- 計算と表示 ---
    if st.session_state.n > 0:
        n = st.session_state.n
        k = st.session_state.k
        
        priors = {key: 1.0/len(SETTING_KEYS) for key in SETTING_KEYS}
        posteriors = compute_posteriors(n, k, priors)
        hit_prob = k / n
        
        prob_456 = sum(posteriors[x] for x in ["4", "5", "6"])
        prob_12 = sum(posteriors[x] for x in ["1", "2"])
        prob_56 = sum(posteriors[x] for x in ["5", "6"])
        prob_124 = sum(posteriors[x] for x in ["1", "2", "4"])

        se = math.sqrt(hit_prob * (1.0 - hit_prob) / n) if hit_prob < 1.0 else 0.0
        ci_range_pct = (1.96 * se * 2) * 100.0
        
        eval_456 = evaluate_goal("456", prob_456, prob_12, n, ci_range_pct)
        eval_56 = evaluate_goal("56", prob_56, prob_124, n, ci_range_pct)

        st.markdown("---")
        
        # 結果カード (456期待度)
        render_mobile_result_card(
            title="456期待度",
            value_text=format_percent(prob_456),
            sub_text=f"信頼度: {eval_456['stars']}/5",
            stars=eval_456['stars'],
            comment=eval_456['comment'],
            is_highlight=(eval_456['stars'] >= 4)
        )

        # 結果カード (56期待度)
        render_mobile_result_card(
            title="56期待度",
            value_text=format_percent(prob_56),
            sub_text=f"信頼度: {eval_56['stars']}/5",
            stars=eval_56['stars'],
            comment=eval_56['comment'],
            is_highlight=(eval_56['stars'] >= 4)
        )

        # 実測値
        top_setting = max(posteriors, key=posteriors.get)
        expected_prob = SETTINGS[top_setting]
        
        # 確率分母での比較
        current_denom = 1.0 / hit_prob if hit_prob > 0 else 0.0
        expected_denom = 1.0 / expected_prob
        diff_denom = current_denom - expected_denom
        
        sign_str = "+" if diff_denom > 0 else ""
        
        render_mobile_result_card(
            title="現在の確率",
            value_text=format_denominator(hit_prob),
            sub_text=f"{k}回 / {n}G (設定{top_setting}の理論値 1/{expected_denom:.1f})",
            comment=f"理論値とのズレ: {sign_str}{diff_denom:.1f} (分母)"
        )

        # 詳細データ
        with st.expander("📊 設定別詳細データ", expanded=False):
            render_probability_bars_mobile(posteriors)

        # シェア用テキスト生成
        stars_456 = "★" * eval_456['stars'] + "☆" * (5 - eval_456['stars'])
        stars_56 = "★" * eval_56['stars'] + "☆" * (5 - eval_56['stars'])
        
        share_text = f"""【モンキーターンV 設定判別】
総回転数: {n}G
5枚役: {format_denominator(hit_prob)} ({k}回)

[456期待度] {format_percent(prob_456)}
{stars_456}
{eval_456['comment']}

[56期待度] {format_percent(prob_56)}
{stars_56}
{eval_56['comment']}

現在の確率: 設定{top_setting}近似
(理論値ズレ {sign_str}{diff_denom:.1f})
"""
        render_copy_button(share_text)

    else:
        st.info("👆 回転数と小役回数を入力してください")

if __name__ == "__main__":
    main()
