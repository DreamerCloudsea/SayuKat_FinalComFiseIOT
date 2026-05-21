import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import seaborn as sns
from influxdb_client import InfluxDBClient

# ─── Configuración de página ──────────────────────────────────
st.set_page_config(
    page_title='CSP · Sensores IoT',
    page_icon='🛰️',
    layout='wide',
    initial_sidebar_state='expanded'
)

# ─── CSS Premium ──────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

    /* ── Reset & base ── */
    *, *::before, *::after { box-sizing: border-box; }

    .stApp {
        background: #07080d;
        color: #d4daf0;
        font-family: 'DM Sans', sans-serif;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: #0c0e18 !important;
        border-right: 1px solid #1c2035;
        padding-top: 0 !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 0 !important;
    }

    /* ── Sidebar header badge ── */
    .sidebar-brand {
        background: linear-gradient(135deg, #0f1525 0%, #111827 100%);
        border-bottom: 1px solid #1c2035;
        padding: 28px 20px 22px 20px;
        margin-bottom: 8px;
    }
    .sidebar-brand .icon {
        font-size: 2.2rem;
        display: block;
        margin-bottom: 6px;
    }
    .sidebar-brand .title {
        font-family: 'Space Mono', monospace;
        font-size: 0.95rem;
        font-weight: 700;
        color: #e2e8ff;
        letter-spacing: 0.06em;
        display: block;
    }
    .sidebar-brand .sub {
        font-size: 0.72rem;
        color: #4a5278;
        letter-spacing: 0.1em;
        display: block;
        margin-top: 4px;
        text-transform: uppercase;
    }

    /* ── Sidebar section labels ── */
    .sidebar-label {
        font-family: 'Space Mono', monospace;
        font-size: 0.65rem;
        font-weight: 700;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: #3d4468;
        margin: 20px 0 8px 0;
        padding: 0 4px;
    }

    /* ── Sliders ── */
    [data-testid="stSlider"] > div > div > div {
        background: #1c2035 !important;
    }
    [data-testid="stSlider"] > div > div > div > div {
        background: #4f6ef7 !important;
    }
    .stSlider [data-baseweb="slider"] > div:first-child {
        background: #1c2035 !important;
    }

    /* ── Multiselect tags ── */
    [data-testid="stMultiSelect"] [data-baseweb="tag"] {
        background: #1a2040 !important;
        border: 1px solid #2a3560 !important;
        border-radius: 6px !important;
        color: #8fa3f5 !important;
        font-size: 0.78rem !important;
        font-family: 'Space Mono', monospace !important;
    }
    [data-testid="stMultiSelect"] [data-baseweb="tag"] span { color: #8fa3f5 !important; }
    [data-testid="stMultiSelect"] [data-baseweb="tag"] button svg { fill: #4a5278 !important; }

    /* ── Main header ── */
    .main-header {
        padding: 32px 0 20px 0;
        border-bottom: 1px solid #1c2035;
        margin-bottom: 28px;
    }
    .main-header .eyebrow {
        font-family: 'Space Mono', monospace;
        font-size: 0.65rem;
        letter-spacing: 0.25em;
        text-transform: uppercase;
        color: #4f6ef7;
        margin-bottom: 6px;
    }
    .main-header h1 {
        font-family: 'DM Sans', sans-serif;
        font-size: 2rem;
        font-weight: 600;
        color: #e8ecff;
        margin: 0 0 6px 0;
        letter-spacing: -0.02em;
    }
    .main-header .sub {
        font-size: 0.85rem;
        color: #3d4468;
        letter-spacing: 0.03em;
    }

    /* ── Section titles ── */
    .section-title {
        font-family: 'Space Mono', monospace;
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        color: #3d4468;
        margin: 32px 0 16px 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .section-title::after {
        content: '';
        flex: 1;
        height: 1px;
        background: #1c2035;
    }

    /* ── Metric cards ── */
    [data-testid="stMetric"] {
        background: #0c0f1d;
        border: 1px solid #1c2035;
        border-radius: 14px;
        padding: 20px 18px !important;
        position: relative;
        overflow: hidden;
        transition: border-color 0.2s ease, transform 0.2s ease;
    }
    [data-testid="stMetric"]:hover {
        border-color: #2a3560;
        transform: translateY(-2px);
    }
    [data-testid="stMetric"]::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, #4f6ef7, #7c3aed);
        opacity: 0.6;
    }
    [data-testid="stMetricValue"] {
        font-family: 'Space Mono', monospace !important;
        color: #e8ecff !important;
        font-size: 1.55rem !important;
        font-weight: 400 !important;
        letter-spacing: -0.02em;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.75rem !important;
        letter-spacing: 0.06em;
        color: #4a5278 !important;
        text-transform: uppercase;
        font-weight: 500 !important;
    }
    [data-testid="stMetricDelta"] {
        font-family: 'Space Mono', monospace !important;
        font-size: 0.72rem !important;
    }

    /* ── Status bar ── */
    .status-bar {
        display: flex;
        align-items: center;
        gap: 10px;
        background: #0c0f1d;
        border: 1px solid #1c2035;
        border-radius: 10px;
        padding: 10px 16px;
        margin-bottom: 28px;
        font-size: 0.8rem;
    }
    .status-dot {
        width: 7px; height: 7px;
        border-radius: 50%;
        background: #22c55e;
        box-shadow: 0 0 6px #22c55e88;
        flex-shrink: 0;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
    }
    .status-text { color: #4a5278; }
    .status-text strong { color: #8fa3f5; font-family: 'Space Mono', monospace; font-size: 0.75rem; }

    /* ── DataFrame ── */
    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #1c2035 !important;
        background: #0c0f1d;
    }

    /* ── Alerts ── */
    .stAlert {
        border-radius: 12px !important;
        border: 1px solid #2a1515 !important;
        background: #130a0a !important;
    }

    /* ── Spinner ── */
    .stSpinner > div { border-top-color: #4f6ef7 !important; }

    /* ── HR ── */
    hr { border-color: #1c2035 !important; margin: 28px 0 !important; }

    /* ── Footer ── */
    .footer {
        text-align: center;
        color: #252840;
        font-size: 0.72rem;
        font-family: 'Space Mono', monospace;
        letter-spacing: 0.1em;
        padding: 28px 0 16px 0;
        text-transform: uppercase;
    }

    /* ── Live badge ── */
    .live-badge {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        background: #0a1a0e;
        border: 1px solid #14532d;
        border-radius: 20px;
        padding: 3px 10px;
        font-size: 0.68rem;
        font-family: 'Space Mono', monospace;
        color: #22c55e;
        letter-spacing: 0.1em;
    }
    .live-badge::before {
        content: '';
        width: 6px; height: 6px;
        border-radius: 50%;
        background: #22c55e;
        animation: pulse 1.5s infinite;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #0c0e18; }
    ::-webkit-scrollbar-thumb { background: #1c2035; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #2a3560; }

    /* ── Caption ── */
    .stCaption { color: #2d3458 !important; font-size: 0.72rem !important; }

    /* ── Hide Streamlit chrome ── */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    .stDeployButton { display: none; }
</style>
""", unsafe_allow_html=True)

# ─── Configuración de datos ───────────────────────────────────
TOKEN  = 'Uj6JUIaa_2U-_EGXBEe1PmfBpwDBYhW0QfbIrPcRMjTntF-3rGLOiVGKedHdZHmFEI81SHDiJxAymYVZSJvjoA=='
ORG    = 'Sofi, Cami, Phio'
BUCKET = 'CSP'
URL    = 'https://us-east-1-1.aws.cloud2.influxdata.com'
CAMPOS = ['temperatura', 'humedad', 'nivel_agua', 'intensidad_solar', 'distancia']
META   = {
    'temperatura'     : ('#f87171', '°C',  '🌡️'),
    'humedad'         : ('#34d399', '%',   '💧'),
    'nivel_agua'      : ('#60a5fa', '%',   '🪣'),
    'intensidad_solar': ('#fbbf24', '%',   '☀️'),
    'distancia'       : ('#a78bfa', 'cm',  '📏'),
}

# ─── Matplotlib: tema premium oscuro ─────────────────────────
plt.rcParams.update({
    'figure.facecolor'  : '#0c0f1d',
    'axes.facecolor'    : '#0c0f1d',
    'axes.edgecolor'    : '#1c2035',
    'axes.labelcolor'   : '#4a5278',
    'xtick.color'       : '#2d3458',
    'ytick.color'       : '#2d3458',
    'grid.color'        : '#111525',
    'grid.alpha'        : 1,
    'grid.linewidth'    : 1,
    'text.color'        : '#8892b0',
    'legend.facecolor'  : '#0a0c18',
    'legend.edgecolor'  : '#1c2035',
    'legend.fontsize'   : 8,
    'axes.grid'         : True,
    'axes.spines.top'   : False,
    'axes.spines.right' : False,
    'axes.spines.left'  : False,
    'font.family'       : 'monospace',
    'xtick.labelsize'   : 8,
    'ytick.labelsize'   : 8,
})

# ─── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div class="sidebar-brand">
            <span class="icon">🛰️</span>
            <span class="title">SENSORES CSP</span>
            <span class="sub">ESP32 · InfluxDB · Streamlit</span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-label">⏱ Ventana de tiempo</div>', unsafe_allow_html=True)
    horas = st.slider('', 1, 24, 2, label_visibility='collapsed')
    st.caption(f'Últimas {horas}h de datos')

    st.markdown('<div class="sidebar-label">📌 Variables activas</div>', unsafe_allow_html=True)
    campos_sel = st.multiselect('', CAMPOS, default=CAMPOS, label_visibility='collapsed')

    st.markdown('<div class="sidebar-label">⚠️ Umbral Z-score</div>', unsafe_allow_html=True)
    UMBRAL_Z = st.slider('', 1.5, 4.0, 2.5, step=0.1, label_visibility='collapsed')
    st.caption(f'Detecta anomalías con |z| > {UMBRAL_Z}')

    st.markdown("""
        <div style="margin-top: 28px; padding: 12px; background: #080a12;
                    border: 1px solid #1c2035; border-radius: 10px; text-align: center;">
            <div style="font-size:0.65rem; color:#2d3458; font-family:'Space Mono',monospace;
                        letter-spacing:0.12em; text-transform:uppercase;">
                Actualización
            </div>
            <div style="font-size:1.1rem; color:#4f6ef7; font-family:'Space Mono',monospace;
                        font-weight:700; margin-top:4px;">
                60s
            </div>
        </div>
    """, unsafe_allow_html=True)

# ─── Header principal ─────────────────────────────────────────
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("""
        <div class="main-header">
            <div class="eyebrow">● Tiempo real</div>
            <h1>Dashboard IoT</h1>
            <div class="sub">ESP32 → InfluxDB → Streamlit &nbsp;·&nbsp; Proyecto CSP</div>
        </div>
    """, unsafe_allow_html=True)
with col_h2:
    st.markdown("""
        <div style="padding-top:42px; text-align:right;">
            <span class="live-badge">EN VIVO</span>
        </div>
    """, unsafe_allow_html=True)

# ─── Carga de datos ───────────────────────────────────────────
@st.cache_data(ttl=60)
def cargar_datos(horas):
    def consultar_campo(client, campo):
        query = f'''
        from(bucket: "{BUCKET}")
          |> range(start: -{horas}h)
          |> filter(fn: (r) => r._measurement == "Sensores_CSP")
          |> filter(fn: (r) => r._field == "{campo}")
        '''
        tablas = client.query_api().query(query, org=ORG)
        tiempos, valores = [], []
        for tabla in tablas:
            for record in tabla.records:
                tiempos.append(record.get_time())
                valores.append(record.get_value())
        if not tiempos:
            return pd.Series([], dtype=float, name=campo, index=pd.DatetimeIndex([]))
        idx = pd.DatetimeIndex(
            pd.to_datetime(pd.Series(tiempos), utc=True)
        ).tz_convert('America/Bogota')
        return pd.Series(valores, index=idx, name=campo, dtype=float).sort_index()

    client_db = InfluxDBClient(url=URL, token=TOKEN, org=ORG, verify_ssl=False)
    series = {c: consultar_campo(client_db, c) for c in CAMPOS}
    df = pd.concat(series.values(), axis=1)
    df.columns = CAMPOS
    if df.empty:
        return pd.DataFrame()
    df.index = pd.to_datetime(df.index, errors='coerce')
    df = df[~df.index.isna()]
    if len(df.index) == 0:
        return pd.DataFrame()
    df = df.sort_index()
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.DatetimeIndex(df.index)
    df = df.resample('1min').mean()
    df.index.name = 'tiempo'
    return df

with st.spinner('Conectando a InfluxDB…'):
    df = cargar_datos(horas)

if df.empty:
    st.error("❌ No hay datos disponibles en el rango seleccionado.")
    st.stop()

# ─── Status bar ───────────────────────────────────────────────
st.markdown(f"""
    <div class="status-bar">
        <div class="status-dot"></div>
        <div class="status-text">
            Conexión establecida · 
            <strong>{len(df)}</strong> registros · 
            <strong>{df.index[0].strftime('%d/%m %H:%M')}</strong>
            →
            <strong>{df.index[-1].strftime('%d/%m %H:%M')}</strong>
            &nbsp;(Bogotá)
        </div>
    </div>
""", unsafe_allow_html=True)

# ─── Métricas ─────────────────────────────────────────────────
st.markdown('<div class="section-title">Valores actuales</div>', unsafe_allow_html=True)
cols = st.columns(len(campos_sel))
for col, campo in zip(cols, campos_sel):
    color, unidad, emoji = META[campo]
    valor = df[campo].iloc[-1]
    delta = valor - df[campo].mean()
    col.metric(
        label=f'{emoji}  {campo.replace("_", " ").title()}',
        value=f'{valor:.1f} {unidad}',
        delta=f'{delta:+.2f} vs media'
    )

# ─── Helper: figura base ──────────────────────────────────────
def nueva_fig(rows=1, cols_n=1, h=4, w=14, sharex=False):
    fig, axes = plt.subplots(rows, cols_n, figsize=(w, h * rows), sharex=sharex,
                             facecolor='#0c0f1d')
    fig.patch.set_facecolor('#0c0f1d')
    if rows == 1 and cols_n == 1:
        axes = [axes]
    elif rows == 1 or cols_n == 1:
        axes = list(axes)
    return fig, axes

# ─── Series de tiempo ─────────────────────────────────────────
st.markdown('<div class="section-title">Series de tiempo</div>', unsafe_allow_html=True)

fig, axes = nueva_fig(rows=len(campos_sel), h=3, w=14, sharex=True)
for ax, campo in zip(axes, campos_sel):
    color, unidad, emoji = META[campo]
    serie = df[campo].dropna()
    mean_v = serie.mean()

    # Área de relleno con gradiente simulado
    ax.fill_between(serie.index, serie, mean_v, where=(serie >= mean_v),
                    alpha=0.15, color=color, interpolate=True)
    ax.fill_between(serie.index, serie, mean_v, where=(serie < mean_v),
                    alpha=0.07, color=color, interpolate=True)

    # Línea principal
    ax.plot(serie.index, serie, color=color, linewidth=1.8, alpha=0.95, zorder=3)

    # Media
    ax.axhline(mean_v, color=color, linestyle=':', linewidth=1, alpha=0.4, zorder=2)

    # Etiqueta de variable
    ax.set_ylabel(f'{emoji} {campo}\n({unidad})', fontsize=8.5,
                  color='#3d4468', labelpad=12)
    ax.yaxis.set_label_coords(-0.06, 0.5)

    # Valor actual como anotación
    ultimo = serie.iloc[-1]
    ax.annotate(f' {ultimo:.1f}{unidad}',
                xy=(serie.index[-1], ultimo),
                fontsize=7.5, color=color, va='center',
                fontfamily='monospace',
                xytext=(6, 0), textcoords='offset points')

    ax.tick_params(axis='both', length=0, labelsize=7.5)
    ax.set_facecolor('#0c0f1d')

# Eje X compartido
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
axes[-1].xaxis.set_major_locator(mdates.MinuteLocator(interval=15))
plt.gcf().autofmt_xdate(rotation=0, ha='center')
plt.tight_layout(pad=1.2, h_pad=0.5)
st.pyplot(fig, use_container_width=True)
plt.close()

# ─── Histogramas + Boxplots (fila lado a lado) ────────────────
st.markdown('<div class="section-title">Distribuciones &amp; dispersión</div>', unsafe_allow_html=True)

col_hist, col_box = st.columns([3, 2])

with col_hist:
    n = len(campos_sel)
    fig, axes = plt.subplots(1, n, figsize=(4.5 * n, 4), facecolor='#0c0f1d')
    if n == 1:
        axes = [axes]
    fig.patch.set_facecolor('#0c0f1d')
    for ax, campo in zip(axes, campos_sel):
        color, unidad, emoji = META[campo]
        datos = df[campo].dropna()
        sns.histplot(datos, bins=22, kde=True, ax=ax, color=color, alpha=0.25,
                     line_kws={'linewidth': 2, 'color': color})
        ax.axvline(datos.mean(), color='#e2e8ff', linestyle='--', linewidth=1.2,
                   label=f'μ {datos.mean():.1f}')
        ax.axvline(datos.median(), color=color, linestyle='-', linewidth=1,
                   alpha=0.7, label=f'med {datos.median():.1f}')
        ax.set_title(f'{emoji} {campo}', fontsize=9, color='#8892b0',
                     fontfamily='monospace', pad=10)
        ax.set_xlabel(unidad, fontsize=8, color='#3d4468')
        ax.legend(fontsize=7.5, framealpha=0.4)
        ax.tick_params(length=0, labelsize=7)
        ax.set_facecolor('#0c0f1d')
    plt.tight_layout(pad=1)
    st.pyplot(fig, use_container_width=True)
    plt.close()

with col_box:
    fig, ax = plt.subplots(figsize=(5, 4), facecolor='#0c0f1d')
    fig.patch.set_facecolor('#0c0f1d')
    ax.set_facecolor('#0c0f1d')

    data_all = [df[c].dropna().values for c in campos_sel]
    colors   = [META[c][0] for c in campos_sel]
    labels   = [f"{META[c][2]} {c.split('_')[0]}" for c in campos_sel]

    bp = ax.boxplot(data_all, patch_artist=True, widths=0.5,
                    medianprops=dict(color='#e2e8ff', linewidth=2),
                    flierprops=dict(marker='o', markersize=4, alpha=0.5),
                    whiskerprops=dict(linewidth=1.2),
                    capprops=dict(linewidth=1.2))

    for patch, color, flier, w, c in zip(bp['boxes'], colors,
                                          bp['fliers'], bp['whiskers'][::2],
                                          bp['caps'][::2]):
        patch.set_facecolor(color)
        patch.set_alpha(0.25)
        patch.set_edgecolor(color)
        flier.set_markerfacecolor(color)
        flier.set_markeredgecolor(color)
        w.set_color(color)
        c.set_color(color)
    for w in bp['whiskers'][1::2]:
        w.set_color(colors[bp['whiskers'][1::2].index(w) % len(colors)])
    for c in bp['caps'][1::2]:
        c.set_color(colors[bp['caps'][1::2].index(c) % len(colors)])

    ax.set_xticks(range(1, len(campos_sel) + 1))
    ax.set_xticklabels(labels, fontsize=7.5, rotation=20, ha='right')
    ax.set_ylabel('Valor', fontsize=8, color='#3d4468')
    ax.tick_params(length=0, labelsize=7)
    ax.set_title('Boxplots — outliers', fontsize=9, color='#8892b0',
                 fontfamily='monospace', pad=10)
    plt.tight_layout(pad=1)
    st.pyplot(fig, use_container_width=True)
    plt.close()

# ─── Correlación + Anomalías ──────────────────────────────────
st.markdown('<div class="section-title">Correlación &amp; anomalías</div>', unsafe_allow_html=True)
col_corr, col_anom = st.columns([1, 1.7])

with col_corr:
    fig, ax = plt.subplots(figsize=(5.5, 5), facecolor='#0c0f1d')
    fig.patch.set_facecolor('#0c0f1d')
    cmap = sns.diverging_palette(230, 20, as_cmap=True)
    mask = pd.DataFrame(False, index=df[campos_sel].columns,
                        columns=df[campos_sel].columns)
    # Triángulo superior
    import numpy as np
    mask_np = np.triu(np.ones_like(df[campos_sel].corr(), dtype=bool), k=1)

    sns.heatmap(df[campos_sel].corr(), annot=True, fmt='.2f', cmap=cmap,
                center=0, vmin=-1, vmax=1, ax=ax,
                annot_kws={'size': 9, 'color': '#ccd6f6'},
                linewidths=3, linecolor='#07080d', square=True,
                cbar_kws={'shrink': 0.75},
                mask=mask_np)
    ax.tick_params(colors='#4a5278', labelsize=8, length=0)
    ax.set_facecolor('#0c0f1d')
    plt.title('Correlación de Pearson', fontsize=9, color='#8892b0',
              fontfamily='monospace', pad=14)
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close()

with col_anom:
    fig, axes = plt.subplots(len(campos_sel), 1, figsize=(9, 2.6 * len(campos_sel)),
                             sharex=True, facecolor='#0c0f1d')
    if len(campos_sel) == 1:
        axes = [axes]
    fig.patch.set_facecolor('#0c0f1d')
    for ax, campo in zip(axes, campos_sel):
        color, unidad, emoji = META[campo]
        serie = df[campo].dropna()
        z = (serie - serie.mean()) / serie.std()
        anomalias = serie[z.abs() > UMBRAL_Z]

        # Zona segura sombreada
        ax.fill_between(serie.index,
                        serie.mean() - UMBRAL_Z * serie.std(),
                        serie.mean() + UMBRAL_Z * serie.std(),
                        alpha=0.05, color=color, zorder=1)
        ax.axhline(serie.mean() + UMBRAL_Z * serie.std(),
                   color=color, linestyle=':', linewidth=0.8, alpha=0.25)
        ax.axhline(serie.mean() - UMBRAL_Z * serie.std(),
                   color=color, linestyle=':', linewidth=0.8, alpha=0.25)

        # Serie principal
        ax.plot(serie.index, serie, color=color, linewidth=1.5, alpha=0.8, zorder=2)

        # Anomalías
        if not anomalias.empty:
            ax.scatter(anomalias.index, anomalias, color='#fbbf24',
                       s=45, zorder=5, edgecolors='#f59e0b', linewidths=0.8)

        # Label
        n_anom = len(anomalias)
        ax.set_ylabel(f'{emoji} {campo.split("_")[0]}\n({unidad})',
                      fontsize=8, color='#3d4468')
        anom_color = '#f87171' if n_anom > 0 else '#22c55e'
        ax.annotate(f'{n_anom} anomalías', xy=(1, 1), xycoords='axes fraction',
                    fontsize=7.5, color=anom_color, ha='right', va='top',
                    xytext=(-8, -8), textcoords='offset points',
                    fontfamily='monospace')
        ax.tick_params(length=0, labelsize=7)
        ax.set_facecolor('#0c0f1d')

    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    axes[-1].xaxis.set_major_locator(mdates.MinuteLocator(interval=15))
    plt.gcf().autofmt_xdate(rotation=0, ha='center')
    plt.tight_layout(pad=1.2, h_pad=0.3)
    st.pyplot(fig, use_container_width=True)
    plt.close()

# ─── Tabla resumen ────────────────────────────────────────────
st.markdown('<div class="section-title">Reporte estadístico</div>', unsafe_allow_html=True)
resumen = []
for campo in campos_sel:
    color, unidad, emoji = META[campo]
    s = df[campo].dropna()
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    n_out = int(((s < q1 - 1.5*iqr) | (s > q3 + 1.5*iqr)).sum())
    resumen.append({
        'Variable'  : f'{emoji}  {campo}',
        'Mín'       : f'{s.min():.2f} {unidad}',
        'Máx'       : f'{s.max():.2f} {unidad}',
        'Media'     : f'{s.mean():.2f} {unidad}',
        'Mediana'   : f'{s.median():.2f} {unidad}',
        'Desv. std' : f'{s.std():.2f} {unidad}',
        'IQR'       : f'{iqr:.2f} {unidad}',
        'Outliers'  : n_out,
    })

st.dataframe(
    pd.DataFrame(resumen).set_index('Variable'),
    use_container_width=True,
    height=min(40 * (len(campos_sel) + 1) + 38, 380)
)

# ─── Footer ───────────────────────────────────────────────────
st.markdown("""
    <div class="footer">
        CSP · Sofi &nbsp;·&nbsp; Cami &nbsp;·&nbsp; Phio &nbsp;·&nbsp; 2025
        &nbsp;&nbsp;|&nbsp;&nbsp;
        ESP32 + InfluxDB + Streamlit
    </div>
""", unsafe_allow_html=True)
