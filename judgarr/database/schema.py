"""
SQLite database schema for Judgarr.
"""

SCHEMA_VERSION = 1

# SQL statements for creating database tables
CREATE_TABLES = [
    # Schema version tracking
    """
    CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER PRIMARY KEY
    )
    """,
    
    # User requests
    """
    CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY,
        user_id TEXT NOT NULL,
        media_id TEXT NOT NULL,
        media_type TEXT NOT NULL CHECK (media_type IN ('movie', 'tv')),
        request_date timestamp NOT NULL,
        size_bytes INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL,
        created_at timestamp DEFAULT CURRENT_TIMESTAMP,
        updated_at timestamp DEFAULT CURRENT_TIMESTAMP
    )
    """,
    
    # Request size history (for tracking changes)
    """
    CREATE TABLE IF NOT EXISTS request_size_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id INTEGER NOT NULL,
        size_bytes INTEGER NOT NULL,
        recorded_at timestamp DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (request_id) REFERENCES requests (id) ON DELETE CASCADE
    )
    """,
    
    # User punishments
    """
    CREATE TABLE IF NOT EXISTS punishments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        level INTEGER NOT NULL,
        start_date timestamp NOT NULL,
        end_date timestamp NOT NULL,
        cooldown_days INTEGER NOT NULL,
        request_reduction INTEGER NOT NULL,
        reason TEXT NOT NULL,
        data_usage INTEGER NOT NULL DEFAULT 0,
        is_active BOOLEAN NOT NULL DEFAULT 1,
        created_at timestamp DEFAULT CURRENT_TIMESTAMP,
        updated_at timestamp DEFAULT CURRENT_TIMESTAMP
    )
    """,
    
    # User statistics
    """
    CREATE TABLE IF NOT EXISTS user_stats (
        user_id TEXT PRIMARY KEY,
        username TEXT NOT NULL,
        total_data_usage INTEGER NOT NULL DEFAULT 0,
        total_requests INTEGER NOT NULL DEFAULT 0,
        punishment_level INTEGER NOT NULL DEFAULT 0,
        cooldown_days INTEGER NOT NULL DEFAULT 0,
        request_limit INTEGER NOT NULL DEFAULT 10,
        last_request_date timestamp,
        current_punishment_id INTEGER,
        updated_at timestamp DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (current_punishment_id) REFERENCES punishments (id) ON DELETE SET NULL
    )
    """
]

# Indexes for performance
CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_requests_user_id ON requests (user_id)",
    "CREATE INDEX IF NOT EXISTS idx_requests_media_id ON requests (media_id)",
    "CREATE INDEX IF NOT EXISTS idx_requests_request_date ON requests (request_date)",
    "CREATE INDEX IF NOT EXISTS idx_punishments_user_id ON punishments (user_id)",
    "CREATE INDEX IF NOT EXISTS idx_punishments_is_active ON punishments (is_active)",
    "CREATE INDEX IF NOT EXISTS idx_request_size_history_request_id ON request_size_history (request_id)",
]

# Triggers for automatic timestamp updates
CREATE_TRIGGERS = [
    """
    CREATE TRIGGER IF NOT EXISTS update_requests_timestamp 
    AFTER UPDATE ON requests
    BEGIN
        UPDATE requests SET updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.id;
    END;
    """,
    
    """
    CREATE TRIGGER IF NOT EXISTS update_punishments_timestamp
    AFTER UPDATE ON punishments
    BEGIN
        UPDATE punishments SET updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.id;
    END;
    """,
    
    """
    CREATE TRIGGER IF NOT EXISTS update_user_stats_timestamp
    AFTER UPDATE ON user_stats
    BEGIN
        UPDATE user_stats SET updated_at = CURRENT_TIMESTAMP
        WHERE user_id = NEW.user_id;
    END;
    """
]
