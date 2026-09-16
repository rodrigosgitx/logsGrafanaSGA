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
DEFAULT_ENVIRONMENT = "pro"
DEFAULT_PLATFORM = "Openshift-IOP Tordera Logistics5"
DEFAULT_TARGET = "prendacolgadadutti-c1"
DEFAULT_SINCE = "1h"
DEFAULT_PORT = 7861

# Jerarquia: platform -> projectkey -> slots disponibles (descubierto via Loki).
SLOT_CHOICES: dict[str, dict[str, list[str]]] = {
    "Openshift-IOP Tordera Logistics5": {
        "SGASOR": [
            "paqueteriadutti-c1", "paqueteriadutti-c2", "paqueteriaoysho-c1", "paqueteriaoysho-c2",
            "paqueteriapalafolls-c2", "paqueteriapalafolls-c3", "paqueteriapalafolls-c4",
            "prendacolgadadutti-c1", "prendacolgadapalafolls-c1",
        ],
        "SGAASR": [
            "paqueteriamassimodutti", "paqueteriaoysho-multishuttle1", "paqueteriapalafolls-silo1",
            "paqueteriapalafolls-silo2", "paqueteriapalafolls-siloshuttle", "paqueteriapalafolls-siloshuttle2",
            "prendacolgadamassimodutti-silo1", "prendacolgadamassimodutti-siloshuttle",
            "prendacolgadapalafolls-siloshuttle",
        ],
        "SGARCP": ["paqueteriamassimodutti", "paqueteriaoysho", "paqueteriapalafolls", "prendacolgadamassimodutti", "prendacolgadapalafolls"],
        "SGAMSRSRV": ["paqueteriamassimodutti", "paqueteriaoysho", "paqueteriapalafolls", "prendacolgadamassimodutti", "prendacolgadapalafolls"],
        "SGAGIB": [
            "massimoduttigib", "massimoduttipick", "palafollspick", "prendacolgadaespalafollspick",
            "prendacolgadamassimoduttigib", "prendacolgadamassimoduttipick", "prendacolgadapalafollspick",
        ],
        "PMESGA": ["prendacolgadapalafolls"],
        "SGACAR": ["paqueteriamassimodutti", "paqueteriaoysho", "paqueteriapalafolls"],
        "SGAMSS": ["paqueteriamassimodutti", "paqueteriaoysho", "paqueteriapalafolls", "prendacolgadamassimodutti"],
        "SGASQB": [
            "paqueteriamassimodutti", "paqueteriaoysho1", "paqueteriaoysho2", "paqueteriapalafolls1",
            "paqueteriapalafolls2", "paqueteriapalafolls3", "paqueteriapalafolls4", "paqueteriaespalafolls1",
            "paqueteriaespalafolls3", "paqueteriaespalafolls4", "paqueteriaoysho-1", "paqueteriaoysho-2",
            "paqueteriapalafolls-1", "paqueteriapalafolls-2", "paqueteriapalafolls-3", "paqueteriapalafolls-4",
        ],
        "SGASHP": ["paqueteriamassimodutti", "paqueteriaoysho", "paqueteriapalafolls"],
        "WMSXWSRV": ["paqueteriamassimodutti", "paqueteriaoysho", "paqueteriapalafolls", "prendacolgadamassimodutti", "prendacolgadapalafolls"],
    },
    "Openshift-SGA Arteixo 1": {
        "SGASOR": [
            "paqueteriaarteixo-c1", "paqueteriaarteixo-c2", "prendacolgadaarteixo-c1", "prendacolgadaarteixo-c2",
            "prendacolgadaarteixo-c5", "prendacolgadaarteixo-c6",
        ],
        "SGAASR": ["paqueteriaarteixo-siloshuttleshp", "paqueteriaarteixo-siloshuttleshp-new"],
        "SGARCP": ["paqueteriaarteixo", "paqueteriazarahomefactory", "prendacolgadaarteixo"],
        "SGAMSRSRV": ["paqueteriaarteixo", "prendacolgadaarteixo"],
        "SGAGIB": ["arteixogib", "prendacolgadaesarteixogib", "prendacolgadaarteixogib"],
        "SGACAR": ["paqueteriaarteixo"],
        "SGAMSS": ["paqueteriaarteixo"],
        "SGASHP": ["paqueteriaarteixo"],
        "WMSXWSRV": ["paqueteriaarteixo", "prendacolgadaarteixo"],
    },
    "AKS-IOP Southwest EU 3 Ontigola5 Logistics3": {
        "SGASOR": ["paqueteriaontigola5-c1", "paqueteriaontigola5-c2"],
        "SGAASR": ["paqueteriaontigola5-silo1"],
        "SGARCP": ["paqueteriaontigola5"],
        "SGAMSRSRV": ["paqueteriaontigola5"],
        "SGACAR": ["paqueteriaontigola5"],
        "SGAMSS": ["paqueteriaontigola5"],
        "SGASQB": ["paqueteriaontigola5"],
        "SGASHP": ["paqueteriaontigola5"],
        "WMSXWSRV": ["paqueteriaontigola5"],
    },
    "OpenShift-Logistica Cabanillas 1": {
        "SGASOR": [
            "paqueteriacabanillas-c1", "paqueteriacabanillas-c2", "paqueteriacabanillas-c3",
            "paqueteriacabanillas2-c1", "paqueteriacabanillas2-c2", "paqueteriacabanillas2-c3",
            "paqueteriacabanillas2-c4", "prendacolgadacabanillas-c1",
        ],
        "SGAASR": [
            "paqueteriacabanillas-silo1", "paqueteriacabanillas-silo2", "paqueteriacabanillas-siloshuttle",
            "paqueteriazarahomecabanillas-silo1", "paqueteriazarahomecabanillas-silo2",
            "paqueteriazarahomecabanillas-siloshuttle",
        ],
        "SGARCP": ["paqueteriacabanillas", "paqueteriazarahomecabanillas", "prendacolgadacabanillas"],
        "SGAMSRSRV": ["paqueteriacabanillas", "paqueteriacabanillas2", "paqueteriazarahomecabanillas", "prendacolgadacabanillas"],
        "SGAGIB": ["prendacolgadaescabanillasgib", "prendacolgadacabanillasgib"],
        "SGACAR": ["paqueteriacabanillas", "paqueteriazarahomecabanillas"],
        "SGAMSS": ["paqueteriacabanillas"],
        "SGASQB": [
            "paqueteriacabanillas1", "paqueteriacabanillas2", "paqueteriazhcabanillas1", "paqueteriazhcabanillas2",
            "paqueteriaescabanillas1", "paqueteriacabanillas-1", "paqueteriacabanillas-2",
            "paqueteriazarahomecabanillas-1",
        ],
        "SGASHP": ["paqueteriacabanillas", "paqueteriazarahome"],
        "WMSXWSRV": ["paqueteriacabanillas", "paqueteriazarahomecabanillas", "prendacolgadacabanillas"],
    },
    "Openshift-IOP Lelystad Logistics13": {
        "SGASOR": [
            "paqueterialelystad-c1", "paqueterialelystad-c2", "paqueterialelystad-c3", "paqueterialelystad-c4",
            "paqueterialelystad-c5", "paqueterialelystad-c6", "paqueterialelystad-c7", "paqueterialelystad-c8",
        ],
        "SGAASR": [
            "paqueterialelystad-silo1", "paqueterialelystad-silo2", "paqueterialelystad-siloshuttleshp",
            "prendacolgadalelystad-multishuttle3", "prendacolgadalelystad-multishuttle4",
            "prendacolgadalelystad-siloshuttle1", "prendacolgadalelystad-siloshuttle2",
        ],
        "SGARCP": ["macrotallernllelystad", "macrotallernllelystad2", "paqueterialelystad", "prendacolgadalelystad"],
        "SGAMSRSRV": ["macrotallernllelystad", "macrotallernllelystad2", "paqueterialelystad", "prendacolgadalelystad"],
        "SGAGIB": ["prendacolgadanllelystadgib", "prendacolgadalelystadgib"],
        "SGACAR": ["paqueterialelystad"],
        "SGAMSS": ["macrotallernllelystad", "macrotallernllelystad2", "paqueterialelystad", "prendacolgadalelystad"],
        "SGASQB": ["paqueterialelystad"],
        "SGASHP": ["macrotallernllelystad", "macrotallernllelystad2", "paqueterialelystad"],
        "WMSXWSRV": ["paqueterialelystad", "prendacolgadalelystad", "macrotallernllelystad2"],
    },
    "Openshift-IOP Malpica Logistics 20": {
        "SGASOR": ["paqueteriamalpica-c1", "paqueteriamalpica-c2", "paqueteriamalpica-c3"],
        "SGAASR": ["paqueteriamalpica-multishuttle1", "paqueteriamalpica-silo1", "prendacolgadamalpica-multishuttle1"],
        "SGARCP": ["paqueteriamalpica", "prendacolgadamalpica"],
        "SGAMSRSRV": ["paqueteriamalpica", "prendacolgadamalpica"],
        "SGAGIB": ["malpicagib", "prendacolgadaesmalpicagib", "prendacolgadamalpicagib"],
        "PMESGA": ["prendacolgadamalpica"],
        "SGACAR": ["paqueteriamalpica"],
        "SGAMSS": ["paqueteriamalpica"],
        "SGASQB": ["paqueteriamalpica", "paqueteriaesmalpica"],
        "SGASHP": ["paqueteriamalpica"],
        "WMSXWSRV": ["paqueteriamalpica", "prendacolgadamalpica"],
    },
    "Openshift-IOP Meco Logistics1": {
        "SGASOR": [
            "paqueteriameco-c1", "paqueteriameco-c2", "paqueteriameco-c3", "paqueteriameco-c4", "paqueteriameco-c5",
            "prendacolgadameco-c1", "prendacolgadameco-c2", "prendacolgadameco-c3", "prendacolgadameco-c4",
            "prendacolgadameco-c5", "prendacolgadameco-c6",
        ],
        "SGAASR": [
            "paqueteriameco-silo1", "paqueteriameco-silo2", "paqueteriameco-silo3", "paqueteriameco-siloshuttle",
            "paqueteriameco-siloshuttleshp", "prendacolgadameco-silo1",
        ],
        "SGARCP": ["paqueteriameco", "prendacolgadameco"],
        "SGAMSRSRV": ["paqueteriameco", "prendacolgadameco"],
        "SGAGIB": ["mecogib", "mecopick", "prendacolgadamecogib", "prendacolgadamecopick"],
        "PMESGA": ["prendacolgadameco"],
        "SGACAR": ["paqueteriameco"],
        "SGASQB": ["paqueteriameco", "paqueteriameco3", "paqueteriameco4", "paqueteriameco-1", "paqueteriameco-3", "paqueteriameco-4"],
        "SGASHP": ["paqueteriameco"],
        "WMSXWSRV": ["paqueteriameco", "prendacolgadameco"],
    },
    "Openshift-IOP Sallent Logistics4": {
        "SGASOR": ["paqueteriasallent-c1", "paqueteriasallent-c2", "paqueteriasallent-c3", "prendacolgadasallent-c1", "prendacolgadasallent-c2"],
        "SGAASR": [
            "paqueteriasallent", "paqueteriasallent-shuttle1", "paqueteriasallentsilo2", "paqueteriasallentsilo3",
            "paqueteriasallentsilo4", "prendacolgadasallentshuttle1",
        ],
        "SGARCP": ["paqueteriasallent", "prendacolgadasallent"],
        "SGAMSRSRV": ["paqueteriasallent", "prendacolgadasallent"],
        "SGAGIB": ["sallentgib", "sallentpick", "prendacolgadasallentgib", "prendacolgadasallentpick", "prendacolgadaessallentgib"],
        "SGACAR": ["paqueteriasallent"],
        "SGAMSS": ["paqueteriasallentperfumeria"],
        "SGASQB": [
            "paqueteriasallent1", "paqueteriasallent2", "paqueteriasallent3", "paqueteriaessallent1",
            "paqueteriaessallent2", "paqueteriaessallent3", "paqueteriasallent-1", "paqueteriasallent-2", "paqueteriasallent-3",
        ],
        "SGASHP": ["paqueteriasallent"],
        "WMSXWSRV": ["paqueteriasallent", "prendacolgadasallent"],
    },
    "Openshift-IOP Tempe Logistics6": {
        "SGASOR": ["paqueteriatempe3-c1", "paqueteriatempe3-c2"],
        "SGAASR": [
            "paqueteriatempe-silo3", "paqueteriatempe-siloshuttle", "paqueteriatempe3-commissioner",
            "paqueteriatempe3-magnus", "paqueteriatempe3-stratus1", "paqueteriatempe3-stratus2",
        ],
        "SGARCP": ["almacentempesatelite2", "paqueteriatempe", "paqueteriatempedevoluciones"],
        "SGAMSRSRV": ["almacentempesatelite2", "paqueteriatempe2", "paqueteriatempe3", "paqueteriatempe3devol"],
        "SGACAR": ["paqueteriatempe2", "paqueteriatempe3", "paqueteriatempesatelite2"],
        "SGAMSS": ["paqueteriatempe2", "paqueteriatempe3", "paqueteriatempesatelite2"],
        "SGASHP": ["paqueteriatempe2", "paqueteriatempe3"],
        "WMSXWSRV": ["almacentempesatelite2", "paqueteriatempe2", "paqueteriatempe3", "paqueteriatempe3devol"],
    },
    "Openshift-IOP Toledo Logistics16": {
        "SGASOR": ["paqueteriatoledo-c1", "paqueteriatoledo-c2"],
        "SGAASR": ["paqueteriatoledo-silopale", "paqueteriatoledo-siloshuttle2"],
        "SGARCP": ["ecomcadenasestoledo", "paqueteriatoledo"],
        "SGAMSRSRV": ["ecomcadenasestoledo", "paqueteriatoledo"],
        "SGACAR": ["ecomcadenasestoledo", "paqueteriatoledo"],
        "SGAMSS": ["ecomcadenasestoledo", "paqueteriatoledo"],
        "SGASQB": ["paqueteriatoledo1", "paqueteriatoledo2", "paqueteriatoledo-1", "paqueteriatoledo-2"],
        "SGASHP": ["paqueteriatoledo"],
        "WMSXWSRV": ["paqueteriatoledo"],
    },
    "Openshift-IOP Zaragoza Logistics8": {
        "SGASOR": [
            "paqueteriazaragoza-c1", "paqueteriazaragoza-c2", "prendacolgadazaragoza-c1", "prendacolgadazaragoza-c2",
            "prendacolgadazaragoza-c3", "prendacolgadazaragoza-c4", "prendacolgadazaragoza-c5",
            "prendacolgadazaragoza-c6", "prendacolgadazaragoza-c7", "prendacolgadazaragoza-c8", "prendacolgadazaragoza-c9",
        ],
        "SGAASR": [
            "paqueteriazaragoza-silo1", "paqueteriazaragoza-silo2", "paqueteriazaragoza-siloshuttle",
            "prendacolgadazaragoza-silo1", "prendacolgadazaragoza-siloshuttle1",
        ],
        "SGARCP": ["paqueteriazaragoza", "prendacolgadazaragoza"],
        "SGAMSRSRV": ["paqueteriazaragoza", "prendacolgadazaragoza"],
        "SGAGIB": ["zaragozagib", "zaragozapick", "prendacolgadazaragozagib", "prendacolgadazaragozapick"],
        "PMESGA": ["prendacolgadazaragoza"],
        "SGACAR": ["paqueteriazaragoza"],
        "SGAMSS": ["paqueteriazaragoza"],
        "SGASQB": ["paqueteriazaragoza", "paqueteriaeszaragoza"],
        "SGASHP": ["paqueteriazaragoza"],
        "WMSXWSRV": ["paqueteriazaragoza", "prendacolgadazaragoza"],
    },
    "Openshift-SSCC Arteixo": {
        "SGASOR": [
            "paqueteriamalpica-c1", "paqueteriamalpica-c2", "paqueteriamalpica-c3", "paqueteriatoledo-c1",
            "paqueteriatoledo-c2", "paqueteriaarteixo-c1", "paqueteriaarteixo-c2", "paqueteriadutti-c1",
            "paqueteriadutti-c2", "paqueteriameco-c1", "paqueteriameco-c2", "paqueteriameco-c3", "paqueteriameco-c4",
            "paqueteriameco-c5", "paqueterianaron-c1", "paqueterianaron-c2", "paqueteriaoysho-c1", "paqueteriaoysho-c2",
            "paqueteriapalafolls-c2", "paqueteriapalafolls-c3", "paqueteriapalafolls-c4", "paqueteriasallent-c1",
            "paqueteriasallent-c2", "paqueteriasallent-c3", "paqueteriacabanillas-c1", "paqueteriacabanillas-c2",
            "paqueteriacabanillas-c3", "paqueteriacabanillas2-c1", "paqueteriacabanillas2-c2", "paqueteriacabanillas2-c3",
            "paqueteriacabanillas2-c4", "paqueterialelystad-c1", "paqueterialelystad-c2", "paqueterialelystad-c3",
            "paqueterialelystad-c4", "paqueterialelystad-c5", "paqueterialelystad-c6", "paqueterialelystad-c7",
            "paqueterialelystad-c8", "paqueteriazaragoza-c1", "paqueteriazaragoza-c2", "prendacolgadaarteixo-c1",
            "prendacolgadaarteixo-c2", "prendacolgadaarteixo-c5", "prendacolgadaarteixo-c6", "prendacolgadadutti-c1",
            "prendacolgadameco-c1", "prendacolgadameco-c2", "prendacolgadameco-c3", "prendacolgadameco-c4",
            "prendacolgadameco-c5", "prendacolgadameco-c6", "prendacolgadapalafolls-c1", "prendacolgadasallent-c1",
            "prendacolgadasallent-c2", "prendacolgadacabanillas-c1",
        ],
        "SGAASR": ["paqueteriameco-siloshuttleshp", "paqueteriaontigola5-silo1", "paqueteriaarteixo-siloshuttleshp-new"],
        "SGASHP": ["paqueterialelystad", "paqueteriameco", "paqueteriaarteixo"],
        "WMSXWSRV": ["plataformaleon"],
    },
    "Openshift-IOP Naron Logistics2": {
        "SGASOR": ["paqueterianaron-c2"],
        "SGAASR": ["paqueterianaron-silo1"],
        "SGARCP": ["paqueterianaron"],
        "SGAMSRSRV": ["paqueterianaron"],
        "SGACAR": ["paqueterianaron"],
        "SGASQB": ["paqueterianaron"],
        "SGASHP": ["paqueterianaron"],
        "WMSXWSRV": ["paqueterianaron"],
    },
    "Openshift-IOP  Logistics15": {
        "SGARCP": ["ecomzaraesillescas"],
        "SGAMSRSRV": ["ecomzaraesillescas"],
        "SGACAR": ["ecomzaraesillescas"],
        "SGAMSS": ["ecomzaraesillescas"],
    },
    "Openshift-IOP Europa Logistics7": {
        "SGARCP": ["ecomzaraesmarchamalo", "ecomzaraesmarchamalosur"],
        "SGAMSRSRV": ["ecomzaraesmarchamalo", "ecomzaraesmarchamalosur"],
        "SGACAR": ["ecomzaraesmarchamalo", "ecomzaraesmarchamalosur", "ecomzaraesmarchamalosur2"],
        "SGAMSS": ["ecomzaraesmarchamalo", "ecomzaraesmarchamalosur"],
        "SGASHP": ["ecomzaraesmarchamalo", "ecomzaraesmarchamalosur"],
        "WMSXWSRV": [
            "almacenindipunt", "devolucionesarteixo", "macrotalleresarteixo", "macrotalleresguadalajara",
            "macrotallerestoledo", "macrotallereszaragoza1", "macrotallereszaragoza2", "macrotallereszaragoza3",
            "macrotallereszaragoza4", "macrotallereszaragoza5", "paqueteriazarahomefactory", "talleresazuqueca",
            "talleresillescas", "talleresmarchamalo", "tallergratenas", "tallerplstrykow", "tallerreopplkatowice",
            "tallertrgebze", "wstr381", "zaragozaplaza", "macrotalleresfranqueses", "macrotalleresmeco",
            "tallerukbrackmills", "localesriudellots", "macrotallerescabanillas", "almacenmanualtrestambul",
            "macrotalleresalovera", "macrotalleresontigola", "localzajohannesburgo", "macrotallerescabanillas2",
            "talleritcortemaggiore", "tallertrtuzla", "macrotalleresleon", "paqueteriamanualontigolazh",
        ],
    },
    "Openshift-IOP Illescas Logistics17": {
        "SGARCP": ["ecomzaraesillescas"],
        "SGAMSRSRV": ["ecomzaraesillescas"],
        "SGACAR": ["ecomzaraesillescas"],
        "SGAMSS": ["ecomzaraesillescas"],
    },
    "Openshift-IOP Leon Logistics12": {
        "SGARCP": ["plataformaleon"],
        "SGAMSRSRV": ["plataformaleonpaq", "plataformaleonprc"],
        "SGAGIB": ["plataformaleongib", "prendacolgadaplataformaleongib"],
        "SGACAR": ["plataformaleon", "plataformaleondevoluciones"],
        "SGAMSS": ["plataformaleon"],
        "SGASHP": ["plataformaleon"],
        "WMSXWSRV": ["plataformaleon"],
    },
    "Openshift-SSCC China": {
        "SGARCP": ["almacenmanualcnshanghai", "ecomzaracnjinshan", "ecomzaracnsongjiang", "localcnbeijing", "localcndongguan", "localcnshanghai", "localcnchengdu"],
        "SGAMSRSRV": ["almacenmanualcnshanghai", "almacenmanualcnshanghaireturns", "ecomzaracnjinshan", "ecomzaracnsongjiang", "localcnbeijing", "localcndongguan", "localcnshanghai", "localcnchengdu"],
        "SGACAR": ["almacenmanualcnshanghai", "almacenmanualcnshanghaireturns", "ecomzaracnsongjiang", "localcnbeijing", "localcndongguan", "localcnshanghai", "localcnchengdu"],
        "SGAMSS": ["almacenmanualcnshanghai-r1", "almacenmanualcnshanghai-r2", "almacenmanualcnshanghai-r3", "almacenmanualcnshanghai-r4", "almacenmanualcnshanghai-r5", "almacenmanualcnshanghaireturns-r1", "almacenmanualcnshanghaireturns-r2", "ecomzaracnsongjiang"],
        "SGASHP": ["almacenmanualcnshanghaireturns", "localcnbeijing", "localcndongguan", "localcnshanghai", "localcnchengdu"],
        "WMSXWSRV": ["almacenmanualcnshanghaireturns", "localcnshanghai", "localcndongguan", "localcnbeijing"],
    },
    "AKS-IOP East US 1 Whiamer1": {
        "SGARCP": [
            "almacenlocalbrsaopaulo", "almacenmanualbrsaopaulo", "almacenmanualmxtultitlan", "almacenmanualmxvallejo",
            "almacenperfumeriabrasil", "ecomcadenasbrsaopaulo", "ecomcadenascaontario", "ecomcadenascaontario2",
            "ecomcadenasclsantiago", "ecomcadenasmxtultitlan", "ecomcadenasuseaston", "ecomcadenasuseaston6",
            "ecomcadenasuycanelones", "ecomzaraargarin", "ecomzaraartortuguitas", "ecomzarabrsaopaulo",
            "ecomzaracatoronto", "ecomzaracavancouver", "ecomzaraclsantiago", "ecomzaracochia", "ecomzarauseaston",
            "ecomzarausrialto", "ecomzarauymontevideo", "localarbuenosaires", "localcatoronto", "localcavancouver",
            "localmxcuautitlan", "localuseaston", "localuslosangeles", "localusmiami", "tallerbrsaopaulo",
            "tallermxaifa", "tallerreopcaontario", "tallerreopcatoronto", "tallerreopclsantiago", "talleruseaston",
            "tallerusmiami", "tallerusrialto", "tallercatoronto",
        ],
        "SGAMSRSRV": [
            "almacenlocalbrsaopaulo", "almacenmanualbrsaopaulo", "almacenmanualmxtultitlan", "almacenmanualmxvallejo",
            "almacenperfumeriabrasil", "ecomcadenasbrsaopaulo", "ecomcadenascaontario", "ecomcadenascaontario2",
            "ecomcadenasclsantiago", "ecomcadenasmxtultitlan", "ecomcadenasuseaston", "ecomcadenasuseaston6",
            "ecomcadenasuycanelones", "ecomzaraargarin", "ecomzaraartortuguitas", "ecomzarabrsaopaulo",
            "ecomzaracatoronto", "ecomzaracavancouver", "ecomzaraclsantiago", "ecomzaracochia", "ecomzarauseaston",
            "ecomzarausrialto", "ecomzarauymontevideo", "localarbuenosaires", "localcatoronto", "localcavancouver",
            "localmxcuautitlan", "localuseaston", "localuslosangeles", "localusmiami", "tallerreopbrsaopaulo",
            "tallerreopcaontario", "tallerreopclsantiago", "tallerreopecommx329", "tallerreopusaeaston",
            "tallerusrialto", "wsca268", "wsus333",
        ],
        "SGACAR": [
            "almacenlocalbrsaopaulo", "almacenmanualbrsaopaulo", "almacenmanualmxtultitlan", "almacenmanualmxvallejo",
            "almacenperfumeriabrasil", "ecomcadenasbrsaopaulo", "ecomcadenascaontario", "ecomcadenascaontario2",
            "ecomcadenasclsantiago", "ecomcadenasmxtultitlan", "ecomcadenasuycanelones", "ecomzaraargarin",
            "ecomzaraartortuguitas", "ecomzarabrsaopaulo", "ecomzaracatoronto", "ecomzaracavancouver",
            "ecomzaraclsantiago", "ecomzaracochia", "ecomzaramxaifa", "ecomzarapelima", "ecomzarauseaston",
            "ecomzarausmiami", "ecomzarausnazareth", "ecomzarausrialto", "ecomzarauymontevideo", "localarbuenosaires",
            "localcatoronto", "localcavancouver", "localmxcuautitlan", "localuseaston", "localuslosangeles",
            "localusmiami", "tallerreopbrsaopaulo", "tallerreopcaontario", "tallerreopclsantiago",
            "tallerreopusaeaston", "tallerusrialto", "wsca268", "wsmx329", "wsus333",
        ],
        "SGAMSS": [
            "almacenmanualbrsaopaulo-paq", "almacenmanualbrsaopaulo-prc", "almacenmanualbrsaopaulo-tem",
            "almacenmanualmxtultitlan", "almacenmanualmxvallejo-r1", "almacenmanualmxvallejo-r2",
            "almacenmanualmxvallejo-r3", "almacenmanualmxvallejo-r4", "almacenperfumeriabrasil",
            "ecomcadenasbrsaopaulo", "ecomcadenascaontario", "ecomcadenascaontario2", "ecomcadenasclsantiago",
            "ecomcadenasmxtultitlan", "ecomcadenasuycanelones", "ecomzaraargarin", "ecomzaraartortuguitas-paq",
            "ecomzaraartortuguitas-prc", "ecomzaraartortuguitas-tempe", "ecomzarabrsaopaulo", "ecomzaracatoronto",
            "ecomzaracavancouver", "ecomzaraclsantiago", "ecomzaracochia", "ecomzarauseaston", "ecomzarausrialto",
            "ecomzarauymontevideo", "tallerreopcaontario",
        ],
        "SGASHP": [
            "almacenlocalbrsaopaulo", "almacenmanualbrsaopaulo", "almacenmanualmxtultitlan", "almacenmanualmxvallejo",
            "almacenperfumeriabrasil", "localarbuenosaires", "localcatoronto", "localcavancouver",
            "localmxcuautitlan", "localuseaston", "localuslosangeles", "localusmiami", "tallermxaifa",
            "tallerreopcaontario", "tallerreopclsantiago", "talleruseaston", "tallerusmiami", "tallerusrialto",
            "wsbr370", "wsca268", "wsmx329", "wsus333",
        ],
        "WMSXWSRV": [
            "almacenlocalbrsaopaulo", "almacenmanualmxvallejo", "localcatoronto", "localuseaston", "tallermxaifa",
            "tallerreopcaontario", "tallerreopclsantiago", "talleruseaston", "tallerusmiami", "localarbuenosaires",
            "localcavancouver", "almacenmanualmxtultitlan", "tallerusrialto", "almacenmanualbrsaopaulo",
            "almacenperfumeriabrasil", "localusmiami", "localmxcuautitlan", "tallercatoronto",
        ],
    },
    "AKS-IOP Southeast AS 1 Whiapac1": {
        "SGARCP": [
            "almacenmanualinluhari", "ecomcadenascnhongkong", "ecomcadenasinfarukh", "ecomcadenasjpichikawa",
            "ecomcadenaskricheon", "ecomzaraausidney", "ecomzaraidjakarta", "ecomzaraindelhi", "ecomzarajpichikawa",
            "ecomzarakricheon", "ecomzaraphmanila", "ecomzarathbangkok", "ecomzaratwtaoyuan", "ecomzaravnhochiminh",
            "localhktsuenwan", "localjptokio", "localkrseoul", "localtwtaipei", "tallercnhongkong", "tallercnnaniwa",
            "tallerinluhari", "tallerjptokio", "tallerkricheon", "tallerreopausidney",
        ],
        "SGAMSRSRV": [
            "almacenmanualinluhari", "ecomcadenasinfarukh", "ecomzaraausidney", "ecomzaracnhongkong",
            "ecomzaraindelhi", "ecomzarajpichikawa", "ecomzarakricheon", "ecomzaratwtaoyuan", "localhktsuenwan",
            "localjptokio", "localkrseoul", "localtwtaipei", "tallercnnaniwa", "tallerreopausidney",
            "tallerreopin377", "wshk365", "wsjp292", "ecomzaraphmanila",
        ],
        "SGACAR": [
            "almacenmanualinluhari", "ecomcadenasinfarukh", "ecomzaraausidney", "ecomzaracnhongkong",
            "ecomzaraindelhi", "ecomzarajpichikawa", "ecomzarakricheon", "ecomzaratwtaoyuan", "localhktsuenwan",
            "localjptokio", "localkrseoul", "localtwtaipei", "tallercnnaniwa", "tallerreopausidney",
            "tallerreopin377", "tallerreopkr376", "wshk365", "wsjp292", "ecomzaraphmanila",
        ],
        "SGAMSS": ["almacenmanualinluhari-r1", "almacenmanualinluhari-r2", "ecomcadenasinfarukh", "ecomzaraausidney", "ecomzaraindelhi", "ecomzarajpichikawa", "ecomzarakricheon", "ecomzaratwtaoyuan", "ecomzaraphmanila"],
        "SGASHP": ["almacenmanualinluhari", "localhktsuenwan", "localjptokio", "localkrseoul", "localtwtaipei", "tallercnnaniwa", "tallerreopausidney", "tallerreopin377", "wsjp292", "wskr376"],
        "WMSXWSRV": ["tallerjptokio", "tallerreopausidney", "almacenmanualinluhari", "tallercnnaniwa", "localtwtaipei", "tallercnhongkong", "tallerinluhari"],
    },
}

PLATFORM_CHOICES: list[str] = list(SLOT_CHOICES.keys())


def get_projectkeys_for_platform(platform: str) -> list[str]:
    return [pk for pk, slots in SLOT_CHOICES.get(platform, {}).items() if slots]


def get_slots_for(platform: str, projectkey: str) -> list[str]:
    return SLOT_CHOICES.get(platform, {}).get(projectkey, [])


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

    labels = f'{{projectkey="{pk}",platform="{platform_value}",environment="{env}"}}'
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
    platform: str,
    projectkey: str,
    environment: str,
    target: str,
    free_text_fragment: str,
) -> tuple[str, str]:
    try:
        query = build_logql(
            projectkey=projectkey,
            platform=platform,
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

        default_projectkeys = get_projectkeys_for_platform(DEFAULT_PLATFORM)
        default_slots = get_slots_for(DEFAULT_PLATFORM, DEFAULT_PROJECTKEY)

        with gr.Row():
            platform = gr.Dropdown(
                label="platform",
                choices=PLATFORM_CHOICES,
                value=DEFAULT_PLATFORM,
                allow_custom_value=False,
            )
            projectkey = gr.Dropdown(
                label="projectkey",
                choices=default_projectkeys,
                value=DEFAULT_PROJECTKEY,
                allow_custom_value=False,
            )
            environment = gr.Textbox(label="environment", value=DEFAULT_ENVIRONMENT)
            target = gr.Dropdown(
                label="Slot / Regex objetivo",
                choices=default_slots,
                value=(default_slots[0] if default_slots else ""),
                allow_custom_value=True,
            )

        def _on_platform_change(platform_value: str):
            projectkeys = get_projectkeys_for_platform(platform_value) or [""]
            new_pk = projectkeys[0]
            slots = get_slots_for(platform_value, new_pk)
            return (
                gr.Dropdown(choices=projectkeys, value=new_pk),
                gr.Dropdown(choices=slots, value=(slots[0] if slots else "")),
            )

        def _on_projectkey_change(platform_value: str, projectkey_value: str):
            slots = get_slots_for(platform_value, projectkey_value)
            return gr.Dropdown(choices=slots, value=(slots[0] if slots else ""))

        platform.change(
            fn=_on_platform_change,
            inputs=[platform],
            outputs=[projectkey, target],
        )

        projectkey.change(
            fn=_on_projectkey_change,
            inputs=[platform, projectkey],
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
                platform,
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
