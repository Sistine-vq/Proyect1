# app.py
import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config("Votación Demo (educativa)", page_icon="🗳️", layout="centered")
st.title("🗳️ Votación — Demo educativa")
st.write(
    "⚠️ **ATENCIÓN:** Solo demo educativa. No usar DNIs reales ni desplegar como sistema de votación real."
)

# ----- Configuración -----
VOTERS_CSV = "voters_sample.csv"      # CSV con columnas: dni,name,district,mesa (opcional)
AUDIT_LOG = "votes_log.csv"           # registro de votos
RESULTS_CACHE = "results_cache.csv"   # (opcional) cache de resultados

# Candidatos de ejemplo
CANDIDATES = {
    "1": "Candidato A",
    "2": "Candidato B",
    "3": "Candidato C",
    "BLANCO": "Voto en Blanco",
    "NULO": "Voto Nulo"
}

# ----- Cargar lista de votantes de prueba -----
st.sidebar.header("Carga de votantes (demo)")
uploaded = st.sidebar.file_uploader("Sube CSV de votantes (opcional)", type=["csv"])
if uploaded:
    voters_df = pd.read_csv(uploaded, dtype=str)
else:
    try:
        voters_df = pd.read_csv(VOTERS_CSV, dtype=str)
    except FileNotFoundError:
        # Crear ejemplo si no existe
        voters_df = pd.DataFrame({
            "dni": [f"0000000{n}" for n in range(1, 21)],
            "name": [f"Votante Demo {n}" for n in range(1, 21)],
            # asignar distrito y mesa de ejemplo
            "district": [f"Distrito {((n-1)//5)+1}" for n in range(1, 21)],
            "mesa": [f"Mesa {((n-1)%5)+1}" for n in range(1, 21)]
        })
        # guardar ejemplo localmente (opcional)
        voters_df.to_csv(VOTERS_CSV, index=False)

st.sidebar.markdown(f"Votantes de prueba: **{len(voters_df)}**")

# ----- Utilidades: cargar audit log y resultados -----
def load_audit_log():
    if os.path.exists(AUDIT_LOG):
        return pd.read_csv(AUDIT_LOG, dtype=str)
    else:
        df = pd.DataFrame(columns=["timestamp","dni","name","district","mesa","candidate_key","candidate_name"])
        df.to_csv(AUDIT_LOG, index=False)
        return df

def append_audit_row(row: dict):
    df = load_audit_log()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(AUDIT_LOG, index=False)

audit_df = load_audit_log()

# Obtener DNIs que ya votaron (persistente en AUDIT_LOG)
voted_dnies_global = set(audit_df["dni"].astype(str).str.strip().tolist())

# ----- Interfaz principal -----
st.subheader("Iniciar (demo)")
st.write("Introduce un DNI de prueba (no usar DNIs reales). Verificaremos que esté en la lista de votantes de demo.")

col1, col2 = st.columns([2,1])
with col1:
    dni_input = st.text_input("DNI (demo):", value="")
with col2:
    if st.button("🔎 Validar DNI"):
        dni = dni_input.strip()
        if dni == "":
            st.warning("Escribe un DNI de prueba.")
        else:
            matched = voters_df[voters_df["dni"].astype(str).str.strip() == dni]
            if matched.empty:
                st.error("DNI NO encontrado en la lista de votantes de demo.")
                st.session_state.pop("dni_verified", None)
            else:
                name = matched.iloc[0].get("name", "")
                district = matched.iloc[0].get("district", "")
                mesa = matched.iloc[0].get("mesa", "")
                if dni in voted_dnies_global:
                    st.error("Este DNI ya aparece en el registro de votos (ya votó).")
                    st.session_state.pop("dni_verified", None)
                else:
                    st.success(f"DNI verificado: {dni} — {name}")
                    st.session_state["dni_verified"] = dni
                    st.session_state["dni_name"] = name
                    st.session_state["dni_district"] = district
                    st.session_state["dni_mesa"] = mesa

if st.button("🔁 Limpiar verificación"):
    st.session_state.pop("dni_verified", None)
    st.session_state.pop("dni_name", None)
    st.session_state.pop("dni_district", None)
    st.session_state.pop("dni_mesa", None)
    st.experimental_rerun()

# ----- Si verificado, mostrar boleta -----
if st.session_state.get("dni_verified"):
    st.markdown("---")
    st.subheader("Boleta (demo)")
    st.write(f"Votante: **{st.session_state.get('dni_name','')}** — DNI: **{st.session_state['dni_verified']}**")
    # Permitir cambiar distrito/mesa si se quiere (simulación)
    district = st.text_input("Distrito (simulado):", value=st.session_state.get("dni_district",""))
    mesa = st.text_input("Mesa (simulado):", value=st.session_state.get("dni_mesa",""))
    choice = st.radio("Selecciona tu opción:", options=list(CANDIDATES.keys()),
                      format_func=lambda k: f"{k} — {CANDIDATES[k]}")
    if st.button("🗳️ Emitir voto (demo)"):
        dni = st.session_state["dni_verified"]
        if dni in voted_dnies_global:
            st.error("Error: este DNI ya votó (registro persistente).")
        else:
            # registrar en log (append CSV)
            row = {
                "timestamp": datetime.utcnow().isoformat(),
                "dni": dni,
                "name": st.session_state.get("dni_name",""),
                "district": district,
                "mesa": mesa,
                "candidate_key": choice,
                "candidate_name": CANDIDATES[choice]
            }
            append_audit_row(row)
            st.success(f"Voto registrado para: {CANDIDATES[choice]}")
            # actualizar set local para prevenir voto repetido en la misma instancia
            voted_dnies_global.add(dni)
            # limpiar verificación
            st.session_state.pop("dni_verified", None)

st.markdown("---")
# ----- Mostrar resultados agregados (en tiempo real, a partir del log) -----
st.subheader("Resultados agregados (demo)")
audit_df = load_audit_log()
if audit_df.empty:
    st.info("Aún no hay votos registrados (demo).")
else:
    # conteo por candidato
    counts = audit_df.groupby(["candidate_key","candidate_name"]).size().reset_index(name="votos")
    counts = counts.sort_values("votos", ascending=False)
    st.table(counts)

    # conteo por distrito (ejemplo)
    st.write("Conteo por distrito (demo):")
    try:
        by_dist = audit_df.groupby(["district","candidate_key"]).size().reset_index(name="votos")
        pivot = by_dist.pivot(index="district", columns="candidate_key", values="votos").fillna(0).astype(int)
        st.dataframe(pivot)
    except Exception:
        st.info("No hay campos 'district' bien definidos en los registros de votantes demo.")

# ----- Herramientas administrativas (demo) -----
st.markdown("---")
st.subheader("Administración (demo)")

colA, colB, colC = st.columns(3)
with colA:
    if st.button("📥 Descargar log (CSV)"):
        csv = audit_df.to_csv(index=False).encode("utf-8")
        st.download_button("Descargar registro de votos", data=csv, file_name="votes_log.csv", mime="text/csv")
with colB:
    if st.button("📊 Descargar resultados agregados (CSV)"):
        # generar conteo por candidato
        if audit_df.empty:
            st.warning("No hay votos para exportar.")
        else:
            results = audit_df.groupby(["candidate_key","candidate_name"]).size().reset_index(name="votos")
            csv2 = results.to_csv(index=False).encode("utf-8")
            st.download_button("Descargar resultados", data=csv2, file_name="results_agg.csv", mime="text/csv")
with colC:
    if st.button("♻️ Reiniciar registros (demo)"):
        # Precaución: esto borra el archivo de log en el servidor (solo demo)
        if os.path.exists(AUDIT_LOG):
            os.remove(AUDIT_LOG)
        # re-crear vacío
        load_audit_log()
        st.success("Registros reiniciados (demo).")
        st.experimental_rerun()

# Mostrar lista de votantes demo (opcional)
if st.checkbox("Mostrar lista de votantes (demo)"):
    st.dataframe(voters_df)

st.markdown("---")
st.write(
    "ℹ️ **Notas:**\n"
    "- Esta app es **solo una simulación educativa**.\n"
    "- No se conecta a RENIEC/ONPE, no valida identidad real ni implementa seguridad para votaciones reales.\n"
    "- No uses DNIs reales aquí.\n"
)
