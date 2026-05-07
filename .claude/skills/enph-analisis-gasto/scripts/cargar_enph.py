"""
Utilidades para cargar y preparar microdatos de la ENPH del DANE.

Soporta archivos .csv, .sav (SPSS, vía pyreadstat) y .dta (Stata).

Uso típico:
    from cargar_enph import cargar_modulo, unir_a_nivel_hogar, anualizar_gasto

    viv = cargar_modulo('Datos de la vivienda y su hogar.csv', ruta='./datos')
    per = cargar_modulo('Características generales (Personas).csv', ruta='./datos')
    gas = cargar_modulo('Gastos del hogar.csv', ruta='./datos')

    hogar = unir_a_nivel_hogar(viv, per, gas)
    gasto = anualizar_gasto(gas, col_valor='valor_pagado', col_freq='frecuencia')
"""

from pathlib import Path
import pandas as pd
import numpy as np


# Mapeo de frecuencia → días de un año
FACTOR_ANUAL = {
    1: 365,    # diaria
    2: 52,     # semanal
    3: 12,     # mensual
    4: 4,      # trimestral
    5: 2,      # semestral
    6: 1,      # anual
}

# Llaves estándar de la ENPH (ajustar si la versión específica las nombra distinto)
LLAVES_VIVIENDA = ['directorio']
LLAVES_HOGAR = ['directorio', 'secuencia_encuesta']
LLAVES_PERSONA = ['directorio', 'secuencia_encuesta', 'orden']


def _normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """Pasa los nombres de columnas a minúsculas y quita espacios."""
    df = df.copy()
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
    return df


def cargar_modulo(nombre: str, ruta: str = '.', sep: str = ',', encoding: str = 'utf-8') -> pd.DataFrame:
    """
    Carga un módulo de la ENPH detectando el formato por extensión.

    Args:
        nombre: nombre del archivo (con extensión).
        ruta: directorio donde está el archivo.
        sep: separador para CSV (cambiar a ';' si el archivo viene con ese separador).
        encoding: codificación; algunos archivos del DANE vienen en 'latin1'.

    Returns:
        DataFrame con columnas en minúsculas.
    """
    p = Path(ruta) / nombre
    ext = p.suffix.lower()

    if ext == '.csv':
        try:
            df = pd.read_csv(p, sep=sep, encoding=encoding, low_memory=False)
        except UnicodeDecodeError:
            df = pd.read_csv(p, sep=sep, encoding='latin1', low_memory=False)
    elif ext == '.sav':
        try:
            import pyreadstat
        except ImportError:
            raise ImportError("Instala pyreadstat: pip install pyreadstat")
        df, _ = pyreadstat.read_sav(str(p))
    elif ext == '.dta':
        df = pd.read_stata(str(p))
    elif ext in ('.xlsx', '.xls'):
        df = pd.read_excel(str(p))
    else:
        raise ValueError(f"Extensión no soportada: {ext}")

    df = _normalizar_columnas(df)
    print(f"Cargado {nombre}: {df.shape[0]:,} filas, {df.shape[1]} columnas")
    return df


def detectar_factor_expansion(df: pd.DataFrame) -> str | None:
    """
    Intenta detectar el nombre de la columna del factor de expansión.

    Devuelve el nombre si lo encuentra, o None para que la usuaria lo proporcione.
    """
    candidatos = ['fex_c', 'fex_hogar', 'fex', 'factor_expansion', 'fex_calibrado']
    for c in candidatos:
        if c in df.columns:
            return c
    # Buscar columnas que empiecen con fex_
    fex_like = [c for c in df.columns if c.startswith('fex')]
    if fex_like:
        return fex_like[0]
    return None


def validar_factor_expansion(df: pd.DataFrame, col_fex: str | None = None,
                              hogares_esperados: tuple = (12_000_000, 17_000_000)) -> None:
    """
    Verifica que la suma del factor de expansión esté en un rango razonable
    para el total de hogares de Colombia (entre 12M y 17M aprox).

    Lanza un AssertionError si no.
    """
    if col_fex is None:
        col_fex = detectar_factor_expansion(df)
        if col_fex is None:
            raise ValueError("No se detectó factor de expansión; pásalo explícitamente.")

    total = df[col_fex].sum()
    print(f"Factor de expansión '{col_fex}' suma: {total:,.0f}")
    assert hogares_esperados[0] <= total <= hogares_esperados[1], (
        f"Suma de factores ({total:,.0f}) fuera del rango esperado "
        f"{hogares_esperados[0]:,}–{hogares_esperados[1]:,}. "
        f"Verifica si es un módulo a nivel de persona, no hogar."
    )


def caracteristicas_jefe_hogar(df_personas: pd.DataFrame,
                                col_parentesco: str = 'p6051',
                                codigo_jefe: int = 1) -> pd.DataFrame:
    """
    Extrae una fila por hogar con las características del jefe de hogar.

    Ajusta `col_parentesco` y `codigo_jefe` según el diccionario de la versión
    específica de la ENPH que se esté usando.
    """
    jefe = df_personas[df_personas[col_parentesco] == codigo_jefe].copy()
    print(f"Jefes detectados: {len(jefe):,} (debería ser ≈ número de hogares)")
    return jefe


def anualizar_gasto(df: pd.DataFrame,
                    col_valor: str = 'valor_pagado',
                    col_freq: str = 'frecuencia') -> pd.DataFrame:
    """
    Crea una columna 'gasto_anual' a partir del valor reportado y su frecuencia.

    Lanza ValueError si hay frecuencias no reconocidas.
    """
    df = df.copy()
    freq_unicas = set(df[col_freq].dropna().unique())
    no_reconocidas = freq_unicas - set(FACTOR_ANUAL.keys())
    if no_reconocidas:
        raise ValueError(
            f"Frecuencias no reconocidas: {no_reconocidas}. "
            f"Verifica el diccionario de la ENPH; quizá usa codificación distinta."
        )
    df['gasto_anual'] = df[col_valor] * df[col_freq].map(FACTOR_ANUAL)
    return df


def agregar_gasto_a_hogar(df_gastos: pd.DataFrame,
                           col_categoria: str | None = None,
                           col_valor: str = 'gasto_anual') -> pd.DataFrame:
    """
    Suma el gasto a nivel de hogar.

    Si `col_categoria` se da, devuelve un DataFrame con columnas por categoría
    (formato wide, una fila por hogar).
    """
    grupos = LLAVES_HOGAR
    if col_categoria:
        agg = (df_gastos
               .groupby(grupos + [col_categoria])[col_valor]
               .sum()
               .unstack(col_categoria, fill_value=0)
               .reset_index())
        agg.columns.name = None
        # Total
        agg['gasto_total_anual'] = agg.drop(columns=grupos).sum(axis=1)
        return agg
    else:
        agg = df_gastos.groupby(grupos)[col_valor].sum().reset_index()
        agg = agg.rename(columns={col_valor: 'gasto_total_anual'})
        return agg


def unir_a_nivel_hogar(*dfs: pd.DataFrame, how: str = 'left') -> pd.DataFrame:
    """
    Une múltiples DataFrames a nivel de hogar por las llaves estándar.

    El primer DataFrame es la base; los siguientes se hacen merge contra él.
    Detecta el nivel de cada DataFrame por las llaves presentes.
    """
    if not dfs:
        raise ValueError("Pasa al menos un DataFrame.")

    base = dfs[0].copy()
    nivel_base = _detectar_nivel(base)

    for i, df in enumerate(dfs[1:], start=1):
        nivel = _detectar_nivel(df)
        # Llaves comunes
        if nivel == 'persona':
            raise ValueError(f"DataFrame {i} es a nivel persona; agrégalo a hogar primero.")
        llaves = LLAVES_HOGAR if nivel == 'hogar' else LLAVES_VIVIENDA
        antes = len(base)
        base = base.merge(df, on=llaves, how=how)
        despues = len(base)
        print(f"Merge {i}: {antes:,} → {despues:,} filas")

    return base


def _detectar_nivel(df: pd.DataFrame) -> str:
    cols = set(df.columns)
    if set(LLAVES_PERSONA).issubset(cols):
        return 'persona'
    if set(LLAVES_HOGAR).issubset(cols):
        return 'hogar'
    if set(LLAVES_VIVIENDA).issubset(cols):
        return 'vivienda'
    raise ValueError(f"No se pudo detectar nivel. Columnas: {list(cols)[:10]}...")


if __name__ == '__main__':
    print("Módulo cargar_enph. Importa las funciones y úsalas en tu análisis.")
    print("Funciones disponibles:")
    for f in [cargar_modulo, detectar_factor_expansion, validar_factor_expansion,
              caracteristicas_jefe_hogar, anualizar_gasto,
              agregar_gasto_a_hogar, unir_a_nivel_hogar]:
        print(f"  - {f.__name__}")
