DROP TABLE IF EXISTS public.authors CASCADE;

CREATE TABLE public.authors (
    id VARCHAR,
    login VARCHAR,
    type VARCHAR,
    site_admin bool,
    CONSTRAINT authors_pkey PRIMARY KEY (id)
);
