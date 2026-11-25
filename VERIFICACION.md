# Verificación de CyberScope 4.3.0

Se verificaron las 397 probabilidades y predicciones del test contra la tesis, las doce demostraciones, las tres clases y la recodificación de severidad, las categorías nuevas, los lotes válidos e inválidos, los límites de archivo, la neutralización de fórmulas al exportar CSV, la correspondencia de LIME con la salida del modelo y la generación de PDF con caracteres especiales y entradas largas.

Las pruebas nuevas verifican ROS completo con 775 filas por clase, ausencia de estrategias alternativas en los resultados, los 261 tipos refinados y 16 pendientes, la auditoría de 277 registros, los soportes de las matrices balanceadas y la pertenencia de los quince casos equilibrados al test, sin duplicación de identidad.

Streamlit AppTest comprobó las cuatro páginas, las tres opciones de matriz, el filtro de pendientes, la carga de un caso real, la predicción individual, la exportación PDF y la explicación LIME con sus cuatro pesos. Las pruebas automatizadas no sustituyen la inspección del despliegue en el navegador del usuario.

Se renderizó un informe PDF con LIME para comprobar su maquetación. No se ha publicado la aplicación ni se ha accedido al repositorio del usuario. Esta entrega contiene los archivos para que el usuario los suba a GitHub.

El balanceo repite observaciones del entrenamiento; no aumenta la cantidad de casos reales low del test. La matriz de entrenamiento y la muestra de test equilibrada están etiquetadas como diagnósticas o descriptivas. La evaluación principal conserva el test original de 397 registros.

Resultado: 16 pruebas de backend aprobadas y 10 comprobaciones de interfaz aprobadas. Python 3.11.
