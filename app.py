import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Configuración premium de la plataforma visual
st.set_page_config(page_title="Cava Algorithmic Core", layout="wide", initial_sidebar_state="expanded")

# CSS Minimalista Premium
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght=300;400;600&display=swap');
        html, body, [data-testid="stAppViewContainer"] { font-family: 'Inter', sans-serif; background-color: #0d0e12; color: #ffffff; }
        .metric-card { background: #141722; border: 1px solid #1f232d; padding: 20px; border-radius: 12px; text-align: left; }
        .metric-title { color: #7f8c8d; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
        .metric-value { font-size: 24px; font-weight: 600; color: #ffffff; }
        .alert-trigger { background: #1c2826; border-left: 4px solid #2ecc71; padding: 15px; border-radius: 4px; margin-bottom: 12px; }
        .alert-radar { background: #1f1f2e; border-left: 4px solid #f1c40f; padding: 15px; border-radius: 4px; margin-bottom: 12px; }
    </style>
""", unsafe_allow_html=True)

# ─── 📦 DESCARGA DEL UNIVERSO OFICIAL DE ACCIONES ───
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

# Pestañas nativas de la aplicación
tab_indice, tab_screener = st.tabs(["📊 Monitor Índice S&P 500", "🚦 Screener Autónomo Cava System"])

# =====================================================================
# PESTAÑA 1: MONITOR DE ÍNDICE (Mapeo de Estructura de Opciones)
# =====================================================================
with tab_indice:
    st.sidebar.markdown("## ⚙️ Parámetros del Índice")
    zero_gamma = st.sidebar.number_input("Nivel Zero Gamma", value=5120.0, step=5.0)
    put_wall = st.sidebar.number_input("Put Wall (Suelo Crítico)", value=5080.0, step=5.0)
    call_wall = st.sidebar.number_input("Call Wall (Techo)", value=5220.0, step=5.0)
    soporte_elliott = st.sidebar.number_input("Soporte Geométrico Elliott", value=5100.0, step=5.0)

    st.subheader("Análisis Microestructural del S&P 500")
    
    spx = yf.Ticker("^SPX")
    df_hist = spx.history(period="30d", interval="1d")
    
    if not df_hist.empty:
        df_hoy = spx.history(period="1d", interval="1m")
        if df_hoy.empty:
            spot = float(df_hist['Close'].iloc[-1])
            volumen = int(df_hist['Volume'].iloc[-1])
            vol_media_20 = int(df_hist['Volume'].iloc[-22:-2].mean())
            estado_mercado = "⚠️ MERCADO CERRADO (Último Cierre Oficial)"
        else:
            spot = float(df_hoy['Close'].iloc[-1])
            volumen = int(df_hoy['Volume'].sum())
            vol_media_20 = int(df_hist['Volume'].iloc[-21:-1].mean())
            estado_mercado = "⚡ MERCADO EN VIVO"
        
        if spot > zero_gamma:
            color, status, msg = "#2ecc71", f"🟢 POSICIÓN COMPLETA ({estado_mercado})", "Régimen de Gamma Positiva real. Dealers amortiguan volatilidad[cite: 2]."
        elif spot > put_wall:
            color, status, msg = "#f1c40f", f"🟡 POSICIÓN MODERADA ({estado_mercado})", "Gamma Negativa activa. Reducir Sizing por volatilidad[cite: 2]."
        else:
            color, status, msg = "#e74c3c", f"🔴 RIESGO EXTREMO ({estado_mercado})", "Precio por debajo del Put Wall. Evitar compras[cite: 2]."

        st.markdown(f"""
            <div style="background: #141722; border-left: 4px solid {color}; padding: 20px; border-radius: 8px; margin-bottom: 25px;">
                <div style="font-size: 16px; font-weight: bold; color: {color}; text-transform: uppercase;">{status}</div>
                <p style="color: #a9b0bd; font-size: 14px; margin: 8px 0 0 0;">{msg}</p>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        col1.markdown(f'<div class="metric-card"><div class="metric-title">S&P 500</div><div class="metric-value">{spot:.2f}</div></div>', unsafe_allow_html=True)
        col2.markdown(f'<div class="metric-card"><div class="metric-title">Put Wall</div><div class="metric-value" style="color:#e74c3c;">{put_wall:.2f}</div></div>', unsafe_allow_html=True)
        col3.markdown(f'<div class="metric-card"><div class="metric-title">Call Wall</div><div class="metric-value" style="color:#2ecc71;">{call_wall:.2f}</div></div>', unsafe_allow_html=True)
    else:
        st.error("No se han podido descargar datos del índice desde Yahoo Finance.")

# =====================================================================
# PESTAÑA 2: SCREENER AUTÓNOMO (Unificación Completa Cava System)
# =====================================================================
with tab_screener:
    st.subheader("🔍 Filtro Tecnológico Avanzado")
    st.markdown("El robot analiza la tendencia de largo plazo, calcula la geometría de Fibonacci e identifica la huella institucional[cite: 2].")

    watchlist = st.multiselect(
        "Añadir o modificar acciones en la mesa de control:",
        options=universo_tickers,
        default=["AAPL", "NVDA", "GOOGL", "META", "MSFT", "AMZN", "DDOG", "DELL"]
    )

    # Definición explícita de columnas para evitar fallos de inicialización (KeyError)
    columnas_tabla = ["Activo", "Precio ($)", "EMA 55 ($)", "Soporte Fibonacci ($)", "Distancia Suelo", "RSI (14)", "Drummond", "Vol. Inst.", "Dictamen Técnico"]

    if st.button("🚀 Iniciar Escaneo Cuantitativo Autónomo"):
        if not watchlist:
            st.warning("Selecciona al menos una acción para comenzar el rastreo.")
        else:
            resultados = []
            
            for ticker in watchlist:
                try:
                    asset = yf.Ticker(ticker)
                    df = asset.history(period="6mo", interval="1d")
                    
                    if df.empty or len(df) < 55:
                        continue
                    
                    # ─── 📊 INDICADORES MATEMÁTICOS DEL MANUAL DE CAVA ───
                    df['EMA55'] = df['Close'].ewm(span=55, adjust=False).mean()
                    
                    fast_ema = df['Close'].ewm(span=12, adjust=False).mean()
                    slow_ema = df['Close'].ewm(span=26, adjust=False).mean()
                    df['MACD_Line'] = fast_ema - slow_ema
                    df['MACD_Signal'] = df['MACD_Line'].ewm(span=9, adjust=False).mean()
                    
                    delta = df['Close'].diff()
                    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
                    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
                    loss = loss.replace(0, 0.00001)
                    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
                    
                    df['Stoch_K'] = 100 * ((df['Close'] - df['Low'].rolling(14).min()) / (df['High'].rolling(14).max() - df['Low'].rolling(14).min()))
                    df['Stoch_D'] = df['Stoch_K'].rolling(3).mean()
                    
                    # ─── 📐 GEOMETRÍA AUTOMÁTICA DE FIBONACCI ───
                    df_trimestre = df.iloc[-60:]
                    swing_low = float(df_trimestre['Low'].min())
                    swing_high = float(df_trimestre['High'].max())
                    rango = swing_high - swing_low
                    
                    fib_382 = swing_high - (0.382 * rango)
                    fib_500 = swing_high - (0.500 * rango)
                    fib_618 = swing_high - (0.618 * rango)
                    
                    precio_actual = float(df['Close'].iloc[-1])
                    soportes_posibles = [fib_382, fib_500, fib_618, swing_low]
                    soportes_validos = [s for s in soportes_posibles if s < precio_actual]
                    soporte_cava = max(soportes_validos) if soportes_validos else fib_618
                    
                    # ─── 🔎 SUELO DE DRUMMOND (Mínimo Aislado) ───
                    mínimo_aislado_detectado = False
                    for i in range(-5, -1):
                        if df['Low'].iloc[i] < df['Low'].iloc[i-1] and df['Low'].iloc[i] < df['Low'].iloc[i+1]:
                            mínimo_aislado_detectado = True
                            break
                    
                    # ─── ⚡ REGLAS CRÍTICAS DEL FILTRO DE ENTRADA ───
                    hoy = df.iloc[-1]
                    ayer = df.iloc[-2]
                    
                    en_tendencia_madre = bool(hoy['Close'] > hoy['EMA55'])
                    volumen_institucional = bool(hoy['Volume'] > (1.5 * df['Volume'].iloc[-21:-1].mean()))
                    
                    cruce_alcista_macd = bool((ayer['MACD_Line'] <= ayer['MACD_Signal']) and (hoy['MACD_Line'] > hoy['MACD_Signal']))
                    cruce_alcista_stoch = bool((ayer['Stoch_K'] <= ayer['Stoch_D']) and (hoy['Stoch_K'] > hoy['Stoch_D']))
                    rsi_zona_caza = bool(hoy['RSI'] <= 45)
                    
                    desviacion_soporte = float((precio_actual - soporte_cava) / soporte_cava)
                    cerca_del_soporte = bool(0.0 <= desviacion_soporte <= 0.025)
                    
                    if en_tendencia_madre and cerca_del_soporte and volumen_institucional and (cruce_alcista_macd or cruce_alcista_stoch or mínimo_aislado_detectado):
                        estado = "🚀 COMPRA (Gatillo Activo)"
                    elif en_tendencia_madre and (rsi_zona_caza or cerca_del_soporte):
                        estado = "👀 RADAR (Esperando Volumen)"
                    elif not en_tendencia_madre:
                        estado = "📉 EVITAR (Estructura Bajista)"
                    else:
                        estado = "⚪ NEUTRO (Esperar Retroceso)"
                    
                    resultados.append([
                        ticker, round(precio_actual, 2), round(hoy['EMA55'], 2), round(soporte_cava, 2),
                        f"{desviacion_soporte*100:.1f}%", round(hoy['RSI'], 1),
                        "🟢 SÍ" if mínimo_aislado_detectado else "条 No",
                        "🔥 ALTO" if volumen_institucional else "Normal", estado
                    ])
                except:
                    continue  # Si un activo falla de forma aislada, salta al siguiente sin romper la app
            
            df_final = pd.DataFrame(resultados, columns=columnas_tabla)
            
            if not df_final.empty:
                # Imprimir alertas críticas de compra arriba del todo
                alertas = df_final[df_final['Dictamen Técnico'].str.contains('🚀')]
                if not alertas.empty:
                    for _, row in alertas.iterrows():
                        st.markdown(f"""
                            <div class="alert-trigger">
                                🔥 <b>¡TRIGGER DE COMPRA EN {row['Activo']}!</b><br>
                                El precio está apoyado en su soporte Fibonacci de <b>{row['Soporte Fibonacci ($)']}</b> (a solo {row['Distancia Suelo']} de distancia)[cite: 2]. <br>
                                Confirmación de Manos Fuertes: <b>Volumen Institucional Activo</b> y filtro de Drummond validado[cite: 2].
                            </div>
                        """, unsafe_allow_html=True)
                
                # Imprimir radares intermedios
                radares = df_final[df_final['Dictamen Técnico'].str.contains('👀')]
                if not radares.empty:
                    for _, row in radares.iterrows():
                        st.markdown(f"""
                            <div class="alert-radar">
                                👀 <b>{row['Activo']} EN RADAR ESTRUCTURAL:</b> Precio en zona de descuento favorable ($ {row['Precio ($)']})[cite: 2]. Esperando fogonazo de volumen comprador[cite: 2].
                            </div>
                        """, unsafe_allow_html=True)
                
                st.markdown("### 📋 Cuadrícula de Control de la Watchlist")
                st.dataframe(df_final.sort_values(by="Dictamen Técnico", ascending=False), use_container_width=True)
            else:
                st.info("Ningún activo ha podido ser analizado en este momento. Inténtalo de nuevo en unos minutos.")
