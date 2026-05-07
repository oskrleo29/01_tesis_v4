"""
script_seleccion_variables.py

Aplica el procedimiento formal de selección de variables descrito en la
Sección 5.5 del manuscrito. Para cada variable candidata calcula:

- Test de asociación con log_gastos_2025:
    * Categóricas: Kruskal-Wallis (p-valor)
    * Numéricas:   Spearman ponderado y Pearson ponderado
- Tamaño del efecto:
    * Categóricas: eta-cuadrado ponderado por FEX_C
    * Numéricas:   |rho| ponderado por FEX_C
- Representatividad:
    * N muestral mínimo por categoría
    * % poblacional expandido mínimo por categoría
- No redundancia:
    * VIF entre numéricas
    * V de Cramér entre pares de categóricas
- Disponibilidad operativa:
    * Marca manual (lista DISPONIBLES_EN_FORMULARIO)

Salida:
    - tabla_seleccion_variables.xlsx con la decisión por variable
    - Print en pantalla del resumen y de los pares redundantes detectados

Uso en el notebook (después de tener df_temp_a cargado):

    exec(open('script_seleccion_variables.py').read())

Autora: Paola Velandia
"""
import numpy as np
import pandas as pd
from scipy import stats
from itertools import combinations
from pathlib import Path


# ============================================================
# Helpers
# ============================================================
def _to_float(s):
    """Convierte a float manejando coma decimal."""
    return pd.to_numeric(
        s.astype(str).str.replace(',', '.', regex=False),
        errors='coerce'
    ).astype(float)


def media_ponderada(x, w):
    x = pd.to_numeric(x, errors='coerce').astype(float)
    w = pd.to_numeric(w, errors='coerce').astype(float)
    valid = ~(np.isnan(x) | np.isnan(w))
    if valid.sum() == 0:
        return np.nan
    return np.average(x[valid], weights=w[valid])


def correlacion_pearson_ponderada(x, y, w):
    """Pearson ponderado: cov(x,y;w) / (sd(x;w)·sd(y;w))."""
    x = np.asarray(pd.to_numeric(x, errors='coerce').astype(float))
    y = np.asarray(pd.to_numeric(y, errors='coerce').astype(float))
    w = np.asarray(pd.to_numeric(w, errors='coerce').astype(float))
    valid = ~(np.isnan(x) | np.isnan(y) | np.isnan(w))
    x, y, w = x[valid], y[valid], w[valid]
    if len(x) < 3:
        return np.nan
    mx = np.average(x, weights=w)
    my = np.average(y, weights=w)
    cov = np.average((x - mx) * (y - my), weights=w)
    sx = np.sqrt(np.average((x - mx) ** 2, weights=w))
    sy = np.sqrt(np.average((y - my) ** 2, weights=w))
    if sx == 0 or sy == 0:
        return np.nan
    return cov / (sx * sy)


def correlacion_spearman_ponderada(x, y, w):
    """Spearman ponderado = Pearson sobre rangos ponderados."""
    x = pd.Series(x).rank()
    y = pd.Series(y).rank()
    return correlacion_pearson_ponderada(x.values, y.values, w)


def eta_cuadrado_ponderado(grupo, valor, fex):
    """
    Eta-cuadrado ponderado por FEX_C.
    η² = SS_entre / SS_total (con pesos).
    """
    df_local = pd.DataFrame({'g': grupo, 'y': valor, 'w': fex}).dropna()
    df_local = df_local[df_local['w'] > 0]
    if df_local.empty or df_local['w'].sum() == 0:
        return np.nan
    media_global = np.average(df_local['y'], weights=df_local['w'])
    ss_total = np.sum(df_local['w'] * (df_local['y'] - media_global) ** 2)
    ss_entre = 0.0
    for _, sub in df_local.groupby('g'):
        sub = sub[sub['w'] > 0]
        if sub.empty:
            continue
        media_g = np.average(sub['y'], weights=sub['w'])
        peso_g = sub['w'].sum()
        ss_entre += peso_g * (media_g - media_global) ** 2
    if ss_total == 0:
        return np.nan
    return ss_entre / ss_total


def v_cramer(x, y):
    """V de Cramér: medida de asociación entre dos categóricas."""
    tabla = pd.crosstab(x, y)
    chi2 = stats.chi2_contingency(tabla, correction=False)[0]
    n = tabla.values.sum()
    r, k = tabla.shape
    denom = n * min(r - 1, k - 1)
    if denom == 0:
        return np.nan
    return float(np.sqrt(chi2 / denom))


def vif_simple(df_num):
    """VIF para cada variable numérica respecto del resto."""
    from sklearn.linear_model import LinearRegression
    out = {}
    for col in df_num.columns:
        X = df_num.drop(columns=[col]).values
        y = df_num[col].values
        valid = ~(np.isnan(X).any(axis=1) | np.isnan(y))
        if valid.sum() < 10:
            out[col] = np.nan
            continue
        modelo = LinearRegression().fit(X[valid], y[valid])
        r2 = modelo.score(X[valid], y[valid])
        out[col] = 1.0 / (1.0 - r2) if r2 < 0.999 else np.inf
    return out


# ============================================================
# Configuración del análisis
# ============================================================
TARGET = 'log_gastos_2025'
FEX = 'FEX_C'

# Umbrales de decisión
UMBRAL_P = 0.05
UMBRAL_ETA2 = 0.01
UMBRAL_RHO = 0.05
UMBRAL_N_MUE_CAT = 30
UMBRAL_N_POB_CAT_PCT = 0.5
UMBRAL_VIF = 10
UMBRAL_V_CRAMER = 0.8

# Variables disponibles en formulario crediticio
DISPONIBLES_EN_FORMULARIO = {
    'log_ingresos_2025', 'INGRESOS_AL_2025',
    'Edad', 'Sexo_', 'EstadoCivil_', 'Estrato', 'REGION', 'DOMINIO',
    'nivel_educ_agrupado', 'actividad_ppal', 'PersonasHogar',
    'Grupo_Aportantes', 'tipo_vivienda_agrup', 'Antiguedad_Actividad',
}

# Variables candidatas (se mantienen las que estén en df_temp_a)
CANDIDATAS_NUMERICAS = ['log_ingresos_2025', 'Edad', 'PersonasHogar']
CANDIDATAS_CATEGORICAS = [
    'Sexo_', 'EstadoCivil_', 'nivel_educ_agrupado', 'actividad_ppal',
    'Antiguedad_Actividad', 'Estrato', 'REGION', 'DOMINIO',
    'Grupo_Aportantes', 'tipo_vivienda_agrup',
]


# ============================================================
# Ejecución principal
# ============================================================
print('=' * 70)
print('SELECCIÓN DE VARIABLES — Sección 5.5 del manuscrito')
print('=' * 70)

# Convertir FEX_C
fex_norm = _to_float(df_temp_a[FEX])
n_total = len(df_temp_a)
n_exp_total = fex_norm.sum()
print(f'\nN muestral total:  {n_total:,}')
print(f'N expandido total: {n_exp_total:,.0f}')

filas_resumen = []

# ---------- VARIABLES NUMÉRICAS ----------
print('\n' + '-' * 70)
print('VARIABLES NUMÉRICAS')
print('-' * 70)

numericas_presentes = [c for c in CANDIDATAS_NUMERICAS if c in df_temp_a.columns]
y = pd.to_numeric(df_temp_a[TARGET], errors='coerce').astype(float).values

for var in numericas_presentes:
    x = pd.to_numeric(df_temp_a[var], errors='coerce').astype(float).values
    valid = ~(np.isnan(x) | np.isnan(y))

    rho_p = correlacion_pearson_ponderada(x, y, fex_norm.values)
    rho_s = correlacion_spearman_ponderada(x, y, fex_norm.values)

    # p-valor del test de Spearman (no ponderado, conservador con N grande)
    sp_stat, sp_p = stats.spearmanr(x[valid], y[valid])

    cumple_p = sp_p < UMBRAL_P
    cumple_efecto = abs(rho_s) >= UMBRAL_RHO
    cumple_disp = var in DISPONIBLES_EN_FORMULARIO

    decision = 'Incluir' if (cumple_p and cumple_efecto and cumple_disp) else 'Descartar'

    print(f'\n{var}:')
    print(f'  Spearman ρ ponderado : {rho_s:.4f}')
    print(f'  Pearson ρ ponderado  : {rho_p:.4f}')
    print(f'  p-valor (Spearman)   : {sp_p:.4g}')
    print(f'  Decisión             : {decision}')

    # Formateo del p-valor: con N grande es típicamente <1e-300 (underflow).
    # Reportar en notación científica o como "<0.001" para legibilidad.
    if np.isnan(sp_p):
        p_str = 'NaN'
    elif sp_p < 1e-300:
        p_str = '<1e-300'
    elif sp_p < 0.001:
        p_str = f'{sp_p:.2e}'
    else:
        p_str = f'{sp_p:.4f}'

    filas_resumen.append({
        'Variable': var,
        'Tipo': 'Numérica',
        'Test': 'Spearman',
        'p-valor': p_str,
        'Tamaño efecto': round(rho_s, 4),
        'Métrica efecto': '|ρ| Spearman pond.',
        'N representativo': 'OK' if valid.sum() >= UMBRAL_N_MUE_CAT else 'Bajo',
        'Disponible originación': 'Sí' if cumple_disp else 'No',
        'Decisión': decision,
    })

# VIF entre numéricas
print('\n--- VIF (multicolinealidad entre numéricas) ---')
df_num = df_temp_a[numericas_presentes].apply(pd.to_numeric, errors='coerce')
df_num = df_num.dropna()
vifs = vif_simple(df_num)
for v, val in vifs.items():
    flag = '⚠ alto' if val >= UMBRAL_VIF else 'OK'
    print(f'  {v:25s} VIF = {val:8.2f}  [{flag}]')

# ---------- VARIABLES CATEGÓRICAS ----------
print('\n' + '-' * 70)
print('VARIABLES CATEGÓRICAS')
print('-' * 70)

categoricas_presentes = [c for c in CANDIDATAS_CATEGORICAS if c in df_temp_a.columns]

for var in categoricas_presentes:
    grupo = df_temp_a[var]
    valor = pd.to_numeric(df_temp_a[TARGET], errors='coerce').astype(float)
    valid = ~(grupo.isna() | valor.isna() | fex_norm.isna())

    # Kruskal-Wallis
    grupos = [valor[valid][grupo[valid] == g].values
              for g in grupo[valid].unique() if (grupo[valid] == g).sum() >= 5]
    if len(grupos) >= 2:
        kw_stat, kw_p = stats.kruskal(*grupos)
    else:
        kw_stat, kw_p = np.nan, np.nan

    # Eta-cuadrado ponderado
    eta2 = eta_cuadrado_ponderado(grupo[valid], valor[valid], fex_norm[valid])

    # Representatividad
    n_por_cat = grupo[valid].value_counts()
    fex_por_cat = fex_norm[valid].groupby(grupo[valid]).sum()
    pct_pob_por_cat = fex_por_cat / n_exp_total * 100

    n_min_mue = n_por_cat.min()
    n_min_pob_pct = pct_pob_por_cat.min()

    repr_ok = (n_min_mue >= UMBRAL_N_MUE_CAT) and (n_min_pob_pct >= UMBRAL_N_POB_CAT_PCT)

    cumple_p = (not np.isnan(kw_p)) and (kw_p < UMBRAL_P)
    cumple_efecto = (not np.isnan(eta2)) and (eta2 >= UMBRAL_ETA2)
    cumple_disp = var in DISPONIBLES_EN_FORMULARIO

    decision = 'Incluir' if (cumple_p and cumple_efecto and cumple_disp) else 'Descartar'
    if cumple_p and cumple_efecto and cumple_disp and not repr_ok:
        decision = 'Agrupar categorías'

    print(f'\n{var}:')
    print(f'  Kruskal-Wallis p-valor : {kw_p:.4g}')
    print(f'  Eta-cuadrado ponderado : {eta2:.4f}')
    print(f'  N min muestral / cat   : {n_min_mue}')
    print(f'  % min poblacional / cat: {n_min_pob_pct:.2f}%')
    print(f'  Representatividad      : {"OK" if repr_ok else "agrupar"}')
    print(f'  Decisión               : {decision}')

    # Formateo del p-valor: con N grande es típicamente <1e-300 (underflow).
    if np.isnan(kw_p):
        p_str_kw = 'NaN'
    elif kw_p < 1e-300:
        p_str_kw = '<1e-300'
    elif kw_p < 0.001:
        p_str_kw = f'{kw_p:.2e}'
    else:
        p_str_kw = f'{kw_p:.4f}'

    filas_resumen.append({
        'Variable': var,
        'Tipo': 'Categórica',
        'Test': 'Kruskal-Wallis',
        'p-valor': p_str_kw,
        'Tamaño efecto': round(eta2, 4) if not np.isnan(eta2) else None,
        'Métrica efecto': 'η² ponderado',
        'N representativo': 'OK' if repr_ok else 'Agrupar',
        'Disponible originación': 'Sí' if cumple_disp else 'No',
        'Decisión': decision,
    })

# ---------- V de Cramér entre categóricas ----------
print('\n' + '-' * 70)
print('V de Cramér (redundancia entre pares de categóricas)')
print('-' * 70)
pares_redundantes = []
for v1, v2 in combinations(categoricas_presentes, 2):
    s1 = df_temp_a[v1].astype(str)
    s2 = df_temp_a[v2].astype(str)
    valid = ~(s1.isna() | s2.isna())
    if valid.sum() < 10:
        continue
    v = v_cramer(s1[valid], s2[valid])
    flag = '⚠ ALTO' if v >= UMBRAL_V_CRAMER else ''
    if v >= 0.5:
        print(f'  {v1:25s} ↔ {v2:25s} V = {v:.3f} {flag}')
    if v >= UMBRAL_V_CRAMER:
        pares_redundantes.append((v1, v2, v))

if pares_redundantes:
    print(f'\n⚠ {len(pares_redundantes)} pares con redundancia problemática (V ≥ {UMBRAL_V_CRAMER}):')
    for v1, v2, v in pares_redundantes:
        print(f'    {v1} ↔ {v2}: V = {v:.3f}')
    print('  Considerar mantener solo una de cada par.')

# ---------- Exportar tabla resumen ----------
df_resumen = pd.DataFrame(filas_resumen)
ruta_excel = Path.cwd() / 'tabla_seleccion_variables.xlsx'
df_resumen.to_excel(ruta_excel, index=False)

print('\n' + '=' * 70)
print('RESUMEN FINAL')
print('=' * 70)
print(df_resumen[['Variable', 'Tipo', 'p-valor', 'Tamaño efecto', 'Decisión']]
      .to_string(index=False))

print(f'\nTabla guardada en: {ruta_excel}')
print('Pegue los valores en los placeholders [W:XXX] de la Tabla 20 del manuscrito.')

# ---------- Recomendaciones operativas ----------
print('\n' + '=' * 70)
print('RECOMENDACIONES OPERATIVAS')
print('=' * 70)
incluidas = df_resumen[df_resumen['Decisión'] == 'Incluir']['Variable'].tolist()
descartadas = df_resumen[df_resumen['Decisión'] == 'Descartar']['Variable'].tolist()
agrupar = df_resumen[df_resumen['Decisión'] == 'Agrupar categorías']['Variable'].tolist()

print(f'Variables a INCLUIR en el modelo ({len(incluidas)}):')
for v in incluidas:
    print(f'  • {v}')

if agrupar:
    print(f'\nVariables que requieren AGRUPACIÓN previa ({len(agrupar)}):')
    for v in agrupar:
        print(f'  • {v}')

if descartadas:
    print(f'\nVariables a DESCARTAR ({len(descartadas)}):')
    for v in descartadas:
        print(f'  • {v}')

if pares_redundantes:
    print(f'\nResolver redundancia (mantener una sola por par):')
    for v1, v2, _ in pares_redundantes:
        print(f'  • {v1} ↔ {v2}')
