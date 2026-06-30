# BasketKastil — App del torneo nocturno de baloncesto 5x5

Aplicación en Streamlit para gestionar el torneo: equipos, partidos, clasificaciones automáticas
(con desempate por basket average en el masculino), calendario, galería de fotos con aprobación
y panel de administrador. Pensada para configurarse una vez y no tocar el código durante el torneo.

## 1. Estructura del proyecto

```
torneo/
    app.py          → navegación y todas las páginas
    database.py     → toda la comunicación con Supabase
    torneo.py       → clasificaciones, desempates y generación automática de eliminatorias
    gallery.py      → integración con Cloudinary y componentes de la galería
    style.css       → estética tipo app móvil
    requirements.txt
    sql/schema.sql  → esquema de base de datos para Supabase
    assets/
        logo.png
        cartel.jpg
    .streamlit/
        secrets.toml.example
```

## 2. Configurar Supabase (base de datos)

1. Crea un proyecto gratuito en [supabase.com](https://supabase.com).
2. Ve a **SQL Editor** → **New query**, pega el contenido completo de `sql/schema.sql` y pulsa **Run**.
   Esto crea las tablas `equipos`, `partidos`, `fotos` y `configuracion`.
3. Ve a **Project Settings → API** y copia:
   - **Project URL** → será tu `SUPABASE_URL` 
   - **anon public key** → será tu `SUPABASE_KEY`
   - Project RUL: https://wmsaazrurlrugisvdick.supabase.co/rest/v1/
   - anon key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indtc2FhenJ1cmxydWdpc3ZkaWNrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODI4MzM3ODAsImV4cCI6MjA5ODQwOTc4MH0.6AXOSA9ZpXGzhLIgyE_XIxiDxksbXnybJz3d-d8PkyQ

> Por simplicidad, el esquema deja Row Level Security desactivado (la protección del panel de
> administrador la hace la propia app con contraseña). Si más adelante queréis reforzar la
> seguridad a nivel de base de datos, en `sql/schema.sql` hay un ejemplo de políticas RLS comentado.

## 3. Configurar Cloudinary (almacenamiento de fotos)

1. Crea una cuenta gratuita en [cloudinary.com](https://cloudinary.com).
2. En el **Dashboard** copia: **Cloud name**, **API Key** y **API Secret**.
3. No es necesario crear nada más: la carpeta `torneo_baloncesto` se crea sola al subir la primera foto.
Cloud name: fsp6f7aj
API Keys: 218444232357969
API Secret: pPNP2rEbF7y9CzBIQy3BDsjrER4

## 4. Configurar las credenciales en la app

Copia el archivo de ejemplo y rellena tus credenciales reales:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edita `.streamlit/secrets.toml` con tus valores de Supabase, Cloudinary y la contraseña que
quieras usar para el panel de Administrador (`ADMIN_PASSWORD`).

Si despliegas en **Streamlit Community Cloud**, pega el mismo contenido en
**App settings → Secrets** en lugar de subir el archivo.

## 5. Ejecutar en local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 6. Primeros pasos dentro de la app

1. Entra en **🔑 Administrador** con la contraseña configurada.
2. Pestaña **Equipos**: añade los 12 equipos masculinos (asignando grupo A/B/C/D, 3 por grupo)
   y los 5 equipos femeninos.
3. Pestaña **Partidos**: crea los partidos de la fase de grupos (masculino y femenino).
   Las semifinales y la final masculinas, y la final femenina, se generan **solas** en cuanto
   se completan los resultados de la fase anterior — no hay que crearlas a mano.
4. Pestaña **Configuración**: añade nombre del torneo, descripción, dirección y contacto.
5. Comparte la web con los equipos para que suban fotos desde **📸 Galería**; aparecerán en
   la galería pública en cuanto las apruebes desde **Administrador → Fotos**.

## 7. Formato del torneo (recordatorio)

- **Masculino**: 12 equipos, 4 grupos de 3 (todos contra todos dentro del grupo). El 1º de cada
  grupo pasa a semifinales (cruce A vs D, B vs C) y los ganadores juegan la final.
- **Femenino**: 5 equipos, partidos creados a mano por el administrador (cada equipo juega
  como máximo 2 partidos). Los 2 primeros de la clasificación juegan la final automáticamente.
