"""
gallery.py
Integración con Cloudinary (almacenamiento de imágenes) y componentes
de interfaz de la galería de fotos del torneo.
Supabase solo guarda los metadatos (url, public_id, nombre, equipo...).
"""

import streamlit as st
import cloudinary
import cloudinary.uploader

import database as bd

_CONFIGURADO = False


def _configurar_cloudinary():
    global _CONFIGURADO
    if _CONFIGURADO:
        return
    cloudinary.config(
        cloud_name=st.secrets["CLOUDINARY_CLOUD_NAME"],
        api_key=st.secrets["CLOUDINARY_API_KEY"],
        api_secret=st.secrets["CLOUDINARY_API_SECRET"],
        secure=True,
    )
    _CONFIGURADO = True


def subir_imagen(archivo, carpeta: str = "torneo_baloncesto") -> tuple[str, str]:
    """Sube un archivo a Cloudinary y devuelve (url_segura, public_id)."""
    _configurar_cloudinary()
    resultado = cloudinary.uploader.upload(
        archivo,
        folder=carpeta,
        resource_type="image",
    )
    return resultado["secure_url"], resultado["public_id"]


def eliminar_imagen(public_id: str) -> None:
    """Borra la imagen de Cloudinary (se usa al eliminar una foto desde Admin)."""
    _configurar_cloudinary()
    try:
        cloudinary.uploader.destroy(public_id)
    except Exception:
        pass  # si ya no existe en Cloudinary no debe romper el borrado en la BD


# ---------------------------------------------------------------------------
# Componentes de interfaz
# ---------------------------------------------------------------------------

def formulario_subida(equipos: list[dict], partidos: list[dict]):
    st.markdown("#### 📤 Subir una fotografía")
    with st.form("formulario_subida_foto", clear_on_submit=True):
        archivo = st.file_uploader("Elige una imagen", type=["jpg", "jpeg", "png", "webp"])
        nombre = st.text_input("Tu nombre (opcional)")
        opciones_equipo = ["—"] + sorted({e["nombre"] for e in equipos})
        equipo = st.selectbox("Equipo relacionado (opcional)", opciones_equipo)
        opciones_partido = ["—"] + [
            f"{p['id']} · {p.get('local', {}).get('nombre', '?')} vs {p.get('visitante', {}).get('nombre', '?')}"
            for p in partidos
        ]
        partido_sel = st.selectbox("Partido relacionado (opcional)", opciones_partido)
        comentario = st.text_area("Comentario (opcional)", max_chars=200)
        enviado = st.form_submit_button("📸 Enviar fotografía", use_container_width=True)

        if enviado:
            if not archivo:
                st.warning("Selecciona primero una imagen.")
                return
            with st.spinner("Subiendo imagen..."):
                url, public_id = subir_imagen(archivo)
                partido_id = None
                if partido_sel != "—":
                    partido_id = int(partido_sel.split(" · ")[0])
                bd.crear_foto(
                    url=url,
                    public_id=public_id,
                    nombre=nombre or None,
                    equipo=None if equipo == "—" else equipo,
                    partido_id=partido_id,
                    comentario=comentario or None,
                )
            st.success("¡Foto enviada! Quedará visible cuando un administrador la apruebe. 🎉")


def mostrar_galeria(fotos: list[dict], columnas: int = 3):
    if not fotos:
        st.info("Todavía no hay fotografías aprobadas en la galería.")
        return

    filas = [fotos[i:i + columnas] for i in range(0, len(fotos), columnas)]
    for fila in filas:
        cols = st.columns(columnas)
        for col, foto in zip(cols, fila):
            with col:
                pie = foto.get("equipo") or ""
                if foto.get("comentario"):
                    pie = f"{pie} — {foto['comentario']}" if pie else foto["comentario"]
                pie_html = f'<div class="pie-foto">{pie}</div>' if pie else ""
                st.markdown(
                    f"""
                    <div class="tarjeta-foto">
                        <img src="{foto['url']}" style="width:100%;border-radius:12px;display:block;">
                        {pie_html}
                        <a href="{foto['url']}" download target="_blank" class="boton-descarga">⬇️ Descargar</a>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def panel_moderacion_fotos():
    """Usado solo desde la sección Administrador."""
    st.markdown("#### 🕓 Fotos pendientes de aprobación")
    pendientes = bd.obtener_fotos(solo_aprobadas=False)
    pendientes = [f for f in pendientes if not f["aprobada"]]

    if not pendientes:
        st.success("No hay fotos pendientes. ✅")
    else:
        for foto in pendientes:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.image(foto["url"], use_container_width=True)
            with c2:
                st.write(f"**Equipo:** {foto.get('equipo') or '—'}")
                st.write(f"**Comentario:** {foto.get('comentario') or '—'}")
                ca, cb = st.columns(2)
                if ca.button("✅ Aprobar", key=f"aprobar_{foto['id']}", use_container_width=True):
                    bd.aprobar_foto(foto["id"])
                    st.rerun()
                if cb.button("🗑️ Eliminar", key=f"borrar_pend_{foto['id']}", use_container_width=True):
                    eliminar_imagen(foto["public_id"])
                    bd.eliminar_foto(foto["id"])
                    st.rerun()
            st.divider()

    st.markdown("#### ✅ Fotos ya aprobadas")
    aprobadas = bd.obtener_fotos(solo_aprobadas=True)
    if not aprobadas:
        st.caption("Ninguna todavía.")
    for foto in aprobadas:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.image(foto["url"], use_container_width=True)
        with c2:
            st.write(f"**Equipo:** {foto.get('equipo') or '—'}")
            if st.button("🗑️ Eliminar", key=f"borrar_aprob_{foto['id']}"):
                eliminar_imagen(foto["public_id"])
                bd.eliminar_foto(foto["id"])
                st.rerun()
        st.divider()
