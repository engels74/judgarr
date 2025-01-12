"""
Database manager for Judgarr.
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, cast
import sqlite3

import aiosqlite

from ..shared.types import UserId
from .schema import SCHEMA_VERSION, CREATE_TABLES, CREATE_INDEXES, CREATE_TRIGGERS
from .models import UserRequest, UserStats, UserPunishment
from judgarr.database.migrations.migration_manager import MigrationManager

logger = logging.getLogger(__name__)

def adapt_datetime(val: datetime) -> str:
    """Adapt datetime to SQLite."""
    return val.isoformat()

def convert_datetime(val: bytes) -> datetime:
    """Convert SQLite value to datetime."""
    return datetime.fromisoformat(val.decode())

class DatabaseManager:
    """Manager for database operations."""
    
    def __init__(self, database_path: Path):
        """Initialize the database manager.
        
        Args:
            database_path: Path to the SQLite database file
        """
        self.database_path = database_path
        self._connection: Optional[aiosqlite.Connection] = None
        self._migration_manager = MigrationManager(str(database_path))
        
        # Register adapters
        sqlite3.register_adapter(datetime, adapt_datetime)
        sqlite3.register_converter("datetime", convert_datetime)
        sqlite3.register_converter("timestamp", convert_datetime)
    
    async def _ensure_connection(self) -> aiosqlite.Connection:
        """Ensure database connection exists."""
        if self._connection is None:
            self._connection = await aiosqlite.connect(
                self.database_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                isolation_level=None  # Enable autocommit mode
            )
            self._connection.row_factory = aiosqlite.Row
            
            # Configure datetime handling for SQLite
            await self._connection.execute("PRAGMA datetime_precision = 'subsecond'")
            await self._connection.execute("""
                CREATE TABLE IF NOT EXISTS datetime_config (
                    name TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            await self._connection.execute("""
                INSERT OR REPLACE INTO datetime_config (name, value)
                VALUES ('format', 'ISO8601')
            """)
            
            # Enable WAL mode for better concurrency
            await self._connection.execute("PRAGMA journal_mode=WAL")
            await self._connection.execute("PRAGMA busy_timeout=5000")  # 5 second timeout
            
        return self._connection
    
    async def initialize(self) -> None:
        """Initialize the database schema and run any pending migrations."""
        conn = await self._ensure_connection()
        async with conn.cursor() as cursor:
            # Create tables
            for table in CREATE_TABLES:
                await cursor.execute(table)
            
            # Create indexes
            for index in CREATE_INDEXES:
                await cursor.execute(index)
            
            # Create triggers
            for trigger in CREATE_TRIGGERS:
                await cursor.execute(trigger)
            
            # Check/update schema version
            await cursor.execute(
                "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
                (SCHEMA_VERSION,)
            )
            
            await conn.commit()
    
    async def close(self) -> None:
        """Close the database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None
    
    async def __aenter__(self):
        """Enter async context."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        await self.close()
    
    async def add_request(self, request: UserRequest) -> int:
        """Add a new request to the database.
        
        Args:
            request: Request to add
            
        Returns:
            ID of the inserted request
            
        Raises:
            ValueError: If the request could not be inserted
        """
        conn = await self._ensure_connection()
        async with conn.cursor() as cursor:
            # First, check if user stats exist
            await cursor.execute(
                "SELECT * FROM user_stats WHERE user_id = ?",
                (request.user_id,)
            )
            stats = await cursor.fetchone()
            
            if not stats:
                # Initialize user stats with default values
                await cursor.execute(
                    """
                    INSERT INTO user_stats (
                        user_id, username, total_data_usage, total_requests,
                        punishment_level, cooldown_days, request_limit
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        request.user_id,
                        f"user_{request.user_id}",  # Default username
                        request.size_bytes,
                        1,  # First request
                        0,  # No punishment
                        0,  # No cooldown
                        10  # Default request limit
                    )
                )
            else:
                # Update existing stats
                await cursor.execute(
                    """
                    UPDATE user_stats 
                    SET total_data_usage = total_data_usage + ?,
                        total_requests = total_requests + 1
                    WHERE user_id = ?
                    """,
                    (request.size_bytes, request.user_id)
                )
            
            # Add the request
            await cursor.execute(
                """
                INSERT INTO requests (
                    user_id, media_id, media_type, request_date,
                    size_bytes, status
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    request.user_id,
                    request.media_id,
                    request.media_type,
                    request.request_date,
                    request.size_bytes,
                    request.status
                )
            )
            request_id = cursor.lastrowid
            await conn.commit()
            return cast(int, request_id)
    
    async def update_request_size(
        self,
        request_id: int,
        new_size: int
    ) -> None:
        """Update the size of a request and record the change.
        
        Args:
            request_id: ID of the request to update
            new_size: New size in bytes
        """
        conn = await self._ensure_connection()
        async with conn.cursor() as cursor:
            # Update request
            await cursor.execute(
                "UPDATE requests SET size_bytes = ? WHERE id = ?",
                (new_size, request_id)
            )
            
            # Record size change
            await cursor.execute(
                """
                INSERT INTO request_size_history (
                    request_id, size_bytes
                ) VALUES (?, ?)
                """,
                (request_id, new_size)
            )
            
            await conn.commit()
    
    async def get_user_requests(
        self,
        user_id: UserId,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[UserRequest]:
        """Get requests for a user in a date range.
        
        Args:
            user_id: User ID to get requests for
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            List of user requests
        """
        conn = await self._ensure_connection()
        query = "SELECT * FROM requests WHERE user_id = ?"
        params: list[str | datetime] = [user_id]
        
        if start_date:
            query += " AND request_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND request_date <= ?"
            params.append(end_date)
            
        query += " ORDER BY request_date DESC"
        
        async with conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [
                UserRequest(
                    id=row["id"],
                    user_id=row["user_id"],
                    media_id=row["media_id"],
                    media_type=row["media_type"],
                    request_date=row["request_date"],
                    size_bytes=row["size_bytes"],
                    status=row["status"],
                )
                for row in rows
            ]
    
    async def add_punishment(self, punishment: UserPunishment) -> int:
        """Add a new punishment record.
        
        Args:
            punishment: Punishment to add
            
        Returns:
            ID of the inserted punishment
            
        Raises:
            ValueError: If the punishment could not be inserted
        """
        conn = await self._ensure_connection()
        async with conn.cursor() as cursor:
            # Deactivate any existing active punishments for the user
            await cursor.execute(
                """
                UPDATE punishments
                SET is_active = 0
                WHERE user_id = ? AND is_active = 1
                """,
                (punishment.user_id,)
            )
            
            # Insert new punishment
            await cursor.execute(
                """
                INSERT INTO punishments (
                    user_id, level, start_date, end_date,
                    cooldown_days, request_reduction, data_usage,
                    reason, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    punishment.user_id,
                    punishment.level,
                    punishment.start_date,
                    punishment.end_date,
                    punishment.cooldown_days,
                    punishment.request_reduction,
                    punishment.data_usage,
                    punishment.reason,
                    punishment.is_active
                )
            )
            
            punishment_id = cast(int, cursor.lastrowid)
            if punishment_id is None:
                raise ValueError("Failed to insert punishment")
            
            # Update user stats with current punishment
            await cursor.execute(
                """
                UPDATE user_stats
                SET current_punishment_id = ?,
                    punishment_level = ?,
                    cooldown_days = ?
                WHERE user_id = ?
                """,
                (
                    punishment_id,
                    punishment.level,
                    punishment.cooldown_days,
                    punishment.user_id
                )
            )
            
            await conn.commit()
            return punishment_id
    
    async def get_active_punishment(
        self,
        user_id: UserId
    ) -> Optional[UserPunishment]:
        """Get active punishment for a user.
        
        Args:
            user_id: User to get punishment for
            
        Returns:
            Active punishment if found, None otherwise
        """
        conn = await self._ensure_connection()
        async with conn.cursor() as cursor:
            await cursor.execute(
                """
                SELECT * FROM punishments 
                WHERE user_id = ? AND is_active = 1 
                ORDER BY start_date DESC LIMIT 1
                """,
                (user_id,)
            )
            row = await cursor.fetchone()
            if not row:
                return None
                
            return UserPunishment(
                id=row['id'],
                user_id=row['user_id'],
                level=row['level'],
                start_date=row['start_date'],
                end_date=row['end_date'],
                cooldown_days=row['cooldown_days'],
                request_reduction=row['request_reduction'],
                reason=row['reason'],
                data_usage=row['data_usage'],
                is_active=row['is_active']
            )
    
    async def get_punished_users(self) -> list[UserStats]:
        """Get all users with active punishments.
        
        Returns:
            List of user stats for punished users
        """
        query = """
            SELECT us.*
            FROM user_stats us
            JOIN punishments p ON us.current_punishment_id = p.id
            WHERE p.is_active = 1 AND p.end_date > datetime('now')
        """
        
        conn = await self._ensure_connection()
        async with conn.execute(query) as cursor:
            rows = await cursor.fetchall()
            return [UserStats(**dict(row)) for row in rows]
    
    async def update_user_stats(
        self,
        stats: UserStats
    ) -> None:
        """Update statistics for a user.
        
        Args:
            stats: User statistics to update
        """
        conn = await self._ensure_connection()
        async with conn.cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO user_stats (
                    user_id, total_requests, total_data_usage,
                    last_request_date
                ) VALUES (?, ?, ?, ?)
                ON CONFLICT (user_id) DO UPDATE SET
                    total_requests = excluded.total_requests,
                    total_data_usage = excluded.total_data_usage,
                    last_request_date = excluded.last_request_date
                """,
                (
                    stats.user_id,
                    stats.total_requests,
                    stats.total_data_usage,
                    stats.last_request_date,
                )
            )
            await conn.commit()
    
    async def get_user_stats(
        self,
        user_id: UserId
    ) -> Optional[UserStats]:
        """Get user statistics.
        
        Args:
            user_id: User ID to get stats for
            
        Returns:
            User stats if found, None otherwise
        """
        conn = await self._ensure_connection()
        async with conn.cursor() as cursor:
            await cursor.execute(
                """
                SELECT * FROM user_stats WHERE user_id = ?
                """,
                (user_id,)
            )
            row = await cursor.fetchone()
            if not row:
                return None
                
            return UserStats(
                user_id=row['user_id'],
                username=row['username'],
                total_data_usage=row['total_data_usage'],
                total_requests=row['total_requests'],
                punishment_level=row['punishment_level'],
                cooldown_days=row['cooldown_days'],
                request_limit=row['request_limit']
            )
    
    async def create_user_stats(self, stats: UserStats) -> None:
        """Create a new user stats record.
        
        Args:
            stats: User stats to create
        """
        query = """
            INSERT INTO user_stats (
                user_id, total_requests, total_data_usage,
                current_punishment_id, last_request_date
            ) VALUES (?, ?, ?, ?, ?)
        """
        params = (
            stats.user_id,
            stats.total_requests,
            stats.total_data_usage,
            stats.current_punishment_id,
            stats.last_request_date,
        )
        
        conn = await self._ensure_connection()
        async with conn.cursor() as cursor:
            await cursor.execute(query, params)
            await conn.commit()
            
    async def get_punishment(self, punishment_id: int) -> Optional[UserPunishment]:
        """Get a punishment by ID.
        
        Args:
            punishment_id: ID of the punishment to get
            
        Returns:
            Punishment if found, None otherwise
        """
        query = "SELECT * FROM punishments WHERE id = ?"
        
        conn = await self._ensure_connection()
        async with conn.execute(query, (punishment_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            return UserPunishment(
                id=row['id'],
                user_id=row['user_id'],
                level=int(row['level']),
                start_date=row['start_date'],
                end_date=row['end_date'],
                cooldown_days=row['cooldown_days'],
                request_reduction=row['request_reduction'],
                data_usage=row['data_usage'],
                is_active=bool(row['is_active']),
                reason=row['reason'] if row['reason'] else None
            )

    async def create_punishment(
        self,
        user_id: UserId,
        level: int,
        start_date: datetime,
        end_date: datetime,
        cooldown_days: int,
        request_reduction: int,
        data_usage: int,
        is_active: bool = True,
        reason: Optional[str] = None,
    ) -> UserPunishment:
        """Create a new punishment record.
        
        Args:
            user_id: User to punish
            level: Punishment level
            start_date: When punishment starts
            end_date: When punishment ends
            cooldown_days: Number of cooldown days
            request_reduction: Percentage to reduce requests by
            data_usage: Data usage that triggered punishment
            is_active: Whether punishment is active
            reason: Optional reason for punishment
            
        Returns:
            Created punishment record
        """
        conn = await self._ensure_connection()
        
        query = """
        INSERT INTO punishments (
            user_id, level, start_date, end_date, 
            cooldown_days, request_reduction, data_usage,
            is_active, reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            str(user_id), level, start_date, end_date,
            cooldown_days, request_reduction, data_usage,
            is_active, reason
        )
        
        async with conn.execute(query, params) as cursor:
            punishment_id = cursor.lastrowid
            await conn.commit()
            
            return UserPunishment(
                id=int(punishment_id) if punishment_id is not None else 0,
                user_id=user_id,
                level=level,
                start_date=start_date,
                end_date=end_date,
                cooldown_days=cooldown_days,
                request_reduction=request_reduction,
                data_usage=data_usage,
                is_active=is_active,
                reason=reason
            )

    async def update_punishment(
        self,
        punishment: UserPunishment
    ) -> None:
        """Update an existing punishment record.
        
        Args:
            punishment: Punishment record to update
        """
        conn = await self._ensure_connection()
        
        query = """
        UPDATE punishments SET
            level = ?,
            start_date = ?,
            end_date = ?,
            cooldown_days = ?,
            request_reduction = ?,
            data_usage = ?,
            is_active = ?,
            reason = ?
        WHERE id = ?
        """
        
        params = (
            punishment.level,
            punishment.start_date,
            punishment.end_date,
            punishment.cooldown_days,
            punishment.request_reduction,
            punishment.data_usage,
            punishment.is_active,
            punishment.reason,
            punishment.id
        )
        
        async with conn.execute(query, params):
            await conn.commit()

    async def deactivate_punishment(
        self,
        user_id: UserId,
        reason: Optional[str] = None
    ) -> None:
        """Deactivate a user's active punishment.
        
        Args:
            user_id: User whose punishment to deactivate
            reason: Optional reason for deactivation
        """
        conn = await self._ensure_connection()
        async with conn.cursor() as cursor:
            await cursor.execute(
                """
                UPDATE punishments
                SET is_active = 0, reason = COALESCE(?, reason)
                WHERE user_id = ? AND is_active = 1
                """,
                (reason, str(user_id))
            )
            await conn.commit()

    async def remove_user_punishments(self, user_id: UserId) -> None:
        """Remove all punishments for a user.
        
        Args:
            user_id: User whose punishments to remove
        """
        query = "DELETE FROM punishments WHERE user_id = ?"
        
        conn = await self._ensure_connection()
        async with conn.cursor() as cursor:
            await cursor.execute(query, (user_id,))
            await conn.commit()

    async def adjust_user_limit(self, user_id: UserId, adjustment: int, reason: str) -> None:
        """Adjust a user's request limit.
        
        Args:
            user_id: User to adjust limit for
            adjustment: Number of requests to add/remove (positive/negative)
            reason: Reason for the adjustment
        """
        query = """
            UPDATE user_stats 
            SET request_limit = request_limit + ?
            WHERE user_id = ?
        """
        
        conn = await self._ensure_connection()
        async with conn.cursor() as cursor:
            await cursor.execute(query, (adjustment, user_id))
            await conn.commit()

    async def get_tables(self) -> list[str]:
        """Get list of tables in database.
        
        Returns:
            List of table names
        """
        conn = await self._ensure_connection()
        async with conn.cursor() as cursor:
            await cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = await cursor.fetchall()
            return [table[0] for table in tables]

    async def get_request(self, request_id: int) -> Optional[UserRequest]:
        """Get a request by ID.
        
        Args:
            request_id: ID of request to get
            
        Returns:
            Request if found
        """
        conn = await self._ensure_connection()
        async with conn.execute(
            "SELECT * FROM requests WHERE id = ?", (request_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            return UserRequest(**dict(row))

    async def save_user_stats(self, stats: UserStats) -> None:
        """Save user statistics.
        
        Args:
            stats: Stats to save
        """
        conn = await self._ensure_connection()
        async with conn.cursor() as cursor:
            await cursor.execute(
                """
                UPDATE user_stats SET
                    username = ?,
                    total_data_usage = ?,
                    total_requests = ?,
                    punishment_level = ?,
                    cooldown_days = ?,
                    request_limit = ?
                WHERE user_id = ?
                """,
                (
                    stats.username,
                    stats.total_data_usage,
                    stats.total_requests,
                    stats.punishment_level,
                    stats.cooldown_days,
                    stats.request_limit,
                    stats.user_id,
                ),
            )
            await conn.commit()

    async def adjust_request_limit(
        self,
        user_id: UserId,
        adjustment: int,
    ) -> bool:
        """Adjust a user's request limit.
        
        Args:
            user_id: User to adjust
            adjustment: Amount to adjust by
            
        Returns:
            True if successful
        """
        conn = await self._ensure_connection()
        async with conn.cursor() as cursor:
            await cursor.execute(
                """
                UPDATE users 
                SET request_limit = request_limit + ?
                WHERE user_id = ?
                """,
                (adjustment, str(user_id))
            )
            await conn.commit()
            return cursor.rowcount > 0

    async def ensure_user_exists(self, stats: UserStats) -> None:
        """Ensure user exists in user_stats table.
        
        If user doesn't exist, creates a new record.
        If user exists, does nothing.
        
        Args:
            stats: User stats to create if user doesn't exist
        """
        conn = await self._ensure_connection()
        async with conn.cursor() as cursor:
            # Check if user exists
            await cursor.execute(
                "SELECT user_id FROM user_stats WHERE user_id = ?",
                (stats.user_id,)
            )
            if not await cursor.fetchone():
                # User doesn't exist, create new record
                await cursor.execute(
                    """
                    INSERT INTO user_stats (
                        user_id, username, total_data_usage, total_requests,
                        punishment_level, cooldown_days, request_limit
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        stats.user_id,
                        stats.username,
                        stats.total_data_usage,
                        stats.total_requests,
                        stats.punishment_level,
                        stats.cooldown_days,
                        stats.request_limit
                    )
                )
                await conn.commit()
