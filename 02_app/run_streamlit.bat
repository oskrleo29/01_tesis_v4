@echo off
echo Iniciando Estimador de Gasto Personal v3.0 (Modelo Hibrido)...

REM Ir a la raiz del proyecto
cd /d %~dp0..

REM Activar entorno virtual (ajustar si usas conda)
REM call venv\Scripts\activate
REM Si usas conda:
REM call conda activate nombre_entorno

set PYTHON_EXE=python
set STREAMLIT_CMD=
if exist ..\venv\Scripts\python.exe set PYTHON_EXE=..\venv\Scripts\python.exe
if exist ..\venv\Scripts\streamlit.exe set STREAMLIT_CMD=..\venv\Scripts\streamlit.exe
if not defined STREAMLIT_CMD (
	where /q streamlit
	if %ERRORLEVEL%==0 set STREAMLIT_CMD=streamlit
)

REM Ir a la carpeta de la app
cd 02_app

REM Ejecutar Streamlit
if defined STREAMLIT_CMD (
	%STREAMLIT_CMD% run app.py
) else (
	%PYTHON_EXE% -m streamlit run app.py
)

pause
