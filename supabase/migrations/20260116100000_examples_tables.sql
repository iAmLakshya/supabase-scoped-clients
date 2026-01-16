-- Notes table for examples
create table if not exists notes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  title text not null,
  content text,
  created_at timestamp with time zone default now()
);

-- Enable RLS
alter table notes enable row level security;

-- Policy: users can only see their own notes
create policy "Users can view own notes"
  on notes for select
  using (auth.uid() = user_id);

-- Policy: users can insert their own notes
create policy "Users can insert own notes"
  on notes for insert
  with check (auth.uid() = user_id);

-- Policy: users can update their own notes
create policy "Users can update own notes"
  on notes for update
  using (auth.uid() = user_id);

-- Policy: users can delete their own notes
create policy "Users can delete own notes"
  on notes for delete
  using (auth.uid() = user_id);
