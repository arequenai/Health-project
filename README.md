# Health-git

BACKLOG

Whoop
 - Dataprocessing journal

TrainingPeaks
 - Incorporar TrainingPeaks

Sueño
 - Añadir métricas de sueño
 - Incorporar comportamientos
 - Correlacionar comportamientos con métricas de sueño

Charts
 - PowerBI TrainingPeaks
 - Salud


### Export process
Whoop
  - Direct through API
  - Journal from app: More/App Settings/Data export

LibreLink
  - https://www.libreview.com/

TrainingPeaks
  - Web / Photo / Settings / Export data / Workout Summary

Apple Health (includes food)
 - iPhone app Salud, foto, Exportar todos los datos de salud

### Process to generate clean data

1. ETL - Whoop.py
2. ETL - LibreView.py
3. ETL - TrainingPeaks.py
4. DataProcessing MFP.py
5. DataProcessing - MFP Api.ipynb
6. DataProcessing - MFP data matching v2.ipynb
7. IntegrateData.ipynb