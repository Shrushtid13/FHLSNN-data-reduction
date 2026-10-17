-- rls_test.sql: Proves Row Level Security (RLS) enforcement
-- 1. User A cannot select User B's dataset
-- 2. User A can select a benchmark experiment
-- 3. User A cannot update an experiment

-- Ensure auth schema and helper functions exist (standard in Supabase)
create schema if not exists auth;

create table if not exists auth.users (
    id uuid primary key default gen_random_uuid(),
    email text unique,
    created_at timestamptz default now()
);

-- auth.uid() function mimicking Supabase's jwt-based auth.uid()
create or replace function auth.uid() returns uuid as $$
    select coalesce(
        nullif(current_setting('request.jwt.claim.sub', true), ''),
        (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'sub')
    )::uuid;
$$ language sql stable;

-- Grant permissions to authenticated role (standard in Supabase)
do $$
begin
    if not exists (select 1 from pg_roles where rolname = 'authenticated') then
        create role authenticated;
    end if;
    grant usage on schema public to authenticated;
    grant all on all tables in schema public to authenticated;
    grant all on all sequences in schema public to authenticated;
end $$;

-- Clean test data
truncate table reports, experiments, datasets cascade;

-- Setup two test users
insert into auth.users (id, email)
values 
    ('11111111-1111-1111-1111-111111111111'::uuid, 'user_a@test.com'),
    ('22222222-2222-2222-2222-222222222222'::uuid, 'user_b@test.com')
on conflict (id) do update set email = excluded.email;

-- ============================================================================
-- TEST 1: User A inserts a dataset; User B cannot select User A's dataset
-- ============================================================================
set role authenticated;
select set_config('request.jwt.claim.sub', '11111111-1111-1111-1111-111111111111', false);

-- User A inserts Dataset A
insert into datasets (id, owner, name, storage_path, target_column, n_rows, n_features, n_classes)
values (
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'::uuid,
    '11111111-1111-1111-1111-111111111111'::uuid,
    'Dataset A (User A)',
    '11111111-1111-1111-1111-111111111111/dataset_a.csv',
    'target',
    100, 4, 3
);

-- User A should see 1 dataset
select count(*) as user_a_sees_own_dataset from datasets;

-- Now switch to User B
select set_config('request.jwt.claim.sub', '22222222-2222-2222-2222-222222222222', false);

-- User B attempts to select Dataset A
select count(*) as user_b_sees_user_a_dataset from datasets;

-- ============================================================================
-- TEST 2: User A can select a benchmark experiment
-- ============================================================================
-- Switch back to admin/service role to seed a benchmark experiment
reset role;

insert into experiments (id, owner, dataset_id, method, source, status, progress)
values (
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'::uuid,
    null, -- benchmark source must have null owner
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'::uuid,
    'm1',
    'benchmark',
    'done',
    100
);

-- Switch to User A
set role authenticated;
select set_config('request.jwt.claim.sub', '11111111-1111-1111-1111-111111111111', false);

-- User A selects benchmark experiment
select count(*) as user_a_sees_benchmark_experiment 
from experiments 
where id = 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'::uuid and source = 'benchmark';

-- ============================================================================
-- TEST 3: User A cannot update an experiment (only service role can)
-- ============================================================================
-- User A inserts their own user experiment
insert into experiments (id, owner, dataset_id, method, source, status, progress)
values (
    'cccccccc-cccc-cccc-cccc-cccccccccccc'::uuid,
    '11111111-1111-1111-1111-111111111111'::uuid,
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'::uuid,
    'hybrid',
    'user',
    'queued',
    0
);

-- User A attempts to update progress on their own experiment
update experiments 
set progress = 99, status = 'done' 
where id = 'cccccccc-cccc-cccc-cccc-cccccccccccc'::uuid;

-- Verify progress is STILL 0 (update had 0 effect due to lack of update policy)
select progress as user_a_experiment_progress_after_unauthorized_update 
from experiments 
where id = 'cccccccc-cccc-cccc-cccc-cccccccccccc'::uuid;

-- Reset role
reset role;

-- Summary Assertion Block
do $$
declare
    v_user_b_count int;
    v_benchmark_count int;
    v_progress int;
begin
    -- Check 1: User B sees 0 of User A's datasets
    set role authenticated;
    perform set_config('request.jwt.claim.sub', '22222222-2222-2222-2222-222222222222', false);
    select count(*) into v_user_b_count from datasets where owner = '11111111-1111-1111-1111-111111111111'::uuid;
    if v_user_b_count <> 0 then
        raise exception 'RLS TEST 1 FAILED: User B was able to see User A dataset';
    end if;

    -- Check 2: User A sees benchmark experiment
    perform set_config('request.jwt.claim.sub', '11111111-1111-1111-1111-111111111111', false);
    select count(*) into v_benchmark_count from experiments where source = 'benchmark';
    if v_benchmark_count <> 1 then
        raise exception 'RLS TEST 2 FAILED: User A could not see benchmark experiment';
    end if;

    -- Check 3: User A cannot update experiment
    select progress into v_progress from experiments where id = 'cccccccc-cccc-cccc-cccc-cccccccccccc'::uuid;
    if v_progress <> 0 then
        raise exception 'RLS TEST 3 FAILED: User A was able to update experiment progress to %', v_progress;
    end if;

    reset role;
    raise notice 'ALL RLS TESTS PASSED SUCCESSFULLY!';
end $$;
