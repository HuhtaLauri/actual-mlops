DROP TABLE IF EXISTS public.daily_issues;

CREATE TABLE public.daily_issues (
  id varchar,
  number bigint,
  state varchar,
  created_at timestamp,
  updated_at timestamp,
  closed_at timestamp,
  date DATE,
  repo varchar,
  PRIMARY KEY(id, updated_at, date)
);
