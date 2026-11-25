# CyberScope para GitHub y Streamlit

Versión 4.3.0. Autor: Bryan Madrid, Universidad Andrés Bello. Modelo de macrofamilia y contexto tecnológico con tres severidades y ROS completo.

## Actualizar tu repositorio

1. Extrae CyberScope_GitHub_Streamlit_Actualizado.zip.
2. Abre la carpeta CyberScope_GitHub_Streamlit. Sube su contenido al repositorio: app.py, core.py, reports.py, requirements.txt, metadata.json, metricas_evaluacion.json, los CSV de ejemplo, README.md, VERIFICACION.md y las carpetas artifacts, assets, tests y .streamlit. app.py y requirements.txt deben quedar en la raíz del repositorio.
3. Reemplaza los archivos de la versión anterior como un conjunto. Conserva los nombres y las carpetas. No mezcles el modelo nuevo con metadata o artifacts antiguos y no subas solamente el ZIP.
4. Confirma los cambios en la rama que utiliza tu aplicación Streamlit. Si despliegas desde cero, conecta ese repositorio, selecciona su rama y app.py como archivo principal. Usa Python 3.11, que es la versión con la que se comprobó esta entrega.
5. Reinicia la aplicación desde su administración si mantiene caché o estado anterior. La versión visible debe ser 4.3.0.

No necesitas subir el notebook, los datasets originales de investigación ni la carpeta de tesis al repositorio de la web. El ZIP de la web ya contiene todos los artefactos que necesita. El entrenamiento no se ejecuta durante el despliegue y la aplicación no descarga datasets al arrancar.

## Ejecutar en Visual Studio Code

Desde esta carpeta, con Python 3.11:

```bash
python -m venv .venv
```

Windows PowerShell, sin necesidad de activar el entorno:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\streamlit.exe run app.py
```

macOS o Linux:

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/streamlit run app.py
```

## Mejoras incluidas

- Solo ROS completo en los siete algoritmos comparados: 775 filas por clase al ajustar el modelo final sobre desarrollo, incluidas las repeticiones. Se conserva la selección por F1 macro en cuatro folds temporales.
- Dataset de 1.984 registros con 261 tipos específicos recuperados de nombres antes genéricos y 16 tipos pendientes por falta de evidencia. La columna original se conserva únicamente para auditoría. El refinamiento no cambia severidades, macrofamilias ni predictores.
- Selector de tres matrices dentro de Evidencia del modelo: test original de 397 casos, entrenamiento balanceado y test equilibrado descriptivo de cinco casos reales por clase. Cada vista indica qué datos evalúa y permite descargar su gráfico.
- Auditoría de tipos con evidencia textual, filtro de pendientes, reglas consultables y descargas CSV.
- Predicción individual y por lotes, gráficos LIME, informes PDF y exportaciones JSON y CSV. Se mantienen los cuatro predictores: Vendor, Platform, Product_normalized y risk_family_6.
- Navegación: Inicio, Análisis individual, Análisis por lotes y Evidencia del modelo. No incluye las páginas de propuesta empresarial ni casos y explicaciones. Los ejemplos reales se conservan en el formulario individual, y LIME se consulta allí.

## Modelo y evaluación

El modelo seleccionado sigue siendo XGBoost con ROS completo. Accuracy CV: 76,34 %. Accuracy del test original: 72,54 %. F1 macro de tres clases: 0,6807 en CV y 0,5464 en test. La web reproduce las 397 predicciones guardadas de la investigación.

La matriz de entrenamiento es un diagnóstico de ajuste con repeticiones, no una evaluación de generalización. La muestra equilibrada de test contiene solo quince registros y no sustituye al test completo. low conserva cinco casos reales en test y un acierto; el sobremuestreo no añade casos independientes.

Se mantienen las etiquetas de origen de la tesis. El refinamiento de tipos no verifica que todos los registros medium tengan esa severidad correcta. Las etiquetas de referencia no equivalen automáticamente a CVSS ni al riesgo del negocio. El prototipo requiere revisión humana y validación propia de cada organización. high integra high y critical.

Los datos del usuario se procesan en memoria durante la sesión del servidor elegido. No se incorporan al entrenamiento ni se envían a servicios externos de inferencia. Las exportaciones se descargan al equipo del usuario. El prototipo no implementa cuentas ni expedientes persistentes por organización.

## Verificaciones

```bash
python -m unittest discover -s tests -v
```

VERIFICACION.md describe las pruebas de esta versión. La aplicación comprueba los hashes de sus artefactos al iniciar para detectar entregas mezcladas o incompletas. No edites manualmente los CSV del paquete sin actualizar de forma coherente el modelo, sus evidencias y el manifiesto.
