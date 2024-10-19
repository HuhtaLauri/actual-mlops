INSERT INTO public.daily_issues (
  id,
  number,
  state,
  created_at,
  updated_at,
  closed_at,
  date,
  repo
)
WITH
    latest_revision AS (
        SELECT id,
                MAX(updated_at) AS updated_at
        FROM public.issues
        WHERE updated_at <= {current_date}
        GROUP BY id
)
SELECT
  id,
  number,
  state,
  created_at,
  updated_at,
  closed_at,
  DATE {current_date},
  repo
FROM public.issues
JOIN latest_revision USING (id, updated_at)
ON CONFLICT DO NOTHING
