-- ============================================================
-- CallShield AI — MySQL Database Schema Dump
-- Database Name: callshield_db
-- ============================================================

CREATE DATABASE IF NOT EXISTS `callshield_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `callshield_db`;

-- ------------------------------------------------------------
-- Table structure for `call_reports`
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `call_reports` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `call_type` VARCHAR(50) DEFAULT 'live_call',
    `phone_number` VARCHAR(50) DEFAULT '',
    `name` VARCHAR(255) NOT NULL,
    `transcript` TEXT,
    `scam_type` VARCHAR(255),
    `fraud_score` INT DEFAULT 0,
    `risk_level` VARCHAR(50) DEFAULT 'Low',
    `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Table structure for `contacts`
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `contacts` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL,
    `number` VARCHAR(50) NOT NULL,
    `category` VARCHAR(50) DEFAULT 'Safe',
    `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Table structure for `chat_logs`
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `chat_logs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `sender` VARCHAR(50) NOT NULL,
    `message` TEXT NOT NULL,
    `response` TEXT,
    `source` VARCHAR(100) DEFAULT 'assistant',
    `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Seed Data for `contacts`
-- ------------------------------------------------------------
INSERT INTO `contacts` (`name`, `number`, `category`) VALUES
('Mom', '+1 555-0192', 'Safe'),
('Bank Customer Service', '+1 800-555-0199', 'Verified'),
('Manager John', '+1 555-0143', 'Safe'),
('Tech Support Hotline', '+1 555-0188', 'Suspicious'),
('Emergency Services', '911', 'Emergency')
ON DUPLICATE KEY UPDATE `name` = VALUES(`name`);
