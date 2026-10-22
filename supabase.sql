-- Olimpo do Código: tabela de progresso + regras de segurança.
-- Cole TUDO isto no SQL Editor do Supabase e clique em Run.

create table if not exists public.saves (
  user_id    uuid    not null default auth.uid() references auth.users(id) on delete cascade,
  doc_id     text    not null,
  json       text    not null,
  t          bigint  not null default 0,
  updated_at timestamptz not null default now(),
  primary key (user_id, doc_id)
);

-- Cada pessoa só enxerga e altera as próprias linhas.
alter table public.saves enable row level security;

drop policy if exists "saves_select" on public.saves;
drop policy if exists "saves_insert" on public.saves;
drop policy if exists "saves_update" on public.saves;
drop policy if exists "saves_delete" on public.saves;

create policy "saves_select" on public.saves for select to authenticated
  using (user_id = (select auth.uid()));
create policy "saves_insert" on public.saves for insert to authenticated
  with check (user_id = (select auth.uid()));
create policy "saves_update" on public.saves for update to authenticated
  using (user_id = (select auth.uid())) with check (user_id = (select auth.uid()));
create policy "saves_delete" on public.saves for delete to authenticated
  using (user_id = (select auth.uid()));

-- Permissões (necessárias nos projetos novos do Supabase).
revoke all on public.saves from anon;
grant select, insert, update, delete on public.saves to authenticated;

-- Função "ping": o GitHub chama uma vez por dia para o projeto gratuito
-- não ser pausado por falta de uso. Não expõe nenhum dado.
create or replace function public.ping()
returns integer
language plpgsql
security definer
set search_path = public
as $$
begin
  perform 1 from public.saves limit 1;
  return 1;
end;
$$;

revoke all on function public.ping() from public;
grant execute on function public.ping() to anon, authenticated;
