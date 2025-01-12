"""
Migration manager for handling database schema migrations.
"""

import logging
import sqlite3
from pathlib import Path
from typing import List, Optional

from judgarr.database.schema import SCHEMA_VERSION

logger = logging.getLogger(__name__)

class MigrationManager:
    """Manages database migrations for Judgarr."""
    
    def __init__(self, db_path: str):
        """Initialize the migration manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
    
    @property
    def conn(self) -> sqlite3.Connection:
        """Get the database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn
    
    def close(self):
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
    
    def get_current_version(self) -> int:
        """Get the current database schema version."""
        try:
            cursor = self.conn.execute(
                "SELECT version FROM schema_version ORDER BY version DESC LIMIT 1"
            )
            result = cursor.fetchone()
            return result[0] if result else 0
        except sqlite3.OperationalError:
            return 0
    
    def set_version(self, version: int):
        """Set the database schema version.
        
        Args:
            version: The new schema version
        """
        self.conn.execute("DELETE FROM schema_version")
        self.conn.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
        self.conn.commit()
    
    def run_migration(self, migration_file: Path):
        """Run a single migration file.
        
        Args:
            migration_file: Path to the migration file
        """
        logger.info(f"Running migration: {migration_file.name}")
        with open(migration_file, 'r') as f:
            sql = f.read()
            
        try:
            self.conn.executescript(sql)
            self.conn.commit()
            logger.info(f"Successfully applied migration: {migration_file.name}")
        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(f"Failed to apply migration {migration_file.name}: {e}")
            raise
    
    def get_pending_migrations(self) -> List[Path]:
        """Get a list of pending migrations that need to be applied."""
        current_version = self.get_current_version()
        migrations_dir = Path(__file__).parent
        
        pending = []
        for migration_file in sorted(migrations_dir.glob("*.sql")):
            try:
                version = int(migration_file.stem.split('_')[0])
                if version > current_version:
                    pending.append(migration_file)
            except (ValueError, IndexError):
                continue
                
        return sorted(pending)
    
    def migrate(self):
        """Run all pending migrations."""
        pending = self.get_pending_migrations()
        if not pending:
            logger.info("Database is up to date")
            return
            
        logger.info(f"Found {len(pending)} pending migrations")
        
        try:
            for migration_file in pending:
                version = int(migration_file.stem.split('_')[0])
                self.run_migration(migration_file)
                self.set_version(version)
                
            logger.info(f"Successfully migrated database to version {SCHEMA_VERSION}")
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
        finally:
            self.close()
