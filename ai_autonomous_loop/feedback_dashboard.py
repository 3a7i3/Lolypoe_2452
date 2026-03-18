import streamlit as st
import json
import glob
from pathlib import Path

st.set_page_config(page_title="R&D Feedback Dashboard", layout="wide")
st.title("🧠 R&D Feedback Dashboard")

feedback_dir = Path(__file__).parent / "feedback_logs"
feedback_files = sorted(glob.glob(str(feedback_dir / "feedback_*.json")), reverse=True)

if not feedback_files:
    st.warning("Aucun feedback trouvé. Lancez d'abord la boucle R&D.")
else:
    selected = st.selectbox("Sélectionnez un cycle de feedback :", feedback_files)
    with open(selected, encoding="utf-8") as f:
        report = json.load(f)
    st.subheader(f"Rapport du cycle : {Path(selected).name}")
    st.json(report)
    st.markdown("---")
    st.metric("Sharpe moyen", f"{report.get('avg_sharpe', 0):.2f}")
    st.metric("Rendement moyen", f"{report.get('avg_return', 0):.2%}")
    st.metric("Max Drawdown", f"{report.get('max_drawdown', 0):.2%}")
    st.write("**Suggestion :**", report.get("suggestion", "-"))
    st.write("**Exploration :**", ", ".join(report.get("exploration", [])))
    st.write("**Insights :**", ", ".join(report.get("insights", [])))

    # Historique rapide
    st.markdown("## Historique des feedbacks")
    for fpath in feedback_files[:10]:
        with open(fpath, encoding="utf-8") as f:
            rep = json.load(f)
        st.write(f"{Path(fpath).name} : Sharpe={rep.get('avg_sharpe', 0):.2f}, Return={rep.get('avg_return', 0):.2%}, Action={rep.get('suggestion', '-')}")
