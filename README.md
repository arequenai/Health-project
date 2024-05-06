# Health-git

BACKLOG

Input
 - JeFit
 - Cambiar a Appends
 - Cambiar ETL a functiones, que revisen que sea data nueva

Análisis
 - Nutrition score
 - Correlacionar comportamientos con métricas de sueño
 - Correlar TSS con Whoop Strain, por si vale esa

Charts


### Export process
Whoop
  - Direct through API
  - Journal from app: More/App Settings/Data export

LibreLink
  - https://www.libreview.com/

TrainingPeaks
  - Web / Photo / Settings / Export data / Workout Summary

Apple Health (food times and weight)
 - iPhone app Salud, foto, Exportar todos los datos de salud

 Garmin (activities not yet used)
 - Direct from API
 - Activities: run on terminal garmin-backup --backup-dir=Data/Garmin requenalberto@gmail.com

### Process to generate clean data

1. All ETL
2. DataProcessing - MFP Api.ipynb
3. DataProcessing - MFP data matching v2.ipynb
4. IntegrateData.ipynb