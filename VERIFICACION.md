# Verificación de la actualización

- Quince pruebas automatizadas superadas con Python 3.12 y las dependencias fijadas en requirements.txt.
- Las 397 predicciones y probabilidades del test coinciden con los resultados guardados de la tesis, dentro de la tolerancia numérica del modelo.
- Los doce casos reproducen sus etiquetas y probabilidades al ingresar sus variables en el predictor de la web.
- Las tres severidades y su recodificación coinciden en todas las filas del dataset.
- Las cuatro páginas se ejecutan sin excepciones mediante Streamlit AppTest.
- Se verifican generación de LIME individual, explicación de la clase real en fallos, persistencia del resultado en la sesión, categorías nuevas, procesamiento de doce filas de ejemplo y rechazo de entradas inválidas.
- Se recorren los doce casos y sus dos clases explicadas cuando hay un fallo.
- El informe PDF admite caracteres especiales y entradas extensas. Un informe actualizado de dos páginas fue renderizado y revisado visualmente.
- Se conservaron los parámetros del modelo evaluado; únicamente se corrigió el texto del criterio de selección a tres clases.
- El manifiesto SHA-256 cubre los artefactos incluidos.

La verificación de interfaz utiliza Streamlit AppTest; no se hizo una revisión visual de la web en un navegador ni un despliegue en Streamlit Cloud. El ZIP es el entregable para actualizar el repositorio conectado.

Para repetir las pruebas desde la raíz del proyecto:

```bash
python -m unittest discover -s tests -v
```

La actualización 4.1.0 elimina la página de evidencia y sus enlaces de navegación. El inicio presenta capacidades para empresas. Los modelos y sus resultados no cambian.
