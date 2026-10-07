# CyberScope - Bryan Madrid

Aplicación de análisis de severidad cibernética con modelos evaluados, explicaciones LIME y propuesta de piloto empresarial.

Este paquete contiene los archivos necesarios para servir las seis secciones de la web. La investigación completa, los CSV originales y el código de entrenamiento permanecen en el paquete Prototipo_Predictor_Severidad_Ciber_V3.

## GitHub

1. Extrae CyberScope_GitHub_Streamlit.zip.
2. Crea un repositorio GitHub llamado `cyberscope-severidad`. Puedes inicializarlo con un README para disponer del botón Add file.
3. En Add file > Upload files, arrastra **el contenido** de la carpeta CyberScope_GitHub_Streamlit: archivos sueltos y carpetas, incluyendo `.streamlit`, `assets` y `artifacts`.
4. Conserva la estructura. `app.py` y `requirements.txt` deben quedar en la raíz del repositorio, no dentro de una carpeta adicional.
5. Confirma la subida en Commit changes. Se incluyen menos de 100 archivos y cada uno es menor de 25 MiB para permitir la carga por navegador.

No subas el ZIP como archivo del repositorio: Streamlit necesita los archivos extraídos. El paquete no contiene un entorno `.venv` ni contraseñas.

## Streamlit Community Cloud

1. Entra a https://share.streamlit.io y vincula tu cuenta GitHub.
2. Pulsa Create app y selecciona Yup, I have an app si aparece esa pregunta.
3. Selecciona tu repositorio, la rama `main` y el archivo principal `app.py`.
4. En Advanced settings, selecciona **Python 3.12**, la versión en la que se verificó la aplicación y se entrenaron los artefactos.
5. Pulsa Deploy y espera a que termine la instalación.
6. La plataforma mostrará una dirección `https://...streamlit.app` para abrir la web.

El despliegue carga los modelos incluidos; no entrena al iniciar y no requiere CSV adicionales. Para la demostración usa los casos de ejemplo incluidos en la página.

## Archivos indispensables

- `app.py`, `core.py`, `reports.py`.
- `requirements.txt`, `metadata.json` y `metricas_evaluacion.json`.
- `artifacts/` con los dos modelos, dataset y evidencia consultada por la web.
- `assets/` con estilos, foto y fuentes PDF.
- `.streamlit/config.toml`.
- Las dos plantillas CSV y los dos PDF incluidos.

XGBoost no es una dependencia de esta aplicación: participa en el entrenamiento de investigación, que se entrega en el proyecto completo.

## Verificación

Se verificó la carga del predictor y el renderizado de las seis secciones con Streamlit AppTest sobre este paquete de despliegue. Los modelos son copias exactas de los artefactos evaluados y se validan con sus hashes. La investigación completa pasó doce pruebas automatizadas. No se ha publicado esta copia en tu cuenta; los pasos anteriores realizan ese despliegue.

## Alcance

Prototipo experimental para revisión humana. Los resultados provienen de etiquetas de referencia de CISA y MITRE; el piloto empresarial debe validar la rúbrica local. No incorpora autenticación propia, almacenamiento de usuarios ni remediación automática. La foto y autoría corresponden a Bryan Madrid, Ingeniería Civil Informática, Universidad Andrés Bello.

## Documentación oficial

- https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
