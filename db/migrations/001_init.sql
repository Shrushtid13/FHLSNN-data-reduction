-- 001_init.sql: Platform Database Schema with pgvector and Row Level Security (RLS)

-- Enable pgvector extension
create extension if not exists vector;

-- 1. Datasets Table
create table if not exists datasets (
    id uuid primary key default gen_random_uuid(),
    owner uuid not null references auth.users(id) on delete cascade,
    name text not null,
    storage_path text not null,
    target_column text not null,
    n_rows int,
    n_features int,
    n_classes int,
    class_counts jsonb,
    profile jsonb,
    profile_vec vector(8),
    created_at timestamptz default now()
);

-- 2. Experiments Table
create table if not exists experiments (
    id uuid primary key default gen_random_uuid(),
    owner uuid references auth.users(id) on delete cascade,
    dataset_id uuid references datasets(id) on delete cascade,
    method text not null check (method in ('unreduced', 'm1', 'm3', 'hybrid')),
    params jsonb default '{}'::jsonb,
    seed int default 42,
    status text default 'queued' check (status in ('queued', 'running', 'done', 'failed')),
    progress int default 0 check (progress between 0 and 100),
    metrics jsonb,
    facts jsonb,
    error text,
    source text default 'user' check (source in ('benchmark', 'user', 'agent')),
    parent_id uuid references experiments(id) on delete set null,
    created_at timestamptz default now(),
    constraint chk_experiments_source_owner check (
        (source = 'benchmark' and owner is null) or 
        (source <> 'benchmark' and owner is not null)
    )
);

-- 3. Reports Table
create table if not exists reports (
    id uuid primary key default gen_random_uuid(),
    experiment_id uuid not null references experiments(id) on delete cascade,
    explanation text,
    facts_snapshot jsonb,
    created_at timestamptz default now()
);

-- 4. Enable Row Level Security (RLS)
alter table datasets enable row level security;
alter table experiments enable row level security;
alter table reports enable row level security;

-- 5. RLS Policies: Datasets
-- Users select, insert, delete only their own datasets
drop policy if exists "Users can select own datasets" on datasets;
create policy "Users can select own datasets"
    on datasets for select
    using (owner = auth.uid());

drop policy if exists "Users can insert own datasets" on datasets;
create policy "Users can insert own datasets"
    on datasets for insert
    with check (owner = auth.uid());

drop policy if exists "Users can delete own datasets" on datasets;
create policy "Users can delete own datasets"
    on datasets for delete
    using (owner = auth.uid());

-- 6. RLS Policies: Experiments
-- Users can select own rows or benchmark rows
drop policy if exists "Users can select own or benchmark experiments" on experiments;
create policy "Users can select own or benchmark experiments"
    on experiments for select
    using (owner = auth.uid() or source = 'benchmark');

-- Users can insert only their own user experiments
drop policy if exists "Users can insert own user experiments" on experiments;
create policy "Users can insert own user experiments"
    on experiments for insert
    with check (owner = auth.uid() and source = 'user');

-- Crucial: No update policy for users. Only service role can update progress, status, and metrics.
drop policy if exists "Users can update experiments" on experiments;

-- 7. RLS Policies: Reports
-- Reports: users select, insert, delete only via owning experiment
drop policy if exists "Users can select own reports" on reports;
create policy "Users can select own reports"
    on reports for select
    using (
        exists (
            select 1 from experiments
            where experiments.id = reports.experiment_id
              and experiments.owner = auth.uid()
        )
    );

drop policy if exists "Users can insert own reports" on reports;
create policy "Users can insert own reports"
    on reports for insert
    with check (
        exists (
            select 1 from experiments
            where experiments.id = reports.experiment_id
              and experiments.owner = auth.uid()
        )
    );

drop policy if exists "Users can delete own reports" on reports;
create policy "Users can delete own reports"
    on reports for delete
    using (
        exists (
            select 1 from experiments
            where experiments.id = reports.experiment_id
              and experiments.owner = auth.uid()
        )
    );

-- 8. Storage bucket and policies (for Supabase Storage environment)
do $$
begin
    if exists (select 1 from information_schema.tables where table_schema = 'storage' and table_name = 'buckets') then
        insert into storage.buckets (id, name, public)
        values ('datasets', 'datasets', false)
        on conflict (id) do nothing;
    end if;

    if exists (select 1 from information_schema.tables where table_schema = 'storage' and table_name = 'objects') then
        drop policy if exists "Users can read own dataset objects" on storage.objects;
        create policy "Users can read own dataset objects"
            on storage.objects for select
            using (
                bucket_id = 'datasets'
                and (storage.foldername(name))[1] = auth.uid()::text
            );
    end if;
end $$;
