SELECT U.first_name, U.last_name, COUNT(*) AS num_images FROM
users AS U JOIN documents AS D ON U.id = D.user_id
JOIN images as I ON D.id = I.document_id
GROUP BY U.id
ORDER BY num_images DESC
LIMIT 100