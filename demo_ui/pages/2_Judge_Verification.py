"""Streamlit judge verification page — reproducibility and evidence inspection."""

import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="Judge Verification", page_icon="⚖️", layout="wide")
st.title("Judge Verification Center")
st.caption("Independent reproducibility and evidence inspection")

pkg = ROOT / "evidence" / "judge_package"
eval_path = ROOT / "outputs" / "calibrated_eval_results.json"

col1, col2 = st.columns(2)

with col1:
    st.subheader("Reproduce Pipeline")
    st.code(
        "bash scripts/reproduce.sh\n"
        "python scripts/generate_judge_package.py --train",
        language="bash",
    )
    if st.button("Show eval artifact"):
        if eval_path.exists():
            st.json(json.loads(eval_path.read_text()))
        else:
            st.warning("Run `bash scripts/reproduce.sh` first.")

with col2:
    st.subheader("Evidence Package")
    if (pkg / "verification_manifest.json").exists():
        manifest = json.loads((pkg / "verification_manifest.json").read_text())
        st.json(manifest.get("provenance", {}))
        st.success(f"Package contains {len(manifest.get('files', []))} verified files")
        html = pkg / "index.html"
        if html.exists():
            st.markdown(f"Open **`{html}`** in a browser for the full visual report.")
    else:
        st.warning("Run `python scripts/generate_judge_package.py --train` to build evidence.")

if (pkg / "survey_intelligence.json").exists():
    survey = json.loads((pkg / "survey_intelligence.json").read_text())
    fv = survey.get("field_verification", {})

    st.subheader("If your team visits only three places tomorrow")
    st.metric("Village Accessibility Score", f"{fv.get('village_accessibility_score', 0):.0f} / 100")
    for line in fv.get("top_field_priorities", [])[:3]:
        st.markdown(f"- **{line}**")

    priority_map = pkg / "overlays" / "07_field_priority_map.png"
    if priority_map.exists():
        st.image(str(priority_map), caption="Field verification priority map (1 = go first)", use_container_width=True)

    queue = fv.get("field_verification_queue", [])
    if queue:
        st.markdown("**Ranked queue (with score breakdown)**")
        for item in queue[:5]:
            bd = item.get("score_breakdown", {})
            st.markdown(
                f"**#{item['rank']}** {item['label']} — score **{item['score']:.1f}** "
                f"({item['access_assessment']}, conf {item['mean_confidence']:.2f})  \n"
                f"{item['reason']}  \n"
                f"_Components: confidence risk {bd.get('confidence_risk', 0):.0f}, "
                f"isolation {bd.get('isolation_risk', 0):.0f}, "
                f"size {bd.get('cluster_size', 0):.0f}, "
                f"water {bd.get('water_proximity', 0):.0f}, "
                f"fragmentation {bd.get('fragmentation_context', 0):.0f}_"
            )

    with st.expander("Full survey intelligence JSON"):
        st.json(survey)

if (pkg / "metrics.json").exists():
    st.subheader("Patch Verification Metrics")
    metrics = json.loads((pkg / "metrics.json").read_text())
    st.json(metrics.get("patch_verification", {}))

overlays = pkg / "overlays"
if overlays.exists():
    st.subheader("Evidence Overlays")
    cols = st.columns(3)
    for i, name in enumerate(sorted(overlays.glob("*.png"))):
        with cols[i % 3]:
            st.image(str(name), caption=name.name, use_container_width=True)
