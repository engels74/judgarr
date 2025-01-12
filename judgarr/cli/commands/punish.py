"""Command to manually punish a user."""

from argparse import ArgumentParser, Namespace
from typing import Optional
from datetime import datetime, timedelta

from ..commands.base import BaseCommand
from ...core.punishments import PunishmentLevel
from ...core.punishments.manager import PunishmentManager
from ...database.manager import DatabaseManager
from ...core.notifications.manager import NotificationManager
from ...shared.constants import DEFAULT_DATABASE_PATH
from ...shared.types import UserId
from ...database.models import UserPunishment

class PunishCommand(BaseCommand):
    """Manually punish a user."""

    def __init__(self) -> None:
        """Initialize the punish command."""
        super().__init__()
        self.db_manager: Optional[DatabaseManager] = None
        self.punishment_manager: Optional[PunishmentManager] = None
        self.notification_manager: Optional[NotificationManager] = None

    def setup_parser(self, parser: ArgumentParser) -> None:
        """Set up the argument parser for the punish command.
        
        Args:
            parser: The argument parser to configure
        """
        parser.add_argument(
            'user',
            help='User to punish'
        )
        parser.add_argument(
            '--level',
            type=int,
            help='Punishment level (1-3)',
            choices=[1, 2, 3],
            required=True
        )
        parser.add_argument(
            '--reason',
            help='Reason for punishment',
            type=str,
            required=False
        )

    async def execute(self, args: Namespace) -> int:
        """Execute the punish command.
        
        Args:
            args: The parsed command line arguments
            
        Returns:
            int: Exit code (0 for success, non-zero for failure)
        """
        try:
            # Initialize services
            self.db_manager = DatabaseManager(database_path=DEFAULT_DATABASE_PATH)
            await self.db_manager.initialize()
            
            self.punishment_manager = PunishmentManager(
                db_manager=self.db_manager
            )
            
            self.notification_manager = NotificationManager()

            # Create punishment
            now = datetime.now()
            # Convert numeric level to PunishmentLevel enum
            punishment_level = PunishmentLevel(args.level)
            
            # Get punishment parameters based on level
            cooldown_days = 7 * args.level  # 7 days per level
            request_reduction = 5 * args.level  # 5 requests reduction per level
            
            punishment = UserPunishment(
                id=0,  # Will be set by database
                user_id=UserId(args.user),
                level=punishment_level,
                start_date=now,
                end_date=now + timedelta(days=cooldown_days),
                cooldown_days=cooldown_days,
                request_reduction=request_reduction,
                reason=args.reason or "Manual punishment",
                data_usage=0,  # Not data-based
                is_active=True
            )

            # Apply punishment
            punishment_id = await self.db_manager.add_punishment(punishment)

            if not punishment_id:
                print(f"Error: Failed to create punishment for user '{args.user}'")
                return 1

            # Get full punishment details
            full_punishment = await self.db_manager.get_punishment(punishment_id)
            if not full_punishment:
                print(f"Error: Failed to retrieve punishment details for ID {punishment_id}")
                return 1

            # Send notification
            await self.notification_manager.notify_punishment(
                recipient=args.user,
                cooldown_days=full_punishment.cooldown_days,
                request_limit=full_punishment.request_reduction,
                reason=args.reason,
                manual=True
            )

            print(f"Successfully punished user '{args.user}' at level {args.level}")
            return 0

        except Exception as e:
            print(f"Error: {str(e)}")
            return 1
