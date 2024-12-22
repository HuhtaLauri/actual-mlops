INSERT INTO public.users (
    login,
    id,
    node_id,
    avatar_url,
    url,
    type,
    user_view_type,
    site_admin
)
SELECT
    data #>> '{{ author, login }}' AS login,
    data #>> '{{ author, id }}' AS id,
    data #>> '{{ author, node_id }}' AS node_id,
    data #>> '{{ author, avatar_url }}' AS avatar_url,
    data #>> '{{ author, url }}' AS url,
    data #>> '{{ author, type }}' AS type,
    data #>> '{{ author, user_view_type }}' AS user_view_type,
    (data #>> '{{ author, site_admin }}')::bool AS site_admin
FROM staging
WHERE data #>> '{{ author, id }}' IS NOT NULL
UNION ALL
SELECT
    data #>> '{{ committer, login }}' AS login,
    data #>> '{{ committer, id }}' AS id,
    data #>> '{{ committer, node_id }}' AS node_id,
    data #>> '{{ committer, avatar_url }}' AS avatar_url,
    data #>> '{{ committer, url }}' AS url,
    data #>> '{{ committer, type }}' AS type,
    data #>> '{{ committer, user_view_type }}' AS user_view_type,
    (data #>> '{{ committer, site_admin }}')::bool AS site_admin
FROM staging
WHERE data #>> '{{ committer, id }}' IS NOT NULL
ON CONFLICT DO NOTHING
