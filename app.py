import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import numpy as np

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Ronnin DataLab | Estrés Térmico y Fricción",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- PALETA DE COLORES FIJA PARA PLOTLY GO ---
COLOR_MAP = {
    'Emergencia': '#E74C3C', # Rojo
    'Brusco': '#F39C12',     # Naranja
    'Progresivo': '#3498DB', # Azul
    'Suave': '#1ABC9C',      # Turquesa
}

# --- 2. CARGA DE DATA Y ANÁLISIS DE INGENIERÍA ---
@st.cache_data
def load_data():
    """Carga y procesa la data simulada."""
    try:
        df = pd.read_csv('brake_data.csv')
        temp_ambiente_media = df['Temperatura_Ambiente_C'].mean()
        energia_total_acumulada = df['Energia_Disipada_kJ'].sum()
        temp_final = df['Temperatura_Ambiente_C'].iloc[-1]

        df['Color_Frenado'] = df['Tipo_Frenado'].map(COLOR_MAP).fillna('#BDC3C7')
        df['Deceleracion_Visual'] = np.abs(df['Deceleracion_ms2']) * 5

        return df, temp_ambiente_media, energia_total_acumulada, temp_final
    except FileNotFoundError:
        st.error("Error: Archivo 'brake_data.csv' no encontrado.")
        return pd.DataFrame(), 0, 0, 0

df, temp_ambiente_media, energia_total_acumulada, temp_final = load_data()
energia_max = df['Energia_Disipada_kJ'].max()


# --- 3. INTERFAZ Y NARRATIVA (Artículo B1) ---

st.markdown("# **Ronnin DataLab** | Estrés Térmico y Desgaste en Frenos")
st.markdown("### **Análisis de Fricción:** Cómo la baja calidad de las pastillas deforma su disco 🏍️")

st.write(
    """
    **El Contexto:** Ronnin DataLab simuló un ciclo de conducción de **60 minutos (3,600 segundos)**, replicando el esfuerzo al que se somete una moto de **250 kg (incluyendo piloto y equipaje)**. Esta evaluación demuestra que el riesgo de **alabeo de disco** y **falla por *vapor lock*** no se mide en simple kilometraje, sino en la **ingeniería de la fricción** que soporta su sistema.
    """
)
st.divider()

if not df.empty:

    # --- 4. HALLAZGOS CLAVE (Métricas) ---
    deceleracion_max = df['Deceleracion_ms2'].min()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Temperatura Ambiente Media 🌡️", value=f"{temp_ambiente_media:.1f} °C")
    with col2:
        st.metric(label="Energía Máx. por Pico",
                    value=f"{energia_max:.1f} kJ",
                    delta="UMBRAL EBULLICIÓN: Alerta Vapor Lock",
                    delta_color="inverse")
    with col3:
        st.metric(label="Energía Total Disipada (Acum.)",
                    value=f"{energia_total_acumulada:.0f} kJ")
    with col4:
        st.metric(label="Deceleración Máx. Registrada",
                    value=f"{deceleracion_max:.1f} m/s²",
                    delta="FATIGA ESTRUCTURAL",
                    delta_color="inverse")

    st.markdown("---")

    # --- 5. GRÁFICA UNIFICADA: Causa, Estrés y Efecto ---

    st.markdown("## Análisis de Ciclo Unificado: Causa (Velocidad), Estrés (Deceleración) y Efecto (Calor)")

    fig_unificada = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=('Gráfica 1: Velocidad y Estrés Mecánico',
                        'Gráfica 2: Picos de Estrés Térmico por Fricción (Energía Disipada)')
    )

    fig_unificada.add_trace(
        go.Scatter(x=df['Tiempo_s'], y=df['Velocidad_kmh'], name='Velocidad (km/h)',
                   line=dict(color='#1ABC9C', width=3)),
        row=1, col=1
    )

    df['Decel_Top'] = df['Velocidad_kmh'] + np.abs(df['Deceleracion_ms2']) * 5

    fig_unificada.add_trace(
        go.Scatter(
            x=df['Tiempo_s'],
            y=df['Decel_Top'],
            fill='tonexty',
            fillcolor='rgba(231, 76, 60, 0.4)',
            line=dict(width=1, color='rgba(231, 76, 60, 0.6)'),
            name='Estrés Mecánico (m/s²)',
            customdata=df[['Deceleracion_ms2', 'Velocidad_kmh']],
            hovertemplate='Deceleración Máx: %{customdata[0]:.2f} m/s²<br>Velocidad: %{customdata[1]:.0f} km/h',
            showlegend=True
        ),
        row=1, col=1
    )

    df_frenado = df[df['Energia_Disipada_kJ'] > 0].copy()

    for tipo, color_hex in COLOR_MAP.items():
        df_segmento = df_frenado[df_frenado['Tipo_Frenado'] == tipo]

        if not df_segmento.empty:
            fig_unificada.add_trace(
                go.Scatter(x=df_segmento['Tiempo_s'], y=df_segmento['Energia_Disipada_kJ'], mode='markers',
                            name=tipo,
                            marker=dict(size=df_segmento['Energia_Disipada_kJ']/5,
                                        color=color_hex,
                                        sizemode='area', sizeref=2.*max(df_frenado['Energia_Disipada_kJ'])/(20.**2),
                                        sizemin=4, opacity=0.8),
                            legendgroup=tipo,
                            showlegend=True),
                row=2, col=1
            )

    fig_unificada.update_layout(height=650,
                                 title_text="Correlación Causa-Estrés-Efecto: Donde Frenaste vs. Cuanto Calor Generaste",
                                 legend=dict(tracegroupgap=0)
                                 )
    fig_unificada.update_yaxes(title_text="Velocidad (km/h)", row=1, col=1)
    fig_unificada.update_yaxes(title_text="Energía Disipada (kJ)", row=2, col=1)
    fig_unificada.update_xaxes(title_text="Tiempo (segundos)", row=2, col=1)

    st.plotly_chart(fig_unificada, use_container_width=True)

    st.markdown("---")

    # --- 6. TEXTO DE CONSECUENCIAS ---

    st.markdown(
    """
    Nuestro análisis se basa en la ley de **Conservación de la Energía**, donde cada frenada transforma energía cinética en calor. Esta acumulación de calor es la causa de la **Fatiga de Frenos** o *Fading*.

    El *Fading* es la pérdida de eficacia del sistema de frenos por sobrecalentamiento, lo que puede causar:
    1.  **Vapor Lock:** Ebullición del líquido de frenos.
    2.  **Alabeo de Disco:** Deformación por picos de temperatura.

    La **Deceleración** (Estrés Mecánico), representada por el **área sombreada en la gráfica superior**, se calcula como la variación de velocidad en el tiempo. Una sombra más grande y oscura significa **mayor esfuerzo aplicado** al sistema.
    """
)

    st.warning(
        f"""
        **VEREDICTO DE INGENIERÍA RONNIN:** El análisis térmico registra una **huella de fatiga de {energia_total_acumulada:.0f} kJ**.
        Este nivel de estrés acumulado, en conjunto con los picos de calor, invalida el intervalo estándar. Nuestra recomendación técnica es adelantar la
        **inspección de pastillas y alabeo de discos a 3.000 kilómetros**, en lugar del estándar de **6.000 km**.
        Su data exige una corrección: **la ingeniería supera al manual**.
        """
    )

    # ✅ CORRECCIÓN 5: Se elimina la línea que confunde al usuario con la promesa de "descargar el estudio"
    # st.markdown("Para acceder al análisis completo de riesgo de *vapor lock* y descargar el estudio de **3.000 km** vs. **6.000 km**, **vote por su próximo artículo de interés en el formulario inferior.**")

    st.markdown("---")


    # --- 7. Gráfica 3: Gradiente Térmico (Riesgo Ambiental) ---
    T_CRIT = 150
    st.markdown("## Análisis de Riesgo Ambiental: El Factor Vapor Lock")

    fig_t = px.line(
        df,
        x='Tiempo_s',
        y='Temperatura_Ambiente_C',
        title='Impacto del Clima: Descenso de Temperatura Ambiente durante el Viaje',
        labels={'Temperatura_Ambiente_C': 'Temperatura Ambiente (°C)', 'Tiempo_s': 'Tiempo (segundos)'},
        color_discrete_sequence=['#3498DB']
    )

    fig_t.add_hline(
        y=T_CRIT,
        line_dash="dash",
        line_color="#E74C3C",
        annotation_text="UMBRAL CRÍTICO DE VAPOR LOCK (150°C)",
        annotation_position="top right",
        annotation_font_color="#E74C3C"
    )

    fig_t.update_yaxes(range=[15, T_CRIT + 20])

    df_critico = df[df['Energia_Disipada_kJ'] > 0].copy()

    if not df_critico.empty:
        fig_t.add_trace(
            go.Scatter(
                x=df_critico['Tiempo_s'],
                y=[T_CRIT] * len(df_critico),
                mode='markers',
                name='Picos Críticos de Calor',
                marker=dict(size=15, symbol='star', color='#E74C3C', line=dict(width=1, color='Black')),
                text=df_critico['Energia_Disipada_kJ'].apply(lambda x: f'{x:.1f} kJ'),
                hovertemplate='Pico Crítico de Calor: %{text} @ Umbral de Riesgo',
                showlegend=True
            )
        )

    fig_t.update_layout(
        height=450,
        showlegend=True,
        legend=dict(
            yanchor="top", y=0.99, xanchor="left", x=0.01,
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(0,0,0,0)"
        )
    )
    st.plotly_chart(fig_t, use_container_width=True)

    st.info(
        f"""
        **DIAGNÓSTICO TÉRMICO:** El sistema opera en un **ambiente térmico favorable** ({temp_final:.1f} °C), confirmando que el ambiente no es el origen de la falla.
        Las **estrellas rojas** marcan picos de energía de **{energia_max:.1f} kJ**, suficientes para forzar el líquido de frenos contaminado más allá de su punto de ebullición húmedo de **150°C**,
        provocando *vapor lock*. La causa-raíz no es el clima; es la **ineficiencia térmica del compuesto de fricción**.
        """
    )

    st.divider()


# --- 8. CAPTURA DE LEADS Y VALIDACIÓN DE DEMANDA (GOOGLE FORMS - ENLACE) ---
st.markdown("## 🔥 DATA RIDER: Desbloquea el Próximo Reporte Crítico")
st.markdown(
    """
    **¿Qué esconde tu moto?** Tienes el poder de decidir nuestro próximo análisis profundo sobre fallas de potencia o puntos débiles. Vota por el tema que más te intriga.
    """
)

# Opciones de votación según el formulario de Google (image_fd5e4d.png)
st.markdown(
    """
    1.  **Falla Silenciosa:** Cómo el Calor de sus Frenadas Evapora el DOT 4 (Continuación Frenos) 🏍️
    2.  **Doble Vida:** Análisis de Aceite en Moto de Trabajo vs. Moto de Stunt (El Factor Aditivo Oculto) 💥
    3.  **El Corazón Oculto de la 2T:** Por qué la 'Panza' del Exhosto da Potencia (Análisis de Ondas) 🧪
    """
)

FORM_URL = "https://forms.gle/Hoifu4bfpN8581A4A"
st.markdown(
    f"""
    <div style="text-align: center; background-color: #34495E; padding: 15px; border-radius: 5px; margin-top: 30px;">
        <p style="color: white; font-weight: bold; margin: 0; font-size: 1.1em;">
            Si quieres votar por el próximo artículo, haz clic en el enlace:
        </p>
        <a href="{FORM_URL}" target="_blank" style="color: white; text-decoration: none; font-size: 1.3em;">
            <span style="border-bottom: 2px solid white; padding-bottom: 2px;">VOTAR Y ACCEDER A LOS INFORMES EXCLUSIVOS</span>
        </a>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("---")


# --- 9. PIE DE PÁGINA Y BRANDING ---

st.markdown(
    """
    <div style="text-align: center; margin-top: 20px; margin-bottom: 10px;">
        <p style="font-size: 1em; margin: 0;">Una iniciativa de <strong>Ronnin DataLab</strong> | Ingeniería de Precisión para Motocicletas.</p>
        <p style="font-size: 0.9em; color: #888; margin: 0;">Transformando la telemetría en mantenimiento inteligente.</p>
    </div>
    """,
    unsafe_allow_html=True
)