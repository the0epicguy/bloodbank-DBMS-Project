-- =====================================================
-- Blood Bank Management System - MySQL Schema
-- Migration 002 (Person 4): Auth + Issue hardening + Report views
--
-- What this migration does:
--   1. Creates `user_account` (JWT login + role-based access)
--   2. Hardens `issue`:
--        - issue_date DATE -> DATETIME (full audit timestamp)
--        - adds `issued_by` (which user performed the issue)
--        - UNIQUE (bank_id, unit_id): a physical bag can be issued ONCE
--   3. Adds a BEFORE INSERT trigger on `issue` (DB-level safety net)
--   4. Adds two views used by the dashboard / viva queries
--
-- Safe to run more than once (all steps are guarded).
-- Run AFTER 001_create_tables.sql.
-- =====================================================

USE bloodbank;

-- =====================================================
-- TABLE: user_account
-- entity_ref_id links a user to a bank_id, hospital_id or donor_id
-- depending on `role` (NULL for ADMIN).
-- =====================================================
CREATE TABLE IF NOT EXISTS user_account (
    user_id        INT AUTO_INCREMENT PRIMARY KEY,
    username       VARCHAR(50)  NOT NULL UNIQUE,
    email          VARCHAR(100) NOT NULL UNIQUE,
    password_hash  VARCHAR(255) NOT NULL,
    full_name      VARCHAR(100) NOT NULL,
    role           ENUM('ADMIN','BANK_STAFF','HOSPITAL_STAFF','DONOR') NOT NULL,
    entity_ref_id  INT DEFAULT NULL,
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- =====================================================
-- Guarded ALTERs on `issue` (so the script can be re-run)
-- =====================================================
DROP PROCEDURE IF EXISTS p4_migrate_issue;

DELIMITER //
CREATE PROCEDURE p4_migrate_issue()
BEGIN
    -- issue_date: DATE -> DATETIME (idempotent, MODIFY can be repeated)
    ALTER TABLE issue
        MODIFY issue_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP;

    -- issued_by: which user performed the issue (audit trail)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'issue'
          AND COLUMN_NAME = 'issued_by'
    ) THEN
        ALTER TABLE issue ADD COLUMN issued_by INT DEFAULT NULL;
        ALTER TABLE issue ADD CONSTRAINT fk_issue_user
            FOREIGN KEY (issued_by) REFERENCES user_account(user_id)
            ON DELETE SET NULL;
    END IF;

    -- A physical blood bag can only ever be issued once
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.TABLE_CONSTRAINTS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'issue'
          AND CONSTRAINT_NAME = 'uq_unit_single_issue'
    ) THEN
        ALTER TABLE issue
            ADD CONSTRAINT uq_unit_single_issue UNIQUE (bank_id, unit_id);
    END IF;

    -- Speeds up "all issues of a request" lookups
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'issue'
          AND INDEX_NAME = 'idx_issue_req'
    ) THEN
        CREATE INDEX idx_issue_req ON issue (request_id);
    END IF;
END //
DELIMITER ;

CALL p4_migrate_issue();
DROP PROCEDURE p4_migrate_issue;

-- =====================================================
-- TRIGGER: refuse to issue a unit that is not AVAILABLE or is expired.
-- The Python service already checks this (clean error messages), the
-- trigger guarantees it even if someone inserts straight into MySQL.
-- =====================================================
DROP TRIGGER IF EXISTS trg_before_issue_insert;

DELIMITER //
CREATE TRIGGER trg_before_issue_insert
BEFORE INSERT ON issue
FOR EACH ROW
BEGIN
    DECLARE v_status VARCHAR(20);
    DECLARE v_expiry DATE;

    SELECT status, expiry_date INTO v_status, v_expiry
    FROM blood_unit
    WHERE bank_id = NEW.bank_id AND unit_id = NEW.unit_id;

    IF v_status <> 'AVAILABLE' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Blood unit is not AVAILABLE and cannot be issued';
    END IF;

    IF v_expiry < CURRENT_DATE() THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Blood unit has expired and cannot be issued';
    END IF;
END //
DELIMITER ;

-- =====================================================
-- VIEW 1: Available stock matrix (bank x group x component)
-- =====================================================
CREATE OR REPLACE VIEW vw_available_stock AS
SELECT
    b.bank_id,
    b.name           AS bank_name,
    u.blood_group,
    u.component_type,
    COUNT(*)         AS available_units,
    MIN(u.expiry_date) AS earliest_expiry
FROM blood_unit u
JOIN blood_bank b ON u.bank_id = b.bank_id
WHERE u.status = 'AVAILABLE' AND u.expiry_date >= CURRENT_DATE()
GROUP BY b.bank_id, b.name, u.blood_group, u.component_type;

-- =====================================================
-- VIEW 2: Request fulfilment progress
-- (the blood group comes from the recipient)
-- =====================================================
CREATE OR REPLACE VIEW vw_request_status_summary AS
SELECT
    r.request_id,
    h.name              AS hospital_name,
    rec.name            AS recipient_name,
    rec.blood_group     AS blood_group,
    r.component_type,
    r.quantity          AS requested_units,
    COUNT(i.issue_id)   AS issued_units,
    (r.quantity - COUNT(i.issue_id)) AS remaining_units,
    r.urgency,
    r.status
FROM request r
JOIN hospital  h   ON r.hospital_id  = h.hospital_id
JOIN recipient rec ON r.recipient_id = rec.recipient_id
LEFT JOIN issue i  ON r.request_id   = i.request_id
GROUP BY r.request_id, h.name, rec.name, rec.blood_group,
         r.component_type, r.quantity, r.urgency, r.status;
