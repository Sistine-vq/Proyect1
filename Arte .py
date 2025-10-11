import streamlit as st
import random

st.set_page_config(page_title="Ecuaciones de primer grado", page_icon="🧮")

st.title("🧮 Práctica de ecuaciones de primer grado")
st.write("Resuelve la ecuación y verifica tu respuesta.")

# --- Generar ecuación aleatoria ---
if "a" not in st.session_state:
    st.session_state.a = random.randint(1, 10)
    st.session_state.b = random.randint(1, 10)
    st.session_state.c = random.randint(1, 20)
    st.session_state.x = (st.session_state.c - st.session_state.b) / st.session_state.a

# Mostrar ecuación
st.markdown(f"### {st.session_state.a}x + {st.session_state.b} = {st.session_state.c}")

# Entrada del usuario
respuesta = st.number_input("Tu respuesta para x:", step=0.1, format="%.2f")

# Botones
col1, col2 = st.columns(2)
with col1:
    verificar = st.button("✅ Verificar respuesta")
with col2:
    nueva = st.button("🔁 Nueva ecuación")

# Verificar resultado
if verificar:
    x_real = round(st.session_state.x, 2)
    if round(respuesta, 2) == x_real:
        st.success(f"¡Correcto! 🎉 La respuesta es x = {x_real}")
    else:
        st.error(f"Incorrecto 😢. La respuesta correcta era x = {x_real}")

# Generar nueva ecuación
if nueva:
    st.session_state.a = random.randint(1, 10)
    st.session_state.b = random.randint(1, 10)
    st.session_state.c = random.randint(1, 20)
    st.session_state.x = (st.session_state.c - st.session_state.b) / st.session_state.a
    st.experimental_rerun()
  
