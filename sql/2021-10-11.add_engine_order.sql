ALTER TABLE public.ocr
    ADD COLUMN "order" integer;

ALTER TABLE public.layout_detectors
    ADD COLUMN "order" integer;

ALTER TABLE public.language_model
    ADD COLUMN "order" integer;

ALTER TABLE public.baseline
    ADD COLUMN "order" integer;