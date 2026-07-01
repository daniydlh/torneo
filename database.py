"""
database.py
Centraliza toda la comunicación con Supabase.
Ninguna otra parte de la app debe importar la librería supabase directamente.
"""

import streamlit as st
from supabase import create_client


# ---------------------------------------------------------------------------
# Cliente
# ---------------------------------------------------------------------------

@st.cache_resource
def obtener_cliente():
    """Crea (una sola vez por sesión) el cliente de Supabase usando los secrets."""
    url = st.secrets["SUPABASE_URL"]
    clave = st.secrets["SUPABASE_KEY"]
    return create_client(url, clave)


def _limpiar_cache():
    """Limpia la cache de lecturas tras cualquier escritura en la base de datos."""
    obtener_equipos.clear()
    obtener_partidos.clear()
    obtener_fotos.clear()
    obtener_configuracion.clear()
    obtener_djs.clear()


# ---------------------------------------------------------------------------
# EQUIPOS
# ---------------------------------------------------------------------------

@st.cache_data(ttl=30)
def obtener_equipos(categoria: str = None) -> list[dict]:
    """Devuelve la lista de equipos, opcionalmente filtrada por categoría."""
    cliente = obtener_cliente()
    consulta = cliente.table("equipos").select("*").order("nombre")
    if categoria:
        consulta = consulta.eq("categoria", categoria)
    return consulta.execute().data


def crear_equipo(nombre: str, categoria: str, grupo: str = None) -> None:
    cliente = obtener_cliente()
    cliente.table("equipos").insert({
        "nombre": nombre,
        "categoria": categoria,
        "grupo": grupo,
    }).execute()
    _limpiar_cache()


def actualizar_equipo(id_equipo: int, **campos) -> None:
    cliente = obtener_cliente()
    cliente.table("equipos").update(campos).eq("id", id_equipo).execute()
    _limpiar_cache()


def eliminar_equipo(id_equipo: int) -> None:
    cliente = obtener_cliente()
    cliente.table("equipos").delete().eq("id", id_equipo).execute()
    _limpiar_cache()


# ---------------------------------------------------------------------------
# PARTIDOS
# ---------------------------------------------------------------------------

@st.cache_data(ttl=15)
def obtener_partidos(categoria: str = None, fase: str = None) -> list[dict]:
    """Devuelve los partidos con los nombres de los equipos ya resueltos."""
    cliente = obtener_cliente()
    consulta = cliente.table("partidos").select(
        "*, local:equipo_local_id(id,nombre,grupo), visitante:equipo_visitante_id(id,nombre,grupo)"
    ).order("fecha_hora")
    if categoria:
        consulta = consulta.eq("categoria", categoria)
    if fase:
        consulta = consulta.eq("fase", fase)
    return consulta.execute().data


def crear_partido(categoria, fase, equipo_local_id, equipo_visitante_id,
                   fecha_hora, grupo=None, estado="pendiente") -> dict:
    cliente = obtener_cliente()
    resultado = cliente.table("partidos").insert({
        "categoria": categoria,
        "fase": fase,
        "grupo": grupo,
        "equipo_local_id": equipo_local_id,
        "equipo_visitante_id": equipo_visitante_id,
        "fecha_hora": fecha_hora,
        "estado": estado,
    }).execute()
    _limpiar_cache()
    return resultado.data[0] if resultado.data else None


def actualizar_partido(id_partido: int, **campos) -> None:
    cliente = obtener_cliente()
    cliente.table("partidos").update(campos).eq("id", id_partido).execute()
    _limpiar_cache()


def eliminar_partido(id_partido: int) -> None:
    cliente = obtener_cliente()
    cliente.table("partidos").delete().eq("id", id_partido).execute()
    _limpiar_cache()


# ---------------------------------------------------------------------------
# FOTOS (galería)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=20)
def obtener_fotos(solo_aprobadas: bool = True) -> list[dict]:
    cliente = obtener_cliente()
    consulta = cliente.table("fotos").select("*").order("fecha", desc=True)
    if solo_aprobadas:
        consulta = consulta.eq("aprobada", True)
    return consulta.execute().data


def crear_foto(url, public_id, nombre) -> None:
    cliente = obtener_cliente()
    cliente.table("fotos").insert({
        "url": url,
        "public_id": public_id,
        "nombre": nombre,
        "aprobada": False,
    }).execute()
    _limpiar_cache()


def aprobar_foto(id_foto: int) -> None:
    cliente = obtener_cliente()
    cliente.table("fotos").update({"aprobada": True}).eq("id", id_foto).execute()
    _limpiar_cache()


def eliminar_foto(id_foto: int) -> None:
    cliente = obtener_cliente()
    cliente.table("fotos").delete().eq("id", id_foto).execute()
    _limpiar_cache()


# ---------------------------------------------------------------------------
# CONFIGURACIÓN (clave / valor) - textos editables: descripción, contacto, ubicación...
# ---------------------------------------------------------------------------

@st.cache_data(ttl=30)
def obtener_configuracion() -> dict:
    """Devuelve toda la configuración como un diccionario clave -> valor."""
    cliente = obtener_cliente()
    filas = cliente.table("configuracion").select("*").execute().data
    return {fila["clave"]: fila["valor"] for fila in filas}


def guardar_configuracion(clave: str, valor: str) -> None:
    cliente = obtener_cliente()
    cliente.table("configuracion").upsert({"clave": clave, "valor": valor}).execute()
    _limpiar_cache()


# ---------------------------------------------------------------------------
# DJs (horario de la noche)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=30)
def obtener_djs() -> list[dict]:
    """Devuelve los DJs ordenados por hora de inicio."""
    cliente = obtener_cliente()
    return cliente.table("djs").select("*").order("hora_inicio").execute().data


def crear_dj(nombre: str, hora_inicio: str, hora_fin: str, estilo: str, logo_url: str, logo_public_id: str) -> None:
    cliente = obtener_cliente()
    cliente.table("djs").insert({
        "nombre": nombre,
        "hora_inicio": hora_inicio,
        "hora_fin": hora_fin,
        "estilo": estilo,
        "logo_url": logo_url,
        "logo_public_id": logo_public_id,
    }).execute()
    _limpiar_cache()


def actualizar_dj(id_dj: int, **campos) -> None:
    cliente = obtener_cliente()
    cliente.table("djs").update(campos).eq("id", id_dj).execute()
    _limpiar_cache()


def eliminar_dj(id_dj: int) -> None:
    cliente = obtener_cliente()
    cliente.table("djs").delete().eq("id", id_dj).execute()
    _limpiar_cache()
