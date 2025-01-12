"""Main CLI entry point."""

import click
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

from ..database.manager import DatabaseManager
from ..shared.types import UserId
from ..database.models import UserRequest, UserStats, UserPunishment

@click.group()
def cli():
    """Judgarr CLI tool."""
    pass

@cli.command()
@click.option('--db', type=click.Path(), required=True, help='Path to database file')
def init(db: str):
    """Initialize the database."""
    db_path = Path(db)
    manager = DatabaseManager(db_path)
    async def _init():
        async with manager:
            await manager.initialize()
    asyncio.run(_init())
    click.echo("Database initialized")

@cli.group()
def user():
    """User management commands."""
    pass

@user.command()
@click.option('--user-id', required=True, help='User ID to get stats for')
@click.option('--db', type=click.Path(), required=True, help='Path to database file')
def stats(user_id: str, db: str):
    """Get user stats."""
    db_path = Path(db)
    manager = DatabaseManager(db_path)
    async def _get_stats():
        async with manager:
            stats = await manager.get_user_stats(UserId(user_id))
            if stats:
                click.echo(f"Stats for {user_id}:")
                click.echo(f"Total Requests: {stats.total_requests}")
                click.echo(f"Total Data Usage: {stats.total_data_usage}")
                if stats.last_request_date:
                    click.echo(f"Last Request: {stats.last_request_date}")
            else:
                click.echo("No stats found")
    asyncio.run(_get_stats())

@cli.group()
def request():
    """Request management commands."""
    pass

@request.command(name='add')
@click.option('--user-id', required=True, help='User ID')
@click.option('--media-id', required=True, help='Media ID')
@click.option('--media-type', required=True, help='Media type')
@click.option('--size', type=int, required=True, help='Size in bytes')
@click.option('--db', type=click.Path(), required=True, help='Path to database file')
def add_request(user_id: str, media_id: str, media_type: str, size: int, db: str):
    """Add a new request."""
    db_path = Path(db)
    manager = DatabaseManager(db_path)
    async def _add_request():
        async with manager:
            # First ensure user exists
            stats = UserStats(
                user_id=UserId(user_id),
                username=f"user_{user_id}",  # Default username based on ID
                total_data_usage=0,
                total_requests=0,
                punishment_level=0,
                cooldown_days=0,
                request_limit=10,
                current_punishment_id=None
            )
            await manager.ensure_user_exists(stats)
            
            request = UserRequest(
                id=0,  # Will be set by database
                user_id=UserId(user_id),
                media_id=media_id,
                media_type=media_type,
                request_date=datetime.now(),
                size_bytes=size,
                status="pending"
            )
            await manager.add_request(request)
    asyncio.run(_add_request())
    click.echo("Request added successfully")

@request.command(name='list')
@click.option('--user-id', required=True, help='User ID')
@click.option('--db', type=click.Path(), required=True, help='Path to database file')
def list_requests(user_id: str, db: str):
    """List user requests."""
    db_path = Path(db)
    manager = DatabaseManager(db_path)
    async def _list_requests():
        async with manager:
            requests = await manager.get_user_requests(UserId(user_id))
            if not requests:
                click.echo("No requests found")
                return
            for req in requests:
                click.echo(f"{req.media_id} ({req.media_type}) - {req.size_bytes} bytes")
    asyncio.run(_list_requests())

@cli.group()
def punishment():
    """Punishment management commands."""
    pass

@punishment.command(name='add')
@click.option('--user-id', required=True, help='User ID')
@click.option('--level', type=int, required=True, help='Punishment level')
@click.option('--days', type=int, required=True, help='Duration in days')
@click.option('--reason', required=True, help='Reason for punishment')
@click.option('--db', type=click.Path(), required=True, help='Path to database file')
def add_punishment(user_id: str, level: int, days: int, reason: str, db: str):
    """Add a punishment."""
    db_path = Path(db)
    manager = DatabaseManager(db_path)
    async def _add_punishment():
        async with manager:
            # First ensure user exists
            stats = UserStats(
                user_id=UserId(user_id),
                username=f"user_{user_id}",  # Default username based on ID
                total_data_usage=0,
                total_requests=0,
                punishment_level=0,
                cooldown_days=0,
                request_limit=10,
                current_punishment_id=None
            )
            await manager.ensure_user_exists(stats)
            
            punishment = UserPunishment(
                id=0,
                user_id=UserId(user_id),
                level=level,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=days),
                cooldown_days=days,
                request_reduction=level * 2,
                reason=reason,
                data_usage=0,
                is_active=True
            )
            await manager.add_punishment(punishment)
    asyncio.run(_add_punishment())
    click.echo("Punishment added successfully")

@punishment.command(name='list')
@click.option('--user-id', required=True, help='User ID')
@click.option('--db', type=click.Path(), required=True, help='Path to database file')
def list_punishments(user_id: str, db: str):
    """List user punishments."""
    db_path = Path(db)
    manager = DatabaseManager(db_path)
    async def _list_punishments():
        async with manager:
            punishment = await manager.get_active_punishment(UserId(user_id))
            if punishment:
                click.echo(f"Level {punishment.level} - {punishment.reason} ({punishment.cooldown_days} days)")
            else:
                click.echo("No active punishments")
    asyncio.run(_list_punishments())

@punishment.command(name='remove')
@click.option('--user-id', required=True, help='User ID')
@click.option('--reason', required=True, help='Reason for removal')
@click.option('--db', type=click.Path(), required=True, help='Path to database file')
def remove_punishment(user_id: str, reason: str, db: str):
    """Remove punishment."""
    db_path = Path(db)
    manager = DatabaseManager(db_path)
    async def _remove_punishment():
        async with manager:
            # Ensure user exists before trying to remove punishment
            stats = UserStats(
                user_id=UserId(user_id),
                username=f"user_{user_id}",  # Default username based on ID
                total_data_usage=0,
                total_requests=0,
                punishment_level=0,
                cooldown_days=0,
                request_limit=10,
                current_punishment_id=None
            )
            await manager.ensure_user_exists(stats)
            
            # Remove punishment
            await manager.deactivate_punishment(UserId(user_id), reason)
    asyncio.run(_remove_punishment())
    click.echo("Punishment removed successfully")
