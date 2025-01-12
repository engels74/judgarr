"""Command to guide users through initial setup."""

import os
from argparse import ArgumentParser, Namespace
from typing import Dict, Any
import yaml

from ..commands.base import BaseCommand
from ...shared.constants import DEFAULT_CONFIG_PATH as CONFIG_FILE_PATH

class SetupCommand(BaseCommand):
    """Interactive setup for initial configuration."""

    def __init__(self) -> None:
        """Initialize the setup command."""
        super().__init__()
        self.config: Dict[str, Any] = {}

    def setup_parser(self, parser: ArgumentParser) -> None:
        """Set up the argument parser for the setup command.
        
        Args:
            parser: The argument parser to configure
        """
        parser.add_argument(
            '--advanced',
            action='store_true',
            help='Enable advanced configuration options'
        )
        parser.add_argument(
            '--non-interactive',
            action='store_true',
            help='Run setup without prompts (requires all values as arguments)'
        )

    def execute(self, args: Namespace) -> int:
        """Execute the setup command.
        
        Args:
            args: The parsed command line arguments
            
        Returns:
            int: Exit code (0 for success, non-zero for failure)
        """
        try:
            print("\nWelcome to the Judgarr Setup Wizard!")
            print("=====================================")

            # Load template if it exists
            template_path = os.path.join(os.path.dirname(CONFIG_FILE_PATH), 'config.yml.template')
            if os.path.exists(template_path):
                with open(template_path, 'r') as f:
                    self.config = yaml.safe_load(f)
            else:
                self.config = {}

            # Basic setup
            self._setup_api_keys()
            self._setup_notification_settings()
            self._setup_basic_punishment_settings()

            # Advanced setup if requested
            if args.advanced:
                self._setup_advanced_punishment_settings()
                self._setup_advanced_tracking_settings()

            # Save configuration
            os.makedirs(os.path.dirname(CONFIG_FILE_PATH), exist_ok=True)
            with open(CONFIG_FILE_PATH, 'w') as f:
                yaml.safe_dump(self.config, f, default_flow_style=False)

            print("\nSetup complete! Configuration saved to:", CONFIG_FILE_PATH)
            print("\nYou can modify these settings later using the 'judgarr config' command.")
            return 0

        except KeyboardInterrupt:
            print("\nSetup cancelled.")
            return 1
        except Exception as e:
            print(f"\nError during setup: {str(e)}")
            return 1

    def _prompt(self, message: str, default: Any = None, required: bool = True) -> str:
        """Prompt the user for input.
        
        Args:
            message: The prompt message
            default: Default value if user enters nothing
            required: Whether the value is required
            
        Returns:
            str: The user's input or default value
        """
        if default:
            prompt = f"{message} [{default}]: "
        else:
            prompt = f"{message}: "

        while True:
            value = input(prompt)
            if not value:
                if default is not None:
                    return default
                if not required:
                    return ''
                print("This field is required.")
                continue
            return value

    def _setup_api_keys(self) -> None:
        """Set up API keys for external services."""
        print("\nAPI Configuration")
        print("-----------------")
        print("Please enter your API keys for the following services:")

        self.config.setdefault('api', {})
        
        # Overseerr
        print("\nOverseerr Configuration:")
        self.config['api']['overseerr'] = {
            'url': self._prompt("Overseerr URL (e.g., http://localhost:5055)"),
            'api_key': self._prompt("Overseerr API Key")
        }

        # Radarr
        print("\nRadarr Configuration:")
        self.config['api']['radarr'] = {
            'url': self._prompt("Radarr URL (e.g., http://localhost:7878)"),
            'api_key': self._prompt("Radarr API Key")
        }

        # Sonarr
        print("\nSonarr Configuration:")
        self.config['api']['sonarr'] = {
            'url': self._prompt("Sonarr URL (e.g., http://localhost:8989)"),
            'api_key': self._prompt("Sonarr API Key")
        }

    def _setup_notification_settings(self) -> None:
        """Set up notification settings."""
        print("\nNotification Settings")
        print("--------------------")
        
        self.config.setdefault('notifications', {})
        
        # Discord
        print("\nDiscord Notifications:")
        use_discord = self._prompt("Enable Discord notifications? (y/n)", 'y').lower() == 'y'
        if use_discord:
            self.config['notifications']['discord'] = {
                'webhook_url': self._prompt("Discord Webhook URL")
            }

        # Email
        print("\nEmail Notifications:")
        use_email = self._prompt("Enable email notifications? (y/n)", 'n').lower() == 'y'
        if use_email:
            self.config['notifications']['email'] = {
                'smtp_host': self._prompt("SMTP Host"),
                'smtp_port': int(self._prompt("SMTP Port", "587")),
                'smtp_user': self._prompt("SMTP Username"),
                'smtp_pass': self._prompt("SMTP Password"),
                'from_address': self._prompt("From Email Address"),
                'use_tls': self._prompt("Use TLS? (y/n)", 'y').lower() == 'y'
            }

    def _setup_basic_punishment_settings(self) -> None:
        """Set up basic punishment settings."""
        print("\nPunishment Settings")
        print("------------------")
        
        self.config.setdefault('punishment', {})
        self.config['punishment'].update({
            'cooldown_increment': int(self._prompt(
                "Base cooldown increment in days",
                "3"
            )),
            'request_limit_decrement': int(self._prompt(
                "Base request limit reduction",
                "5"
            )),
            'max_cooldown_days': int(self._prompt(
                "Maximum cooldown period in days",
                "100"
            )),
            'min_request_limit': int(self._prompt(
                "Minimum request limit",
                "0"
            ))
        })

    def _setup_advanced_punishment_settings(self) -> None:
        """Set up advanced punishment settings."""
        print("\nAdvanced Punishment Settings")
        print("--------------------------")
        
        self.config['punishment'].update({
            'exponential_factor': float(self._prompt(
                "Punishment exponential growth factor",
                "1.5"
            )),
            'cooldown_reset_days': int(self._prompt(
                "Days of good behavior before resetting punishment level",
                "30"
            )),
            'override_roles': self._prompt(
                "Comma-separated list of roles exempt from punishments",
                "admin,moderator"
            ).split(',')
        })

    def _setup_advanced_tracking_settings(self) -> None:
        """Set up advanced tracking settings."""
        print("\nAdvanced Tracking Settings")
        print("-------------------------")
        
        self.config.setdefault('tracking', {})
        self.config['tracking'].update({
            'history_days': int(self._prompt(
                "Number of days to track request history",
                "30"
            )),
            'check_interval': int(self._prompt(
                "Check interval in minutes",
                "60"
            )),
            'size_thresholds': {
                'warning': float(self._prompt(
                    "Data usage warning threshold in GB",
                    "500"
                )),
                'punishment': float(self._prompt(
                    "Data usage punishment threshold in GB",
                    "1000"
                ))
            }
        })
