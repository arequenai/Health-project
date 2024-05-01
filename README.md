# Health-git

BACKLOG

Input
 - Whoop Dataprocessing journal
 - JeFit
 - Cambiar a Appends
 - Cambiar ETL a functiones, que revisen que sea data nueva

Análisis
 - Correlacionar comportamientos con métricas de sueño

Charts


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

 Garmin (not yet used)
 - Direct from API
- Activities: run on terminal garmin-backup --backup-dir=Data/Garmin requenalberto@gmail.com

### Process to generate clean data

1. ETL - Whoop.py
2. ETL - LibreView.py
3. ETL - TrainingPeaks.py
4. ETL - Garmin.py
5. ETL - Apple Health.py
6. DataProcessing - MFP Api.ipynb
7. DataProcessing - MFP data matching v2.ipynb
8. IntegrateData.ipynb