"""Command to reset a user's punishment."""

from argparse import ArgumentParser, Namespace
from typing import Optional

from ..commands.base import BaseCommand
from ...core.punishments.manager import PunishmentManager
from ...database.manager import DatabaseManager
from ...core.notifications.manager import NotificationManager
from ...shared.constants import DEFAULT_DATABASE_PATH
from ...shared.types import UserId

class ResetCommand(BaseCommand):
    """Reset a user's punishment."""

    def __init__(self) -> None:
        """Initialize the reset command."""
        super().__init__()
        self.db_manager: Optional[DatabaseManager] = None
        self.punishment_manager: Optional[PunishmentManager] = None
        self.notification_manager: Optional[NotificationManager] = None

    def setup_parser(self, parser: ArgumentParser) -> None:
        """Set up the argument parser for the reset command.
        
        Args:
            parser: The argument parser to configure
        """
        parser.add_argument(
            'user',
            help='User to reset punishment for'
        )
        parser.add_argument(
            '--reason',
            help='Reason for reset',
            type=str,
            required=False
        )
        parser.add_argument(
            '--no-notify',
            action='store_true',
            help='Skip sending notification to user'
        )

    async def execute(self, args: Namespace) -> int:
        """Execute the reset command.
        
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
            
            if not args.no_notify:
                self.notification_manager = NotificationManager()

            # Reset punishment
            success = await self.punishment_manager.reset_punishment(
                user_id=UserId(args.user),
                reason=args.reason
            )

            if not success:
                print(f"Error: Failed to reset punishment for user '{args.user}'")
                return 1

            # Send notification if enabled
            if not args.no_notify and self.notification_manager:
                await self.notification_manager.notify_reset(
                    recipient=args.user,
                    reason=args.reason
                )

            print(f"Successfully reset punishment for user '{args.user}'")
            if args.reason:
                print(f"Reason: {args.reason}")

            return 0

        except Exception as e:
            print(f"Error: {str(e)}")
            return 1
