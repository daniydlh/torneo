"""
torneo.py
Lógica pura del torneo: clasificaciones, desempates (basket average)
y generación automática de semifinales / final.
No contiene nada de interfaz: solo cálculo y escritura en base de datos.
"""

from datetime import datetime, timedelta
import pandas as pd

import database as bd

GRUPOS_MASCULINO = ["A", "B", "C", "D"]


# ---------------------------------------------------------------------------
# Estadísticas y clasificación (válido tanto para grupos masculinos
# como para la liguilla femenina: solo depende de los partidos recibidos)
# ---------------------------------------------------------------------------

def _construir_estadisticas(equipos: list[dict], partidos: list[dict]) -> dict:
    """Calcula PJ, PG, PP, PF, PC por equipo a partir de los partidos finalizados."""
    stats = {
        e["id"]: {"equipo": e, "pj": 0, "pg": 0, "pp": 0, "pf": 0, "pc": 0}
        for e in equipos
    }
    for p in partidos:
        if p.get("estado") != "finalizado":
            continue
        if p.get("puntos_local") is None or p.get("puntos_visitante") is None:
            continue
        id_local, id_visitante = p["equipo_local_id"], p["equipo_visitante_id"]
        if id_local not in stats or id_visitante not in stats:
            continue
        pl, pv = p["puntos_local"], p["puntos_visitante"]
        stats[id_local]["pj"] += 1
        stats[id_visitante]["pj"] += 1
        stats[id_local]["pf"] += pl
        stats[id_local]["pc"] += pv
        stats[id_visitante]["pf"] += pv
        stats[id_visitante]["pc"] += pl
        if pl > pv:
            stats[id_local]["pg"] += 1
            stats[id_visitante]["pp"] += 1
        elif pv > pl:
            stats[id_visitante]["pg"] += 1
            stats[id_local]["pp"] += 1
    return stats


def ordenar_clasificacion(equipos: list[dict], partidos: list[dict]) -> list[dict]:
    """
    Devuelve la lista de estadísticas ordenada según:
    1) victorias (descendente)
    2) diferencia de puntos a favor menos en contra (descendente)
    3) puntos a favor, como último desempate (descendente)
    Mismo criterio para masculino y femenino.
    """
    stats = _construir_estadisticas(equipos, partidos)
    return sorted(
        stats.values(),
        key=lambda e: (e["pg"], e["pf"] - e["pc"], e["pf"]),
        reverse=True,
    )


def clasificacion_a_dataframe(clasificacion: list[dict]) -> pd.DataFrame:
    filas = []
    for pos, item in enumerate(clasificacion, start=1):
        filas.append({
            "Pos": pos,
            "Equipo": item["equipo"]["nombre"],
            "PJ": item["pj"],
            "PG": item["pg"],
            "PP": item["pp"],
            "PF": item["pf"],
            "PC": item["pc"],
            "Dif": item["pf"] - item["pc"],
        })
    return pd.DataFrame(filas)


# ---------------------------------------------------------------------------
# TORNEO MASCULINO — 4 grupos de 3, semifinales y final automáticas
# ---------------------------------------------------------------------------

def clasificaciones_masculino(equipos: list[dict], partidos: list[dict]) -> dict[str, pd.DataFrame]:
    """Devuelve {grupo: DataFrame_clasificacion} para A, B, C y D."""
    partidos_grupos = [p for p in partidos if p["fase"] == "grupos"]
    resultado = {}
    for grupo in GRUPOS_MASCULINO:
        equipos_grupo = [e for e in equipos if e.get("grupo") == grupo]
        partidos_grupo = [
            p for p in partidos_grupos
            if p["equipo_local_id"] in [e["id"] for e in equipos_grupo]
            or p["equipo_visitante_id"] in [e["id"] for e in equipos_grupo]
        ]
        clasificacion = ordenar_clasificacion(equipos_grupo, partidos_grupo)
        resultado[grupo] = clasificacion_a_dataframe(clasificacion)
    return resultado


def _fase_completa(partidos_fase: list[dict], minimo: int) -> bool:
    finalizados = [p for p in partidos_fase if p["estado"] == "finalizado"]
    return len(partidos_fase) >= minimo and len(finalizados) == len(partidos_fase)


def _ganador(partido: dict) -> int:
    """Id del equipo ganador de un partido finalizado."""
    if partido["puntos_local"] >= partido["puntos_visitante"]:
        return partido["equipo_local_id"]
    return partido["equipo_visitante_id"]


def actualizar_eliminatorias_masculino(equipos: list[dict], partidos: list[dict]) -> None:
    """
    Comprueba el estado del torneo masculino y crea automáticamente
    semifinales y/o final en cuanto la fase anterior está completa.
    Es idempotente: nunca duplica partidos ya creados.
    """
    partidos_grupos = [p for p in partidos if p["fase"] == "grupos"]
    partidos_semis = [p for p in partidos if p["fase"] == "semifinal"]
    partidos_final = [p for p in partidos if p["fase"] == "final"]

    # 1) Semifinales: requieren los 12 partidos de grupos finalizados (3 por grupo x 4 grupos)
    if not partidos_semis and _fase_completa(partidos_grupos, minimo=12):
        clasificaciones = clasificaciones_masculino(equipos, partidos)
        primeros = {}
        for grupo, tabla in clasificaciones.items():
            if tabla.empty:
                return
            nombre_primero = tabla.iloc[0]["Equipo"]
            equipo_obj = next(e for e in equipos if e["nombre"] == nombre_primero and e.get("grupo") == grupo)
            primeros[grupo] = equipo_obj

        if len(primeros) == 4:
            ultima_fecha = max((p["fecha_hora"] for p in partidos_grupos), default=datetime.now().isoformat())
            base = datetime.fromisoformat(str(ultima_fecha).replace("Z", "")) + timedelta(hours=2)
            bd.crear_partido(
                categoria="masculino", fase="semifinal",
                equipo_local_id=primeros["A"]["id"], equipo_visitante_id=primeros["D"]["id"],
                fecha_hora=base.isoformat(),
            )
            bd.crear_partido(
                categoria="masculino", fase="semifinal",
                equipo_local_id=primeros["B"]["id"], equipo_visitante_id=primeros["C"]["id"],
                fecha_hora=(base + timedelta(minutes=45)).isoformat(),
            )
        return

    # 2) Final: requiere las 2 semifinales finalizadas
    if not partidos_final and partidos_semis and _fase_completa(partidos_semis, minimo=2):
        ganador_sf1 = _ganador(partidos_semis[0])
        ganador_sf2 = _ganador(partidos_semis[1])
        ultima_fecha = max(p["fecha_hora"] for p in partidos_semis)
        base = datetime.fromisoformat(str(ultima_fecha).replace("Z", "")) + timedelta(hours=1)
        bd.crear_partido(
            categoria="masculino", fase="final",
            equipo_local_id=ganador_sf1, equipo_visitante_id=ganador_sf2,
            fecha_hora=base.isoformat(),
        )


# ---------------------------------------------------------------------------
# TORNEO FEMENINO — 5 equipos, partidos manuales, los 2 mejores van a la final
# ---------------------------------------------------------------------------

def clasificacion_femenino(equipos: list[dict], partidos: list[dict]) -> pd.DataFrame:
    partidos_grupo = [p for p in partidos if p["fase"] == "grupos"]
    clasificacion = ordenar_clasificacion(equipos, partidos_grupo)
    return clasificacion_a_dataframe(clasificacion)


def actualizar_final_femenino(equipos: list[dict], partidos: list[dict]) -> None:
    """
    Crea automáticamente la final femenina cuando todos los partidos de
    la liguilla (creados manualmente por el administrador) están finalizados.
    Idempotente: no duplica la final si ya existe.
    """
    partidos_grupo = [p for p in partidos if p["fase"] == "grupos"]
    partidos_final = [p for p in partidos if p["fase"] == "final"]

    if partidos_final or not partidos_grupo:
        return
    if not _fase_completa(partidos_grupo, minimo=1):
        return

    tabla = clasificacion_femenino(equipos, partidos)
    if len(tabla) < 2:
        return

    primero = next(e for e in equipos if e["nombre"] == tabla.iloc[0]["Equipo"])
    segundo = next(e for e in equipos if e["nombre"] == tabla.iloc[1]["Equipo"])
    ultima_fecha = max(p["fecha_hora"] for p in partidos_grupo)
    base = datetime.fromisoformat(str(ultima_fecha).replace("Z", "")) + timedelta(hours=1)

    bd.crear_partido(
        categoria="femenino", fase="final",
        equipo_local_id=primero["id"], equipo_visitante_id=segundo["id"],
        fecha_hora=base.isoformat(),
    )


# ---------------------------------------------------------------------------
# Utilidades compartidas (página de Inicio / Calendario)
# ---------------------------------------------------------------------------

def proximo_partido(partidos: list[dict]) -> dict | None:
    """Devuelve el próximo partido pendiente o en juego, ordenado por fecha."""
    candidatos = [p for p in partidos if p["estado"] in ("pendiente", "en_juego")]
    if not candidatos:
        return None
    return sorted(candidatos, key=lambda p: p["fecha_hora"])[0]


def nombre_equipo(partido: dict, lado: str) -> str:
    """lado: 'local' o 'visitante'. Devuelve el nombre ya resuelto por el join de Supabase."""
    info = partido.get(lado)
    if info and isinstance(info, dict):
        return info.get("nombre", "?")
    return "?"
