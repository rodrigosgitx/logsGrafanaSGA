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
- La jerarquia de seleccion en la interfaz es `platform` -> `projectkey` -> `slot`: al elegir un `platform` se filtran los `projectkey` disponibles, y al elegir un `projectkey` se filtran los `slot` disponibles para esa combinacion.
- `SLOT_CHOICES` (en el propio script) es un diccionario anidado `platform -> projectkey -> lista de slots`, descubierto consultando los labels `platform`, `projectkey` y `slot` en Loki. Solo se incluyen combinaciones `platform`/`projectkey` que tienen al menos un slot con datos.

## Slots futuros

Los slots que aún no están en OCP, o los nuevos `platform`/`projectkey` que se añadan, hay que incorporarlos en el diccionario `SLOT_CHOICES` al inicio del script.

## Añadir o actualizar un centro (platform)

Para descubrir que `platform` tienen logs disponibles para un `projectkey`:

```
{projectkey="SGARCP"} | label_values(platform)
```

Para descubrir los `slot` disponibles de una combinacion `projectkey` + `platform`:

```
sum by (slot) (count_over_time({projectkey="SGARCP",platform="Openshift-IOP Tordera Logistics5",environment="pro"} | json [1h]))
```

Con esos resultados, añadir/actualizar la entrada correspondiente en `SLOT_CHOICES[platform][projectkey]`. Si un `platform` no tiene ningun `projectkey` con slots, no debe incluirse en el diccionario.


