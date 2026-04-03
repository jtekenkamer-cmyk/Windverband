import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from solver_wind import calculate_wind_bracing, get_l_profiles, get_bolt_data
from fpdf import FPDF
from datetime import date
import os

st.set_page_config(page_title="Windverband Calculator Pro", layout="wide")

# --- SIDEBAR INPUTS ---
st.sidebar.header("📁 Projectinformatie")
prj_naam = st.sidebar.text_input("Projectnaam", "Nieuwe Loods")
prj_ond = st.sidebar.text_input("Onderdeel", "Windverband As 1")
prj_datum = st.sidebar.date_input("Datum", date.today())

st.sidebar.divider()
st.sidebar.header("⚙️ Invoer Parameters")
v_h = st.sidebar.number_input("Veldhoogte (m)", 1.0, 20.0, 6.0)
v_b = st.sidebar.number_input("Veldbreedte (m)", 1.0, 20.0, 5.0)
f_ed = st.sidebar.number_input("Trekkracht F_ed (kN)", 1.0, 1000.0, 50.0)

type_s = st.sidebar.selectbox("Type schoor", ["L-profiel", "Strip", "Ronde staaf"])
fy = st.sidebar.selectbox("Staalsterkte (N/mm2)", [235, 355], index=1)

d_str, b_str, gekozen_p = 10.0, 60.0, "L 50x50x5"
if type_s == "L-profiel":
    gekozen_p = st.sidebar.selectbox("Selecteer L-profiel", list(get_l_profiles().keys()))
elif type_s == "Strip":
    d_str = st.sidebar.number_input("Dikte strip (mm)", 5, 30, 10)
    b_str = st.sidebar.number_input("Breedte strip (mm)", 20, 300, 60)
else:
    gekozen_p = st.sidebar.slider("Diameter staaf (mm)", 10, 40, 20)

st.sidebar.divider()
st.sidebar.header("🔩 Boutgegevens")
b_d = st.sidebar.selectbox("Boutmaat M", [12, 16, 20, 24], index=1)
b_kl = st.sidebar.selectbox("Boutklasse", ["8.8", "10.9"])
b_n = st.sidebar.number_input("Aantal bouten", 1, 10, 2)

# --- BEREKENING ---
res = calculate_wind_bracing(
    v_h=v_h, v_b=v_b, f_ed_input=f_ed, fy=fy, 
    keuze_p=gekozen_p, type_s=type_s, d_str=d_str, 
    b_str=b_str, b_d=b_d, b_kl=b_kl, b_n=b_n
)

# --- HOOFDSCHERM OUTPUT ---
st.title(f"🌪️ Rapportage: {prj_naam}")
st.info(f"Berekening windverband: {type_s} {gekozen_p if type_s != 'Strip' else f'{b_str}x{d_str}'}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Trekkracht F_ed", f"{res['F_ed']} kN")
c2.metric("Cap. Staaf", f"{res['N_rd_staal']} kN")
c3.metric("Cap. Bouten", f"{res['N_rd_bouten']} kN")
uc_max = max(res['UC_staal'], res['UC_bout'])
c4.metric("Max Unity Check", f"{uc_max}")

if uc_max <= 1.0:
    st.success("✅ HET ONTWERP VOLDOET")
else:
    st.error("❌ HET ONTWERP VOLDOET NIET")

# --- DETAILTEKENING ---
st.subheader("📐 Verbindingsdetail (Uiteinde)")
fig, ax = plt.subplots(figsize=(10, 3))
draw_w = res['kopmaat'] + 40
draw_h = res['breedte']

# Teken de staaf
ax.add_patch(plt.Rectangle((0, 0), draw_w, draw_h, facecolor='#d3d3d3', edgecolor='black', lw=2))

# Teken bouten en maatvoering
for i in range(int(b_n)):
    x_pos = res['e1'] + i * res['p1']
    y_pos = draw_h / 2
    ax.scatter(x_pos, y_pos, color='red', s=200, zorder=3)
    ax.text(x_pos, y_pos - (draw_h*0.3), f"M{b_d}", ha='center', color='red', weight='bold')

# Maatlijnen annotaties
ax.annotate('', xy=(0, draw_h/2), xytext=(res['e1'], draw_h/2), arrowprops=dict(arrowstyle='<->'))
ax.text(res['e1']/2, draw_h/2 + 5, f"e1={res['e1']}", ha='center', fontsize=9)

if b_n > 1:
    ax.annotate('', xy=(res['e1'], draw_h/2), xytext=(res['e1']+res['p1'], draw_h/2), arrowprops=dict(arrowstyle='<->'))
    ax.text(res['e1'] + res['p1']/2, draw_h/2 + 5, f"p1={res['p1']}", ha='center', fontsize=9)

ax.set_xlim(-10, draw_w + 10)
ax.set_ylim(-20, draw_h + 20)
ax.set_aspect('equal')
ax.axis('off')
st.pyplot(fig)
fig.savefig("temp_detail.png", bbox_inches='tight')

# --- TEKSTUEEL RAPPORT ---
with st.expander("📝 Toelichting Berekening (Eurocode 3)"):
    st.write(f"**Sterkte Staaf:** Getoetst op vloeien (bruto) en breuk (netto bij boutgaten). Gatdiameter: {res['d0']} mm.")
    st.write(f"**Boutverbinding:** Afschuivingscapaciteit per bout: {res['F_v_rd']} kN. Stuikcapaciteit per bout: {res['F_b_rd']} kN.")
    st.write(f"**Geometrie:** Gebaseerde minimale randafstand e1={res['e1']} mm en h.o.h. afstand p1={res['p1']} mm.")

# --- PDF GENERATIE ---
def create_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Rapport: {prj_naam}", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 8, f"Onderdeel: {prj_ond} | Datum: {prj_datum}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, "Resultaten (kN)", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 7, f"- Rekenwaarde trekkracht F_ed: {res['F_ed']}", ln=True)
    pdf.cell(0, 7, f"- Capaciteit staaf N_rd: {res['N_rd_staal']} (UC: {res['UC_staal']})", ln=True)
    pdf.cell(0, 7, f"- Capaciteit bouten N_rd: {res['N_rd_bouten']} (UC: {res['UC_bout']})", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11); pdf.cell(0, 8, f"Conclusie: {'VOLDOET' if uc_max <= 1.0 else 'NIET VOLDOET'}", ln=True)
    if os.path.exists("temp_detail.png"):
        pdf.image("temp_detail.png", x=10, y=90, w=150)
    return pdf.output(dest="S").encode("latin-1")

if st.sidebar.button("📄 Genereer PDF"):
    pdf_bytes = create_pdf()
    st.sidebar.download_button("⬇️ Download PDF", pdf_bytes, f"Rapport_{prj_naam}.pdf", "application/pdf")
