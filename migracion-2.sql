-- =============================================================================
-- BasketKastil — Migración para los nuevos cambios
-- Ejecutar en: Supabase > SQL Editor > New query > Run
-- (No borra ni toca tus datos existentes, solo añade lo nuevo)
-- =============================================================================

-- Tabla nueva: djs (horario de la noche)
create table if not exists djs (
    id              bigint generated always as identity primary key,
    nombre          text not null,
    hora_inicio     text not null,   -- formato "HH:MM", ej. "22:00"
    hora_fin        text not null,   -- formato "HH:MM", ej. "23:30"
    estilo          text,
    logo_url        text not null,
    logo_public_id  text not null,
    creado_en       timestamptz default now()
);

-- Nueva clave de configuración para el texto de "¿Quiénes somos?"
insert into configuracion (clave, valor) values
    ('quienes_somos', ''),
    ('quienes_somos_imagen_url', ''),
    ('quienes_somos_imagen_public_id', '')
on conflict (clave) do nothing;

-- Nota: las columnas "equipo", "partido_id" y "comentario" de la tabla
-- "fotos" ya no se usan (el formulario de subida se ha simplificado a
-- solo imagen + nombre), pero se dejan en la base de datos sin tocar
-- para no perder datos antiguos. No es necesario borrarlas.
