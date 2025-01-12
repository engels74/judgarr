-- Initial database schema migration

-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);

-- User requests
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    media_id TEXT NOT NULL,
    media_type TEXT NOT NULL CHECK (media_type IN ('movie', 'tv')),
    request_date TIMESTAMP NOT NULL,
    size_bytes INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Request size history (for tracking changes)
CREATE TABLE IF NOT EXISTS request_size_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    size_bytes INTEGER NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES requests (id) ON DELETE CASCADE
);

-- User punishments
CREATE TABLE IF NOT EXISTS punishments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    level TEXT NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    cooldown_days INTEGER NOT NULL,
    request_reduction INTEGER NOT NULL,
    reason TEXT NOT NULL,
    data_usage INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User statistics
CREATE TABLE IF NOT EXISTS user_stats (
    user_id TEXT PRIMARY KEY,
    total_requests INTEGER NOT NULL DEFAULT 0,
    total_data INTEGER NOT NULL DEFAULT 0,
    last_request_date TIMESTAMP,
    current_punishment_id INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (current_punishment_id) REFERENCES punishments (id) ON DELETE SET NULL
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_requests_user_id ON requests (user_id);
CREATE INDEX IF NOT EXISTS idx_requests_media_id ON requests (media_id);
CREATE INDEX IF NOT EXISTS idx_requests_request_date ON requests (request_date);
CREATE INDEX IF NOT EXISTS idx_punishments_user_id ON punishments (user_id);
CREATE INDEX IF NOT EXISTS idx_punishments_is_active ON punishments (is_active);
CREATE INDEX IF NOT EXISTS idx_request_size_history_request_id ON request_size_history (request_id);

-- Create triggers
CREATE TRIGGER IF NOT EXISTS update_requests_timestamp 
AFTER UPDATE ON requests
BEGIN
    UPDATE requests SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_punishments_timestamp
AFTER UPDATE ON punishments
BEGIN
    UPDATE punishments SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_user_stats_timestamp
AFTER UPDATE ON user_stats
BEGIN
    UPDATE user_stats SET updated_at = CURRENT_TIMESTAMP
    WHERE user_id = NEW.user_id;
END;
