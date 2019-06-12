drop table if exists updates;
create table updates
  (institution text primary key,
  last_update timestamptz);

drop table if exists requirement_blocks;
create table requirement_blocks (
institution text,
requirement_id text primary key,
block_type text,
block_value text,
title text,
period_start text,
period_stop text,
major1 text,
major2 text,
concentration text,
minor text,
requirement_text text);
