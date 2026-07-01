"""
app.py
Punto de entrada único de la aplicación. Aquí vive TODA la navegación
(no se usan páginas múltiples de Streamlit). El resto de módulos
(database, torneo, gallery) solo exponen funciones que esta app consume.
"""

import base64
from datetime import datetime, date, time as time_cls

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

import database as bd
import torneo
import gallery


@st.cache_data
def _logo_base64() -> str:
    with open("assets/logo.png", "rb") as f:
        return base64.b64encode(f.read()).decode()


# ---------------------------------------------------------------------------
# Configuración general de la página
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="BasketKastil — Torneo Nocturno",
    page_icon="assets/logo.png",
    layout="centered",
    initial_sidebar_state="collapsed",
)

with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

SECCIONES = [
    ("inicio", "🏠", "Inicio"),
    ("masculino", "🏀", "Masc."),
    ("femenino", "🏀", "Fem."),
    ("calendario", "📅", "Calendario"),
    ("galeria", "📸", "Galería"),
    ("djs", "🎧", "DJs"),
    ("admin", "🔑", "Admin"),
]

if "pagina" not in st.session_state:
    st.session_state.pagina = "inicio"
if "admin_autenticado" not in st.session_state:
    st.session_state.admin_autenticado = False


def ir_a(pagina: str):
    st.session_state.pagina = pagina


# ---------------------------------------------------------------------------
# Cabecera
# ---------------------------------------------------------------------------

def mostrar_cabecera(config: dict):
    st.markdown(
        f"""
        <a href="?pagina=quienes_somos" style="text-decoration:none;color:inherit;">
            <div class="cabecera-app">
                <img src="data:image/png;base64,{_logo_base64()}">
            </div>
        </a>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Componentes pequeños reutilizables
# ---------------------------------------------------------------------------

def parsear_hora(texto: str) -> time_cls | None:
    """Convierte un texto tipo '19:37' o '9:5' en un objeto time. Devuelve None si no es válido."""
    texto = (texto or "").strip()
    for formato in ("%H:%M", "%H.%M"):
        try:
            return datetime.strptime(texto, formato).time()
        except ValueError:
            continue
    return None


def chip_estado(estado: str) -> str:
    etiquetas = {"pendiente": "Pendiente", "en_juego": "En juego", "finalizado": "Finalizado"}
    return f'<span class="chip chip-{estado}">{etiquetas.get(estado, estado)}</span>'


def fila_partido_html(p: dict, mostrar_categoria: bool = False) -> str:
    local = torneo.nombre_equipo(p, "local")
    visitante = torneo.nombre_equipo(p, "visitante")
    hora = datetime.fromisoformat(str(p["fecha_hora"]).replace("Z", "")).strftime("%H:%M")
    if p["estado"] == "finalizado":
        marcador = f'{p["puntos_local"]} - {p["puntos_visitante"]}'
    elif p["estado"] == "en_juego":
        marcador = f'{p.get("puntos_local") or 0} - {p.get("puntos_visitante") or 0}'
    else:
        marcador = "vs"
    icono_cat = "🏀♂️" if p["categoria"] == "masculino" else "🏀♀️"
    prefijo = f"{icono_cat} " if mostrar_categoria else ""
    return f"""
    <div class="fila-partido">
        <div class="hora">{hora}</div>
        <div class="equipos">{prefijo}{local} <span class="marcador">{marcador}</span> {visitante}</div>
        {chip_estado(p['estado'])}
    </div>
    """


# ---------------------------------------------------------------------------
# PÁGINA · INICIO
# ---------------------------------------------------------------------------

def pagina_inicio(config: dict):
    columnas = st.columns(2)
    accesos = [
        ("🧡 Quiénes somos", "quienes_somos"), ("🏀 Masculino", "masculino"),
        ("🏀 Femenino", "femenino"), ("📅 Calendario", "calendario"),
        ("🎧 DJs", "djs"), ("📸 Galería", "galeria"),
    ]
    for i, (etiqueta, destino) in enumerate(accesos):
        with columnas[i % 2]:
            if st.button(etiqueta, key=f"acceso_{destino}", use_container_width=True):
                ir_a(destino)
                st.rerun()

    if config.get("ubicacion_direccion"):
        st.markdown("##### 📍 Ubicación")
        direccion = config["ubicacion_direccion"]
        components.html(
            f'<iframe width="100%" height="220" style="border:0;border-radius:16px" '
            f'src="https://maps.google.com/maps?q={direccion}&output=embed"></iframe>',
            height=230,
        )

    if config.get("contacto_telefono") or config.get("contacto_email"):
        lineas = []
        if config.get("contacto_telefono"):
            lineas.append(f"📞 {config['contacto_telefono']}")
        if config.get("contacto_email"):
            lineas.append(f"✉️ {config['contacto_email']}")
        st.markdown(
            '<div class="tarjeta"><strong style="color:var(--crema)">☎️ Contacto</strong><br>'
            + "<br>".join(f'<span style="color:var(--crema-suave)">{l}</span>' for l in lineas)
            + "</div>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# PÁGINA · ¿QUIÉNES SOMOS?
# ---------------------------------------------------------------------------

def pagina_quienes_somos(config: dict):
    st.markdown("### 🧡 ¿Quiénes somos?")
    texto = config.get("quienes_somos", "Aún no hemos añadido esta información. El administrador puede editarla desde el panel de Configuración.")
    st.markdown(
        f"""<div class="tarjeta"><p style="color:var(--crema-suave);white-space:pre-wrap">{texto}</p></div>""",
        unsafe_allow_html=True,
    )
    if st.button("⬅️ Volver al inicio"):
        ir_a("inicio")
        st.rerun()


# ---------------------------------------------------------------------------
# PÁGINA · TORNEO MASCULINO
# ---------------------------------------------------------------------------

def pagina_masculino():
    st.markdown("### 🏀 Torneo Masculino")
    equipos = bd.obtener_equipos("masculino")
    partidos = bd.obtener_partidos("masculino")

    if len(equipos) < 12:
        st.warning("Aún no se han registrado los 12 equipos masculinos. El administrador puede añadirlos en la sección Admin.")

    torneo.actualizar_eliminatorias_masculino(equipos, partidos)
    partidos = bd.obtener_partidos("masculino")  # recargar tras posible creación de eliminatorias

    pestañas = st.tabs(["Grupo A", "Grupo B", "Grupo C", "Grupo D", "Eliminatorias"])
    clasificaciones = torneo.clasificaciones_masculino(equipos, partidos)

    for pestaña, grupo in zip(pestañas[:4], torneo.GRUPOS_MASCULINO):
        with pestaña:
            tabla = clasificaciones[grupo]
            if tabla.empty:
                st.info("Sin equipos asignados a este grupo todavía.")
            else:
                st.dataframe(tabla, hide_index=True, use_container_width=True)
            st.markdown("##### Partidos")
            partidos_grupo = [
                p for p in partidos
                if p["fase"] == "grupos"
                and torneo.nombre_equipo(p, "local") in tabla["Equipo"].tolist()
            ]
            for p in partidos_grupo:
                st.markdown(fila_partido_html(p), unsafe_allow_html=True)

    with pestañas[4]:
        semis = [p for p in partidos if p["fase"] == "semifinal"]
        final = [p for p in partidos if p["fase"] == "final"]
        if not semis:
            st.info("Las semifinales se generarán automáticamente al completar la fase de grupos.")
        else:
            st.markdown("##### Semifinales")
            for p in semis:
                st.markdown(fila_partido_html(p), unsafe_allow_html=True)
        if final:
            st.markdown("##### 🏆 Final")
            for p in final:
                st.markdown(fila_partido_html(p), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# PÁGINA · TORNEO FEMENINO
# ---------------------------------------------------------------------------

def pagina_femenino():
    st.markdown("### 🏀 Torneo Femenino")
    equipos = bd.obtener_equipos("femenino")
    partidos = bd.obtener_partidos("femenino")

    if not equipos:
        st.warning("Aún no se han registrado equipos femeninos.")
        return

    torneo.actualizar_final_femenino(equipos, partidos)
    partidos = bd.obtener_partidos("femenino")

    st.markdown("##### Clasificación")
    tabla = torneo.clasificacion_femenino(equipos, partidos)
    st.dataframe(tabla, hide_index=True, use_container_width=True)
    st.caption("Los dos primeros clasificados disputan la final.")

    st.markdown("##### Partidos de liguilla")
    for p in [p for p in partidos if p["fase"] == "grupos"]:
        st.markdown(fila_partido_html(p), unsafe_allow_html=True)

    final = [p for p in partidos if p["fase"] == "final"]
    if final:
        st.markdown("##### 🏆 Final")
        for p in final:
            st.markdown(fila_partido_html(p), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# PÁGINA · CALENDARIO
# ---------------------------------------------------------------------------

def pagina_calendario():
    st.markdown("### 📅 Calendario de partidos")
    partidos = bd.obtener_partidos()
    if not partidos:
        st.info("Todavía no hay partidos programados.")
        return

    filtro = st.selectbox("Filtrar por categoría", ["Todas", "Masculino", "Femenino"])
    if filtro != "Todas":
        partidos = [p for p in partidos if p["categoria"] == filtro.lower()]

    for p in sorted(partidos, key=lambda x: x["fecha_hora"]):
        st.markdown(fila_partido_html(p, mostrar_categoria=True), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# PÁGINA · GALERÍA
# ---------------------------------------------------------------------------

def pagina_galeria():
    st.markdown("### 📸 Galería")
    pestaña_ver, pestaña_subir = st.tabs(["Ver fotos", "Subir foto"])
    with pestaña_ver:
        fotos = bd.obtener_fotos(solo_aprobadas=True)
        gallery.mostrar_galeria(fotos)
    with pestaña_subir:
        gallery.formulario_subida()


# ---------------------------------------------------------------------------
# PÁGINA · DJs
# ---------------------------------------------------------------------------

def fila_dj_html(dj: dict) -> str:
    return f"""
    <div class="tarjeta-dj">
        <img src="{dj['logo_url']}">
        <div>
            <div class="nombre-dj">{dj['nombre']}</div>
            <div class="horario-dj">{dj['hora_inicio']} – {dj['hora_fin']}</div>
            <div class="estilo-dj">{dj.get('estilo') or ''}</div>
        </div>
    </div>
    """


def pagina_djs():
    st.markdown("### 🎧 Horario de DJs")
    djs = bd.obtener_djs()
    if not djs:
        st.info("Todavía no hay DJs programados.")
        return
    for dj in djs:
        st.markdown(fila_dj_html(dj), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# PÁGINA · ADMINISTRADOR
# ---------------------------------------------------------------------------

def panel_equipos():
    st.markdown("#### 🏀 Equipos")
    categoria = st.radio("Categoría", ["masculino", "femenino"], horizontal=True, key="cat_equipos")
    equipos = bd.obtener_equipos(categoria)

    with st.expander("➕ Añadir equipo"):
        nombre = st.text_input("Nombre del equipo", key="nuevo_equipo_nombre")
        grupo = None
        if categoria == "masculino":
            grupo = st.selectbox("Grupo", torneo.GRUPOS_MASCULINO, key="nuevo_equipo_grupo")
        if st.button("Guardar equipo", key="guardar_nuevo_equipo"):
            if nombre.strip():
                bd.crear_equipo(nombre.strip(), categoria, grupo)
                st.success(f"Equipo '{nombre}' añadido.")
                st.rerun()
            else:
                st.warning("Escribe un nombre.")

    for e in equipos:
        c1, c2, c3 = st.columns([3, 2, 1])
        with c1:
            nuevo_nombre = st.text_input("Nombre", value=e["nombre"], key=f"nombre_{e['id']}", label_visibility="collapsed")
        with c2:
            if categoria == "masculino":
                nuevo_grupo = st.selectbox(
                    "Grupo", torneo.GRUPOS_MASCULINO,
                    index=torneo.GRUPOS_MASCULINO.index(e["grupo"]) if e.get("grupo") in torneo.GRUPOS_MASCULINO else 0,
                    key=f"grupo_{e['id']}", label_visibility="collapsed",
                )
            else:
                nuevo_grupo = None
        with c3:
            if st.button("🗑️", key=f"borrar_equipo_{e['id']}"):
                bd.eliminar_equipo(e["id"])
                st.rerun()
        if nuevo_nombre != e["nombre"] or nuevo_grupo != e.get("grupo"):
            bd.actualizar_equipo(e["id"], nombre=nuevo_nombre, grupo=nuevo_grupo)


def panel_partidos():
    st.markdown("#### 📅 Partidos")
    equipos = bd.obtener_equipos()
    if len(equipos) < 2:
        st.info("Añade primero al menos dos equipos.")
        return

    with st.expander("➕ Crear partido"):
        categoria = st.selectbox("Categoría", ["masculino", "femenino"], key="np_categoria")
        equipos_cat = [e for e in equipos if e["categoria"] == categoria]
        nombres_equipos = [e["nombre"] for e in equipos_cat]
        if len(nombres_equipos) < 2:
            st.warning("Esta categoría no tiene suficientes equipos.")
        else:
            col1, col2 = st.columns(2)
            local = col1.selectbox("Equipo local", nombres_equipos, key="np_local")
            visitante = col2.selectbox("Equipo visitante", [n for n in nombres_equipos if n != local], key="np_visitante")
            fase = st.selectbox("Fase", ["grupos", "semifinal", "final"], key="np_fase")
            fecha_sel = st.date_input("Fecha", value=date.today(), key="np_fecha")
            hora_texto = st.text_input("Hora (formato 24h, ej. 19:37)", value="20:00", key="np_hora")
            if st.button("Crear partido", key="np_crear"):
                hora_sel = parsear_hora(hora_texto)
                if hora_sel is None:
                    st.warning("Introduce una hora válida, por ejemplo 19:37.")
                else:
                    id_local = next(e["id"] for e in equipos_cat if e["nombre"] == local)
                    id_visitante = next(e["id"] for e in equipos_cat if e["nombre"] == visitante)
                    grupo = next((e["grupo"] for e in equipos_cat if e["nombre"] == local), None) if fase == "grupos" else None
                    fecha_hora = datetime.combine(fecha_sel, hora_sel).isoformat()
                    bd.crear_partido(categoria, fase, id_local, id_visitante, fecha_hora, grupo)
                    st.success("Partido creado.")
                    st.rerun()

    st.markdown("##### Editar partidos existentes")
    filtro_cat = st.selectbox("Filtrar categoría", ["Todas", "masculino", "femenino"], key="ep_filtro")
    partidos = bd.obtener_partidos(None if filtro_cat == "Todas" else filtro_cat)

    for p in sorted(partidos, key=lambda x: x["fecha_hora"]):
        local = torneo.nombre_equipo(p, "local")
        visitante = torneo.nombre_equipo(p, "visitante")
        with st.expander(f"{local} vs {visitante} · {p['fase']} · {p['categoria']}"):
            c1, c2 = st.columns(2)
            pl = c1.number_input("Puntos local", min_value=0, value=p.get("puntos_local") or 0, key=f"pl_{p['id']}")
            pv = c2.number_input("Puntos visitante", min_value=0, value=p.get("puntos_visitante") or 0, key=f"pv_{p['id']}")
            estado = st.selectbox(
                "Estado", ["pendiente", "en_juego", "finalizado"],
                index=["pendiente", "en_juego", "finalizado"].index(p["estado"]),
                key=f"estado_{p['id']}",
            )
            fecha_actual = datetime.fromisoformat(str(p["fecha_hora"]).replace("Z", ""))
            nueva_fecha = st.date_input("Fecha", value=fecha_actual.date(), key=f"fecha_{p['id']}")
            nueva_hora_texto = st.text_input(
                "Hora (formato 24h, ej. 19:37)",
                value=fecha_actual.strftime("%H:%M"),
                key=f"hora_{p['id']}",
            )
            cguardar, cborrar = st.columns(2)
            if cguardar.button("💾 Guardar cambios", key=f"guardar_partido_{p['id']}", use_container_width=True):
                nueva_hora = parsear_hora(nueva_hora_texto)
                if nueva_hora is None:
                    st.warning("Introduce una hora válida, por ejemplo 19:37.")
                else:
                    bd.actualizar_partido(
                        p["id"],
                        puntos_local=int(pl), puntos_visitante=int(pv), estado=estado,
                        fecha_hora=datetime.combine(nueva_fecha, nueva_hora).isoformat(),
                    )
                    st.success("Partido actualizado.")
                    st.rerun()
            if cborrar.button("🗑️ Eliminar partido", key=f"borrar_partido_{p['id']}", use_container_width=True):
                bd.eliminar_partido(p["id"])
                st.rerun()


def panel_configuracion(config: dict):
    st.markdown("#### ⚙️ Configuración general")
    with st.form("form_configuracion"):
        nombre_torneo = st.text_input("Nombre del torneo", value=config.get("nombre_torneo", "BasketKastil"))
        descripcion = st.text_area("Descripción", value=config.get("descripcion", ""))
        direccion = st.text_input("Dirección / ubicación", value=config.get("ubicacion_direccion", ""))
        telefono = st.text_input("Teléfono de contacto", value=config.get("contacto_telefono", ""))
        email = st.text_input("Email de contacto", value=config.get("contacto_email", ""))
        quienes_somos = st.text_area("Texto de '¿Quiénes somos?'", value=config.get("quienes_somos", ""), height=160)
        if st.form_submit_button("Guardar configuración"):
            bd.guardar_configuracion("nombre_torneo", nombre_torneo)
            bd.guardar_configuracion("descripcion", descripcion)
            bd.guardar_configuracion("ubicacion_direccion", direccion)
            bd.guardar_configuracion("contacto_telefono", telefono)
            bd.guardar_configuracion("contacto_email", email)
            bd.guardar_configuracion("quienes_somos", quienes_somos)
            st.success("Configuración guardada.")
            st.rerun()


def panel_djs():
    st.markdown("#### 🎧 DJs")
    djs = bd.obtener_djs()

    with st.expander("➕ Añadir DJ"):
        nombre = st.text_input("Nombre del DJ", key="nuevo_dj_nombre")
        c1, c2 = st.columns(2)
        hora_inicio = c1.text_input("Hora inicio (ej. 22:00)", key="nuevo_dj_inicio")
        hora_fin = c2.text_input("Hora fin (ej. 23:30)", key="nuevo_dj_fin")
        estilo = st.text_input("Descripción / estilo musical", key="nuevo_dj_estilo")
        logo = st.file_uploader("Logo del DJ", type=["jpg", "jpeg", "png", "webp"], key="nuevo_dj_logo")
        if st.button("Guardar DJ", key="guardar_nuevo_dj"):
            hi, hf = parsear_hora(hora_inicio), parsear_hora(hora_fin)
            if not nombre.strip():
                st.warning("Escribe un nombre.")
            elif hi is None or hf is None:
                st.warning("Introduce horas válidas, por ejemplo 22:00.")
            elif not logo:
                st.warning("Sube un logo para el DJ.")
            else:
                url, public_id = gallery.subir_imagen(logo, carpeta="torneo_baloncesto/djs")
                bd.crear_dj(nombre.strip(), hi.strftime("%H:%M"), hf.strftime("%H:%M"), estilo.strip(), url, public_id)
                st.success(f"DJ '{nombre}' añadido.")
                st.rerun()

    for dj in djs:
        with st.expander(f"{dj['nombre']} · {dj['hora_inicio']}–{dj['hora_fin']}"):
            c1, c2 = st.columns(2)
            nuevo_nombre = c1.text_input("Nombre", value=dj["nombre"], key=f"dj_nombre_{dj['id']}")
            nuevo_estilo = c2.text_input("Estilo", value=dj.get("estilo") or "", key=f"dj_estilo_{dj['id']}")
            c3, c4 = st.columns(2)
            nueva_inicio = c3.text_input("Hora inicio", value=dj["hora_inicio"], key=f"dj_inicio_{dj['id']}")
            nueva_fin = c4.text_input("Hora fin", value=dj["hora_fin"], key=f"dj_fin_{dj['id']}")
            nuevo_logo = st.file_uploader("Cambiar logo (opcional)", type=["jpg", "jpeg", "png", "webp"], key=f"dj_logo_{dj['id']}")
            cguardar, cborrar = st.columns(2)
            if cguardar.button("💾 Guardar cambios", key=f"guardar_dj_{dj['id']}", use_container_width=True):
                hi, hf = parsear_hora(nueva_inicio), parsear_hora(nueva_fin)
                if hi is None or hf is None:
                    st.warning("Introduce horas válidas, por ejemplo 22:00.")
                else:
                    campos = {
                        "nombre": nuevo_nombre,
                        "estilo": nuevo_estilo,
                        "hora_inicio": hi.strftime("%H:%M"),
                        "hora_fin": hf.strftime("%H:%M"),
                    }
                    if nuevo_logo:
                        gallery.eliminar_imagen(dj["logo_public_id"])
                        url, public_id = gallery.subir_imagen(nuevo_logo, carpeta="torneo_baloncesto/djs")
                        campos["logo_url"] = url
                        campos["logo_public_id"] = public_id
                    bd.actualizar_dj(dj["id"], **campos)
                    st.success("DJ actualizado.")
                    st.rerun()
            if cborrar.button("🗑️ Eliminar DJ", key=f"borrar_dj_{dj['id']}", use_container_width=True):
                gallery.eliminar_imagen(dj["logo_public_id"])
                bd.eliminar_dj(dj["id"])
                st.rerun()


def pagina_admin(config: dict):
    st.markdown("### 🔑 Administrador")

    if not st.session_state.admin_autenticado:
        clave = st.text_input("Contraseña de administrador", type="password")
        if st.button("Entrar"):
            if clave == st.secrets.get("ADMIN_PASSWORD", ""):
                st.session_state.admin_autenticado = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")
        return

    if st.button("Cerrar sesión"):
        st.session_state.admin_autenticado = False
        st.rerun()

    pestañas = st.tabs(["Equipos", "Partidos", "Fotos", "DJs", "Configuración"])
    with pestañas[0]:
        panel_equipos()
    with pestañas[1]:
        panel_partidos()
    with pestañas[2]:
        gallery.panel_moderacion_fotos()
    with pestañas[3]:
        panel_djs()
    with pestañas[4]:
        panel_configuracion(config)


# ---------------------------------------------------------------------------
# Navegación inferior
# ---------------------------------------------------------------------------

def mostrar_nav_inferior():
    with st.container():
        columnas = st.columns(len(SECCIONES))
        for col, (clave, icono, etiqueta) in zip(columnas, SECCIONES):
            with col:
                es_activo = st.session_state.pagina == clave
                if st.button(
                    f"{icono}  \n{etiqueta}",
                    key=f"nav_{clave}",
                    use_container_width=True,
                    type="primary" if es_activo else "secondary",
                ):
                    ir_a(clave)
                    st.rerun()


# ---------------------------------------------------------------------------
# Enrutado principal
# ---------------------------------------------------------------------------

def main():
    if "pagina" in st.query_params:
        st.session_state.pagina = st.query_params["pagina"]
        st.query_params.clear()

    config = bd.obtener_configuracion()
    mostrar_cabecera(config)

    pagina = st.session_state.pagina
    if pagina == "inicio":
        pagina_inicio(config)
    elif pagina == "quienes_somos":
        pagina_quienes_somos(config)
    elif pagina == "masculino":
        pagina_masculino()
    elif pagina == "femenino":
        pagina_femenino()
    elif pagina == "calendario":
        pagina_calendario()
    elif pagina == "galeria":
        pagina_galeria()
    elif pagina == "djs":
        pagina_djs()
    elif pagina == "admin":
        pagina_admin(config)

    mostrar_nav_inferior()


if __name__ == "__main__":
    main()
