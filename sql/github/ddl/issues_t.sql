DROP TABLE IF EXISTS public.issues;

CREATE TABLE public.issues (
  url varchar,
  repository_url varchar,
  id varchar,
  node_id varchar,
  number bigint,
  title varchar,
  labels varchar[],
  state varchar,
  locked bool,
  comments bigint,
  created_at timestamp,
  updated_at timestamp,
  closed_at timestamp,
  author_association varchar,
  PRIMARY KEY(id, updated_at)
);
