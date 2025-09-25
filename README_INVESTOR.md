
# Benessere – Investor Demo (Streamlit)

Landing/one‑pager interactivo para mostrar a inversionistas:
- Secciones: Portada, Resumen, Producto, Ubicaciones, Unit Economics, Proyección 12M, Propuesta de Valor, Equipo, Ronda, Galería, Contacto.
- Si colocas `Financial_Model_Acai_Lite.xlsx` en la carpeta, la app leerá la hoja **Assumptions** y generará **UnitEconomics** y **Forecast12M** para métricas y gráficos.

## Ejecutar
```bash
pip install -r requirements.txt
streamlit run app_investor.py
```

## Reemplazar imágenes
- Sube tus fotos reales dentro de `assets_investor/` con estos nombres:
  - `logo.png`
  - `hero.jpg`
  - `store.jpg`
  - `menu.jpg`
