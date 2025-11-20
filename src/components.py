import streamlit as st
import streamlit.components.v1 as components
from typing import Dict, Any
from .constants import SETTING_KEYS, SETTINGS
from .logic import format_percent, format_denominator
import json
import uuid

def render_copy_button(text: str, label: str = "結果をコピーしてシェア"):
    """クリップボードにテキストをコピーするボタン"""
    button_id = f"copy-btn-{uuid.uuid4().hex}"
    text_json = json.dumps(text, ensure_ascii=False)
    
    html = f"""
    <div style="text-align: center; margin-top: 20px; margin-bottom: 20px;">
        <button id="{button_id}" style="
            background-color: #2ecc71; 
            color: white; 
            border: none; 
            padding: 12px 24px; 
            border-radius: 25px; 
            font-weight: bold; 
            font-size: 1rem; 
            cursor: pointer; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            width: 100%;
            max-width: 300px;
            transition: transform 0.1s;
        ">
            {label} 📋
        </button>
    </div>
    <script>
        (function() {{
            const btn = document.getElementById('{button_id}');
            const text = {text_json};
            if (btn) {{
                btn.addEventListener('click', function() {{
                    navigator.clipboard.writeText(text).then(function() {{
                        btn.innerText = 'コピーしました！ ✅';
                        setTimeout(function() {{ btn.innerText = '{label} 📋'; }}, 2000);
                    }}, function(err) {{
                        console.error('Could not copy text: ', err);
                        alert('コピーに失敗しました');
                    }});
                }});
            }}
        }})();
    </script>
    """
    components.html(html, height=80)

def render_mobile_header():
    """スマホ向けのコンパクトなヘッダー"""
    st.markdown("<h1>🚤 モンキーターンV 判別</h1>", unsafe_allow_html=True)

def render_star_rating(stars: int) -> str:
    """星のHTML生成"""
    html = '<span class="star-rating">'
    for i in range(5):
        if i < stars:
            html += '<span class="star-on">★</span>'
        else:
            html += '<span class="star-off">★</span>'
    html += '</span>'
    return html

def render_mobile_result_card(
    title: str, 
    value_text: str, 
    sub_text: str, 
    stars: int = 0, 
    comment: str = None,
    is_highlight: bool = False
):
    """スマホで見やすい結果カード"""
    star_html = render_star_rating(stars) if stars > 0 else ""
    highlight_class = "high" if is_highlight else "low"
    
    # HTMLを1行にまとめてMarkdown解釈を回避
    advice_html = f'<div class="advice-box {highlight_class}">{comment}</div>' if comment else ''
    html = f'<div class="info-card"><div class="result-card-header"><span>{title}</span>{star_html}</div><div class="result-card-value">{value_text}</div><div class="result-card-sub">{sub_text}</div>{advice_html}</div>'
    
    st.markdown(html, unsafe_allow_html=True)

def render_probability_bars_mobile(posteriors: Dict[str, float]):
    """スマホ向けの確率バー表示"""
    st.markdown("#### 設定期待度")
    
    html_content = ""
    for key in SETTING_KEYS:
        prob = posteriors[key]
        pct = prob * 100
        bar_class = f"bg-{key}"
        
        # インデントを排除したHTML文字列を作成
        html_content += f"""
        <div class="bar-wrapper">
            <div class="bar-label">設定{key}</div>
            <div class="bar-track">
                <div class="bar-fill {bar_class}" style="width: {pct}%;"></div>
            </div>
            <div class="bar-value">{pct:.1f}%</div>
        </div>
        """
    
    st.markdown(html_content, unsafe_allow_html=True)

def render_input_buttons(current_val: int, step_vals: list, key_prefix: str) -> int:
    """クイック加算ボタン"""
    cols = st.columns(len(step_vals))
    new_val = current_val
    
    for idx, step in enumerate(step_vals):
        with cols[idx]:
            if st.button(f"+{step}", key=f"{key_prefix}_add_{step}", use_container_width=True):
                new_val += step
                
    return new_val
