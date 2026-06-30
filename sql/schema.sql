-- =============================================================================
-- BasketKastil — Esquema de base de datos para Supabase
-- Ejecutar completo en: Supabase > SQL Editor > New query > Run
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Tabla: equipos
-- ---------------------------------------------------------------------------
create table if not exists equipos (
    id          bigint generated always as identity primary key,
    nombre      text not null,
    categoria   text not null check (categoria in ('masculino', 'femenino')),
    grupo       text check (grupo in ('A', 'B', 'C', 'D') or grupo is null),
    creado_en   timestamptz default now()
);

-- ---------------------------------------------------------------------------
-- Tabla: partidos
-- ---------------------------------------------------------------------------
create table if not exists partidos (
    id                  bigint generated always as identity primary key,
    categoria           text not null check (categoria in ('masculino', 'femenino')),
    fase                text not null check (fase in ('grupos', 'semifinal', 'final')),
    grupo               text check (grupo in ('A', 'B', 'C', 'D') or grupo is null),
    equipo_local_id      bigint not null references equipos(id) on delete cascade,
    equipo_visitante_id  bigint not null references equipos(id) on delete cascade,
    puntos_local         integer,
    puntos_visitante     integer,
    fecha_hora          timestamptz not null,
    estado              text not null default 'pendiente'
                         check (estado in ('pendiente', 'en_juego', 'finalizado')),
    creado_en           timestamptz default now()
);

create index if not exists idx_partidos_categoria on partidos(categoria);
create index if not exists idx_partidos_fecha on partidos(fecha_hora);

-- ---------------------------------------------------------------------------
-- Tabla: fotos (galería) — las imágenes viven en Cloudinary, aquí solo metadatos
-- ---------------------------------------------------------------------------
create table if not exists fotos (
    id          bigint generated always as identity primary key,
    url         text not null,
    public_id   text not null,
    nombre      text,
    equipo      text,
    partido_id  bigint references partidos(id) on delete set null,
    comentario  text,
    fecha       timestamptz default now(),
    aprobada    boolean not null default false
);

create index if not exists idx_fotos_aprobada on fotos(aprobada);

-- ---------------------------------------------------------------------------
-- Tabla: configuracion (clave / valor) — textos editables desde Admin
-- ---------------------------------------------------------------------------
create table if not exists configuracion (
    clave   text primary key,
    valor   text
);

-- Valores iniciales de ejemplo (el administrador puede cambiarlos desde la web)
insert into configuracion (clave, valor) values
    ('nombre_torneo', 'BasketKastil'),
    ('descripcion', 'Una noche de baloncesto, equipos y comunidad.'),
    ('ubicacion_direccion', ''),
    ('contacto_telefono', ''),
    ('contacto_email', '')
on conflict (clave) do nothing;

-- ---------------------------------------------------------------------------
-- Seguridad (RLS)
-- ---------------------------------------------------------------------------
-- Por simplicidad, la protección del panel de Administrador se hace dentro
-- de la propia app de Streamlit (contraseña), no a nivel de base de datos.
-- Row Level Security queda DESACTIVADO para que la app (con la clave anon)
-- pueda leer y escribir sin configuración adicional.
--
-- Si en el futuro queréis reforzar la seguridad a nivel de base de datos,
-- activad RLS en cada tabla y añadid políticas, por ejemplo:
--
-- alter table equipos enable row level security;
-- create policy "lectura publica equipos" on equipos for select using (true);
-- create policy "escritura publica equipos" on equipos for all using (true);
-- (repetir de forma análoga para partidos, fotos y configuracion)
