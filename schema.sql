-- Ejecutar una vez en el SQL Editor del proyecto Supabase elegido.
-- Solo crea recursos del buscador. No modifica otras tablas ni documentos.
create table if not exists public.documental_documents (
  id text primary key,
  name text not null,
  original_path text not null,
  preview_path text not null,
  fragments jsonb not null default '[]'::jsonb,
  published boolean not null default false,
  updated_at timestamptz not null default now()
);
alter table public.documental_documents enable row level security;
revoke all on public.documental_documents from anon, authenticated;
grant select on public.documental_documents to anon, authenticated;
grant select, insert, update, delete on public.documental_documents to service_role;
drop policy if exists "documental_public_read" on public.documental_documents;
create policy "documental_public_read" on public.documental_documents
  for select to anon, authenticated using (published = true);
insert into storage.buckets (id, name, public, file_size_limit)
values ('documental-public', 'documental-public', true, 52428800)
on conflict (id) do nothing;
-- Bucket dedicado: lectura pública, sin políticas de escritura para visitantes.
