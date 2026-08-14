-- Initialize databases for SmartFarm services
CREATE DATABASE IF NOT EXISTS smartfarm_users;
CREATE DATABASE IF NOT EXISTS smartfarm_farms;

-- Grant privileges (optional but good practice for safety)
GRANT ALL PRIVILEGES ON smartfarm_users.* TO 'root'@'%';
GRANT ALL PRIVILEGES ON smartfarm_farms.* TO 'root'@'%';
FLUSH PRIVILEGES;
