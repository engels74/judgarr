"""Command to show user data usage and punishments."""

from argparse import ArgumentParser, Namespace
from typing import Optional, List, cast
from pydantic import HttpUrl

from ..commands.base import BaseCommand
from ...api.overseerr.client import OverseerrClient
from ...api.radarr.client import RadarrClient
from ...api.sonarr.client import SonarrClient
from ...core.tracking.service import UserTrackingService
from ...database.manager import DatabaseManager
from ...shared.utils.formatting import format_size
from ...shared.constants import DEFAULT_DATABASE_PATH
from ...config import load_config
from ...database.models import UserStats

class ShowCommand(BaseCommand):
    """List all users and their current data usage and punishments."""

    def __init__(self) -> None:
        """Initialize the show command."""
        super().__init__()
        self.db_manager: Optional[DatabaseManager] = None
        self.tracking_service: Optional[UserTrackingService] = None
        self.config = load_config()

    def setup_parser(self, parser: ArgumentParser) -> None:
        """Set up the argument parser for the show command.
        
        Args:
            parser: The argument parser to configure
        """
        parser.add_argument(
            '--user',
            help='Show data for a specific user (default: all users)',
            type=str,
            required=False
        )
        parser.add_argument(
            '--sort',
            choices=['usage', 'name', 'punishment'],
            default='usage',
            help='Sort results by: usage, name, or punishment level (default: usage)'
        )
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output results in JSON format'
        )

    async def execute(self, args: Namespace) -> int:
        """Execute the show command.
        
        Args:
            args: The parsed command line arguments
            
        Returns:
            int: Exit code (0 for success, non-zero for failure)
        """
        try:
            # Initialize services
            self.db_manager = DatabaseManager(database_path=DEFAULT_DATABASE_PATH)
            await self.db_manager.initialize()
            
            # Initialize API clients
            overseerr_client = OverseerrClient(
                base_url=HttpUrl(str(self.config.api.overseerr.url)),
                api_key=self.config.api.overseerr.api_key
            )
            radarr_client = RadarrClient(
                base_url=HttpUrl(str(self.config.api.radarr.url)),
                api_key=self.config.api.radarr.api_key
            )
            sonarr_client = SonarrClient(
                base_url=HttpUrl(str(self.config.api.sonarr.url)),
                api_key=self.config.api.sonarr.api_key
            )
            
            self.tracking_service = UserTrackingService(
                overseerr_client=overseerr_client,
                radarr_client=radarr_client,
                sonarr_client=sonarr_client
            )

            # Get user data
            users: List[UserStats] = []
            if args.user:
                stats = await self.tracking_service.get_user_stats(args.user)
                if not stats:
                    print(f"Error: User '{args.user}' not found")
                    return 1
                users = [cast(UserStats, stats)]
            else:
                # Get all users from tracking service
                user_stats = await self.tracking_service.get_all_user_stats([])
                users = [cast(UserStats, stats) for stats in user_stats.values()]

            # Sort users
            users.sort(key=self._get_sort_key(args.sort))

            # Display results
            if args.json:
                self._display_json(users)
            else:
                self._display_table(users)

            return 0

        except Exception as e:
            print(f"Error: {str(e)}")
            return 1

    def _get_sort_key(self, sort_by: str):
        """Get the sort key function based on sort criteria.
        
        Args:
            sort_by: The sort criteria ('usage', 'name', or 'punishment')
            
        Returns:
            callable: A function that returns the sort key for a user
        """
        if sort_by == 'usage':
            return lambda u: cast(UserStats, u).total_data_usage
        elif sort_by == 'name':
            return lambda u: cast(UserStats, u).username.lower()
        else:  # punishment
            return lambda u: cast(UserStats, u).punishment_level

    def _display_json(self, users: List[UserStats]) -> None:
        """Display user data in JSON format.
        
        Args:
            users: List of user objects to display
        """
        import json
        data = []
        for user in users:
            user = cast(UserStats, user)
            data.append({
                'username': user.username,
                'data_usage': format_size(user.total_data_usage),
                'punishment_level': user.punishment_level,
                'cooldown_days': user.cooldown_days,
                'request_limit': user.request_limit
            })
        print(json.dumps(data, indent=2))

    def _display_table(self, users: List[UserStats]) -> None:
        """Display user data in a formatted table.
        
        Args:
            users: List of user objects to display
        """
        # Print header
        print("\nUser Data Usage and Punishments:")
        print("-" * 80)
        print(f"{'Username':<20} {'Data Usage':<15} {'Punishment':<10} {'Cooldown':<10} {'Requests':<10}")
        print("-" * 80)

        # Print user data
        for user in users:
            user = cast(UserStats, user)
            print(
                f"{user.username:<20} "
                f"{format_size(user.total_data_usage):<15} "
                f"{user.punishment_level:<10} "
                f"{user.cooldown_days:>8}d "
                f"{user.request_limit:>8}"
            )

        print("-" * 80)
