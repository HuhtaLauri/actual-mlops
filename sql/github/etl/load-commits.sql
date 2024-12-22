INSERT INTO public.commits (
    sha,
    node_id,
    author_id,
    created_at,
    repo,
    committer_id
)
SELECT
    data ->> 'sha',
    data ->> 'node_id',
    data #>> '{{ author, id }}',
    (data #>> '{{ commit, author, date }}')::timestamp,
    data ->> 'repo',
    (data #>> '{ committer, id }') AS committer_id
FROM staging
ON CONFLICT DO NOTHING
