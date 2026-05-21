# -*- coding: utf-8 -*-
"""
Dashboard IoT — Sistema de Seguridad
Sayu & Kat · ESP32 + InfluxDB + Streamlit
Estética: terminal industrial / sala de control
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import seaborn as sns
import numpy as np
from influxdb_client import InfluxDBClient

# ─── Configuración de página ──────────────────────────────────
st.set_page_config(
    page_title='CTRL·SEC — Sistema Seguridad IoT',
    page_icon='🔐',
    layout='wide',
    initial_sidebar_state='expanded'
)

# ─── CSS: Estética terminal industrial ────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Courier+Prime:wght@400;700&display=swap');

    /* ── Variables ── */
    :root {
        --amber:   #FFB000;
        --amber-d: #CC8800;
        --amber-f: #FF6B00;
        --green:   #39FF14;
        --green-d: #1a7a00;
        --red:     #FF3131;
        --red-d:   #7a0000;
        --bg:      #050603;
        --bg2:     #0a0c06;
        --bg3:     #0f1209;
        --border:  #1e2410;
        --text:    #c8b560;
        --text-d:  #4a4220;
    }

    /* ── Scanline overlay ── */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: repeating-linear-gradient(
            0deg,
            transparent,
            transparent 2px,
            rgba(0,0,0,0.08) 2px,
            rgba(0,0,0,0.08) 4px
        );
        pointer-events: none;
        z-index: 9999;
    }

    /* ── Base ── */
    .stApp {
        background: var(--bg);
        color: var(--text);
        font-family: 'Share Tech Mono', monospace;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: var(--bg2) !important;
        border-right: 1px solid var(--border);
    }

    /* ── Sliders: amber track ── */
    [data-testid="stSlider"] [data-baseweb="slider"] > div:first-child {
        background: var(--border) !important;
    }
    [data-testid="stSlider"] [data-baseweb="slider"] > div > div {
        background: var(--amber) !important;
    }

    /* ── Selectbox & Multiselect ── */
    [data-testid="stMultiSelect"] [data-baseweb="tag"] {
        background: #1a1500 !important;
        border: 1px solid var(--amber-d) !important;
        border-radius: 2px !important;
        color: var(--amber) !important;
        font-size: 0.75rem !important;
        font-family: 'Share Tech Mono', monospace !important;
    }
    [data-testid="stMultiSelect"] [data-baseweb="select"] > div {
        background: var(--bg3) !important;
        border-color: var(--border) !important;
    }

    /* ── Metric cards ── */
    [data-testid="stMetric"] {
        background: var(--bg2);
        border: 1px solid var(--border);
        border-top: 2px solid var(--amber-d);
        border-radius: 0px;
        padding: 16px 18px !important;
        font-family: 'Share Tech Mono', monospace;
        clip-path: polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 0 100%);
    }
    [data-testid="stMetricValue"] {
        font-family: 'Share Tech Mono', monospace !important;
        color: var(--amber) !important;
        font-size: 1.6rem !important;
        text-shadow: 0 0 12px rgba(255,176,0,0.4);
    }
    [data-testid="stMetricLabel"] {
        font-family: 'Share Tech Mono', monospace !important;
        color: var(--text-d) !important;
        font-size: 0.7rem !important;
        letter-spacing: 0.15em;
        text-transform: uppercase;
    }
    [data-testid="stMetricDelta"] {
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 0.72rem !important;
    }

    /* ── DataFrame ── */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--border);
        border-radius: 0;
    }

    /* ── Alerts ── */
    .stAlert { border-radius: 0 !important; font-family: 'Share Tech Mono', monospace !important; }
    .stSuccess { border-left: 3px solid var(--green) !important; background: #001a00 !important; }
    .stError   { border-left: 3px solid var(--red) !important; background: #1a0000 !important; }
    .stWarning { border-left: 3px solid var(--amber) !important; background: #1a1000 !important; }

    /* ── Spinner ── */
    .stSpinner > div { border-top-color: var(--amber) !important; }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: var(--bg); }
    ::-webkit-scrollbar-thumb { background: var(--border); }
    ::-webkit-scrollbar-thumb:hover { background: var(--amber-d); }

    /* ── HR ── */
    hr { border-color: var(--border) !important; }

    /* ── Hide chrome ── */
    #MainMenu, footer, .stDeployButton { visibility: hidden; }

    /* ── Caption ── */
    .stCaption { color: var(--text-d) !important; font-size: 0.7rem !important; font-family: 'Share Tech Mono', monospace !important; }
</style>
""", unsafe_allow_html=True)

# ─── Configuración InfluxDB ───────────────────────────────────
TOKEN       = "tb819uTKnRtOkaXdVzqzKvEDPhu5IOe1KjJ93pfCMeJLpLUvxLzPWTs3XE8L9pvoQe8AesbciaEY2-hcAZQQPQ=="
ORG         = "Lectura de datos"
BUCKET      = "T-H"
URL         = "https://us-east-1-1.aws.cloud2.influxdata.com/"
MEASUREMENT = "sistema_seguridad"

CAMPOS_BIN  = ['movimiento', 'alarma_gas', 'ventilador']
CAMPO_GAS   = 'gas'

# ─── Matplotlib: tema terminal ────────────────────────────────
AMBER = '#FFB000'
GREEN = '#39FF14'
RED   = '#FF3131'
BG    = '#07090a'
BG2   = '#0a0c06'

plt.rcParams.update({
    'figure.facecolor'  : BG2,
    'axes.facecolor'    : BG2,
    'axes.edgecolor'    : '#1e2410',
    'axes.labelcolor'   : '#4a4220',
    'xtick.color'       : '#3a3218',
    'ytick.color'       : '#3a3218',
    'grid.color'        : '#111408',
    'grid.alpha'        : 1,
    'grid.linewidth'    : 1,
    'text.color'        : '#c8b560',
    'legend.facecolor'  : '#050603',
    'legend.edgecolor'  : '#1e2410',
    'axes.grid'         : True,
    'font.family'       : 'monospace',
    'axes.spines.top'   : False,
    'axes.spines.right' : False,
    'axes.spines.left'  : False,
    'xtick.labelsize'   : 8,
    'ytick.labelsize'   : 8,
})

# ─── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style="background:#020301; border-bottom:1px solid #1e2410;
                    padding:24px 16px 20px; margin:-1rem -1rem 1rem -1rem;">
            <div style="font-family:'Share Tech Mono',monospace; color:#FFB000;
                        font-size:1.1rem; letter-spacing:0.12em;">
                ▶ CTRL·SEC
            </div>
            <div style="font-family:'Share Tech Mono',monospace; color:#2a2410;
                        font-size:0.65rem; letter-spacing:0.2em; margin-top:4px;
                        text-transform:uppercase;">
                Sistema de Seguridad IoT<br>
                ESP32 · InfluxDB · Streamlit
            </div>
            <div style="margin-top:14px; display:flex; align-items:center; gap:8px;">
                <div style="width:7px;height:7px;border-radius:50%;background:#39FF14;
                            box-shadow:0 0 8px #39FF1488;animation:none;"></div>
                <span style="font-family:'Share Tech Mono',monospace;
                             color:#39FF14;font-size:0.7rem;letter-spacing:0.1em;">
                    SISTEMA ACTIVO
                </span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style="font-family:'Share Tech Mono',monospace; font-size:0.65rem;
                    color:#2a2410; letter-spacing:0.2em; text-transform:uppercase;
                    margin-bottom:8px;">
            ▸ Ventana de tiempo
        </div>
    """, unsafe_allow_html=True)
    horas = st.slider('', 1, 24, 2, label_visibility='collapsed')
    st.caption(f'→ últimas {horas} hora(s)')

    st.markdown("""
        <div style="font-family:'Share Tech Mono',monospace; font-size:0.65rem;
                    color:#2a2410; letter-spacing:0.2em; text-transform:uppercase;
                    margin:20px 0 8px 0;">
            ▸ Umbral Z-score
        </div>
    """, unsafe_allow_html=True)
    UMBRAL_Z = st.slider('', 1.5, 4.0, 2.5, step=0.1, label_visibility='collapsed')
    st.caption(f'→ anomalías |z| > {UMBRAL_Z}')

    st.markdown("""
        <div style="margin-top:28px; border:1px solid #1e2410; padding:14px;
                    background:#020301;">
            <div style="font-family:'Share Tech Mono',monospace; font-size:0.6rem;
                        color:#2a2410; letter-spacing:0.15em; text-transform:uppercase;">
                Refresco automático
            </div>
            <div style="font-family:'Share Tech Mono',monospace; color:#FFB000;
                        font-size:1.4rem; margin-top:4px; text-shadow:0 0 10px #FFB00066;">
                60s
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style="margin-top:16px; border:1px solid #1e2410; padding:14px;
                    background:#020301;">
            <div style="font-family:'Share Tech Mono',monospace; font-size:0.6rem;
                        color:#2a2410; letter-spacing:0.15em; text-transform:uppercase;
                        margin-bottom:8px;">
                Variables monitoreadas
            </div>
            <div style="font-family:'Share Tech Mono',monospace; font-size:0.75rem;
                        color:#c8b560; line-height:2;">
                🔥 GAS<br>
                🚶 MOVIMIENTO<br>
                🚨 ALARMA_GAS<br>
                💨 VENTILADOR
            </div>
        </div>
    """, unsafe_allow_html=True)

# ─── Header ───────────────────────────────────────────────────
st.markdown("""
    <div style="border-bottom:1px solid #1e2410; padding:24px 0 18px 0; margin-bottom:24px;">
        <div style="font-family:'Share Tech Mono',monospace; font-size:0.65rem;
                    color:#2a2410; letter-spacing:0.3em; text-transform:uppercase;
                    margin-bottom:8px;">
            ◈ PANEL DE CONTROL — SEGURIDAD Y MONITOREO
        </div>
        <div style="display:flex; align-items:baseline; gap:20px; flex-wrap:wrap;">
            <span style="font-family:'Courier Prime',monospace; font-size:1.9rem;
                         font-weight:700; color:#FFB000;
                         text-shadow:0 0 20px rgba(255,176,0,0.3);
                         letter-spacing:0.04em;">
                CTRL·SEC
            </span>
            <span style="font-family:'Share Tech Mono',monospace; font-size:0.8rem;
                         color:#3a3218; letter-spacing:0.08em;">
                ESP32 → InfluxDB → Streamlit &nbsp;/&nbsp; Sayu &amp; Kat
            </span>
        </div>
    </div>
""", unsafe_allow_html=True)

# ─── Carga de datos ───────────────────────────────────────────
@st.cache_data(ttl=60)
def cargar_datos(horas):
    query = f'''
    from(bucket: "{BUCKET}")
      |> range(start: -{horas}h)
      |> filter(fn: (r) => r._measurement == "{MEASUREMENT}")
      |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
    '''
    client = InfluxDBClient(url=URL, token=TOKEN, org=ORG, verify_ssl=False)
    result = client.query_api().query_data_frame(query, org=ORG)

    if result is None or (isinstance(result, pd.DataFrame) and result.empty):
        return pd.DataFrame()

    result['_time'] = pd.to_datetime(result['_time'], utc=True)
    result.set_index('_time', inplace=True)
    result.index = result.index.tz_convert('America/Bogota')

    columnas = ['gas', 'movimiento', 'alarma_gas', 'ventilador']
    columnas_ok = [c for c in columnas if c in result.columns]
    result = result[columnas_ok]

    df = result.resample('1min').agg({
        'gas'      : 'mean' if 'gas'       in columnas_ok else 'max',
        **{c: 'max' for c in ['movimiento', 'alarma_gas', 'ventilador'] if c in columnas_ok}
    })
    if 'gas' in df.columns:
        df = df.dropna(subset=['gas'])
    return df

with st.spinner('[ CONECTANDO A INFLUXDB... ]'):
    df = cargar_datos(horas)

if df.empty:
    st.error("[ ERROR ] No hay datos disponibles en el rango seleccionado.")
    st.stop()

# ─── Barra de estado del sistema ──────────────────────────────
alarma_activa   = df['alarma_gas'].max() == 1 if 'alarma_gas' in df.columns else False
movim_reciente  = df['movimiento'].iloc[-5:].max() == 1 if 'movimiento' in df.columns else False
gas_alto        = df['gas'].iloc[-1] > df['gas'].mean() + UMBRAL_Z * df['gas'].std() if 'gas' in df.columns else False

estado_color  = "#FF3131" if alarma_activa else ("#FFB000" if movim_reciente or gas_alto else "#39FF14")
estado_texto  = "⚠ ALARMA ACTIVA" if alarma_activa else ("! ALERTA" if movim_reciente or gas_alto else "✓ SISTEMA NORMAL")
estado_label  = "ALARMA_GAS DETECTADA" if alarma_activa else ("ACTIVIDAD RECIENTE" if movim_reciente else "TODOS LOS PARÁMETROS OK")

st.markdown(f"""
    <div style="background:#030402; border:1px solid {estado_color}44;
                border-left:3px solid {estado_color};
                padding:12px 18px; margin-bottom:24px;
                display:flex; justify-content:space-between; align-items:center;
                flex-wrap:wrap; gap:12px;">
        <div style="display:flex; align-items:center; gap:12px;">
            <div style="width:10px;height:10px;border-radius:50%;background:{estado_color};
                        box-shadow:0 0 10px {estado_color}88;"></div>
            <span style="font-family:'Share Tech Mono',monospace; color:{estado_color};
                         font-size:0.85rem; letter-spacing:0.1em;">
                {estado_texto}
            </span>
            <span style="font-family:'Share Tech Mono',monospace; color:#2a2410;
                         font-size:0.7rem; letter-spacing:0.08em;">
                — {estado_label}
            </span>
        </div>
        <div style="font-family:'Share Tech Mono',monospace; color:#2a2410; font-size:0.7rem;
                    letter-spacing:0.08em;">
            {len(df)} REG · {df.index[0].strftime('%d/%m %H:%M')} → {df.index[-1].strftime('%d/%m %H:%M')} (COL)
        </div>
    </div>
""", unsafe_allow_html=True)

# ─── Métricas clave ───────────────────────────────────────────
st.markdown("""
    <div style="font-family:'Share Tech Mono',monospace; font-size:0.65rem;
                color:#2a2410; letter-spacing:0.25em; text-transform:uppercase;
                margin-bottom:12px;">
        ▸ LECTURAS ACTUALES
    </div>
""", unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    gas_v = df['gas'].iloc[-1] if 'gas' in df.columns else 0
    gas_d = gas_v - df['gas'].mean()
    st.metric("🔥 GAS (ADC)", f"{gas_v:.0f}", f"{gas_d:+.0f} vs μ")

with c2:
    if 'movimiento' in df.columns:
        mov_pct = df['movimiento'].mean() * 100
        mov_n   = int(df['movimiento'].sum())
        st.metric("🚶 MOVIMIENTO", f"{mov_n} eventos", f"{mov_pct:.1f}% tiempo")

with c3:
    if 'alarma_gas' in df.columns:
        alm_pct = df['alarma_gas'].mean() * 100
        alm_n   = int(df['alarma_gas'].sum())
        st.metric("🚨 ALARMA GAS", f"{alm_n} activ.", f"{alm_pct:.1f}% tiempo")

with c4:
    if 'ventilador' in df.columns:
        ven_pct = df['ventilador'].mean() * 100
        ven_n   = int(df['ventilador'].sum())
        st.metric("💨 VENTILADOR", f"{ven_n} ciclos", f"{ven_pct:.1f}% tiempo")

with c5:
    serie_z = (df['gas'] - df['gas'].mean()) / df['gas'].std()
    n_anom  = int((serie_z.abs() > UMBRAL_Z).sum())
    st.metric("⚡ ANOMALÍAS", f"{n_anom} detect.", f"umbral z>{UMBRAL_Z}")

st.markdown("<hr>", unsafe_allow_html=True)

# ─── Sección A: Gas + Movimiento (serie de tiempo) ────────────
st.markdown("""
    <div style="font-family:'Share Tech Mono',monospace; font-size:0.65rem;
                color:#2a2410; letter-spacing:0.25em; text-transform:uppercase;
                margin-bottom:16px;">
        ▸ SEÑAL DE GAS Y EVENTOS DE MOVIMIENTO
    </div>
""", unsafe_allow_html=True)

fig, ax1 = plt.subplots(figsize=(14, 4.5), facecolor=BG2)
ax1.set_facecolor(BG2)

serie_gas = df['gas'].dropna()
ax1.plot(serie_gas.index, serie_gas, color=AMBER, linewidth=1.6, alpha=0.9, zorder=3)
ax1.fill_between(serie_gas.index, serie_gas, serie_gas.mean(),
                 where=(serie_gas > serie_gas.mean()),
                 alpha=0.2, color=AMBER, zorder=2)

# Zona segura
ax1.axhline(serie_gas.mean(), color=AMBER, linestyle='--', linewidth=0.8, alpha=0.35)
ax1.axhline(serie_gas.mean() + UMBRAL_Z * serie_gas.std(),
            color=RED, linestyle=':', linewidth=0.8, alpha=0.5)
ax1.axhline(serie_gas.mean() - UMBRAL_Z * serie_gas.std(),
            color=RED, linestyle=':', linewidth=0.8, alpha=0.5)
ax1.fill_between(serie_gas.index,
                 serie_gas.mean() - UMBRAL_Z * serie_gas.std(),
                 serie_gas.mean() + UMBRAL_Z * serie_gas.std(),
                 alpha=0.04, color=GREEN)

# Anomalías
z = (serie_gas - serie_gas.mean()) / serie_gas.std()
anom = serie_gas[z.abs() > UMBRAL_Z]
if not anom.empty:
    ax1.scatter(anom.index, anom, color=RED, s=50, zorder=6,
                edgecolors='#ff000044', linewidths=2)

ax1.set_ylabel('GAS (ADC)', fontsize=8.5, color='#4a4220', labelpad=10)
ax1.tick_params(axis='both', length=0)

# Eje secundario: movimiento
if 'movimiento' in df.columns:
    ax2 = ax1.twinx()
    ax2.set_facecolor(BG2)
    ax2.fill_between(df.index, 0, df['movimiento'],
                     alpha=0.25, color='#00BFFF', step='mid')
    ax2.step(df.index, df['movimiento'], color='#00BFFF',
             linewidth=0.8, alpha=0.6, where='mid')
    ax2.set_ylabel('MOVIMIENTO', fontsize=8, color='#1a6070', labelpad=10)
    ax2.set_ylim(-0.05, 2)
    ax2.tick_params(axis='both', length=0, labelsize=7, labelcolor='#1a6070')
    ax2.set_yticks([0, 1])
    ax2.set_yticklabels(['OFF', 'ON'])

ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
ax1.xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
plt.gcf().autofmt_xdate(rotation=0, ha='center')
plt.tight_layout(pad=1)
st.pyplot(fig, use_container_width=True)
plt.close()

st.markdown("<hr>", unsafe_allow_html=True)

# ─── Sección B: Eventos binarios timeline ─────────────────────
binarias_existentes = [c for c in CAMPOS_BIN if c in df.columns]
if binarias_existentes:
    st.markdown("""
        <div style="font-family:'Share Tech Mono',monospace; font-size:0.65rem;
                    color:#2a2410; letter-spacing:0.25em; text-transform:uppercase;
                    margin-bottom:16px;">
            ▸ TIMELINE DE EVENTOS (VARIABLES BINARIAS)
        </div>
    """, unsafe_allow_html=True)

    colores_bin = {'movimiento': '#00BFFF', 'alarma_gas': RED, 'ventilador': GREEN}
    n = len(binarias_existentes)
    fig, axes = plt.subplots(n, 1, figsize=(14, 1.8 * n), sharex=True, facecolor=BG2)
    if n == 1:
        axes = [axes]
    fig.patch.set_facecolor(BG2)

    for ax, campo in zip(axes, binarias_existentes):
        color = colores_bin.get(campo, AMBER)
        ax.set_facecolor(BG2)
        ax.fill_between(df.index, 0, df[campo],
                        alpha=0.5, color=color, step='mid')
        ax.step(df.index, df[campo], color=color, linewidth=1.2,
                alpha=0.9, where='mid')
        # Porcentaje activo
        pct = df[campo].mean() * 100
        ax.annotate(f' {pct:.1f}% activo',
                    xy=(1, 0.5), xycoords='axes fraction',
                    fontsize=7.5, color=color, va='center', ha='right',
                    xytext=(-10, 0), textcoords='offset points',
                    fontfamily='monospace')
        ax.set_ylabel(campo.upper(), fontsize=7.5, color=color, labelpad=10)
        ax.set_ylim(-0.05, 1.2)
        ax.set_yticks([0, 1])
        ax.set_yticklabels(['0', '1'], fontsize=7)
        ax.tick_params(length=0)

    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    axes[-1].xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
    plt.gcf().autofmt_xdate(rotation=0, ha='center')
    plt.tight_layout(pad=0.8, h_pad=0.3)
    st.pyplot(fig, use_container_width=True)
    plt.close()

    st.markdown("<hr>", unsafe_allow_html=True)

# ─── Sección C: Distribución + Media móvil ────────────────────
col_dist, col_mm = st.columns([1, 1.6])

with col_dist:
    st.markdown("""
        <div style="font-family:'Share Tech Mono',monospace; font-size:0.65rem;
                    color:#2a2410; letter-spacing:0.25em; text-transform:uppercase;
                    margin-bottom:12px;">
            ▸ DISTRIBUCIÓN — GAS
        </div>
    """, unsafe_allow_html=True)

    fig, ax = plt.subplots(figsize=(5.5, 4), facecolor=BG2)
    ax.set_facecolor(BG2)
    gas_data = df['gas'].dropna()
    media, mediana, std = gas_data.mean(), gas_data.median(), gas_data.std()

    sns.histplot(gas_data, bins=25, kde=True, ax=ax, color=AMBER, alpha=0.25,
                 line_kws={'linewidth': 2, 'color': AMBER})
    ax.axvline(media, color='#e2e8c0', linestyle='--', linewidth=1.5,
               label=f'μ = {media:.0f}')
    ax.axvline(mediana, color=AMBER, linestyle='-', linewidth=1, alpha=0.7,
               label=f'md = {mediana:.0f}')
    ax.axvline(media + std, color=RED, linestyle=':', linewidth=0.8, alpha=0.5,
               label=f'+1σ = {media+std:.0f}')
    ax.axvline(media - std, color=RED, linestyle=':', linewidth=0.8, alpha=0.5,
               label=f'-1σ = {media-std:.0f}')
    ax.set_xlabel('Gas (ADC)', fontsize=8, color='#3a3218')
    ax.set_ylabel('Frecuencia', fontsize=8, color='#3a3218')
    ax.legend(fontsize=7.5, framealpha=0.5)
    ax.tick_params(length=0)
    plt.tight_layout(pad=1)
    st.pyplot(fig, use_container_width=True)
    plt.close()

with col_mm:
    st.markdown("""
        <div style="font-family:'Share Tech Mono',monospace; font-size:0.65rem;
                    color:#2a2410; letter-spacing:0.25em; text-transform:uppercase;
                    margin-bottom:12px;">
            ▸ TENDENCIA — MEDIA MÓVIL (GAS)
        </div>
    """, unsafe_allow_html=True)

    fig, ax = plt.subplots(figsize=(9, 4), facecolor=BG2)
    ax.set_facecolor(BG2)
    serie = df['gas'].dropna()
    rm5  = serie.rolling(window=5,  center=True).mean()
    rm15 = serie.rolling(window=15, center=True).mean()

    ax.plot(serie.index, serie, color=AMBER, alpha=0.2, linewidth=1, label='Original')
    ax.plot(rm5.index,  rm5,  color='#FFD700', alpha=0.7, linewidth=1.8, label='MM 5 min')
    ax.plot(rm15.index, rm15, color='#e2e8c0', alpha=0.85, linewidth=2.5, label='MM 15 min')
    ax.axhline(serie.mean(), linestyle='--', color='#3a3218',
               linewidth=1, label=f'μ global ({serie.mean():.0f})')

    ax.set_ylabel('Gas (ADC)', fontsize=8.5, color='#3a3218')
    ax.set_xlabel('Hora (Colombia)', fontsize=8, color='#3a3218')
    ax.legend(fontsize=8, framealpha=0.5)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
    plt.gcf().autofmt_xdate(rotation=0, ha='center')
    plt.tight_layout(pad=1)
    st.pyplot(fig, use_container_width=True)
    plt.close()

st.markdown("<hr>", unsafe_allow_html=True)

# ─── Sección D: Correlación + Boxplot ─────────────────────────
col_corr, col_box = st.columns([1, 1])

with col_corr:
    st.markdown("""
        <div style="font-family:'Share Tech Mono',monospace; font-size:0.65rem;
                    color:#2a2410; letter-spacing:0.25em; text-transform:uppercase;
                    margin-bottom:12px;">
            ▸ CORRELACIÓN — PEARSON
        </div>
    """, unsafe_allow_html=True)

    fig, ax = plt.subplots(figsize=(5.5, 4.5), facecolor=BG2)
    ax.set_facecolor(BG2)
    cmap = sns.diverging_palette(15, 145, s=80, l=35, as_cmap=True)
    corr = df.corr(method='pearson')
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    sns.heatmap(corr, annot=True, fmt='.2f', cmap=cmap,
                center=0, vmin=-1, vmax=1, ax=ax, mask=mask,
                annot_kws={'size': 9, 'color': '#c8b560'},
                linewidths=2, linecolor='#050603', square=True,
                cbar_kws={'shrink': 0.7})
    ax.tick_params(colors='#4a4220', labelsize=8, length=0)
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close()

with col_box:
    st.markdown("""
        <div style="font-family:'Share Tech Mono',monospace; font-size:0.65rem;
                    color:#2a2410; letter-spacing:0.25em; text-transform:uppercase;
                    margin-bottom:12px;">
            ▸ BOXPLOT — OUTLIERS GAS
        </div>
    """, unsafe_allow_html=True)

    fig, ax = plt.subplots(figsize=(5.5, 4.5), facecolor=BG2)
    ax.set_facecolor(BG2)
    datos = df['gas'].dropna()
    bp = ax.boxplot(datos, patch_artist=True, vert=True, widths=0.45,
                    medianprops=dict(color='#e2e8c0', linewidth=2.5),
                    flierprops=dict(marker='D', color=RED, markersize=5, alpha=0.8,
                                   markerfacecolor=RED, markeredgecolor='#7a0000'),
                    whiskerprops=dict(color=AMBER, linewidth=1.5, linestyle='--'),
                    capprops=dict(color=AMBER, linewidth=2))
    bp['boxes'][0].set_facecolor(AMBER)
    bp['boxes'][0].set_alpha(0.15)
    bp['boxes'][0].set_edgecolor(AMBER)

    q1, q3 = datos.quantile(0.25), datos.quantile(0.75)
    iqr = q3 - q1
    n_out = int(((datos < q1 - 1.5*iqr) | (datos > q3 + 1.5*iqr)).sum())

    ax.annotate(f'Q3 = {q3:.0f}', xy=(1.35, q3), fontsize=8, color='#4a4220')
    ax.annotate(f'Md = {datos.median():.0f}', xy=(1.35, datos.median()),
                fontsize=8, color='#e2e8c0', fontweight='bold')
    ax.annotate(f'Q1 = {q1:.0f}', xy=(1.35, q1), fontsize=8, color='#4a4220')

    ax.set_title(f'{n_out} outlier(s) detectados (IQR)', fontsize=9,
                 color='#4a4220', pad=10)
    ax.set_ylabel('Gas (ADC)', fontsize=8, color='#3a3218')
    ax.set_xticks([])
    plt.tight_layout(pad=1)
    st.pyplot(fig, use_container_width=True)
    plt.close()

st.markdown("<hr>", unsafe_allow_html=True)

# ─── Sección E: Reporte estadístico ──────────────────────────
st.markdown("""
    <div style="font-family:'Share Tech Mono',monospace; font-size:0.65rem;
                color:#2a2410; letter-spacing:0.25em; text-transform:uppercase;
                margin-bottom:12px;">
        ▸ REPORTE ESTADÍSTICO — GAS
    </div>
""", unsafe_allow_html=True)

g = df['gas'].dropna()
q1g, q3g = g.quantile(0.25), g.quantile(0.75)
iqr_g  = q3g - q1g
out_g  = int(((g < q1g - 1.5*iqr_g) | (g > q3g + 1.5*iqr_g)).sum())

col_t1, col_t2 = st.columns(2)

with col_t1:
    reporte_gas = pd.DataFrame([{
        'Estadístico' : stat,
        'Valor'       : val
    } for stat, val in {
        'count'       : f'{len(g)} obs.',
        'min'         : f'{g.min():.2f}',
        'max'         : f'{g.max():.2f}',
        'mean (μ)'    : f'{g.mean():.2f}',
        'median'      : f'{g.median():.2f}',
        'std (σ)'     : f'{g.std():.2f}',
        'IQR'         : f'{iqr_g:.2f}',
        'skewness'    : f'{g.skew():.4f}',
        'kurtosis'    : f'{g.kurt():.4f}',
        'outliers'    : f'{out_g}',
    }.items()])
    st.dataframe(reporte_gas.set_index('Estadístico'), use_container_width=True)

with col_t2:
    st.markdown("""
        <div style="font-family:'Share Tech Mono',monospace; font-size:0.65rem;
                    color:#2a2410; letter-spacing:0.25em; text-transform:uppercase;
                    margin-bottom:12px;">
            ▸ EVENTOS BINARIOS — RESUMEN
        </div>
    """, unsafe_allow_html=True)
    filas_bin = []
    for col_b in CAMPOS_BIN:
        if col_b in df.columns:
            filas_bin.append({
                'Variable'        : col_b.upper(),
                'Activaciones'    : int(df[col_b].sum()),
                '% tiempo activo' : f"{df[col_b].mean()*100:.1f}%",
            })
    if filas_bin:
        st.dataframe(pd.DataFrame(filas_bin).set_index('Variable'),
                     use_container_width=True)

    # Correlación gas ↔ movimiento
    if 'movimiento' in df.columns:
        r = df['gas'].corr(df['movimiento'])
        dir_text  = "↑ gas + movimiento correlacionan" if r > 0.3 else (
                    "↓ relación inversa" if r < -0.3 else "≈ sin relación lineal clara")
        r_color   = RED if abs(r) > 0.5 else AMBER
        st.markdown(f"""
            <div style="margin-top:16px; border:1px solid #1e2410; padding:14px;
                        background:#020301;">
                <div style="font-family:'Share Tech Mono',monospace; font-size:0.62rem;
                            color:#2a2410; letter-spacing:0.15em; text-transform:uppercase;">
                    Correlación gas ↔ movimiento
                </div>
                <div style="font-family:'Share Tech Mono',monospace; font-size:1.6rem;
                            color:{r_color}; margin-top:6px;
                            text-shadow:0 0 10px {r_color}55;">
                    r = {r:.3f}
                </div>
                <div style="font-family:'Share Tech Mono',monospace; font-size:0.72rem;
                            color:#3a3218; margin-top:4px;">
                    {dir_text}
                </div>
            </div>
        """, unsafe_allow_html=True)

# ─── Footer ───────────────────────────────────────────────────
st.markdown("""
    <div style="margin-top:36px; border-top:1px solid #1e2410; padding:16px 0 8px 0;
                font-family:'Share Tech Mono',monospace; font-size:0.65rem;
                color:#1e2010; letter-spacing:0.15em; text-transform:uppercase;
                display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px;">
        <span>CTRL·SEC · SAYU &amp; KAT · 2025</span>
        <span>ESP32 + INFLUXDB + STREAMLIT</span>
        <span>SISTEMA DE SEGURIDAD Y CONTROL IOT</span>
    </div>
""", unsafe_allow_html=True)
