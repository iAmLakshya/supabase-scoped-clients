-- Test table for RLS verification
create table if not exists test_user_data (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  content text not null,
  created_at timestamp with time zone default now()
);

-- Enable RLS
alter table test_user_data enable row level security;

-- Policy: users can only see their own data
create policy "Users can view own data"
  on test_user_data for select
  using (auth.uid() = user_id);

-- Policy: users can insert their own data
create policy "Users can insert own data"
  on test_user_data for insert
  with check (auth.uid() = user_id);

-- Policy: users can update their own data
create policy "Users can update own data"
  on test_user_data for update
  using (auth.uid() = user_id);

-- Policy: users can delete their own data
create policy "Users can delete own data"
  on test_user_data for delete
  using (auth.uid() = user_id);
