
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import os

APP_TITLE = "Benessere – Açaí & Healthy Bowls (Investor Demo)"
DEFAULT_XLSX_PATH = "Financial_Model_Acai_Lite.xlsx"

st.set_page_config(page_title=APP_TITLE, page_icon="🫐", layout="wide")

# ---------- Utilities to read model (compatible with previous app)
def load_excel(path_or_bytes):
    try:
        xls = pd.ExcelFile(path_or_bytes, engine="openpyxl")
        sheets = {name: xls.parse(name) for name in xls.sheet_names}
        return sheets, None
    except Exception as e:
        return {}, f"Error al leer el Excel: {e}"

def normalize_key(s: str):
    return "".join(ch.lower() for ch in str(s) if ch.isalnum())

def kv_from_two_col_df(df):
    if df is None or df.empty or df.shape[1] < 2:
        return {}
    keys = df.iloc[:, 0].astype(str).tolist()
    vals = df.iloc[:, 1].tolist()
    return {normalize_key(k): v for k, v in zip(keys, vals)}

def read_value(kv, label, default=None):
    return kv.get(normalize_key(label), default)

def compute_unit_economics(assumptions_df):
    kv = kv_from_two_col_df(assumptions_df)
    price = read_value(kv, "Price per bowl", np.nan)
    acai = read_value(kv, "Açaí cost per bowl", 0) or read_value(kv, "Acai cost per bowl", 0)
    fruits = read_value(kv, "Fruits cost per bowl", 0)
    granola = read_value(kv, "Granola cost per bowl", 0)
    yogurt = read_value(kv, "Yogurt cost per bowl", 0)
    pack = read_value(kv, "Packaging/others cost per bowl", 0)
    fixed_rent = read_value(kv, "Fixed: Rent/month", 0)
    fixed_salaries = read_value(kv, "Fixed: Salaries/month", 0)
    fixed_util = read_value(kv, "Fixed: Utilities/month", 0)
    fixed_mkt = read_value(kv, "Fixed: Marketing/month", 0)

    v = sum([x if pd.notna(x) else 0 for x in [acai, fruits, granola, yogurt, pack]])
    gm = (price - v) if (pd.notna(price) and pd.notna(v)) else np.nan
    gm_pct = (gm / price) if (pd.notna(gm) and price not in (0, np.nan)) else np.nan

    fixed_total = sum([x if pd.notna(x) else 0 for x in [fixed_rent, fixed_salaries, fixed_util, fixed_mkt]])
    be_units_month = (fixed_total / gm) if (pd.notna(gm) and gm not in (0, np.nan)) else np.nan
    days = read_value(kv, "Working days per month", 26) or 26
    be_units_day = (be_units_month / days) if pd.notna(be_units_month) else np.nan

    df = pd.DataFrame({
        "Metric": ["Price (P)", "Variable cost per bowl (V)", "Gross margin per unit (P-V)",
                   "Gross margin %", "Fixed costs / month", "Break-even units / month", "Break-even units / day"],
        "Value": [price, v, gm, gm_pct, fixed_total, be_units_month, be_units_day]
    })
    return df

def compute_forecast(assumptions_df, unit_df):
    kv = kv_from_two_col_df(assumptions_df)
    months = list(range(1, 13))
    days = int(read_value(kv, "Working days per month", 26) or 26)
    price = float(read_value(kv, "Price per bowl", 0) or 0)
    start_units = float(read_value(kv, "Starting units per day (Month 1)", 30) or 30)
    growth = float(read_value(kv, "Monthly growth rate", 0.10) or 0.10)

    try:
        v = float(unit_df.loc[unit_df["Metric"].str.contains("Variable cost per bowl", case=False), "Value"].iloc[0])
    except Exception:
        v = 0.0

    rows = []
    units_day = start_units
    fixed = float(unit_df.loc[unit_df["Metric"].str.contains("Fixed costs", case=False), "Value"].iloc[0]) if "Fixed costs / month" in unit_df["Metric"].values else 0.0

    for m in months:
        units_month = units_day * days
        revenue = units_month * price
        cogs = units_month * v
        gp = revenue - cogs
        op = gp - fixed
        rows.append([m, round(units_day,2), int(units_month), revenue, cogs, gp, fixed, op])
        units_day *= (1 + growth)

    df = pd.DataFrame(rows, columns=["Month","Units/day","Units/month","Revenue","COGS","Gross Profit","Fixed Costs","Operating Profit"])
    df["Cumulative Profit"] = df["Operating Profit"].cumsum()
    return df

# ---------- Load model (if provided)
uploaded = st.sidebar.file_uploader("Sube tu Excel financiero (opcional)", type=["xlsx"])
if uploaded is not None:
    sheets, err = load_excel(uploaded)
else:
    if os.path.exists(DEFAULT_XLSX_PATH):
        sheets, err = load_excel(DEFAULT_XLSX_PATH)
    else:
        sheets, err = {}, None

assumptions = sheets.get("Assumptions") if sheets else None
unit_df = compute_unit_economics(assumptions) if assumptions is not None else None
forecast_df = compute_forecast(assumptions, unit_df) if unit_df is not None else None

# ---------- Sidebar Navigation
menu = st.sidebar.radio("Secciones", [
    "🏠 Portada",
    "📈 Resumen Ejecutivo",
    "🥣 Producto & Menú",
    "📍 Ubicaciones & Go-to-Market",
    "💸 Unit Economics",
    "📊 Proyección 12 meses",
    "🧩 Propuesta de Valor",
    "🧑‍💼 Equipo",
    "💰 Ronda & Uso de Fondos",
    "🖼️ Galería",
    "✉️ Contacto"
])

# ---------- Helper to show image
def show_image(rel_path, caption=""):
    abs_path = os.path.join("assets_investor", rel_path)
    if os.path.exists(abs_path):
        st.image(abs_path, caption=caption, use_container_width=True)
    else:
        st.info(f"(Coloca {rel_path} en assets_investor/)")

# ---------- Sections
if menu == "🏠 Portada":
    col1, col2 = st.columns([1,2])
    with col1:
        show_image("logo.png", "Benessere")
    with col2:
        st.title("Benessere – Açaí & Healthy Bowls")
        st.subheader("Comida saludable, rápida y deliciosa en campus universitarios de Santa Cruz, Bolivia.")
        st.write("""
**Visión**: Ser la marca líder de opciones saludables en universidades y hubs de alto flujo,
ofreciendo bowls de açaí y frutas frescas con excelente sabor y unit economics probados.
        """)
    show_image("hero.jpg")
    st.caption("Mockup ilustrativo. Reemplazar con fotos reales del local y branding final.")

elif menu == "📈 Resumen Ejecutivo":
    st.header("Resumen Ejecutivo")
    st.markdown("""
- **Problema**: En campus universitarios hay abundancia de comida rápida poco saludable.
- **Solución**: Bowls de **açaí** con toppings frescos, smoothies y snacks saludables.
- **Modelo**: Punto de venta en campus + kioskos satélite. Alta rotación, ticket saludable.
- **Tracción esperada**: Inicio con 1 local en universidad ancla y expansión por replicabilidad.
- **Ventaja**: Preparaciones rápidas, mermas controladas, costos variables claros.
    """)
    if unit_df is not None:
        try:
            gm = unit_df.loc[unit_df["Metric"].str.contains("Gross margin %", case=False), "Value"].iloc[0]
            be_day = unit_df.loc[unit_df["Metric"].str.contains("day", case=False), "Value"].iloc[0]
            col1, col2, col3 = st.columns(3)
            col1.metric("Margen Bruto %", f"{gm:.1%}" if gm<=1 else f"{gm:.1f}%")
            col2.metric("Break-even (unid/día)", f"{be_day:,.1f}")
            price = unit_df.loc[unit_df["Metric"].str.contains("Price", case=False), "Value"].iloc[0]
            col3.metric("Precio por bowl", f"{price:,.2f}")
        except Exception:
            st.info("Carga tu Excel para mostrar KPIs.")
    else:
        st.info("Carga tu Excel para mostrar KPIs del modelo.")

elif menu == "🥣 Producto & Menú":
    st.header("Producto & Menú")
    show_image("menu.jpg", "Açaí base + frutas + toppings.")
    st.markdown("""
**Linea principal**:
- **Açaí Bowl** (tamaños S/M/L), base de açaí con banana, toppings de frutas de temporada,
granola, yogurt, mantequilla de maní, coco, etc.
- **Smoothies** energéticos y detox.
- **Snacks**: barras saludables, parfaits, agua de coco.

**Experiencia**: pedido ágil, personalización de toppings y tiempos < 3 min por bowl.
    """)

elif menu == "📍 Ubicaciones & Go-to-Market":
    st.header("Ubicaciones & Go-to-Market")
    show_image("store.jpg", "Universidades objetivo en Santa Cruz.")
    st.markdown("""
**Fase 1**: 1 local en universidad de alto flujo (kiosko/stand modular).  
**Fase 2**: Replicar en 2–3 campus adicionales + convenios con gimnasios.  
**Marketing**: promos con influencers locales, convenios deportivos, referidos en campus.
    """)

elif menu == "💸 Unit Economics":
    st.header("Unit Economics")
    if unit_df is None:
        st.info("Sube `Financial_Model_Acai_Lite.xlsx` para calcular métricas.")
    else:
        st.dataframe(unit_df, use_container_width=True)
        try:
            gm_pct = unit_df.loc[unit_df["Metric"].str.contains("Gross margin %", case=False), "Value"].iloc[0]
            be_day = unit_df.loc[unit_df["Metric"].str.contains("day", case=False), "Value"].iloc[0]
            col1, col2 = st.columns(2)
            col1.metric("Gross margin %", f"{gm_pct:.1%}" if gm_pct<=1 else f"{gm_pct:.1f}%")
            col2.metric("Break-even (bowls/día)", f"{be_day:,.2f}")
        except Exception:
            pass
        st.markdown("""
**Supuestos clave** se leen de la hoja *Assumptions* (precio, costos variables, días trabajados, etc.).
        """)

elif menu == "📊 Proyección 12 meses":
    st.header("Proyección 12 meses")
    if forecast_df is None:
        st.info("Sube `Financial_Model_Acai_Lite.xlsx` para generar la proyección.")
    else:
        st.dataframe(forecast_df, use_container_width=True)
        # Operating Profit Chart
        fig = plt.figure()
        plt.plot(forecast_df["Month"], forecast_df["Operating Profit"])
        plt.title("Utilidad Operativa por Mes")
        plt.xlabel("Mes")
        plt.ylabel("Bs.")
        st.pyplot(fig)

        # Cumulative Profit Chart
        fig2 = plt.figure()
        plt.plot(forecast_df["Month"], forecast_df["Cumulative Profit"])
        plt.title("Utilidad Acumulada")
        plt.xlabel("Mes")
        plt.ylabel("Bs.")
        st.pyplot(fig2)

elif menu == "🧩 Propuesta de Valor":
    st.header("Propuesta de Valor")
    st.markdown("""
- **Saludable & delicioso**: Açaí auténtico con frutas frescas.
- **Rápido**: preparación < 3 minutos por bowl.
- **Accesible**: ticket promedio competitivo frente a snacks de campus.
- **Escalable**: módulos replicables, entrenamiento sencillo y control de mermas.
- **Datos**: decisiones informadas con indicadores diarios (ventas/unidades, margen, rotación).
    """)

elif menu == "🧑‍💼 Equipo":
    st.header("Equipo")
    st.markdown("""
**Founders**: Operaciones de food service + experiencia en tecnología y analítica.  
**Roles iniciales**: operaciones, compras y abastecimiento, marketing local, community manager, cajero/barista.
    """)

elif menu == "💰 Ronda & Uso de Fondos":
    st.header("Ronda & Uso de Fondos")
    st.markdown("""
**Objetivo de inversión**: Apertura y operación de los **primeros 3 puntos** (capex + opex 6 meses).  
**Uso de fondos estimado** (ejemplo):
- Equipamiento y mobiliario
- Capital de trabajo (inventario inicial açaí, frutas y empaques)
- Alquiler y adecuación
- Marketing de lanzamiento
- Sistema POS y analítica
    """)
    st.info("Puedes enlazar esta sección a la hoja 'UseOfFunds' de tu Excel para mostrar cifras exactas.")

elif menu == "🖼️ Galería":
    st.header("Galería")
    show_image("hero.jpg", "Marca & identidad")
    show_image("store.jpg", "Local en campus (mockup)")
    show_image("menu.jpg", "Propuesta de menú (mockup)")
    st.caption("Reemplaza los mockups por fotos reales al avanzar el proyecto.")

elif menu == "✉️ Contacto":
    st.header("Contacto")
    st.markdown("""
**SolverTic SRL – Benessere**
- Email: obedabcedfg@gmail.com
- Ciudad: Santa Cruz de la Sierra, Bolivia
    """)
    st.success("¿Te gustaría que añadamos un formulario con Google Sheets o EmailJS para capturar leads?")

# Footer
st.divider()
st.caption("Demo para inversionistas – Streamlit • Benessere")
