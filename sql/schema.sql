CREATE DATABASE rescue_db;
USE rescue_db;

-- Agencies Table
CREATE TABLE IF NOT EXISTS agencies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    expertise VARCHAR(100) NOT NULL,
    latitude DECIMAL(10,8) DEFAULT 20.5937,
    longitude DECIMAL(11,8) DEFAULT 78.9629,
    last_updated DATETIME,
    role ENUM('admin','agency') DEFAULT 'agency',
    verified BOOLEAN DEFAULT FALSE,
    agency_type VARCHAR(50) DEFAULT 'local'
);

-- Emergencies Table
CREATE TABLE IF NOT EXISTS emergencies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    latitude DECIMAL(10,8) NOT NULL,
    longitude DECIMAL(11,8) NOT NULL,
    description TEXT NOT NULL,
    status ENUM('pending','responded') DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    reported_by ENUM('agency', 'public') DEFAULT 'public',
    tag VARCHAR(50)
);

-- Resources Table
CREATE TABLE IF NOT EXISTS resources (
    id INT AUTO_INCREMENT PRIMARY KEY,
    agency_id INT,
    name VARCHAR(100) NOT NULL,
    quantity INT NOT NULL,
    FOREIGN KEY (agency_id) REFERENCES agencies(id)
);

-- Create user and grant privileges
CREATE USER 'rescue_admi'@'localhost' IDENTIFIED BY 'SecurePass1234!';
GRANT ALL PRIVILEGES ON rescue_db.* TO 'rescue_admi'@'localhost';
FLUSH PRIVILEGES;

-- Example data operations
SELECT * FROM agencies WHERE email = 'avc@gmail.com';
UPDATE agencies SET role = 'ndrf' WHERE email = 'avc@gmail.com';
SELECT * FROM emergencies;