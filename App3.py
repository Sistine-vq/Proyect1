# nueva_app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Startup Simulator Perú 2026", page_icon="📊", layout="centered")

st.title("📊 Simulador de Negocios Digitales: Startup Perú 2026")
st.write("Analiza el rendimiento potencial de un emprendimiento digital peruano para el año 2026.")

st.header("1️⃣ Datos iniciales del emprendimiento")
precio = st.number_input("Precio promedio del producto o servicio (S/)", min_value=1.0, step=1.0)
costo = st.number_input("Costo promedio por unidad (S/)", min_value=0.5, step=0.5)
usuarios = st.number_input("Número estimado de usuarios mensuales", min_value=1, step=10)
gasto_fijo = st.number_input("Gastos fijos mensuales (S/)", min_value=0.0, step=100.0)

if st.button("Calcular resultados"):
    ingreso = precio * usuarios
    costo_total = (costo * usuarios) + gasto_fijo
    ganancia = ingreso - costo_total
    punto_equilibrio = gasto_fijo / (precio - costo) if (precio - costo) > 0 else None

    st.subheader("2️⃣ Resultados del análisis")
    st.metric("Ingresos totales (S/)", f"{ingreso:,.2f}")
    st.metric("Costos totales (S/)", f"{costo_total:,.2f}")
    st.metric("Ganancia neta (S/)", f"{ganancia:,.2f}")

    if punto_equilibrio:
        st.info(f"📈 Punto de equilibrio: {punto_equilibrio:,.0f} unidades")
    else:
        st.warning("⚠️ El precio debe ser mayor al costo para calcular el punto de equilibrio.")

    st.subheader("3️⃣ Gráfico del rendimiento")
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun"]
    crecimiento = [usuarios * (1 + i*0.05) for i in range(len(meses))]
    ingresos = [precio * u for u in crecimiento]
    costos = [costo * u + gasto_fijo for u in crecimiento]

    df = pd.DataFrame({"Mes": meses, "Ingresos": ingresos, "Costos": costos})

    fig, ax = plt.subplots()
    ax.plot(df["Mes"], df["Ingresos"], label="Ingresos", marker="o")
    ax.plot(df["Mes"], df["Costos"], label="Costos", marker="o")
    ax.set_xlabel("Mes")
    ax.set_ylabel("Soles (S/)")
    ax.set_title("Evolución de Ingresos y Costos")
    ax.legend()
    st.pyplot(fig)

st.caption("Desarrollado por Sistine ✨ | Universidad Peruana de Ciencias Aplicadas (UPC)")
