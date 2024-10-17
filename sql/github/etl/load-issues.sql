INSERT INTO public.issues (
  url,
  repository_url,
  id,
  node_id,
  number,
  title,
  labels,
  state,
  locked,
  comments,
  created_at,
  updated_at,
  closed_at,
  author_association
)
SELECT
    (data ->> 'url'),
    (data ->> 'repository_url'),
    (data ->> 'id'),
    (data ->> 'node_id'),
    (data ->> 'number')::BIGINT,
    (data ->> 'title'),
    ARRAY_AGG(l.item ->> 'name'),
    (data ->> 'state'),
    (data ->> 'locked')::BOOL,
    (data ->> 'comments')::BIGINT,
    (data ->> 'created_at')::TIMESTAMP,
    (data ->> 'updated_at')::TIMESTAMP,
    (data ->> 'closed_at')::TIMESTAMP,
    (data ->> 'author_association')
FROM staging
LEFT JOIN LATERAL jsonb_array_elements(data -> 'labels') AS l(item) ON 1=1
GROUP BY data
ON CONFLICT DO NOTHING
