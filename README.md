# CyberScope para GitHub y Streamlit

Versión 4.1.0. Un único modelo de macrofamilia y contexto tecnológico con tres severidades. Autor: Bryan Madrid, Universidad Andrés Bello.

## Publicar la actualización

1. Extrae este ZIP y abre la carpeta CyberScope_GitHub_Streamlit.
2. En tu repositorio de GitHub, reemplaza el contenido anterior por el contenido de esta carpeta. app.py y requirements.txt deben quedar en la raíz. Incluye assets, artifacts y .streamlit. No subas el ZIP como archivo de la aplicación.
3. Confirma los cambios. Streamlit Community Cloud detecta la actualización del repositorio conectado.
4. Usa Python 3.12 para este modelo. Si tu aplicación ya usa esa versión, conserva su configuración. Si usa otra, revisa su configuración de despliegue antes de ejecutar; las dependencias de esta entrega se verificaron con Python 3.12.
5. Si la aplicación conserva resultados antiguos, reiníciala desde su administración en Streamlit. La versión mostrada debe ser v4.1.0 y el modelo XGBoost.

El paquete tiene una única carpeta contenedora. Al subirlo, selecciona su contenido, no la carpeta exterior completa. Conserva los nombres de los archivos.

## Cambios

- Un único modelo XGBoost seleccionado con cuatro ventanas temporales con purga por entidad. Se elimina el escenario de solo familia.
- low y low/medium se agrupan en low; medium y medium/high en medium; high y critical en high.
- Cuatro predictores: Vendor, Platform, Product_normalized y risk_family_6. Las seis macrofamilias siguen siendo categorías de un predictor.
- Predicción individual y por lotes con tres probabilidades, categorías desconocidas e informes PDF y JSON actualizados.
- La navegación se centra en Inicio, Análisis individual, Análisis por lotes y Casos y explicaciones. La comparación de modelos y el dataset se conservan como archivos técnicos internos, sin una página de evidencia en la aplicación.
- Ocho aciertos y cuatro fallos del nuevo modelo. LIME muestra gráficos y tablas; permite ver las clases real y predicha en los fallos, las métricas de fidelidad, la estabilidad entre semillas y las descargas HTML y CSV. No genera interpretaciones escritas de los casos.
- La aplicación no incluye una página de propuesta empresarial ni una página de evidencia del modelo. El inicio presenta las capacidades de uso y accesos directos a los análisis.

## Resultados guardados

| Métrica | Validación cruzada | Test |
| --- | ---: | ---: |
| Accuracy | 76,34 % | 72,54 % |
| F1 macro de tres clases | 68,07 % | 54,64 % |

El modelo fue ajustado con 1.520 registros de desarrollo; se verifican las 397 predicciones del test contra los resultados de la tesis. Se distribuye el modelo congelado evaluado, sin reentrenamiento en la web.

low tiene cinco registros en test y un acierto. high no distingue criticidad extrema. El contexto puede reflejar la fuente CISA/MITRE y las fechas no están verificadas como fechas de incidentes. El test había sido inspeccionado antes de redefinir las clases; hace falta una cohorte nueva para confirmar generalización. Estas métricas no son directamente comparables con la tarea anterior de seis severidades.

## Datos y uso

La predicción individual acepta cuatro variables; los datos de organización y activo solo documentan el informe. Los lotes admiten CSV UTF-8 con comas, hasta 1.000 filas y 5 MB. Las plantillas incluyen entradas, sin etiquetas de severidad como predictores.

Los datos del usuario se procesan en memoria durante la sesión, no se añaden al entrenamiento ni se envían a servicios de inferencia externos. El paquete contiene los datos públicos de investigación y los modelos. Los resultados individuales son estimaciones para revisión humana, no prioridades ni plazos automáticos.

LIME consulta el mismo modelo utilizado al predecir. La referencia se elige entre desarrollo global, CISA y MITRE; los casos guardados usan desarrollo de su misma fuente, 4.000 perturbaciones y cinco semillas de estabilidad. Sus pesos son asociaciones locales y deben revisarse con el R² y la diferencia con la salida del modelo. Un R² estable o alto no acredita causalidad.

## Ejecutar localmente

Desde esta carpeta, con Python 3.12:

```bash
python -m venv .venv
```

En Windows:

```powershell
.venv\Scripts\activate
python -m pip install -r requirements.txt
streamlit run app.py
```

En macOS o Linux:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

La investigación completa y el notebook se mantienen en el paquete de tesis. Esta entrega incluye los artefactos necesarios para publicar la web, sin ejecutar entrenamiento durante el despliegue.
