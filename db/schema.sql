SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS issue;
DROP TABLE IF EXISTS request;
DROP TABLE IF EXISTS blood_unit;
DROP TABLE IF EXISTS donor;
DROP TABLE IF EXISTS recipient;
DROP TABLE IF EXISTS hospital;
DROP TABLE IF EXISTS blood_bank;
DROP TABLE IF EXISTS user_account;

SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE user_account (
    user_id       INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50) NOT NULL UNIQUE,
    email         VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name     VARCHAR(100) NOT NULL,
    role          ENUM('ADMIN', 'BANK_STAFF', 'HOSPITAL_STAFF', 'DONOR') NOT NULL,
    entity_ref_id INT DEFAULT NULL,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE blood_bank (
    bank_id      INT AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(120) NOT NULL,
    address      TEXT NOT NULL,
    city         VARCHAR(60) NOT NULL DEFAULT 'Pune',
    contact      VARCHAR(20) NOT NULL,
    email        VARCHAR(100) UNIQUE,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE hospital (
    hospital_id  INT AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(120) NOT NULL,
    address      TEXT NOT NULL,
    city         VARCHAR(60) NOT NULL DEFAULT 'Pune',
    contact      VARCHAR(20) NOT NULL,
    email        VARCHAR(100) UNIQUE,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE recipient (
    recipient_id INT AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    age          INT NOT NULL,
    gender       ENUM('MALE', 'FEMALE', 'OTHER') NOT NULL DEFAULT 'OTHER',
    blood_group  ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-') NOT NULL,
    hospital_id  INT DEFAULT NULL,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_recipient_age CHECK (age BETWEEN 0 AND 120),
    CONSTRAINT fk_recipient_hospital FOREIGN KEY (hospital_id)
        REFERENCES hospital(hospital_id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE donor (
    donor_id           INT AUTO_INCREMENT PRIMARY KEY,
    name               VARCHAR(100) NOT NULL,
    blood_group        ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-') NOT NULL,
    phone              VARCHAR(15) NOT NULL UNIQUE,
    email              VARCHAR(100) UNIQUE,
    dob                DATE NOT NULL,
    gender             ENUM('MALE', 'FEMALE', 'OTHER') NOT NULL DEFAULT 'OTHER',
    last_donation_date DATE DEFAULT NULL,
    created_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE blood_unit (
    bank_id          INT NOT NULL,
    unit_id          INT NOT NULL,
    donor_id         INT NOT NULL,
    volume_ml        INT NOT NULL,
    blood_group      ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-') NOT NULL,
    component_type   ENUM('WHOLE_BLOOD','RBC','PLATELETS','PLASMA') NOT NULL,
    donation_date    DATE NOT NULL,
    collection_date  DATE NOT NULL,
    expiry_date      DATE NOT NULL,
    status           ENUM('AVAILABLE','RESERVED','ISSUED','EXPIRED','DISCARDED') NOT NULL DEFAULT 'AVAILABLE',
    discard_reason   TEXT DEFAULT NULL,
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (bank_id, unit_id),
    CONSTRAINT chk_unit_volume CHECK (volume_ml BETWEEN 50 AND 600),
    CONSTRAINT chk_unit_expiry CHECK (expiry_date > collection_date),
    CONSTRAINT fk_unit_bank FOREIGN KEY (bank_id)
        REFERENCES blood_bank(bank_id) ON DELETE CASCADE,
    CONSTRAINT fk_unit_donor FOREIGN KEY (donor_id)
        REFERENCES donor(donor_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE request (
    request_id       INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id      INT NOT NULL,
    recipient_id     INT NOT NULL,
    blood_group      ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-') NOT NULL,
    component_type   ENUM('WHOLE_BLOOD','RBC','PLATELETS','PLASMA') NOT NULL,
    quantity         INT NOT NULL,
    urgency          ENUM('ROUTINE','URGENT','EMERGENCY') NOT NULL DEFAULT 'ROUTINE',
    request_date     DATE NOT NULL,
    status           ENUM('PENDING','PARTIALLY_FULFILLED','FULFILLED','CANCELLED') NOT NULL DEFAULT 'PENDING',
    notes            TEXT DEFAULT NULL,
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_request_qty CHECK (quantity > 0),
    CONSTRAINT fk_request_hospital FOREIGN KEY (hospital_id)
        REFERENCES hospital(hospital_id) ON DELETE RESTRICT,
    CONSTRAINT fk_request_recipient FOREIGN KEY (recipient_id)
        REFERENCES recipient(recipient_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE issue (
    issue_id         INT AUTO_INCREMENT PRIMARY KEY,
    request_id       INT NOT NULL,
    bank_id          INT NOT NULL,
    unit_id          INT NOT NULL,
    issue_date       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    quantity_issued  INT NOT NULL DEFAULT 1,
    notes            TEXT DEFAULT NULL,
    CONSTRAINT chk_issue_qty CHECK (quantity_issued = 1),
    CONSTRAINT uq_unit_single_issue UNIQUE (bank_id, unit_id),
    CONSTRAINT fk_issue_request FOREIGN KEY (request_id)
        REFERENCES request(request_id) ON DELETE RESTRICT,
    CONSTRAINT fk_issue_unit FOREIGN KEY (bank_id, unit_id)
        REFERENCES blood_unit(bank_id, unit_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE INDEX idx_unit_fefo ON blood_unit (blood_group, component_type, status, expiry_date);
CREATE INDEX idx_unit_bank_status ON blood_unit (bank_id, status);
CREATE INDEX idx_request_queue ON request (status, urgency, request_date);
CREATE INDEX idx_issue_req ON issue (request_id);

DELIMITER //

CREATE TRIGGER trg_after_donation_insert
AFTER INSERT ON blood_unit
FOR EACH ROW
BEGIN
    UPDATE donor
    SET last_donation_date = NEW.donation_date
    WHERE donor_id = NEW.donor_id
      AND (last_donation_date IS NULL OR last_donation_date < NEW.donation_date);
END //

CREATE TRIGGER trg_after_issue_insert
AFTER INSERT ON issue
FOR EACH ROW
BEGIN
    DECLARE total_requested INT;
    DECLARE total_issued INT;

    UPDATE blood_unit
    SET status = 'ISSUED'
    WHERE bank_id = NEW.bank_id AND unit_id = NEW.unit_id;

    SELECT quantity INTO total_requested FROM request WHERE request_id = NEW.request_id;
    SELECT COUNT(*) INTO total_issued FROM issue WHERE request_id = NEW.request_id;

    IF total_issued >= total_requested THEN
        UPDATE request SET status = 'FULFILLED' WHERE request_id = NEW.request_id;
    ELSE
        UPDATE request SET status = 'PARTIALLY_FULFILLED' WHERE request_id = NEW.request_id;
    END IF;
END //

DELIMITER ;

CREATE OR REPLACE VIEW vw_available_stock AS
SELECT
    b.bank_id,
    b.name AS bank_name,
    u.blood_group,
    u.component_type,
    COUNT(*) AS available_units,
    MIN(u.expiry_date) AS earliest_expiry
FROM blood_unit u
JOIN blood_bank b ON u.bank_id = b.bank_id
WHERE u.status = 'AVAILABLE' AND u.expiry_date >= CURRENT_DATE()
GROUP BY b.bank_id, b.name, u.blood_group, u.component_type;

CREATE OR REPLACE VIEW vw_request_status_summary AS
SELECT
    r.request_id,
    h.name AS hospital_name,
    rec.name AS recipient_name,
    r.blood_group,
    r.component_type,
    r.quantity AS requested_units,
    COALESCE(COUNT(i.issue_id), 0) AS issued_units,
    (r.quantity - COALESCE(COUNT(i.issue_id), 0)) AS remaining_units,
    r.urgency,
    r.status
FROM request r
JOIN hospital h ON r.hospital_id = h.hospital_id
JOIN recipient rec ON r.recipient_id = rec.recipient_id
LEFT JOIN issue i ON r.request_id = i.request_id
GROUP BY r.request_id, h.name, rec.name, r.blood_group, r.component_type, r.quantity, r.urgency, r.status;
