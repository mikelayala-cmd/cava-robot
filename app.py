import streamlit as st
import yfinance as yf
import psycopg2
from datetime import datetime

# Configuración de la página web (Modo Oscuro Nactivo y diseño limpio)
st.set_page_config(page_title="Cava Algorithmic Core", layout="wide", initial_sidebar_state="expanded")

# Inyección de estilo CSS minimalista para tarjetas elegantes
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
        html, body, [data-testid="stAppViewContainer"] { font-family: 'Inter', sans-serif; background-color: #0d0e12; color: #ffffff; }
        .metric-card { background: #141722; border: 1px solid #1f232d; padding: 20px; border-radius: 12px; text-align: left; }
        .metric-title { color: #7f8c8d; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
        .metric-value { font-size: 24px; font-weight: 600; color: #ffffff; }
</style>
""", unsafe_allow_html=True) # <-- Cambia "lines" por "html" aquí

DB_URI = st.secrets["DB_URI"]

# 🎛️ PANEL LATERAL: Configuración Matinal Manual
st.sidebar.markdown("## ⚙️ Niveles del Día")
st.sidebar.markdown("Introduce los niveles del manual de Cava antes de la apertura:")

zero_gamma = st.sidebar.number_input("Nivel Zero Gamma", value=5120.0, step=5.0)
put_wall = st.sidebar.number_input("Put Wall (Suelo Critico)", value=5080.0, step=5.0)
call_wall = st.sidebar.number_input("Call Wall (Techo)", value=5220.0, step=5.0)
soporte_elliott = st.sidebar.number_input("Soporte Técnico Elliott", value=5100.0, step=5.0)
minimo_barrida = st.sidebar.number_input("Mínimo de la Barrida (Stop)", value=5090.0, step=5.0)

# CUBIERTA PRINCIPAL: Captura de Datos Reales
st.title("Cava Real-Time Core")
st.markdown("---")

@st.cache_data(ttl=60) # Refresca los datos reales cada 60 segundos automáticamente
def obtener_mercado():
    try:
        spx = yf.Ticker("^SPX")
        df_hoy = spx.history(period="1d", interval="1m")
        df_hist = spx.history(period="22d", interval="1d")
        if df_hoy.empty or df_hist.empty: return None
        return float(df_hoy['Close'].iloc[-1]), int(df_hoy['Volume'].sum()), int(df_hist['Volume'].iloc[-21:-1].mean())
    except:
        return None

datos = obtener_mercado()

if datos:
    spot, volumen, vol_media_20 = datos
    
    # Lógica de Regímenes GEX y Semáforo
    gex_ratio = 0.65 if spot > zero_gamma else 0.32
    filtro_volumen = volumen > (1.5 * vol_media_20)
    desviacion_pct = (spot - soporte_elliott) / soporte_elliott
    filtro_holgura = desviacion_pct <= 0.02
    
    if spot > zero_gamma and gex_ratio > 0.5:
        color, status, msg = "#2ecc71", "🟢 POSICIÓN COMPLETA (100% Capital)", "Régimen de Gamma Positiva real. Creadores de mercado amortiguan la volatilidad."
    elif spot > put_wall:
        color, status, msg = "#f1c40f", "🟡 POSICIÓN MODERADA (50% - 75%)", "Gamma Negativa activa. Volatilidad real en curso. Reducir Sizing."
    else:
        color, status, msg = "#e74c3c", "🔴 RIESGO EXTREMO", "Precio por debajo del Put Wall. Alerta de capitulación o rebote táctico violento."
        
    if filtro_volumen and filtro_holgura and spot > soporte_elliott:
        msg += f" | 🚀 ¡TRIGGER DE COMPRA ACTIVADO! Stop-Loss rígido en: {minimo_barrida - 0.5:.2f}"

    # RENDERIZADO VISUAL
    st.markdown(f"""
        <div style="background: #141722; border-left: 4px solid {color}; padding: 20px; border-radius: 8px; margin-bottom: 25px;">
            <div style="font-size: 16px; font-weight: bold; color: {color}; text-transform: uppercase;">{status}</div>
            <p style="color: #a9b0bd; font-size: 14px; margin: 8px 0 0 0;">{msg}</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">S&P 500 Real</div><div class="metric-value">{spot:.2f}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Put Wall (Suelo)</div><div class="metric-value" style="color:#e74c3c;">{put_wall:.2f}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Call Wall (Techo)</div><div class="metric-value" style="color:#2ecc71;">{call_wall:.2f}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    col4, col5, col6 = st.columns(3)
    with col4:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Volumen Hoy</div><div class="metric-value">{volumen:,}</div></div>', unsafe_allow_html=True)
    with col5:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Media Volumen 20d</div><div class="metric-value">{vol_media_20:,}</div></div>', unsafe_allow_html=True)
    with col6:
        st.markdown(f'<div class="metric-card"><div class="metric-title">GEX Ratio Estimado</div><div class="metric-value">{gex_ratio:.2f}</div></div>', unsafe_allow_html=True)

    st.markdown(f"<div style='color:#525c6c; font-size:11px; text-align:right; margin-top:30px;'>Sincronizado con Wall Street. Actualizado: {datetime.now().strftime('%H:%M:%S')}</div>", unsafe_allow_html=True)

else:
    st.info("Conexión en espera. Si el mercado está cerrado (fin de semana), se mostrará el panel en cuanto comience la sesión de pre-apertura.")
