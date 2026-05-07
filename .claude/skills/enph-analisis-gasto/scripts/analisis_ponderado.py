"""
Tabulados y análisis ponderados por FEX_C, en el estilo del notebook
Proyecto_gasto_personal_2026_tesis.ipynb.

Uso típico:
    from analisis_ponderado import (
        descriptivo_ponderado, comparar_muestral_vs_expandido,
        wls_ponderado, kmeans_ponderado, validar_clusters,
        cv_ponderada, ridge_lasso_comparacion
    )

Convenciones:
    - df: DataFrame con columna FEX_C (factor de expansión a nivel persona).
    - Las funciones devuelven DataFrames listos para imprimir o exportar a docx.
    - El target por defecto es 'log_gastos_2025'; los pesos se normalizan
      dividiendo por la media (fex_c_norm), igual que en el notebook.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression, RidgeCV, LassoCV
from sklearn.model_selection import KFold
from sklearn.metrics import (
    r2_score, mean_absolute_error, mean_squared_error, silhouette_score
)
from sklearn.base import clone
from sklearn.pipeline import Pipeline


SEED = 42


# ============================================================
# Descriptivos ponderados
# ============================================================
def normalizar_fex(df: pd.DataFrame, col_fex: str = 'FEX_C') -> np.ndarray:
    """
    Normaliza el factor de expansión dividiéndolo por su media.
    Replica el patrón del notebook: fex_c_norm = fex_c_raw / fex_c_raw.mean().
    """
    fex_raw = pd.to_numeric(
        df[col_fex].astype(str).str.replace(',', '.', regex=False),
        errors='coerce'
    ).astype(float)
    return (fex_raw / fex_raw.mean()).values


def descriptivo_ponderado(df: pd.DataFrame,
                          variables: list[str],
                          col_fex: str = 'FEX_C') -> pd.DataFrame:
    """
    Devuelve estadísticos descriptivos ponderados (media, mediana, desviación,
    percentiles 25/75/90) para cada variable numérica.
    """
    fex = pd.to_numeric(df[col_fex], errors='coerce').astype(float).values
    out = []
    for var in variables:
        x = pd.to_numeric(df[var], errors='coerce').astype(float).values
        valid = ~(np.isnan(x) | np.isnan(fex))
        x_v, w_v = x[valid], fex[valid]
        media = np.average(x_v, weights=w_v)
        # Percentiles ponderados manualmente
        idx = np.argsort(x_v)
        x_s, w_s = x_v[idx], w_v[idx]
        cw = np.cumsum(w_s) / w_s.sum()
        pcts = {}
        for q in [0.25, 0.50, 0.75, 0.90]:
            i = np.searchsorted(cw, q)
            pcts[f'p{int(q*100)}'] = x_s[min(i, len(x_s)-1)]
        var_w = np.average((x_v - media)**2, weights=w_v)
        std = np.sqrt(var_w)
        out.append({
            'variable': var,
            'media_p': media,
            'mediana_p': pcts['p50'],
            'std_p': std,
            'p25': pcts['p25'],
            'p75': pcts['p75'],
            'p90': pcts['p90'],
            'n_muestra': int(valid.sum()),
            'n_expandido': float(w_v.sum()),
        })
    return pd.DataFrame(out)


def comparar_muestral_vs_expandido(df: pd.DataFrame,
                                    variables: list[str],
                                    col_fex: str = 'FEX_C') -> pd.DataFrame:
    """
    Crea una tabla con dos planos paralelos: muestral y poblacional (expandido).
    Útil para la sección 5.3 "Análisis descriptivo" de la tesis.
    """
    pond = descriptivo_ponderado(df, variables, col_fex)
    out = []
    for var in variables:
        x = pd.to_numeric(df[var], errors='coerce').astype(float)
        out.append({
            'variable': var,
            'media_muestral': x.mean(),
            'mediana_muestral': x.median(),
            'std_muestral': x.std(),
            'n_muestra': int(x.notna().sum()),
        })
    muestral = pd.DataFrame(out)
    return muestral.merge(pond[['variable', 'media_p', 'mediana_p', 'std_p', 'n_expandido']],
                          on='variable')


# ============================================================
# Modelo WLS ponderado por FEX_C
# ============================================================
def wls_ponderado(df: pd.DataFrame,
                  preprocess,  # ColumnTransformer ya ajustado o por ajustar
                  features: list[str],
                  target: str = 'log_gastos_2025',
                  col_fex: str = 'FEX_C',
                  test_size: float = 0.20,
                  random_state: int = SEED):
    """
    Ajusta una regresión lineal ponderada por FEX_C usando sklearn,
    replicando el patrón del notebook (modelo principal).

    Devuelve dict con: model, X_train, X_test, y_train, y_test, métricas.
    """
    from sklearn.model_selection import train_test_split

    X = df[features].copy()
    y = df[target].copy()
    fex_norm = normalizar_fex(df, col_fex)

    X_train, X_test, y_train, y_test, w_train, w_test = train_test_split(
        X, y, fex_norm,
        test_size=test_size,
        random_state=random_state
    )

    pipe = Pipeline([
        ('prep', clone(preprocess)),
        ('model', LinearRegression())
    ])
    pipe.fit(X_train, y_train, model__sample_weight=w_train)

    y_train_pred = pipe.predict(X_train)
    y_test_pred = pipe.predict(X_test)

    metricas = {
        'r2_train': r2_score(y_train, y_train_pred),
        'r2_test': r2_score(y_test, y_test_pred),
        'mae_train': mean_absolute_error(y_train, y_train_pred),
        'mae_test': mean_absolute_error(y_test, y_test_pred),
        'rmse_train': np.sqrt(mean_squared_error(y_train, y_train_pred)),
        'rmse_test': np.sqrt(mean_squared_error(y_test, y_test_pred)),
    }
    metricas['error_pct_aprox'] = (np.exp(metricas['mae_test']) - 1) * 100

    return {
        'model': pipe,
        'X_train': X_train, 'X_test': X_test,
        'y_train': y_train, 'y_test': y_test,
        'w_train': w_train, 'w_test': w_test,
        'fex_norm': fex_norm,
        'metricas': metricas,
    }


def cv_ponderada(df: pd.DataFrame,
                 preprocess,
                 features: list[str],
                 target: str = 'log_gastos_2025',
                 col_fex: str = 'FEX_C',
                 n_splits: int = 5,
                 random_state: int = SEED) -> dict:
    """
    K-fold CV con sample_weight=fex_c_norm en cada fold.
    Replica la celda 114 del notebook.
    """
    X = df[features]
    y = df[target]
    fex_norm = normalizar_fex(df, col_fex)

    cv = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    r2s, rmses = [], []
    for tr_idx, val_idx in cv.split(X):
        X_tr, X_val = X.iloc[tr_idx], X.iloc[val_idx]
        y_tr, y_val = y.iloc[tr_idx], y.iloc[val_idx]
        w_tr = fex_norm[tr_idx]
        pipe = Pipeline([('prep', clone(preprocess)),
                         ('model', LinearRegression())])
        pipe.fit(X_tr, y_tr, model__sample_weight=w_tr)
        y_pred = pipe.predict(X_val)
        r2s.append(r2_score(y_val, y_pred))
        rmses.append(np.sqrt(mean_squared_error(y_val, y_pred)))
    return {
        'r2_cv_mean': np.mean(r2s), 'r2_cv_std': np.std(r2s),
        'rmse_cv_mean': np.mean(rmses), 'rmse_cv_std': np.std(rmses),
        'r2s': r2s, 'rmses': rmses,
    }


def ridge_lasso_comparacion(df: pd.DataFrame,
                             preprocess,
                             features: list[str],
                             target: str = 'log_gastos_2025',
                             col_fex: str = 'FEX_C',
                             alphas: list[float] | None = None,
                             cv: int = 5,
                             random_state: int = SEED) -> pd.DataFrame:
    """
    Compara OLS, WLS, Ridge y Lasso en una tabla.
    Útil para profundizar el Anexo F.
    """
    if alphas is None:
        alphas = np.logspace(-3, 2, 30).tolist()

    X = df[features]
    y = df[target]
    fex_norm = normalizar_fex(df, col_fex)

    modelos = {
        'OLS': LinearRegression(),
        'WLS': LinearRegression(),
        'Ridge': RidgeCV(alphas=alphas, cv=cv),
        'Lasso': LassoCV(alphas=alphas, cv=cv, random_state=random_state, max_iter=20000),
    }

    resultados = []
    for nombre, est in modelos.items():
        pipe = Pipeline([('prep', clone(preprocess)), ('model', est)])
        if nombre in ('WLS',):
            pipe.fit(X, y, model__sample_weight=fex_norm)
        else:
            pipe.fit(X, y)
        y_pred = pipe.predict(X)
        r2 = r2_score(y, y_pred)
        rmse = np.sqrt(mean_squared_error(y, y_pred))
        alpha = getattr(pipe.named_steps['model'], 'alpha_', np.nan)
        resultados.append({
            'modelo': nombre,
            'alpha_optimo': alpha,
            'r2_in_sample': r2,
            'rmse_in_sample': rmse,
        })
    return pd.DataFrame(resultados)


# ============================================================
# K-Means ponderado
# ============================================================
def kmeans_ponderado(X_cluster: np.ndarray,
                     fex_norm: np.ndarray,
                     n_clusters: int = 4,
                     n_init: int = 30,
                     random_state: int = SEED) -> KMeans:
    """K-Means con sample_weight, igual que celda 136 del notebook."""
    km = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=n_init)
    km.fit(X_cluster, sample_weight=fex_norm)
    return km


def validar_clusters(X_cluster: np.ndarray,
                     fex_norm: np.ndarray,
                     n_clusters: int = 4,
                     n_sil: int = 8000,
                     random_state: int = SEED) -> dict:
    """
    Calcula silhouette en muestra ponderada (subsample proporcional al peso),
    Calinski-Harabasz y Davies-Bouldin. Replica el patrón de celda 136.
    """
    from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score

    km = kmeans_ponderado(X_cluster, fex_norm, n_clusters=n_clusters, random_state=random_state)
    labels = km.predict(X_cluster)

    np.random.seed(random_state)
    n_sil = min(n_sil, X_cluster.shape[0])
    probs = fex_norm / fex_norm.sum()
    idx = np.random.choice(X_cluster.shape[0], size=n_sil, replace=False, p=probs)

    labels_sub = km.predict(X_cluster[idx])
    metricas = {
        'silhouette': silhouette_score(X_cluster[idx], labels_sub),
        'calinski_harabasz': calinski_harabasz_score(X_cluster, labels),
        'davies_bouldin': davies_bouldin_score(X_cluster, labels),
        'inertia_w': km.inertia_,
    }
    return metricas


def estabilidad_clusters(X_cluster: np.ndarray,
                          fex_norm: np.ndarray,
                          n_clusters: int = 4,
                          n_seeds: int = 10) -> float:
    """
    Mide estabilidad del clustering con ARI promedio entre semillas distintas.
    Útil para defender K=4 ante el jurado.
    """
    from sklearn.metrics import adjusted_rand_score
    base = kmeans_ponderado(X_cluster, fex_norm, n_clusters=n_clusters, random_state=0).labels_
    aris = []
    for s in range(1, n_seeds + 1):
        labs = kmeans_ponderado(X_cluster, fex_norm, n_clusters=n_clusters, random_state=s).labels_
        aris.append(adjusted_rand_score(base, labs))
    return float(np.mean(aris))


def caracterizar_clusters_ponderado(df: pd.DataFrame,
                                     col_cluster: str = 'cluster_ord_w',
                                     col_target: str = 'log_gastos_2025',
                                     col_ingreso: str = 'log_ingresos_2025',
                                     col_fex: str = 'FEX_C') -> pd.DataFrame:
    """
    Tabla de caracterización con N muestral, N expandido, % expandido,
    media/mediana/p90 del gasto y del ingreso por cluster.
    """
    fex = pd.to_numeric(df[col_fex], errors='coerce').astype(float)
    g = df.groupby(col_cluster)
    tabla = pd.DataFrame({
        'n_muestra': g.size(),
        'n_expandido': g.apply(lambda x: fex.loc[x.index].sum()),
        'gasto_log_media': g[col_target].mean(),
        'gasto_log_mediana': g[col_target].median(),
        'gasto_log_p90': g[col_target].quantile(0.90),
        'ingreso_log_media': g[col_ingreso].mean(),
        'ingreso_log_mediana': g[col_ingreso].median(),
    })
    tabla['part_pct_expandido'] = tabla['n_expandido'] / tabla['n_expandido'].sum() * 100
    return tabla.reset_index()


# ============================================================
# WLS con statsmodels (para tablas con SE robustos)
# ============================================================
def wls_statsmodels(df: pd.DataFrame,
                    formula: str,
                    col_fex: str = 'FEX_C',
                    cov_type: str = 'HC3'):
    """
    WLS de statsmodels para producir una tabla académica con coeficientes y
    errores estándar robustos. Útil cuando se necesita un summary() formal.

    Ejemplo:
        modelo = wls_statsmodels(
            df_temp_a,
            'log_gastos_2025 ~ log_ingresos_2025 + Edad + I(Edad**2) '
            '+ C(Estrato) + C(REGION) + C(actividad_ppal)'
        )
        print(modelo.summary())
    """
    import statsmodels.formula.api as smf
    fex_norm = normalizar_fex(df, col_fex)
    return smf.wls(formula, data=df, weights=fex_norm).fit(cov_type=cov_type)


if __name__ == '__main__':
    print("Módulo analisis_ponderado.py")
    print("Funciones disponibles:")
    funcs = [
        normalizar_fex, descriptivo_ponderado, comparar_muestral_vs_expandido,
        wls_ponderado, cv_ponderada, ridge_lasso_comparacion,
        kmeans_ponderado, validar_clusters, estabilidad_clusters,
        caracterizar_clusters_ponderado, wls_statsmodels
    ]
    for f in funcs:
        print(f"  - {f.__name__}")
