"""
script_descriptivos_ponderados.py

Calcula los estadísticos ponderados por FEX_C para todas las variables analizadas
en la sección 5.4 "Análisis descriptivo" de la tesis, y exporta a Excel para que
los valores reales se peguen en las tablas del documento corregido.

Uso en el notebook (después de tener df_temp_a cargado):

    exec(open('script_descriptivos_ponderados.py').read())

O bien, copia las celdas de este archivo en una celda del notebook.

Salida:
    - tablas_ponderadas.xlsx con una hoja por variable
    - resumen_divergencias.xlsx con la Tabla 19 (resumen final)
    - Print en pantalla del total expandido de la población objetivo

Autora: Paola Velandia
"""
import numpy as np
import pandas as pd


# ============================================================
# Helpers de estadística ponderada
# ============================================================
def media_ponderada(x, w):
    """Media ponderada estándar: Σ(x·w) / Σw"""
    x = pd.to_numeric(x, errors='coerce').astype(float)
    w = pd.to_numeric(w, errors='coerce').astype(float)
    valid = ~(np.isnan(x) | np.isnan(w))
    if valid.sum() == 0:
        return np.nan
    return np.average(x[valid], weights=w[valid])


def percentil_ponderado(x, w, q):
    """
    Percentil ponderado: ordena por x y acumula los pesos hasta alcanzar q.
    q = 0.5 para mediana.
    """
    x = pd.to_numeric(x, errors='coerce').astype(float).values
    w = pd.to_numeric(w, errors='coerce').astype(float).values
    valid = ~(np.isnan(x) | np.isnan(w))
    x, w = x[valid], w[valid]
    if len(x) == 0:
        return np.nan
    idx = np.argsort(x)
    x_s, w_s = x[idx], w[idx]
    cw = np.cumsum(w_s) / w_s.sum()
    i = np.searchsorted(cw, q)
    return x_s[min(i, len(x_s) - 1)]


def mediana_ponderada(x, w):
    return percentil_ponderado(x, w, 0.5)


def iqr_ponderado(x, w):
    return percentil_ponderado(x, w, 0.75) - percentil_ponderado(x, w, 0.25)


def safe_round(x, ndigits=0):
    """round() que tolera np.nan y pd.NA (nullable pandas dtypes)."""
    try:
        if pd.isna(x):
            return np.nan
    except (TypeError, ValueError):
        pass
    try:
        return round(float(x), ndigits)
    except (TypeError, ValueError):
        return np.nan


# ============================================================
# Resumen ponderado por categoría de una variable
# ============================================================
def resumen_categoria(df, col_cat, col_fex='FEX_C',
                       col_ingreso='INGRESOS_AL_2025',
                       col_gasto='GASTOS_AL_2025'):
    """
    Para cada categoría de col_cat, devuelve:
    N muestra, N expandido, % muestra, % expandido,
    medianas e ingresos/gastos en plano muestral y expandido,
    diferencia en puntos porcentuales.
    """
    df = df.copy()
    df[col_fex] = pd.to_numeric(
        df[col_fex].astype(str).str.replace(',', '.', regex=False),
        errors='coerce'
    ).astype(float)
    n_total = len(df)
    n_exp_total = df[col_fex].sum()

    out = []
    for cat, grupo in df.groupby(col_cat):
        n_mue = len(grupo)
        n_exp = grupo[col_fex].sum()
        out.append({
            'Categoría': cat,
            'N muestra': n_mue,
            'N expandido': safe_round(n_exp),
            '% muestra': safe_round(n_mue / n_total * 100, 2),
            '% expandido': safe_round(n_exp / n_exp_total * 100, 2),
            'Δ pp (exp - mue)': safe_round(n_exp / n_exp_total * 100 - n_mue / n_total * 100, 2),
            'Ingreso media muestra': safe_round(grupo[col_ingreso].mean()),
            'Ingreso media expandida': safe_round(media_ponderada(grupo[col_ingreso], grupo[col_fex])),
            'Ingreso mediana muestra': safe_round(grupo[col_ingreso].median()),
            'Ingreso mediana expandida': safe_round(mediana_ponderada(grupo[col_ingreso], grupo[col_fex])),
            'Gasto mediana muestra': safe_round(grupo[col_gasto].median()),
            'Gasto mediana expandida': safe_round(mediana_ponderada(grupo[col_gasto], grupo[col_fex])),
        })
    return pd.DataFrame(out)


def resumen_categoria_log(df, col_cat, col_fex='FEX_C',
                           col_log_gasto='log_gastos_2025',
                           col_log_ingreso='log_ingresos_2025'):
    """Versión en logs para variables territoriales (Tabla 17, 18, 19, 20)."""
    df = df.copy()
    df[col_fex] = pd.to_numeric(
        df[col_fex].astype(str).str.replace(',', '.', regex=False),
        errors='coerce'
    ).astype(float)
    n_total = len(df); n_exp_total = df[col_fex].sum()
    out = []
    for cat, grupo in df.groupby(col_cat):
        n_mue = len(grupo); n_exp = grupo[col_fex].sum()
        out.append({
            'Categoría': cat,
            'N muestra': n_mue,
            'N expandido': safe_round(n_exp),
            '% muestra': safe_round(n_mue / n_total * 100, 2),
            '% expandido': safe_round(n_exp / n_exp_total * 100, 2),
            'Δ pp': safe_round(n_exp / n_exp_total * 100 - n_mue / n_total * 100, 2),
            'Mediana log gasto muestra': safe_round(grupo[col_log_gasto].median(), 2),
            'Mediana log gasto expandida': safe_round(mediana_ponderada(grupo[col_log_gasto], grupo[col_fex]), 2),
            'IQR log gasto muestra': safe_round(grupo[col_log_gasto].quantile(0.75) - grupo[col_log_gasto].quantile(0.25), 2),
            'IQR log gasto expandida': safe_round(iqr_ponderado(grupo[col_log_gasto], grupo[col_fex]), 2),
        })
    return pd.DataFrame(out)


# ============================================================
# Generar todas las tablas de la Sección 5.4
# ============================================================
print('=' * 60)
print('TABLAS PONDERADAS POR FEX_C — Sección 5.4 de la tesis')
print('=' * 60)

# Total expandido de la población objetivo
total_exp = pd.to_numeric(
    df_temp_a['FEX_C'].astype(str).str.replace(',', '.', regex=False),
    errors='coerce'
).astype(float).sum()
print(f'\nTotal expandido de la población objetivo (aportantes): {total_exp:,.0f}')

variables_a_analizar = {
    # Variable categórica → nombre de la columna en df_temp_a
    'nivel_academico': 'nivel_educ_agrupado',
    'actividad_economica': 'actividad_ppal',
    'rango_edad': 'rango_edad' if 'rango_edad' in df_temp_a.columns else None,
    'sexo': 'Sexo_',
    'estado_civil': 'EstadoCivil_' if 'EstadoCivil_' in df_temp_a.columns else 'Estado_Civil',
    'estrato': 'Estrato',
    'aportantes_hogar': 'Grupo_Aportantes' if 'Grupo_Aportantes' in df_temp_a.columns else None,
    'region': 'REGION',
    'tipo_vivienda': 'tipo_vivienda_agrup' if 'tipo_vivienda_agrup' in df_temp_a.columns else None,
}

# Generar tablas y guardar en Excel
import openpyxl
from openpyxl.styles import Font, Alignment

writer = pd.ExcelWriter(
    r'C:\Users\geros\OneDrive\Desktop\01_tesis_v4\tablas_ponderadas.xlsx',
    engine='openpyxl'
)

resumen_divergencias = []

for nombre, col in variables_a_analizar.items():
    if col is None or col not in df_temp_a.columns:
        print(f'  - {nombre}: columna no disponible, saltando')
        continue
    print(f'\n--- {nombre} (columna: {col}) ---')
    if nombre in ('region',):
        tabla = resumen_categoria_log(df_temp_a, col)
    else:
        tabla = resumen_categoria(df_temp_a, col)
    print(tabla.to_string(index=False))
    tabla.to_excel(writer, sheet_name=nombre[:31], index=False)

    # Para la tabla resumen final
    if 'Δ pp' in tabla.columns or 'Δ pp (exp - mue)' in tabla.columns:
        col_delta = 'Δ pp' if 'Δ pp' in tabla.columns else 'Δ pp (exp - mue)'
        idx_max = tabla[col_delta].abs().idxmax()
        resumen_divergencias.append({
            'Variable': nombre,
            'Categoría con mayor divergencia': tabla.loc[idx_max, 'Categoría'],
            '% muestra': tabla.loc[idx_max, '% muestra'],
            '% expandido': tabla.loc[idx_max, '% expandido'],
            'Diferencia (pp)': tabla.loc[idx_max, col_delta],
        })

# Tabla resumen (Tabla 19 del documento corregido)
df_resumen = pd.DataFrame(resumen_divergencias).sort_values('Diferencia (pp)',
                                                              key=lambda s: s.abs(),
                                                              ascending=False)
df_resumen.to_excel(writer, sheet_name='resumen_divergencias', index=False)

writer.close()
print('\n' + '=' * 60)
print('TABLA 19 — RESUMEN DE DIVERGENCIAS MUESTRA-VS-EXPANDIDO')
print('=' * 60)
print(df_resumen.to_string(index=False))

print('\n' + '=' * 60)
print('Tablas guardadas en: tablas_ponderadas.xlsx')
print('Una hoja por variable + hoja resumen_divergencias para la Tabla 19')
print('=' * 60)
print('\nPróximo paso: copia los valores desde el Excel a las celdas [W:XXX]')
print('del documento Comprension_datos_corregido.docx')
