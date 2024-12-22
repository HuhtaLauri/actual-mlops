DROP TABLE IF EXISTS public.users CASCADE;

CREATE TABLE public.users (
    login VARCHAR,
    id VARCHAR,
    node_id VARCHAR,
    avatar_url VARCHAR,
    url VARCHAR,
    type VARCHAR,
    user_view_type VARCHAR,
    site_admin VARCHAR,
    CONSTRAINT users_pkey PRIMARY KEY (id)
);
