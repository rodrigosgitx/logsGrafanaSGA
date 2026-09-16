#!/usr/bin/env python3
"""Interfaz interactiva para construir consultas Loki y abrirlas en Grafana Explore.

Requisitos:
  pip install gradio

Uso:
  python grafana_explore_ui.py
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import urllib.parse
import webbrowser

DEFAULT_BASE_URL = "https://grafana.inditex.com"
DEFAULT_ORG_ID = 1
DEFAULT_DATASOURCE = "Loki"
DEFAULT_PROJECTKEY = "SGASOR"
PROJECTKEY_CHOICES = [
    "SGASOR",
    "SGAASR",
    "SGARCP",
    "SGAMSRSRV",
    "SGAGIB",
    "PMESGA",
    "SGACAR",
    "SGAMSS",
    "SGASQB",
    "SGASHP",
    "WMSXWSRV"
]
DEFAULT_ENVIRONMENT = "pro"
DEFAULT_PLATFORM = "Openshift-IOP Tordera Logistics5"
DEFAULT_TARGET = "prendacolgadadutti-c1"
DEFAULT_SINCE = "1h"
DEFAULT_PORT = 7861

SLOT_CHOICES: dict[str, list[str]] = {
    "SGASOR": [
        "paqueteriadutti-c1",
        "paqueteriadutti-c2",
        "paqueteriapalafolls-c3",
        "paqueteriapalafolls-c4",
        "prendacolgadapalafolls-c1",
        "prendacolgadadutti-c1",
        "paqueteriaoysho-c1",
        "paqueteriaoysho-c2",
    ],
    "SGAASR": [
        "paqueteriamassimodutti",
        "paqueteriapalafolls-silo1",
        "paqueteriapalafolls-silo2",
        "paqueteriapalafolls-siloshuttle",
        "paqueteriapalafolls-siloshuttle2",
        "prendacolgadamassimodutti-silo1",
        "prendacolgadamassimodutti-siloshuttle",
        "prendacolgadapalafolls-siloshuttle",
    ],
    "SGARCP": [
        "paqueteriamassimodutti",
        "paqueteriaoysho",
        "paqueteriapalafolls",
        "prendacolgadamassimodutti",
        "prendacolgadapalafolls",
    ],
    "SGAMSRSRV": [
        "paqueteriamassimodutti",
        "paqueteriaoysho",
        "paqueteriapalafolls",
        "prendacolgadamassimodutti",
        "prendacolgadapalafolls",
    ],
    "SGAGIB": [
        "massimoduttigib",
        "massimoduttipick",
        "palafollspick",
    ],
    "PMESGA": [
        "prendacolgadapalafolls",
    ],
    "SGACAR": [
        "paqueteriamassimodutti",
        "paqueteriaoysho",
        "paqueteriapalafolls",
    ],
    "SGAMSS": [
        "paqueteriamassimodutti",
        "paqueteriaoysho",
        "paqueteriapalafolls",
    ],
    "SGASQB": [
        "paqueteriamassimodutti",
        "paqueteriaoysho2",
        "paqueteriapalafolls1",
        "paqueteriapalafolls2",
        "paqueteriapalafolls3",
        "paqueteriapalafolls4",
    ],
    "SGASHP": [
        "paqueteriamassimodutti",
        "paqueteriaoysho",
        "paqueteriapalafolls",
    ],
    "WMSXWSRV": [
        "paqueteriamassimodutti",
        "paqueteriaoysho",
        "paqueteriapalafolls",
        "prendacolgadamassimodutti",
        "prendacolgadapalafolls",
    ]
}


def _escape_label_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _to_unix_ms(value: object) -> int:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, (int, float)):
        return int(float(value) * 1000)
    elif isinstance(value, str):
        raw = value.strip()
        if not raw:
            raise ValueError("Fecha/hora vacia")
        normalized = raw.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
    else:
        raise ValueError("Formato de fecha/hora no soportado")

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def build_logql(
    projectkey: str,
    platform: str,
    environment: str,
    target: str,
    free_text_fragment: str,
) -> str:
    pk = _escape_label_value((projectkey or "").strip() or DEFAULT_PROJECTKEY)
    platform_value = _escape_label_value((platform or "").strip() or DEFAULT_PLATFORM)
    env = _escape_label_value((environment or "").strip() or DEFAULT_ENVIRONMENT)
    target_value = _escape_label_value((target or "").strip() or DEFAULT_TARGET)

    conditions = [
        f'instance=~"{target_value}"',
        f'moduleInstance=~"{target_value}"',
        f'slot=~"{target_value}"',
    ]

    labels = f'{{projectkey="{pk}",platform=~"{platform_value}",environment="{env}"}}'
    filter_expr = " or ".join(conditions)
    query = (
        f"{labels} | json | ({filter_expr}) "
    )

    fragment = free_text_fragment or ""
    if fragment:
        if fragment[0].isspace():
            query += fragment
        else:
            query += f" {fragment}"

    query += (
        f'| line_format "{{{{.level}}}}\\t{{{{.message}}}}"'
    )
    return query


def build_explore_url(
    base_url: str,
    org_id: int,
    datasource_uid: str,
    since: str,
    time_mode: str,
    start_dt: object,
    end_dt: object,
    query: str,
) -> str:
    base = (base_url or DEFAULT_BASE_URL).strip().rstrip("/")
    datasource = (datasource_uid or DEFAULT_DATASOURCE).strip() or DEFAULT_DATASOURCE
    since_value = (since or DEFAULT_SINCE).strip() or DEFAULT_SINCE

    if time_mode == "Absoluto":
        start_ms = _to_unix_ms(start_dt)
        end_ms = _to_unix_ms(end_dt)
        if start_ms >= end_ms:
            raise ValueError("La fecha/hora de inicio debe ser anterior al fin")
        range_obj = {"from": str(start_ms), "to": str(end_ms)}
    else:
        range_obj = {"from": f"now-{since_value}", "to": "now"}

    left = {
        "datasource": datasource,
        "queries": [{"refId": "A", "expr": query}],
        "range": range_obj,
    }
    encoded = urllib.parse.quote(json.dumps(left, separators=(",", ":")))
    return f"{base}/explore?orgId={org_id}&left={encoded}"


def generate_query_and_open(
    time_mode: str,
    since: str,
    start_dt: object,
    end_dt: object,
    projectkey: str,
    environment: str,
    target: str,
    free_text_fragment: str,
) -> tuple[str, str]:
    try:
        query = build_logql(
            projectkey=projectkey,
            platform=DEFAULT_PLATFORM,
            environment=environment,
            target=target,
            free_text_fragment=free_text_fragment,
        )

        url = build_explore_url(
            base_url=DEFAULT_BASE_URL,
            org_id=DEFAULT_ORG_ID,
            datasource_uid=DEFAULT_DATASOURCE,
            since=since,
            time_mode=time_mode,
            start_dt=start_dt,
            end_dt=end_dt,
            query=query,
        )
    except ValueError as exc:
        return "", f"Error: {exc}"

    opened = webbrowser.open(url, new=2)
    if opened:
        return query, "Query generada y Grafana abierto en el navegador."

    return query, "Query generada, pero no se pudo abrir automaticamente Grafana."


def launch_ui() -> None:
    try:
        import gradio as gr
    except ImportError:
        raise SystemExit(
            "No se encontro gradio. Instala con: pip install gradio"
        )

    with gr.Blocks(title="Grafana Explore Builder") as demo:
        gr.Markdown("## Builder de consultas Loki para Grafana Explore")

        now_utc = datetime.now(timezone.utc)
        default_start_utc = now_utc.replace(microsecond=0) - timedelta(hours=1)
        default_end_utc = now_utc.replace(microsecond=0)

        with gr.Row():
            time_mode = gr.Radio(
                label="Modo de tiempo",
                choices=["Relativo", "Absoluto"],
                value="Relativo",
            )
            since = gr.Dropdown(
                label="Rango",
                choices=["15m", "30m", "1h", "2h", "6h", "12h", "1d"],
                value=DEFAULT_SINCE,
                allow_custom_value=True,
            )

        with gr.Row():
            start_dt = gr.DateTime(
                label="Inicio (calendario + hora)",
                include_time=True,
                value=default_start_utc,
            )
            end_dt = gr.DateTime(
                label="Fin (calendario + hora)",
                include_time=True,
                value=default_end_utc,
            )

        with gr.Row():
            projectkey = gr.Dropdown(
                label="projectkey",
                choices=PROJECTKEY_CHOICES,
                value=DEFAULT_PROJECTKEY,
                allow_custom_value=False,
            )
            environment = gr.Textbox(label="environment", value=DEFAULT_ENVIRONMENT)
            target = gr.Dropdown(
                label="Slot / Regex objetivo",
                choices=SLOT_CHOICES[DEFAULT_PROJECTKEY],
                value=SLOT_CHOICES[DEFAULT_PROJECTKEY][0],
                allow_custom_value=True,
            )

        projectkey.change(
            fn=lambda pk: gr.Dropdown(
                choices=SLOT_CHOICES.get(pk, []),
                value=SLOT_CHOICES.get(pk, [""])[0],
            ),
            inputs=[projectkey],
            outputs=[target],
        )

        free_regex = gr.Textbox(
            label="Texto libre (se anade literalmente a la consulta)",
            lines=1,
            value="",
        )

        generate_btn = gr.Button("Generar Query y abrir en Grafana", variant="primary")

        query_out = gr.Textbox(label="LogQL", lines=5)
        status = gr.Textbox(label="Estado", lines=1)

        generate_btn.click(
            fn=generate_query_and_open,
            inputs=[
                time_mode,
                since,
                start_dt,
                end_dt,
                projectkey,
                environment,
                target,
                free_regex,
            ],
            outputs=[query_out, status],
        )

    demo.launch(inbrowser=False, server_name="127.0.0.1", server_port=DEFAULT_PORT)


if __name__ == "__main__":
    launch_ui()
