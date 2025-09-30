import pandas as pd
import numpy as np
import random

# --- 1. CONSTANTES DE INGENIERÍA (Valores típicos de una moto naked o sport) ---
MASA_TOTAL_KG = 300  # Masa moto (180kg) + Piloto (70kg) + Carga (50kg) = 300 kg
TIEMPO_TOTAL_S = 3600 # 60 minutos
INTERVALO_S = 1       # Tomar datos cada 1 segundo

# Constantes para la simulación de Gradiente Térmico
TEMP_INICIAL_C = 30.0  # Inicio en clima cálido (ej. valle)
TEMP_FINAL_C = 18.0    # Final en clima templado (ej. ascenso)
TEMP_DECREMENTO = (TEMP_INICIAL_C - TEMP_FINAL_C) / TIEMPO_TOTAL_S # Decremento por segundo

# Umbrales de Estrés (Para el análisis narrativo en Streamlit)
UMBRAL_DECELERACION_ALTA = -8.0  # Deceleración de emergencia (m/s²)
UMBRAL_ENERGIA_ALTA = 50.0      # Energía disipada alta por evento (kJ)
UMBRAL_ENERGIA_ACUMULADA_RIESGO = 300 # Energía acumulada en 5 min (kJ)


def generar_evento_frenado(df, start_time, initial_speed, final_speed, duration_s, tipo):
    """Genera una transición de frenado dentro del DataFrame."""

    # Asegurar que la velocidad inicial sea mayor que la final
    if initial_speed <= final_speed:
        final_speed = initial_speed * 0.1 # Simular una parada o reducción mínima

    end_time = start_time + duration_s

    # Crear un subconjunto de tiempo para el evento de frenado
    tiempo_segmento = df[(df['Tiempo_s'] >= start_time) & (df['Tiempo_s'] < end_time)]
    n_puntos = len(tiempo_segmento)

    if n_puntos == 0:
        return df

    # Generar la velocidad linealmente decreciente (simplificado)
    velocidades = np.linspace(initial_speed, final_speed, n_puntos)

    # Convertir km/h a m/s para cálculos físicos
    V_inicial_ms = initial_speed / 3.6
    V_final_ms = final_speed / 3.6

    # Calcular la Deceleración (m/s²)
    deceleracion_ms2 = (V_final_ms - V_inicial_ms) / duration_s

    # Calcular la Energía Disipada (en Joules)
    # Energía Disipada = 0.5 * Masa * (V_inicial_ms² - V_final_ms²)
    energia_disipada_J = 0.5 * MASA_TOTAL_KG * (V_inicial_ms**2 - V_final_ms**2)

    # Asignar los valores al DataFrame principal
    df.loc[tiempo_segmento.index, 'Velocidad_kmh'] = velocidades
    df.loc[tiempo_segmento.index, 'Deceleracion_ms2'] = deceleracion_ms2
    df.loc[tiempo_segmento.index, 'Energia_Disipada_kJ'] = energia_disipada_J / n_puntos / 1000 # Distribuir la Energía total en el tiempo del evento (en kJ)
    df.loc[tiempo_segmento.index, 'Tipo_Frenado'] = tipo

    return df

# --- 2. FUNCIÓN PRINCIPAL DE GENERACIÓN DE DATA ---
def generar_data_simulacion():
    # Inicializar el DataFrame
    data = {'Tiempo_s': np.arange(0, TIEMPO_TOTAL_S, INTERVALO_S),
            'Velocidad_kmh': 0.0,
            'Deceleracion_ms2': 0.0,
            'Energia_Disipada_kJ': 0.0,
            'Tipo_Frenado': 'Reposo',
            'Temperatura_Ambiente_C': 0.0} # Inicializamos en 0
    df = pd.DataFrame(data)

    # ******* NUEVO: Aplicar el gradiente térmico *******
    df['Temperatura_Ambiente_C'] = TEMP_INICIAL_C - (df['Tiempo_s'] * TEMP_DECREMENTO)

    tiempo_actual = 0

    # --- CICLO DE 60 MINUTOS DE CONDUCCIÓN SIMULADA ---
    eventos = [
        # 1. Uso Urbano Típico (Frenadas progresivas) - Inicio Cálido
        (300, 80, 50, 5, 'Progresivo'),
        (350, 70, 0, 4, 'Progresivo'),
        (700, 60, 40, 3, 'Suave'),
        (750, 50, 0, 3, 'Progresivo'),

        # 2. Frenada de Emergencia (Máximo Estrés) - Mitad del recorrido (aún templado)
        (1200, 100, 0, 3, 'Emergencia'),

        # 3. Uso en Autopista (Ascenso sostenido y frenada brusca)
        (1800, 120, 90, 2, 'Suave'),
        (2100, 130, 70, 3, 'Brusco'),
        (2400, 90, 0, 4, 'Progresivo'),

        # 4. Estrés Acumulado (Frenadas en colina/tráfico denso) - Final, más fresco
        (2800, 50, 30, 2, 'Brusco'),
        (2810, 40, 20, 2, 'Brusco'),
        (2820, 30, 0, 2, 'Emergencia'), # Frenadas consecutivas sin recuperación

        # 5. Evento final
        (3200, 80, 0, 5, 'Progresivo'),
    ]

    # Ejecutar los eventos de frenado
    for start, v_ini, v_fin, duracion, tipo in eventos:
        df = generar_evento_frenado(df, start, v_ini, v_fin, duracion, tipo)

    # Rellenar los períodos sin frenado (Velocidad de crucero aleatoria o reposo)
    df['Velocidad_kmh'] = df['Velocidad_kmh'].replace(0, np.nan)
    df['Velocidad_kmh'] = df['Velocidad_kmh'].fillna(method='ffill')
    df['Velocidad_kmh'] = df['Velocidad_kmh'].fillna(0)

    # Rellenar el tipo de frenado para no-frenado
    df['Tipo_Frenado'] = np.where(df['Deceleracion_ms2'] == 0, 'Crucero', df['Tipo_Frenado'])
    df.loc[df['Tiempo_s'] < eventos[0][0], 'Tipo_Frenado'] = 'Reposo'

    # Limpieza final de valores para Deceleracion y Energía
    df.loc[df['Deceleracion_ms2'] > 0, 'Deceleracion_ms2'] = 0
    df.loc[df['Deceleracion_ms2'].isnull(), 'Deceleracion_ms2'] = 0
    df.loc[df['Energia_Disipada_kJ'].isnull(), 'Energia_Disipada_kJ'] = 0
    df.loc[df['Energia_Disipada_kJ'] < 0, 'Energia_Disipada_kJ'] = 0

    return df

# --- 3. GUARDAR EL ARCHIVO ---
if __name__ == "__main__":
    df_simulacion = generar_data_simulacion()

    # Asegurar que el TIPO_FRENADO en 'Reposo' o 'Crucero' tenga 0 energía
    df_simulacion.loc[(df_simulacion['Tipo_Frenado'] == 'Reposo') | (df_simulacion['Tipo_Frenado'] == 'Crucero'), 'Energia_Disipada_kJ'] = 0

    # Guardar el resultado en formato CSV
    df_simulacion.to_csv('brake_data.csv', index=False)
    print("✅ Generación de data simulada con gradiente térmico completa.")
    print(f"Archivo 'brake_data.csv' creado con {len(df_simulacion)} puntos de datos.")