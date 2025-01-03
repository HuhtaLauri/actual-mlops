DROP TABLE IF EXISTS public.commits CASCADE;

CREATE TABLE public.commits (
    sha VARCHAR,
    node_id VARCHAR,
    author_id VARCHAR,
    created_at TIMESTAMP,
    repo VARCHAR,
    committer_id VARCHAR,
    CONSTRAINT commits_pk PRIMARY KEY(sha)
);
