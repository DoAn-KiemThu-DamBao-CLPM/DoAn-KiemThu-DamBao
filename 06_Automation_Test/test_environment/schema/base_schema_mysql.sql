-- =====================================================================
-- ANYN — RECONSTRUCTED BASE SCHEMA (MySQL / MariaDB dialect)
-- =====================================================================
-- The source archive "anyn_updated_1.zip" ships only the *incremental* SQL
-- (sql/*.sql) and auto-migrations (includes/schema.php, gems_lib.php, ideas_lib.php, ...).
-- The original CREATE TABLE statements for the core tables were NOT included.
-- This file reconstructs the minimum schema that the PHP code requires, derived by
-- reading every SQL statement in the code base.  Assumption A-01 in the Test Plan.
--
-- Columns that the application adds by itself (users.role, users.bio, users.gems,
-- users.active_avatar_frame, comments.edited_at, ideas.work_status ..., gallery.group_id)
-- are intentionally NOT declared here, so that the auto-migration path is exercised.
--
-- Usable as-is in phpMyAdmin / XAMPP:  CREATE DATABASE anyn; USE anyn; <this file>.
-- =====================================================================

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(255) NULL,
    total_spent DECIMAL(10,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS bots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    description TEXT NULL,
    image_url VARCHAR(500) NOT NULL,
    rp_platform_url VARCHAR(500) NOT NULL DEFAULT '',
    juicy_url VARCHAR(500) NOT NULL DEFAULT '',
    crushon_url VARCHAR(500) NOT NULL DEFAULT '',
    is_pinned TINYINT(1) NOT NULL DEFAULT 0,
    total_rating DECIMAL(3,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS themes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    UNIQUE KEY uq_theme_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS bot_themes (
    bot_id INT NOT NULL,
    theme_id INT NOT NULL,
    PRIMARY KEY (bot_id, theme_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS bot_groups (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    UNIQUE KEY uq_group_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS bot_group_members (
    group_id INT NOT NULL,
    bot_id INT NOT NULL,
    PRIMARY KEY (group_id, bot_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ratings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    bot_id INT NOT NULL,
    score TINYINT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_rating_bot (bot_id),
    INDEX idx_rating_user_bot (user_id, bot_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    bot_id INT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_comment_bot (bot_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS commissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    appearance TEXT NULL,
    context TEXT NULL,
    image_url VARCHAR(500) NULL,
    amount_paid DECIMAL(10,2) NOT NULL DEFAULT 0,
    is_private TINYINT(1) NOT NULL DEFAULT 1,
    status ENUM('Pending','In Progress','Completed') NOT NULL DEFAULT 'Pending',
    admin_note TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_commission_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ideas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    appearance TEXT NULL,
    context TEXT NULL,
    image_url VARCHAR(500) NULL,
    upvotes INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS idea_upvotes (
    user_id INT NOT NULL,
    idea_id INT NOT NULL,
    PRIMARY KEY (user_id, idea_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS gallery (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NULL,
    image_url VARCHAR(500) NOT NULL,
    uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS gallery_reactions (
    user_id INT NOT NULL,
    gallery_id INT NOT NULL,
    reaction_type ENUM('like','love','fire') NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, gallery_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
