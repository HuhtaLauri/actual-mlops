
{{ config(materialized='table') }}


SELECT
    u.login,
    c.repo,
    COUNT(c.*)
FROM {{ source('github', 'commits')}} c
LEFT JOIN {{ source('github', 'users')}} u
ON u.id = c.committer_id
WHERE u.type = 'User' AND u.login != 'web-flow'
GROUP BY u.login, c.repo
ORDER BY COUNT(c.*) DESC
