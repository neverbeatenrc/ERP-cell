-- run in MySQL shell: mysql -u root -p
CREATE DATABASE IF NOT EXISTS erp_database CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'erp_user'@'localhost' IDENTIFIED BY 'StrongPass';
GRANT ALL PRIVILEGES ON erp_database.* TO 'erp_user'@'localhost';
FLUSH PRIVILEGES;