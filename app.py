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
@st.cache_data(ttl=86400) # Se descarga solo una vez al día para ir a máxima velocidad
def cargar_universo_acciones():
    try:
        sp500 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]['Symbol'].tolist()
        nasdaq100 = pd.read_html('https://en.wikipedia.org/wiki/Nasdaq-100')[4]['Ticker'].tolist()
        universo = sorted(list(set(sp500 + nasdaq100)))
        return universo
    except:
        return ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "TSLA", "AMD", "NFLX", "DELL", "DDOG"]

universo_tickers = cargar_universo_acciones()

# 🧠 MEMORIA DE LA WEB: Inicializar almacenamiento de estado de niveles para evitar pérdidas al refrescar
if "valores_tickers" not in st.session_state:
    st.session_state.valores_tickers = {}

# ─── CREACIÓN DE LAS PESTAÑAS DE LA MISMA APP ───
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
# PESTAÑA 2: EL ESCÁNER DE ACCIONES MULTI-ACTIVO (CORREGIDA)
# =====================================================================
with tab_acciones:
    st.subheader("🔍 Escáner Táctico de Acciones (Manual de Cava)")
    st.markdown("Selecciona las compañías que quieres monitorizar e introduce sus soportes geométricos.")

    opciones_seleccionadas = st.multiselect(
        "Añadir acciones a la mesa de operaciones:",
        options=universo_tickers,
        default=["AAPL", "NVDA", "GOOGL", "META"]
    )
    
    ticker_extra = st.text_input("¿Quieres añadir algún ticker extra manualmente? (Ej: PLTR, DELL, DDOG):").upper()
    if ticker_extra and ticker_extra not in opciones_seleccionadas:
        opciones_seleccionadas.append(ticker_extra)

    if opciones_seleccionadas:
        st.markdown("### 📝 Matriz de Niveles Técnicos Diarios")
        st.info("💡 Haz doble clic sobre cualquier celda con 0.0 para cambiar el valor. Al terminar de escribir el número, presiona Enter para fijarlo en la memoria.")
        
        # Sincronizar las opciones con la memoria para retener los datos introducidos previamente
        for ticker in opciones_seleccionadas:
            if ticker not in st.session_state.valores_tickers:
                st.session_state.valores_tickers[ticker] = {"Soporte Elliott": 0.0, "Minimo Barrida (Stop)": 0.0}
        
        # Construir la cuadrícula leyendo directamente de la memoria de la sesión
        filas = []
        for ticker in opciones_seleccionadas:
            filas.append({
                "Ticker": ticker,
                "Soporte Elliott": st.session_state.valores_tickers[ticker]["Soporte Elliott"],
                "Minimo Barrida (Stop)": st.session_state.valores_tickers[ticker]["Minimo Barrida (Stop)"]
            })
        df_niveles = pd.DataFrame(filas)
        
        # Mostrar el editor de datos interactivo
        tabla_editada = st.data_editor(df_niveles, hide_index=True, use_container_width=True)

        # 🔒 CLAVE DEL ARREGLO: Guardar de inmediato cualquier edición en la memoria del servidor
        for index, row in tabla_editada.iterrows():
            st.session_state.valores_tickers[row["Ticker"]] = {
                "Soporte Elliott": float(row["Soporte Elliott"]),
                "Minimo Barrida (Stop)": float(row["Minimo Barrida (Stop)"])
            }

        # Botón de ejecución del escáner
        if st.button("🚀 Lanzar Escáner de Mercado en Vivo"):
            st.markdown("---")
            st.markdown("### 🔔 Panel de Alertas y Señales Activas")
            
            for index, row in tabla_editada.iterrows():
                ticker = row["Ticker"]
                soporte = row["Soporte Elliott"]
                stop_ref = row["Minimo Barrida (Stop)"]
                
                if soporte == 0.0:
                    st.warning(f"⚠️ Saltando {ticker}: Debes definir un nivel de Soporte técnico mayor que 0.")
                    continue
                
                t_data = yf.Ticker(ticker)
                h_hoy = t_data.history(period="1d", interval="1m")
                h_hist = t_data.history(period="22d", interval="1d")
                
                if h_hoy.empty or h_hist.empty:
                    st.error(f"Error al conectar con los datos de {ticker}.")
                    continue
                    
                precio_accion = float(h_hoy['Close'].iloc[-1])
                vol_accion = int(h_hoy['Volume'].sum())
                vol_medio_20_accion = int(h_hist['Volume'].iloc[-21:-1].mean())
                
                volumen_institucional = vol_accion > (1.5 * vol_medio_20_accion)
                desviacion = (precio_accion - soporte) / soporte
                holgura_correcta = 0.0 < desviacion <= 0.02
                
                if volumen_institucional and holgura_correcta and precio_accion > soporte:
                    st.markdown(f"""
                        <div class="alert-trigger">
                            <span style="font-size:16px; font-weight:bold; color:#2ecc71;">🚀 DISPARO EN {ticker}</span><br>
                            El precio actual (<b>{precio_accion:.2f}</b>) está en zona óptima de entrada sobre el soporte ({soporte:.2f}). <br>
                            🔥 <b>Volumen Institucional Confirmado:</b> {vol_accion:,} vs Media: {vol_medio_20_accion:,}.<br>
                            🛑 <b>Nivel Stop-Loss Obligatorio:</b> {stop_ref - 0.2:.2f}
                        </div>
                    """, unsafe_allow_html=True)
                
                elif precio_accion > soporte and desviacion <= 0.03:
                    st.markdown(f"""
                        <div class="alert-radar">
                            <span style="font-size:14px; font-weight:bold; color:#f1c40f;">👀 {ticker} EN RADAR TÁCTICO</span><br>
                            Precio en zona geométrica favorable (<b>{precio_accion:.2f}</b>). Esperando incremento de volumen institucional para validar la entrada.
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.write(f"⚪ {ticker}: Fuera de rango operativo. Precio: {precio_accion:.2f} | Soporte: {soporte:.2f}")
    else:
        st.write("La lista de vigilancia está vacía. Añade tus acciones favoritas arriba.")
