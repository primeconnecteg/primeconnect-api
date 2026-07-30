-- ============================================================
-- PrimeConnect API – Database Schema Initialization
-- Run this once in Supabase SQL Editor to create all tables.
-- ============================================================

-- 1. Create ENUM type for contact request status (if not already created by contact_requests table)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'contactstatus') THEN
        CREATE TYPE contactstatus AS ENUM ('NEW', 'READ', 'REPLIED');
    END IF;
END
$$;

-- 2. Create ENUM type for meeting request status
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'meeting_request_status') THEN
        CREATE TYPE meeting_request_status AS ENUM ('Pending', 'Approved', 'Rejected', 'Completed');
    END IF;
END
$$;

-- 3. Create contact_requests table
CREATE TABLE IF NOT EXISTS contact_requests (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(100)    NOT NULL,
    company     VARCHAR(100)    NOT NULL,
    email       VARCHAR(255)    NOT NULL,
    message     TEXT            NOT NULL,
    status      contactstatus   NOT NULL DEFAULT 'NEW',
    created_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_contact_requests_email  ON contact_requests(email);
CREATE INDEX IF NOT EXISTS ix_contact_requests_company ON contact_requests(company);
CREATE INDEX IF NOT EXISTS ix_contact_requests_status  ON contact_requests(status);

-- 4. Create meeting_requests table
CREATE TABLE IF NOT EXISTS meeting_requests (
    id             UUID                    PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name      VARCHAR(100)            NOT NULL,
    company_name   VARCHAR(150)            NOT NULL,
    business_email VARCHAR(255)            NOT NULL,
    meeting_date   DATE                    NOT NULL,
    comment        TEXT,
    status         meeting_request_status  NOT NULL DEFAULT 'Pending',
    is_deleted     BOOLEAN                 NOT NULL DEFAULT FALSE,
    created_at     TIMESTAMPTZ             NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ             NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_meeting_requests_business_email ON meeting_requests(business_email);
CREATE INDEX IF NOT EXISTS ix_meeting_requests_meeting_date   ON meeting_requests(meeting_date);
CREATE INDEX IF NOT EXISTS ix_meeting_requests_status         ON meeting_requests(status);
CREATE INDEX IF NOT EXISTS ix_meeting_requests_created_at     ON meeting_requests(created_at);

-- 5. Create admins table
CREATE TABLE IF NOT EXISTS admins (
    id            UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    username      VARCHAR(100) NOT NULL UNIQUE,
    password_hash TEXT         NOT NULL,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_admins_username ON admins(username);

-- 6. Verify tables created
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('contact_requests', 'meeting_requests', 'admins')
ORDER BY table_name;
