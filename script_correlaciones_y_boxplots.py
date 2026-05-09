<<<<<<< HEAD
"""
=======
﻿"""
>>>>>>> 8d00cf621d9cf7468b3d289a111d5837cb1310ec
script_correlaciones_y_boxplots.py

Complementa el análisis descriptivo de la Sección 5 con dos componentes que
faltaban en la versión inicial y que el rigor metodológico de la tesis exige:

1. Matriz de correlaciones ponderada por FEX_C (Pearson y Spearman) entre las
   variables numéricas candidatas, exportada como heatmap y como Excel.
2. Boxplots ponderados por FEX_C para las variables categóricas, en
   sustitución de los boxplots muestrales que matplotlib/seaborn producen por
   defecto (matplotlib.boxplot y seaborn.boxplot NO admiten sample_weight).

Salida:
    - matriz_correlaciones_ponderada.xlsx con dos hojas (Pearson, Spearman).
    - figuras/correlaciones_heatmap.png — visualización de la matriz.
    - figuras/boxplot_<variable>.png — boxplot ponderado por FEX_C para cada
      variable categórica analizada.

Uso en el notebook (después de tener df_temp_a cargado):

    exec(open('script_correlaciones_y_boxplots.py').read())

Autora: Paola Velandia
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from pathlib import Path


# ============================================================
# Helpers ponderados
# ============================================================
def _to_float(s):
    return pd.to_numeric(
        pd.Series(s).astype(str).str.replace(',', '.', regex=False),
        errors='coerce'
    ).astype(float)


def percentil_ponderado(x, w, q):
    """Percentil ponderado: ordena por x y acumula los pesos hasta alcanzar q."""
    x = _to_float(x).values
    w = _to_float(w).values
    valid = ~(np.isnan(x) | np.isnan(w)) & (w > 0)
    x, w = x[valid], w[valid]
    if len(x) == 0:
        return np.nan
    idx = np.argsort(x)
    x_s, w_s = x[idx], w[idx]
    cw = np.cumsum(w_s) / w_s.sum()
    if isinstance(q, (list, tuple, np.ndarray)):
        return [x_s[min(np.searchsorted(cw, qi), len(x_s) - 1)] for qi in q]
    return x_s[min(np.searchsorted(cw, q), len(x_s) - 1)]


def correlacion_pearson_ponderada(x, y, w):
    """Pearson ponderado: cov(x,y;w) / (sd(x;w)·sd(y;w))."""
    x = np.asarray(_to_float(x))
    y = np.asarray(_to_float(y))
    w = np.asarray(_to_float(w))
    valid = ~(np.isnan(x) | np.isnan(y) | np.isnan(w)) & (w > 0)
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
    """Spearman ponderado = Pearson sobre rangos."""
    rx = pd.Series(x).rank().values
    ry = pd.Series(y).rank().values
    return correlacion_pearson_ponderada(rx, ry, w)


def matriz_correlaciones_ponderada(df, columnas, fex, metodo='pearson'):
    """Devuelve un DataFrame con la matriz de correlación ponderada."""
    fn = correlacion_pearson_ponderada if metodo == 'pearson' else correlacion_spearman_ponderada
    n = len(columnas)
    M = np.full((n, n), np.nan)
    for i, c1 in enumerate(columnas):
        for j, c2 in enumerate(columnas):
            if i == j:
                M[i, j] = 1.0
            elif j > i:
                M[i, j] = fn(df[c1], df[c2], fex)
                M[j, i] = M[i, j]
    return pd.DataFrame(M, index=columnas, columns=columnas)


# ============================================================
# Configuración
# ============================================================
TARGET = 'log_gastos_2025'
FEX = 'FEX_C'

VARIABLES_NUMERICAS = [
<<<<<<< HEAD
    'log_ingresos_2025', 'log_gastos_2025', 'Edad', 'Aportantes_Hogar',
=======
    'log_ingresos_2025', 'log_gastos_2025', 'Edad', 'PersonasHogar',
>>>>>>> 8d00cf621d9cf7468b3d289a111d5837cb1310ec
    'log_ratio_ingreso',
]

VARIABLES_CATEGORICAS_BOXPLOT = [
    'nivel_educ_agrupado', 'actividad_ppal', 'Sexo_', 'EstadoCivil_',
    'Estrato', 'DOMINIO', 'Grupo_Aportantes', 'tipo_vivienda_agrup',
]

DIR_FIG = Path.cwd() / 'figuras'
DIR_FIG.mkdir(exist_ok=True)


# ============================================================
# 1. MATRIZ DE CORRELACIONES PONDERADA
# ============================================================
print('=' * 70)
print('1. MATRIZ DE CORRELACIONES PONDERADA POR FEX_C')
print('=' * 70)

fex_norm = _to_float(df_temp_a[FEX])
numericas_presentes = [c for c in VARIABLES_NUMERICAS if c in df_temp_a.columns]

print(f'\nVariables numéricas analizadas: {numericas_presentes}')

mat_pearson = matriz_correlaciones_ponderada(df_temp_a, numericas_presentes, fex_norm,
                                              metodo='pearson')
mat_spearman = matriz_correlaciones_ponderada(df_temp_a, numericas_presentes, fex_norm,
                                               metodo='spearman')

print('\n--- Matriz Pearson ponderada ---')
print(mat_pearson.round(3).to_string())
print('\n--- Matriz Spearman ponderada ---')
print(mat_spearman.round(3).to_string())

# Exportar a Excel
ruta_xlsx = Path.cwd() / 'matriz_correlaciones_ponderada.xlsx'
with pd.ExcelWriter(ruta_xlsx, engine='openpyxl') as w:
    mat_pearson.to_excel(w, sheet_name='Pearson_ponderada')
    mat_spearman.to_excel(w, sheet_name='Spearman_ponderada')
print(f'\nMatrices guardadas en: {ruta_xlsx}')


# Heatmap
def heatmap(df_corr, titulo, ruta):
    fig, ax = plt.subplots(figsize=(8, 6.5), dpi=150)
    im = ax.imshow(df_corr.values, vmin=-1, vmax=1, cmap='RdBu_r', aspect='auto')
    ax.set_xticks(range(len(df_corr)))
    ax.set_xticklabels(df_corr.columns, rotation=45, ha='right', fontsize=9)
    ax.set_yticks(range(len(df_corr)))
    ax.set_yticklabels(df_corr.index, fontsize=9)
    ax.set_title(titulo, fontsize=11, pad=12)

    # Anotar valores en cada celda
    for i in range(len(df_corr)):
        for j in range(len(df_corr)):
            v = df_corr.values[i, j]
            color = 'white' if abs(v) > 0.5 else 'black'
            ax.text(j, i, f'{v:.2f}', ha='center', va='center',
                    color=color, fontsize=8)

    cb = fig.colorbar(im, ax=ax, shrink=0.8)
    cb.set_label('rho', rotation=0, labelpad=10)
    fig.tight_layout()
    fig.savefig(ruta, dpi=200, bbox_inches='tight')
    plt.close(fig)
    print(f'  Heatmap guardado: {ruta}')


heatmap(mat_pearson, 'Matriz de correlaciones Pearson ponderada por FEX_C',
        DIR_FIG / 'correlaciones_pearson.png')
heatmap(mat_spearman, 'Matriz de correlaciones Spearman ponderada por FEX_C',
        DIR_FIG / 'correlaciones_spearman.png')


# ============================================================
# 2. BOXPLOTS PONDERADOS POR FEX_C
# ============================================================
print('\n' + '=' * 70)
print('2. BOXPLOTS PONDERADOS POR FEX_C')
print('=' * 70)
print('Sustituyen los boxplots muestrales (matplotlib/seaborn no admiten')
print('sample_weight nativamente).')


def boxplot_ponderado(df, var_cat, var_y, fex, titulo=None, ruta=None,
                      figsize=(9, 5.5), color_caja='#4A7BB7'):
    """
    Construye un boxplot manual usando percentiles ponderados por FEX_C.
    Muestra: P10 (bigote inf), P25 (caja), P50 (línea mediana), P75 (caja),
    P90 (bigote sup). N muestral y N expandido en eje x.
    """
    grupos = df[var_cat].dropna().unique()
    grupos = sorted(grupos, key=lambda x: str(x))

    datos_grupo = []
    etiquetas = []
    for g in grupos:
        mask = df[var_cat] == g
        x = df.loc[mask, var_y]
        w = fex[mask]
        valid = (~x.isna()) & (~w.isna()) & (w > 0)
        if valid.sum() < 5:
            continue
        x_v, w_v = x[valid].values, w[valid].values
        p10, p25, p50, p75, p90 = percentil_ponderado(x_v, w_v,
                                                       [0.10, 0.25, 0.50, 0.75, 0.90])
        datos_grupo.append({
            'grupo': str(g),
            'p10': p10, 'p25': p25, 'p50': p50, 'p75': p75, 'p90': p90,
            'n_mue': int(valid.sum()),
            'n_exp': int(w_v.sum()),
        })
        etiquetas.append(f'{g}\nn={int(valid.sum()):,}\nN={int(w_v.sum()):,}')

    fig, ax = plt.subplots(figsize=figsize, dpi=150)

    width = 0.6
    for i, d in enumerate(datos_grupo):
        # Bigotes
        ax.plot([i, i], [d['p10'], d['p90']], color='black', linewidth=1, zorder=2)
        # Bigotes superior e inferior (capuchones)
        ax.plot([i - 0.15, i + 0.15], [d['p10'], d['p10']], color='black', lw=1)
        ax.plot([i - 0.15, i + 0.15], [d['p90'], d['p90']], color='black', lw=1)
        # Caja (P25 a P75)
        rect = Rectangle((i - width / 2, d['p25']), width, d['p75'] - d['p25'],
                         facecolor=color_caja, edgecolor='black', linewidth=1, zorder=3)
        ax.add_patch(rect)
        # Mediana
        ax.plot([i - width / 2, i + width / 2], [d['p50'], d['p50']],
                color='white', linewidth=2, zorder=4)

    ax.set_xticks(range(len(datos_grupo)))
    ax.set_xticklabels(etiquetas, fontsize=8, rotation=0)
    ax.set_ylabel(var_y)
    ax.set_xlabel(var_cat)
    ax.set_title(titulo or f'Boxplot ponderado por FEX_C — {var_y} por {var_cat}',
                 fontsize=11)
    ax.grid(True, axis='y', alpha=0.3)

    # Nota metodológica
    fig.text(0.5, -0.02,
             'Caja = P25-P75 ponderado por FEX_C; línea blanca = mediana ponderada (P50); '
             'bigotes = P10-P90 ponderado.\n'
             'n = registros muestrales; N = personas representadas (FEX_C).\n'
             'Fuente: cálculos propios con base en ENPH 2016-2017, DANE.',
             ha='center', fontsize=8, style='italic')

    fig.tight_layout()
    if ruta:
        fig.savefig(ruta, dpi=200, bbox_inches='tight')
        plt.close(fig)
        print(f'  Boxplot {var_cat}: {ruta}')
    else:
        plt.show()
    return fig


# Generar boxplots para cada variable categórica
categoricas_presentes = [c for c in VARIABLES_CATEGORICAS_BOXPLOT
                         if c in df_temp_a.columns]

for var in categoricas_presentes:
    ruta = DIR_FIG / f'boxplot_{var}_log_gasto.png'
    boxplot_ponderado(
        df_temp_a, var, TARGET, fex_norm,
        titulo=f'Distribución del log_gastos_2025 por {var} (ponderada por FEX_C)',
        ruta=ruta,
    )

# También boxplots para el ratio gasto/ingreso
if 'log_ratio_ingreso' in df_temp_a.columns:
    print('\n--- Boxplots del log_ratio_ingreso ---')
    for var in categoricas_presentes:
        ruta = DIR_FIG / f'boxplot_{var}_log_ratio.png'
        boxplot_ponderado(
            df_temp_a, var, 'log_ratio_ingreso', fex_norm,
            titulo=f'Distribución del log_ratio_ingreso por {var} (ponderada por FEX_C)',
            ruta=ruta,
        )

print('\n' + '=' * 70)
print('FIN — Archivos generados:')
print('=' * 70)
print(f'  • {ruta_xlsx}')
print(f'  • {DIR_FIG}/correlaciones_pearson.png')
print(f'  • {DIR_FIG}/correlaciones_spearman.png')
print(f'  • {DIR_FIG}/boxplot_<variable>_log_gasto.png  (×{len(categoricas_presentes)})')
if 'log_ratio_ingreso' in df_temp_a.columns:
    print(f'  • {DIR_FIG}/boxplot_<variable>_log_ratio.png  (×{len(categoricas_presentes)})')
print('\nProximo paso: incorporar las figuras al manuscrito en lugar de las versiones')
print('actuales (no ponderadas) y citar la matriz de correlaciones en la nueva')
print('Sub-sección 5.5.10 del documento Comprension_datos_corregido.docx.')
