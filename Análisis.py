import streamlit as st
import pandas as pd

# Título principal
st.set_page_config(page_title="Candidatos Perú 2026", layout="wide")
st.title("🔍 Análisis de Candidatos — Elecciones Perú 2026")

st.markdown("""
Esta app muestra candidatos que hasta ahora han sido mencionados en medios, con datos reales y sus fuentes.  
Actualiza los datos conforme salgan confirmaciones oficiales del JNE u otros medios confiables.
""")

# Datos base (ejemplo) con fuentes
data = [
    {
        "name": "Rafael López Aliaga",
        "party": "Renovación Popular",
        "status": "Anunció postulación",
        "notes": "Renunciará a su cargo de alcalde para postular a la presidencia en 2026",
        "polling": None,
        "sources": ["https://www.reuters.com/world/americas/perus-porky-mayor-lima-quits-run-president-2025-10-13/"]
    },
    {
        "name": "Keiko Fujimori",
        "party": "Fuerza Popular",
        "status": "Figura mencionada",
        "notes": "Aparece en encuestas como posible candidata presidencial",
        "polling": 11.0,
        "sources": ["https://www.ipsos.com/es-pe/encuesta-peru-21-ipsos-quienes-lideran-las-preferencias-electorales-para-el-2026"]
    },
    {
        "name": "Carlos Álvarez",
        "party": None,
        "status": "Mencionado en encuestas",
        "notes": "Está entre los nombres que encabezan intención de voto en encuestas",
        "polling": 6.0,
        "sources": ["https://www.ipsos.com/es-pe/encuesta-peru-21-ipsos-quienes-lideran-las-preferencias-electorales-para-el-2026"]
    },
    {
        "name": "Alfonso López Chau",
        "party": "Ahora Nación",
        "status": "Candidato oficial del partido",
        "notes": "Ahora Nación se postula con López Chau como candidato",
        "polling": None,
        "sources": ["https://es.wikipedia.org/wiki/Ahora_Naci%C3%B3n"]
    },
    {
        "name": "Enrique Valderrama",
        "party": "APRA",
        "status": "Candidato interno",
        "notes": "Candidato por el partido APRA para la nominación presidencial",
        "polling": None,
        "sources": ["https://es.wikipedia.org/wiki/Enrique_Valderrama"]
    },
    {
        "name": "Hernán Garrido Lecca",
        "party": "APRA",
        "status": "Precandidato",
        "notes": "Figura que compite por la candidatura presidencial del APRA",
        "polling": None,
        "sources": ["https://es.wikipedia.org/wiki/Hern%C3%A1n_Garrido_Lecca"]
    }
]

# Convertir a DataFrame
df = pd.DataFrame(data)

# Filtros
st.sidebar.header("Filtros")
# Filtrar por si tiene valor de encuesta
show_with_polling = st.sidebar.checkbox("Solo con polling", value=False)
if show_with_polling:
    df = df[df["polling"].notna()]

search_name = st.sidebar.text_input("Buscar por nombre")
if search_name:
    df = df[df["name"].str.contains(search_name, case=False, na=False)]

# Mostrar tabla principal
st.subheader("Candidatos / figuras mencionadas")
# Mostrar porcentaje si existe
def fmt_poll(v):
    return f"{v:.1f} %" if pd.notna(v) else "-"

df_display = df.copy()
df_display["polling"] = df_display["polling"].apply(fmt_poll)
df_display = df_display.rename(columns={
    "name": "Nombre",
    "party": "Partido",
    "status": "Estado",
    "notes": "Notas",
    "polling": "Encuesta",
    "sources": "Fuentes"
})

st.dataframe(df_display[["Nombre", "Partido", "Estado", "Encuesta", "Notas"]], use_container_width=True)

# Detalle expandible por candidato
st.markdown("---")
st.subheader("Detalles por candidato")

for _, row in df.iterrows():
    with st.expander(row["name"]):
        st.write("**Partido / Agrupación:**", row["party"])
        st.write("**Estado actual:**", row["status"])
        st.write("**Notas:**", row["notes"])
        if pd.notna(row["polling"]):
            st.write("**Encuesta estimada:**", fmt_poll(row["polling"]))
        st.write("**Fuentes:**")
        for s in row["sources"]:
            st.markdown(f"- {s}")

# Pie de página con información general
st.markdown("---")
st.markdown("""
**Información general conocida hasta ahora**  
- Las elecciones generales en Perú están convocadas para el **12 de abril de 2026**.  
- Los candidatos mostrados están en medios, pero podrían cambiar cuando haya inscripciones oficiales del JNE.  
- Actualiza este archivo frecuentemente con fuentes oficiales (JNE, medios reconocidos).

""")
