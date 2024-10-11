INSERT INTO public.authors (
    id,
    login,
    type,
    site_admin
)
SELECT
    data #>> '{{ author, id }}' AS id,
    data #>> '{{ author, login }}' AS login,
    data #>> '{{ author, type }}' AS type,
    (data #>> '{{ author, site_admin }}')::bool AS site_admin
FROM staging
WHERE data #>> '{{ author, id }}' IS NOT NULL
ON CONFLICT DO NOTHING
