
ALTER TABLE public.textlines ADD annotated boolean NOT NULL DEFAULT false;
ALTER TABLE public.documents ADD COLUMN annotated_line_count integer NOT NULL DEFAULT 0;
ALTER TABLE public.documents ADD COLUMN line_count integer NOT NULL DEFAULT 0;

UPDATE textlines
SET annotated = true
FROM annotations
WHERE textlines.id = annotations.text_line_id;

CREATE VIEW doc_ann_line_counts 
AS
SELECT documents.id, COUNT(*) AS line_count
FROM documents, images, textregions, textlines
WHERE documents.id = images.document_id and images.id = textregions.image_id and textregions.id = textlines.region_id and textlines.annotated
GROUP BY documents.id;

CREATE VIEW doc_line_counts 
AS
SELECT documents.id, COUNT(*) AS line_count
FROM documents, images, textregions, textlines
WHERE documents.id = images.document_id and images.id = textregions.image_id and textregions.id = textlines.region_id
GROUP BY documents.id;

UPDATE documents
set annotated_line_count = doc_ann_line_counts.line_count
from doc_ann_line_counts
where documents.id = doc_ann_line_counts.id;

UPDATE documents
set line_count = doc_line_counts.line_count
from doc_line_counts
where documents.id = doc_line_counts.id;





CREATE OR REPLACE FUNCTION update_annotated_insert()
RETURNS TRIGGER AS
'
BEGIN
    UPDATE textlines
        SET annotated = true
        WHERE id = NEW.text_line_id;
    RETURN NEW;
END
' LANGUAGE plpgsql;


CREATE TRIGGER annotations_update_annotated_insert AFTER INSERT ON annotations
    FOR EACH ROW EXECUTE PROCEDURE update_annotated_insert();



CREATE OR REPLACE FUNCTION update_document_annotated()
RETURNS TRIGGER AS
'
DECLARE
    del_update integer := 0;
    ann_update integer := 0;

BEGIN
	if(OLD.annotated != NEW.annotated) then
		UPDATE documents
			SET annotated_line_count = annotated_line_count + 1
			from images, textregions
			where documents.id = images.document_id and images.id = textregions.image_id and textregions.id = NEW.region_id;
	end if;
	if(OLD.deleted != NEW.deleted) then
		if(NEW.annotated) then
			ann_update = 1;
		end if;
		if(NEW.deleted) then
			del_update := -1;
			ann_update := ann_update * -1;
		else
			del_update := +1;
		end if;
		UPDATE documents
			SET 
				annotated_line_count = annotated_line_count + ann_update,
				line_count = line_count + del_update
			from images, textregions
			where documents.id = images.document_id and images.id = textregions.image_id and textregions.id = NEW.region_id;
	end if;
    RETURN NEW;
END
' LANGUAGE plpgsql;

CREATE TRIGGER textlines_update_document_annotated AFTER UPDATE ON textlines
    FOR EACH ROW EXECUTE PROCEDURE update_document_annotated();



CREATE OR REPLACE FUNCTION insert_document_line()
RETURNS TRIGGER AS
'
DECLARE
    del_update integer := 0;
    ann_update integer := 0;

BEGIN
	UPDATE documents
	SET line_count = line_count + 1
	from images, textregions
	where documents.id = images.document_id and images.id = textregions.image_id and textregions.id = NEW.region_id;
    RETURN NEW;
END
' LANGUAGE plpgsql;

CREATE TRIGGER textlines_insert_document_line AFTER INSERT ON textlines
    FOR EACH ROW EXECUTE PROCEDURE insert_document_line();


