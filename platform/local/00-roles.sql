-- Local stand-in for the parts of Supabase the app relies on: API roles for
-- PostgREST and a stub storage schema (keyframe uploads are skipped locally).
CREATE ROLE anon NOLOGIN;
CREATE ROLE service_role NOLOGIN BYPASSRLS;
CREATE ROLE authenticator LOGIN NOINHERIT PASSWORD 'authenticator';
GRANT anon, service_role TO authenticator;

CREATE SCHEMA storage;
CREATE TABLE storage.buckets (id TEXT PRIMARY KEY, name TEXT, public BOOLEAN);
