# Health-git

BACKLOG

Dashboard
 - Chante ATL for another metric. Strenght and stretch?
 - Add TSS, hours of run, hours of strength

Input
 - Revisar food schedule matching
 - MFP function using environment variables, to be able to host
 - JeFit

Análisis
 - Correlacionar comportamientos con métricas de sueño
 - Correlar TSS con Whoop Strain, por si vale esa

Engineering
 - Hosting online, batch


### Manual export process
Whoop
  - Journal from app: More/App Settings/Data export

LibreLink
  - https://www.libreview.com/

TrainingPeaks
  - Web / Photo / Settings / Export data / Workout Summary

Apple Health (food times and weight)
 - iPhone app Salud, foto, Exportar todos los datos de salud

 
### Process to generate clean data

1. All ETL
2. DataProcessing - MFP Api.ipynb
3. DataProcessing - MFP data matching v2.ipynb
4. IntegrateData.ipynb