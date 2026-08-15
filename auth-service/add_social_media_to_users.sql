-- Migration: add social_media column to users table
ALTER TABLE users
    ADD COLUMN social_media VARCHAR(255) NULL;

-- Reverse migration
-- ALTER TABLE users
--     DROP COLUMN social_media;
