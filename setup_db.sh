#!/bin/bash

# Connect as root (passwordless usually in dev envs) and create user/db
mysql -u root -e "CREATE DATABASE IF NOT EXISTS minigame_platform;"
mysql -u root -e "CREATE USER IF NOT EXISTS 'test'@'localhost' IDENTIFIED BY 'SA123';"
mysql -u root -e "GRANT ALL PRIVILEGES ON minigame_platform.* TO 'test'@'localhost';"
mysql -u root -e "FLUSH PRIVILEGES;"

# Create tables
mysql -u test -pSA123 minigame_platform <<EOF
CREATE TABLE IF NOT EXISTS minigame_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(255) DEFAULT '/static/avatars/default.png',
    is_admin TINYINT(1) DEFAULT 0
);

-- Try adding is_admin column if it doesn't exist (for migration)
-- This is a bit hacky in pure SQL without procedure, so we rely on create if not exists
-- If table exists but no column, manual alter is safer or just ignore errors here:
-- ALTER TABLE minigame_users ADD COLUMN is_admin TINYINT(1) DEFAULT 0;

CREATE TABLE IF NOT EXISTS minigame_list (
    game_key VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    icon VARCHAR(10),
    url VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS minigame_scores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    game_key VARCHAR(50),
    user_id INT,
    score INT,
    player_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_key) REFERENCES minigame_list(game_key),
    FOREIGN KEY (user_id) REFERENCES minigame_users(id)
);
EOF

# Separately try to alter table just in case it already existed without is_admin
mysql -u test -pSA123 minigame_platform -e "ALTER TABLE minigame_users ADD COLUMN is_admin TINYINT(1) DEFAULT 0;" 2>/dev/null || true

echo "Database initialized."
