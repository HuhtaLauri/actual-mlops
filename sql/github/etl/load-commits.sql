INSERT INTO public.commits (
    sha,
    node_id,
    author_id,
    created_at
)
SELECT
    data ->> 'sha',
    data ->> 'node_id',
    data #>> '{{ author, id }}',
    (data #>> '{{ commit, author, date }}')::timestamp
FROM staging
ON CONFLICT DO NOTHING
