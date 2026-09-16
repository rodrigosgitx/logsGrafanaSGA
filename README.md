# logsGrafana

Proyecto Python para construir consultas Loki y abrir Grafana Explore en el navegador.

## Estructura

- `src/logs_grafana/grafana_explore_ui.py`: interfaz Gradio para generar la LogQL y abrir Grafana.
- `pyproject.toml`: configuracion del proyecto y punto de entrada ejecutable.
- `dependencies.txt`: dependencias del proyecto.
- `.gitignore`: exclusiones recomendadas para Python.

## Requisitos

- Python 3.10+

## Instalacion

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r dependencies.txt
python -m pip install -e .
```

## Ejecucion

```powershell
python -m logs_grafana
```

Tambien puedes ejecutar con el comando instalado por el proyecto:

```powershell
logs-grafana
```

La interfaz queda disponible en:

- `http://127.0.0.1:7861`

## Notas

- El script genera la consulta LogQL y abre Grafana Explore en el navegador.
- Los `projectkey` y `slot` estan preconfigurados en el propio script.

## Slots futuros

Los slots que aún no están en OCP hay que añadirlos en el diccionario del inicio del script

## Cambio de centro

Para adaptar el código a otro centro, modificar 

DEFAULT_PLATFORM = "Openshift-IOP Tordera Logistics5"
DEFAULT_TARGET = "prendacolgadadutti-c1"

A los deseados y también todo el diccionario posterior, para saber los slots posibles por platform y projectkey, se puede ejecutar esta consulta en loki:

sum by (slot) (count_over_time({projectkey="SGARCP",platform=~"Openshift-IOP Tordera Logistics5",environment="pro"} | json [1h]))


