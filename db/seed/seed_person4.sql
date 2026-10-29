USE bloodbank;

INSERT INTO request (hospital_id, recipient_id, component_type, quantity, urgency, request_date, status) VALUES
(1,  1,  'RBC',         2, 'EMERGENCY', CURRENT_DATE,                          'PENDING'),
(2,  7,  'RBC',         3, 'EMERGENCY', CURRENT_DATE,                          'PENDING'),
(3,  4,  'WHOLE_BLOOD', 2, 'URGENT',    DATE_SUB(CURRENT_DATE, INTERVAL 1 DAY), 'PENDING'),
(4,  2,  'RBC',         1, 'URGENT',    DATE_SUB(CURRENT_DATE, INTERVAL 1 DAY), 'PENDING'),
(5,  5,  'PLASMA',      2, 'ROUTINE',   DATE_SUB(CURRENT_DATE, INTERVAL 2 DAY), 'PENDING'),
(6,  3,  'WHOLE_BLOOD', 1, 'ROUTINE',   DATE_SUB(CURRENT_DATE, INTERVAL 3 DAY), 'PENDING'),
(1,  9,  'PLATELETS',   2, 'URGENT',    CURRENT_DATE,                          'PENDING'),
(7,  8,  'WHOLE_BLOOD', 1, 'ROUTINE',   DATE_SUB(CURRENT_DATE, INTERVAL 5 DAY), 'CANCELLED');
