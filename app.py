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
    nombre_torneo = config.get("nombre_torneo", "BasketKastil")
    st.markdown(
        f"""
        <div class="cabecera-app">
            <img src="data:image/png;base64,{_logo_base64()}">
            <div>
                <div class="titulo-torneo">{nombre_torneo}</div>
                <div class="subtitulo-torneo">Torneo nocturno de baloncesto 5x5</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Componentes pequeños reutilizables
# ---------------------------------------------------------------------------

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


def tarjeta_hero_proximo_partido(siguiente: dict | None):
    """Tarjeta destacada con el próximo partido y cuenta atrás en vivo.
    Se construye como un único bloque HTML/JS autocontenido (vía components.html)
    para poder animar el reloj con JavaScript real."""
    if siguiente:
        local = torneo.nombre_equipo(siguiente, "local")
        visitante = torneo.nombre_equipo(siguiente, "visitante")
        subtitulo = f"{siguiente['fase'].capitalize()} · {siguiente['categoria'].capitalize()}"
        objetivo_js = f'new Date("{siguiente["fecha_hora"]}").getTime()'
        reloj_inicial = "--:--:--"
    else:
        local, visitante, subtitulo = "Por confirmar", "", "Aún no hay próximo partido programado"
        objetivo_js = "null"
        reloj_inicial = ""

    components.html(
        f"""
        <div class="tarjeta-hero">
            <div class="equipos-vs">🏀 {local}{' vs ' + visitante if visitante else ''}</div>
            <div class="subtitulo">{subtitulo}</div>
            <div id="reloj" class="reloj">{reloj_inicial}</div>
        </div>
        <script>
        const objetivo = {objetivo_js};
        function actualizar() {{
            const el = document.getElementById("reloj");
            if (!objetivo) {{ return; }}
            const diff = objetivo - new Date().getTime();
            if (diff <= 0) {{ el.innerHTML = "¡Ya está en juego!"; return; }}
            const h = Math.floor(diff / 3600000);
            const m = Math.floor((diff % 3600000) / 60000);
            const s = Math.floor((diff % 60000) / 1000);
            el.innerHTML = String(h).padStart(2,'0') + ":" + String(m).padStart(2,'0') + ":" + String(s).padStart(2,'0');
        }}
        actualizar();
        setInterval(actualizar, 1000);
        </script>
        <style>
            html, body {{ background: transparent !important; margin:0; }}
            .tarjeta-hero{{
                background: linear-gradient(135deg, #c8541f 0%, #f4a93b 100%);
                border-radius: 26px;
                padding: 20px;
                color:#1a1208;
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
                box-shadow: 0 10px 30px rgba(226,103,42,0.35);
            }}
            .equipos-vs{{ font-size:1.2rem; font-weight:800; }}
            .subtitulo{{ font-size:.8rem; opacity:.85; margin-top:2px; }}
            .reloj{{
                font-size: 2.1rem; font-weight:900; letter-spacing: 1px;
                font-family: 'Courier New', monospace; margin-top:10px;
            }}
        </style>
        """,
        height=165,
    )


# ---------------------------------------------------------------------------
# PÁGINA · INICIO
# ---------------------------------------------------------------------------

def pagina_inicio(config: dict):
    todos_partidos = bd.obtener_partidos()
    siguiente = torneo.proximo_partido(todos_partidos)
    tarjeta_hero_proximo_partido(siguiente)

    with st.container(key="tarjeta_info"):
        st.markdown(f"#### {config.get('nombre_torneo', 'BasketKastil')}")
        st.write(config.get("descripcion", "Una noche de baloncesto, equipos y comunidad."))

    st.markdown("##### Accesos rápidos")
    columnas = st.columns(2)
    accesos = [
        ("🏀 Masculino", "masculino"), ("🏀 Femenino", "femenino"),
        ("📅 Calendario", "calendario"), ("📸 Galería", "galeria"),
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
        with st.container(key="tarjeta_contacto"):
            st.markdown("##### ☎️ Contacto")
            if config.get("contacto_telefono"):
                st.write(f"📞 {config['contacto_telefono']}")
            if config.get("contacto_email"):
                st.write(f"✉️ {config['contacto_email']}")


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
        equipos = bd.obtener_equipos()
        partidos = bd.obtener_partidos()
        gallery.formulario_subida(equipos, partidos)


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
            hora_sel = st.time_input("Hora", value=time_cls(20, 0), key="np_hora")
            if st.button("Crear partido", key="np_crear"):
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
            nueva_hora = st.time_input("Hora", value=fecha_actual.time(), key=f"hora_{p['id']}")
            cguardar, cborrar = st.columns(2)
            if cguardar.button("💾 Guardar cambios", key=f"guardar_partido_{p['id']}", use_container_width=True):
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
        if st.form_submit_button("Guardar configuración"):
            bd.guardar_configuracion("nombre_torneo", nombre_torneo)
            bd.guardar_configuracion("descripcion", descripcion)
            bd.guardar_configuracion("ubicacion_direccion", direccion)
            bd.guardar_configuracion("contacto_telefono", telefono)
            bd.guardar_configuracion("contacto_email", email)
            st.success("Configuración guardada.")
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

    pestañas = st.tabs(["Equipos", "Partidos", "Fotos", "Configuración"])
    with pestañas[0]:
        panel_equipos()
    with pestañas[1]:
        panel_partidos()
    with pestañas[2]:
        gallery.panel_moderacion_fotos()
    with pestañas[3]:
        panel_configuracion(config)


# ---------------------------------------------------------------------------
# Navegación inferior
# ---------------------------------------------------------------------------

def mostrar_nav_inferior():
    with st.container(key="nav_inferior"):
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
    config = bd.obtener_configuracion()
    mostrar_cabecera(config)

    pagina = st.session_state.pagina
    if pagina == "inicio":
        pagina_inicio(config)
    elif pagina == "masculino":
        pagina_masculino()
    elif pagina == "femenino":
        pagina_femenino()
    elif pagina == "calendario":
        pagina_calendario()
    elif pagina == "galeria":
        pagina_galeria()
    elif pagina == "admin":
        pagina_admin(config)

    mostrar_nav_inferior()


if __name__ == "__main__":
    main()
