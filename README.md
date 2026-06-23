# Generador de Reportes de Jira

Genera un reporte en Markdown (y una version en HTML para correo) a partir
de un CSV exportado de Jira.

Los tickets se separan en "En curso" (agrupados por persona asignada) y
"Terminados" (agrupados por Historia/Error). Los tickets en "Backlog"
siempre se excluyen. Los tickets en curso muestran un porcentaje de avance
calculado con su fecha de inicio, fecha de vencimiento y la fecha final del
reporte.

## Requisitos

- Python 3.12+, solo libreria estandar.

## Uso

```
python3 generate_report.py ruta/al/export.csv
```

Por defecto genera un reporte de los ultimos 7 dias en `reports/output/`.

## Opciones

- `--output RUTA` — directorio base de salida; los archivos se escriben en `<output>/<fecha-fin>/` (default: `reports/output`)
- `--start YYYY-MM-DD` / `--end YYYY-MM-DD` — periodo explicito del reporte
- `--days N` — tamano del periodo en dias cuando no se da `--start` (default: 7)
- `--show-type` — muestra el tipo de incidencia (Historia/Error) por ticket
- `--show-status` — muestra el estado de Jira por ticket
- `--hide-due-date` — oculta la fecha de vencimiento por ticket (se muestra por defecto)
- `--no-mail` — omite la generacion de la version `.mail.html`

## Ejemplo

```
python3 generate_report.py reports/haika_2026-06-23.csv --start 2026-06-01 --end 2026-06-23
```

Genera `reports/output/2026-06-23/report_2026-06-01_to_2026-06-23.md` y su
version `.mail.html` correspondiente.

## Columnas esperadas en el CSV

`Clave`, `Tipo de Incidencia`, `Resumen`, `Estado`, `Persona asignada`,
`Fecha de inicio`, `Fecha de inicio deducida`, `Fecha de vencimiento`,
`Fecha de vencimiento deducida`.
