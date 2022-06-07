ALTER TABLE public.requests
    ADD COLUMN "processed_pages" integer;

ALTER TABLE public.requests
    ADD COLUMN "last_processed_page" timestamp without time zone;

ALTER TABLE public.requests
    ADD COLUMN "previous_attempts" integer;