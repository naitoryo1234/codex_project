from pathlib import Path
from typing import Any, Dict, Optional

import streamlit as st
import streamlit.components.v1 as components


KOYAKU_COMPONENT_BUILD_DIR = Path(__file__).parent / "koyaku_counter_component" / "build"
if KOYAKU_COMPONENT_BUILD_DIR.exists():
    _koyaku_counter_component = components.declare_component(
        "koyaku_counter",
        path=str(KOYAKU_COMPONENT_BUILD_DIR),
    )
else:
    _koyaku_counter_component = None


def render_koyaku_counter(**kwargs: Any) -> Optional[Dict[str, Any]]:
    if _koyaku_counter_component is None:
        st.info(
            "Koyaku counter build directory was not found. Run npm run build in koyaku_counter_component."
        )
        return None
    return _koyaku_counter_component(**kwargs)


def snapshot_from_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    snapshot: Dict[str, Any] = {"raw": data}
    primary = data.get("primaryCount")
    if isinstance(primary, int):
        snapshot["primary"] = primary
    counts = data.get("counts")
    if isinstance(counts, (list, tuple)):
        numeric = [x for x in counts if isinstance(x, int)]
        snapshot["counts"] = numeric
        snapshot["total"] = sum(numeric)
    return snapshot


st.set_page_config(
    page_title="Koyaku Counter",
    page_icon="slot",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      .block-container { padding-top: 0.6rem; padding-bottom: 0.8rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


payload = render_koyaku_counter(key="koyaku-counter-standalone")

if isinstance(payload, dict):
    st.session_state["koyaku_latest"] = snapshot_from_payload(payload)

