CREATE DATABASE IF NOT EXISTS bloodbank;
USE bloodbank;

CREATE TABLE IF NOT EXISTS blood_bank (
    bank_id     INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    address     TEXT NOT NULL,
    contact     VARCHAR(20) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS hospital (
    hospital_id INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    address     TEXT NOT NULL,
    contact     VARCHAR(20) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS recipient (
    recipient_id INT AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    age          INT CHECK (age BETWEEN 0 AND 120),
    blood_group  ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-') NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS donor (
    donor_id            INT AUTO_INCREMENT PRIMARY KEY,
    name                VARCHAR(100) NOT NULL,
    blood_group         ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-') NOT NULL,
    phone               VARCHAR(15) NOT NULL UNIQUE,
    dob                 DATE NOT NULL,
    last_donation_date  DATE DEFAULT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS blood_unit (
    bank_id         INT NOT NULL,
    unit_id         INT NOT NULL,
    donor_id        INT NOT NULL,
    volume_ml       INT NOT NULL CHECK (volume_ml BETWEEN 50 AND 600),
    donation_date   DATE NOT NULL,
    blood_group     ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-') NOT NULL,
    component_type  ENUM('WHOLE_BLOOD','RBC','PLATELETS','PLASMA') NOT NULL,
    collection_date DATE NOT NULL,
    expiry_date     DATE NOT NULL,
    status          ENUM('AVAILABLE','RESERVED','ISSUED','EXPIRED','DISCARDED') NOT NULL DEFAULT 'AVAILABLE',
    PRIMARY KEY (bank_id, unit_id),
    FOREIGN KEY (bank_id)  REFERENCES blood_bank(bank_id) ON DELETE CASCADE,
    FOREIGN KEY (donor_id) REFERENCES donor(donor_id),
    CHECK (expiry_date > collection_date)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS request (
    request_id      INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id     INT NOT NULL,
    recipient_id    INT NOT NULL,
    component_type  ENUM('WHOLE_BLOOD','RBC','PLATELETS','PLASMA') NOT NULL,
    quantity        INT NOT NULL CHECK (quantity > 0),
    urgency         ENUM('ROUTINE','URGENT','EMERGENCY') NOT NULL DEFAULT 'ROUTINE',
    request_date    DATE NOT NULL DEFAULT (CURRENT_DATE),
    status          ENUM('PENDING','PARTIALLY_FULFILLED','FULFILLED','CANCELLED') NOT NULL DEFAULT 'PENDING',
    FOREIGN KEY (hospital_id)  REFERENCES hospital(hospital_id),
    FOREIGN KEY (recipient_id) REFERENCES recipient(recipient_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS issue (
    issue_id        INT AUTO_INCREMENT PRIMARY KEY,
    request_id      INT NOT NULL,
    bank_id         INT NOT NULL,
    unit_id         INT NOT NULL,
    issue_date      DATE NOT NULL DEFAULT (CURRENT_DATE),
    quantity_issued INT NOT NULL DEFAULT 1 CHECK (quantity_issued > 0),
    FOREIGN KEY (request_id)       REFERENCES request(request_id),
    FOREIGN KEY (bank_id, unit_id) REFERENCES blood_unit(bank_id, unit_id)
) ENGINE=InnoDB;

CREATE INDEX idx_unit_search    ON blood_unit (blood_group, component_type, status, expiry_date);
CREATE INDEX idx_request_status ON request (status, urgency);
CREATE INDEX idx_donor_phone    ON donor (phone);
CREATE INDEX idx_donor_blood    ON donor (blood_group);
