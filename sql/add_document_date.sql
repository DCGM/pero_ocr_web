ALTER TABLE public.documents ADD COLUMN created_date timestamp NOT NULL DEFAULT now();

CREATE VIEW doc_created_date
AS
SELECT requests.document_id, MIN(requests.created_date) AS created_date
FROM requests
GROUP BY requests.document_id;

UPDATE documents
set created_date = doc_created_date.created_date
from doc_created_date
where documents.id = doc_created_date.document_id;

