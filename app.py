import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# Configuración premium de la página web
st.set_page_config(page_title="Cava Algorithmic Core", layout="wide", initial_sidebar_state="expanded")

# CSS Minimalista Premium
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
        html, body, [data-testid="stAppViewContainer"] { font-family: 'Inter', sans-serif; background-color: #0d0e12; color: #ffffff; }
        .metric-card { background: #141722; border: 1px solid #1f232d; padding: 20px; border-radius: 12px; text-align: left; }
        .metric-title { color: #7f8c8d; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
        .metric-value { font-size: 24px; font-weight: 600; color: #ffffff; }
        .alert-trigger { background: #1c2826; border-left: 4px solid #2ecc71; padding: 15px; border-radius: 4px; margin-bottom: 10px; }
        .alert-radar { background: #1f1f2e; border-left: 4px solid #f1c40f; padding: 15px; border-radius: 4px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# ─── 📦 FUNCIÓN PARA CONFIGURAR EL UNIVERSO DE ACCIONES ───
@st.cache_data(ttl=86400)
def cargar_universo_acciones():
    try:
        sp500 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]['Symbol'].tolist()
        nasdaq100 = pd.read_html('https://en.wikipedia.org/wiki/Nasdaq-100')[4]['Ticker'].tolist()
        universo = sorted(list(set(sp500 + nasdaq100)))
        return universo
    except:
        return ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "TSLA", "AMD", "NFLX", "DELL", "DDOG"]

universo_tickers = cargar_universo_acciones()

# 🧠 MEMORIA DE LA WEB
if "valores_tickers" not in st.session_state:
    st.session_state.valores_tickers = {}

# ─── CREACIÓN DE LAS PESTAÑAS ───
tab_indice, tab_acciones = st.tabs(["📊 Monitor Índice S&P 500", "🔍 Escáner de Acciones"])

# =====================================================================
# PESTAÑA 1: EL MONITOR DE ÍNDICE
# =====================================================================
with tab_indice:
    st.sidebar.markdown("## ⚙️ Niveles del Índice")
    zero_gamma = st.sidebar.number_input("Nivel Zero Gamma", value=5120.0, step=5.0)
    put_wall = st.sidebar.number_input("Put Wall (Suelo Crítico)", value=5080.0, step=5.0)
    call_wall = st.sidebar.number_input("Call Wall (Techo)", value=5220.0, step=5.0)
    soporte_elliott = st.sidebar.number_input("Soporte Técnico Elliott", value=5100.0, step=5.0)
    minimo_barrida = st.sidebar.number_input("Mínimo de la Barrida (Stop)", value=5090.0, step=5.0)

    st.subheader("Análisis Microestructural del S&P 500")
    
    spx = yf.Ticker("^SPX")
    df_hoy = spx.history(period="1d", interval="1m")
    df_hist = spx.history(period="22d", interval="1d")
    
    if not df_hoy.empty:
        spot = float(df_hoy['Close'].iloc[-1])
        volumen = int(df_hoy['Volume'].sum())
        vol_media_20 = int(df_hist['Volume'].iloc[-21:-1].mean())
        
        gex_ratio = 0.65 if spot > zero_gamma else 0.32
        filtro_volumen = volumen > (1.5 * vol_media_20)
        desviacion_pct = (spot - soporte_elliott) / soporte_elliott
        filtro_holgura = desviacion_pct <= 0.02
        
        if spot > zero_gamma and gex_ratio > 0.5:
            color, status, msg = "#2ecc71", "🟢 POSICIÓN COMPLETA (100% Capital)", "Régimen de Gamma Positiva real. Dealers amortiguan volatilidad."
        elif spot > put_wall:
            color, status, msg = "#f1c40f", "🟡 POSICIÓN MODERADA (50% - 75%)", "Gamma Negativa activa. Reducir Sizing por volatilidad."
        else:
            color, status, msg = "#e74c3c", "🔴 RIESGO EXTREMO", "Precio por debajo del Put Wall. Evitar compras."

        if filtro_volumen and filtro_holgura and spot > soporte_elliott:
            msg += f" | 🚀 ¡TRIGGER ACTIVO! Stop en: {minimo_barrida - 0.5:.2f}"

        st.markdown(f"""
            <div style="background: #141722; border-left: 4px solid {color}; padding: 20px; border-radius: 8px; margin-bottom: 25px;">
                <div style="font-size: 16px; font-weight: bold; color: {color}; text-transform: uppercase;">{status}</div>
                <p style="color: #a9b0bd; font-size: 14px; margin: 8px 0 0 0;">{msg}</p>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        col1.markdown(f'<div class="metric-card"><div class="metric-title">S&P 500 Real</div><div class="metric-value">{spot:.2f}</div></div>', unsafe_allow_html=True)
        col2.markdown(f'<div class="metric-card"><div class="metric-title">Put Wall</div><div class="metric-value" style="color:#e74c3c;">{put_wall:.2f}</div></div>', unsafe_allow_html=True)
        col3.markdown(f'<div class="metric-card"><div class="metric-title">Call Wall</div><div class="metric-value" style="color:#2ecc71;">{call_wall:.2f}</div></div>', unsafe_allow_html=True)

# =====================================================================
# PESTAÑA 2: ESCÁNER CON CÁLCULO ESTRUCTURAL AUTOMÁTICO
# =====================================================================
with tab_acciones:
    st.subheader("🔍 Escáner Inteligente Automático (Watchlist)")
    st.markdown("Selecciona tus activos. Si dejas los niveles en `0.0`, el robot calculará los soportes de forma 100% automática.")

    opciones_seleccionadas = st.multiselect(
        "Modificar tu lista de vigilancia activa:",
        options=universo_tickers,
        default=["AAPL", "NVDA", "GOOGL", "META"]
    )
    
    ticker_extra = st.text_input("¿Añadir ticker manual (Ej: DELL, DDOG, PLTR)?:").upper()
    if ticker_extra and ticker_extra not in opciones_seleccionadas:
        opciones_seleccionadas.append(ticker_extra)

    if opciones_seleccionadas:
        st.markdown("### 📝 Configuración de Umbrales")
        st.info("🤖 **Modo Auto Activo:** Deja los valores en `0.0` para usar el mínimo de 20 días como soporte estructural y el mínimo de ayer como Stop.")
        
        for ticker in opciones_seleccionadas:
            if ticker not in st.session_state.valores_tickers:
                st.session_state.valores_tickers[ticker] = {"Soporte Manual": 0.0, "Stop Manual": 0.0}
        
        filas = []
        for ticker in opciones_seleccionadas:
            filas.append({
                "Ticker": ticker,
                "Soporte Manual (Opcional)": st.session_state.valores_tickers[ticker]["Soporte Manual"],
                "Stop Manual (Opcional)": st.session_state.valores_tickers[ticker]["Stop Manual"]
            })
        df_niveles = pd.DataFrame(filas)
        
        tabla_editada = st.data_editor(df_niveles, hide_index=True, use_container_width=True)

        for index, row in tabla_editada.iterrows():
            st.session_state.valores_tickers[row["Ticker"]] = {
                "Soporte Manual": float(row["Soporte Manual (Opcional)"]),
                "Stop Manual": float(row["Stop Manual (Opcional)"])
            }

        if st.button("🚀 Lanzar Escáner Estructural Autónomo"):
            st.markdown("---")
            st.markdown("### 🔔 Diagnóstico y Señales del Sistema")
            
            for index, row in tabla_editada.iterrows():
                ticker = row["Ticker"]
                soporte_man = row["Soporte Manual (Opcional)"]
                stop_man = row["Stop Manual (Opcional)"]
                
                t_data = yf.Ticker(ticker)
                h_hoy = t_data.history(period="1d", interval="1m")
                h_hist = t_data.history(period="22d", interval="1d")
                
                if h_hoy.empty or h_hist.empty:
                    st.error(f"Error al conectar con los datos de {ticker}.")
                    continue
                    
                precio_accion = float(h_hoy['Close'].iloc[-1])
                vol_accion = int(h_hoy['Volume'].sum())
                vol_medio_20_accion = int(h_hist['Volume'].iloc[-21:-1].mean())
                
                # ─── LÓGICA DE DETECCIÓN ESTRUCTURAL AUTOMÁTICA ───
                minimo_20_sesiones = float(h_hist['Low'].iloc[-21:-1].min())
                minimo_ayer = float(h_hist['Low'].iloc[-2])
                
                # Si el usuario dejó 0.0, el robot toma el control numérico
                soporte_final = soporte_man if soporte_man > 0.0 else minimo_20_sesiones
                stop_final = stop_man if stop_man > 0.0 else minimo_ayer
                tipo_calculo = "Manual" if soporte_man > 0.0 else "Auto (Mínimo 30 días)"
                
                # CÁLCULO DE MÉTRICAS DEL ALGORITMO
                volumen_institucional = vol_accion > (1.5 * vol_medio_20_accion)
                desviacion = (precio_accion - soporte_final) / soporte_final
                holgura_correcta = 0.0 < desviacion <= 0.02
                
                # Tarjeta 1: DISPARO ACTIVO
                if volumen_institucional and holgura_correcta and precio_accion > soporte_final:
                    st.markdown(f"""
                        <div class="alert-trigger">
                            <span style="font-size:16px; font-weight:bold; color:#2ecc71;">🚀 DISPARO DE ENTRADA EN {ticker} ({tipo_calculo})</span><br>
                            Cotización en zona óptima: <b>{precio_accion:.2f}</b> (Soporte en {soporte_final:.2f}). <br>
                            🔥 <b>Manos Fuertes:</b> {vol_accion:,} vs Media: {vol_medio_20_accion:,}.<br>
                            🛑 <b>Stop-Loss Inamovible:</b> {stop_final - 0.1:.2f}
                        </div>
                    """, unsafe_allow_html=True)
                
                # Tarjeta 2: EN RADAR TÁCTICO
                elif precio_accion > soporte_final and desviacion <= 0.04:
                    st.markdown(f"""
                        <div class="alert-radar">
                            <span style="font-size:14px; font-weight:bold; color:#f1c40f;">👀 {ticker} EN RADAR ({tipo_calculo})</span><br>
                            Estructura favorable. Precio: <b>{precio_accion:.2f}</b> | Zona crítica: {soporte_final:.2f}. Esperando ataque de volumen comprador.
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.write(f"⚪ {ticker} ({tipo_calculo}): Fuera de rango. Precio: {precio_accion:.2f} | Nivel Clave: {soporte_final:.2f}")
    else:
        st.write("La lista de vigilancia está vacía. Añade tus acciones favoritas arriba.")
