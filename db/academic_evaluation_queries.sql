-- ============================================================================
-- Blood Bank Management System: Academic DBMS Evaluation Queries (Viva / Lab)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Query 1: Critical Stock Alert (Groups with < 5 available units per bank)
-- Demonstrates: Aggregation, HAVING clause, and Date Comparison.
-- ----------------------------------------------------------------------------
SELECT 
    b.name AS bank_name,
    u.blood_group,
    u.component_type,
    COUNT(u.unit_id) AS current_stock
FROM blood_unit u
JOIN blood_bank b ON u.bank_id = b.bank_id
WHERE u.status = 'AVAILABLE' AND u.expiry_date >= CURRENT_DATE()
GROUP BY b.bank_id, b.name, u.blood_group, u.component_type
HAVING COUNT(u.unit_id) < 5
ORDER BY current_stock ASC;

-- ----------------------------------------------------------------------------
-- Query 2: Units Expiring Within Next 7 Days (FEFO Prioritization)
-- Demonstrates: DATEDIFF, DATE_ADD intervals, and Sorting for FIFO/FEFO rotation.
-- ----------------------------------------------------------------------------
SELECT 
    b.name AS bank_name,
    u.bank_id,
    u.unit_id,
    u.blood_group,
    u.component_type,
    u.expiry_date,
    DATEDIFF(u.expiry_date, CURRENT_DATE()) AS days_to_expiry
FROM blood_unit u
JOIN blood_bank b ON u.bank_id = b.bank_id
WHERE u.status = 'AVAILABLE' 
  AND u.expiry_date BETWEEN CURRENT_DATE() AND DATE_ADD(CURRENT_DATE(), INTERVAL 7 DAY)
ORDER BY u.expiry_date ASC;

-- ----------------------------------------------------------------------------
-- Query 3: Hospital Emergency Demand vs Fulfillment Percentage
-- Demonstrates: Conditional aggregation (CASE inside SUM), percentage computation.
-- ----------------------------------------------------------------------------
SELECT 
    h.name AS hospital_name,
    COUNT(r.request_id) AS total_emergency_requests,
    SUM(r.quantity) AS total_units_demanded,
    SUM(CASE WHEN r.status = 'FULFILLED' THEN r.quantity ELSE 0 END) AS total_units_fulfilled,
    ROUND((SUM(CASE WHEN r.status = 'FULFILLED' THEN r.quantity ELSE 0 END) / SUM(r.quantity)) * 100, 2) AS fulfillment_rate_pct
FROM request r
JOIN hospital h ON r.hospital_id = h.hospital_id
WHERE r.urgency = 'EMERGENCY'
GROUP BY h.hospital_id, h.name
ORDER BY total_emergency_requests DESC;

-- ----------------------------------------------------------------------------
-- Query 4: Top Donors Ranked by Donation Frequency (Window Function)
-- Demonstrates: SQL Window Functions (DENSE_RANK() OVER (ORDER BY ... DESC)).
-- ----------------------------------------------------------------------------
SELECT 
    d.donor_id,
    d.name,
    d.blood_group,
    COUNT(u.unit_id) AS total_donations,
    MAX(u.donation_date) AS most_recent_donation,
    DENSE_RANK() OVER (ORDER BY COUNT(u.unit_id) DESC) as donor_rank
FROM donor d
JOIN blood_unit u ON d.donor_id = u.donor_id
GROUP BY d.donor_id, d.name, d.blood_group;

-- ----------------------------------------------------------------------------
-- Query 5: Full Custody Audit Trail (End-to-End Tracing)
-- Demonstrates: 6-table multi-way INNER JOIN tracing complete chain of custody.
-- ----------------------------------------------------------------------------
SELECT 
    i.issue_id,
    i.issue_date,
    u.bank_id,
    u.unit_id,
    u.blood_group,
    u.component_type,
    d.name AS donor_name,
    b.name AS blood_bank_name,
    rec.name AS recipient_name,
    h.name AS hospital_name,
    r.urgency
FROM issue i
JOIN blood_unit u ON i.bank_id = u.bank_id AND i.unit_id = u.unit_id
JOIN donor d ON u.donor_id = d.donor_id
JOIN blood_bank b ON u.bank_id = b.bank_id
JOIN request r ON i.request_id = r.request_id
JOIN recipient rec ON r.recipient_id = rec.recipient_id
JOIN hospital h ON r.hospital_id = h.hospital_id
ORDER BY i.issue_date DESC;
