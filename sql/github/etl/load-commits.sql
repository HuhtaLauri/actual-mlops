INSERT INTO public.commits (
    sha,
    node_id,
    author_id,
    created_at,
    repo
)
SELECT
    data ->> 'sha',
    data ->> 'node_id',
    data #>> '{{ author, id }}',
    (data #>> '{{ commit, author, date }}')::timestamp,
    data ->> 'repo'
FROM staging
ON CONFLICT DO NOTHING
