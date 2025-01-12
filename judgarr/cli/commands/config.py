"""Command to manage global configuration settings."""

import os
from argparse import ArgumentParser, Namespace
from typing import Optional
import yaml

from ..commands.base import BaseCommand
from ...config import Config, load_config
from ...shared.constants import DEFAULT_CONFIG_PATH as CONFIG_FILE_PATH

class ConfigCommand(BaseCommand):
    """View and modify global configuration settings."""

    def __init__(self) -> None:
        """Initialize the config command."""
        super().__init__()
        self.config: Optional[Config] = None

    def setup_parser(self, parser: ArgumentParser) -> None:
        """Set up the argument parser for the config command.
        
        Args:
            parser: The argument parser to configure
        """
        subparsers = parser.add_subparsers(dest='action', help='Config action')

        # View config
        view_parser = subparsers.add_parser('view', help='View current configuration')
        view_parser.add_argument(
            '--json',
            action='store_true',
            help='Output in JSON format'
        )

        # Set config value
        set_parser = subparsers.add_parser('set', help='Set a configuration value')
        set_parser.add_argument(
            'key',
            help='Configuration key (e.g., punishment.cooldown_increment)'
        )
        set_parser.add_argument(
            'value',
            help='New value'
        )

        # Reset config
        reset_parser = subparsers.add_parser('reset', help='Reset configuration to defaults')
        reset_parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompt'
        )

    def execute(self, args: Namespace) -> int:
        """Execute the config command.
        
        Args:
            args: The parsed command line arguments
            
        Returns:
            int: Exit code (0 for success, non-zero for failure)
        """
        try:
            if not args.action:
                print("Error: No action specified. Use --help for usage information.")
                return 1

            # Load current config
            self.config = load_config()

            # Handle different actions
            if args.action == 'view':
                return self._handle_view(args)
            elif args.action == 'set':
                return self._handle_set(args)
            elif args.action == 'reset':
                return self._handle_reset(args)

            return 0

        except Exception as e:
            print(f"Error: {str(e)}")
            return 1

    def _handle_view(self, args: Namespace) -> int:
        """Handle the 'view' action.
        
        Args:
            args: The parsed command line arguments
            
        Returns:
            int: Exit code (0 for success, non-zero for failure)
        """
        if not self.config:
            print("Error: Failed to load configuration")
            return 1

        if args.json:
            import json
            print(json.dumps(self.config.model_dump(), indent=2))
        else:
            print("\nCurrent Configuration:")
            print("-" * 80)
            self._print_config_recursive(self.config.model_dump())
        return 0

    def _handle_set(self, args: Namespace) -> int:
        """Handle the 'set' action.
        
        Args:
            args: The parsed command line arguments
            
        Returns:
            int: Exit code (0 for success, non-zero for failure)
        """
        # Load current config as dict
        with open(CONFIG_FILE_PATH, 'r') as f:
            config_dict = yaml.safe_load(f)

        # Update the value
        keys = args.key.split('.')
        current = config_dict
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Convert value to appropriate type
        try:
            value = yaml.safe_load(args.value)
        except yaml.YAMLError:
            value = args.value

        current[keys[-1]] = value

        # Save updated config
        with open(CONFIG_FILE_PATH, 'w') as f:
            yaml.safe_dump(config_dict, f, default_flow_style=False)

        print(f"Successfully updated {args.key} = {value}")
        return 0

    def _handle_reset(self, args: Namespace) -> int:
        """Handle the 'reset' action.
        
        Args:
            args: The parsed command line arguments
            
        Returns:
            int: Exit code (0 for success, non-zero for failure)
        """
        if not args.force:
            response = input("Are you sure you want to reset the configuration to defaults? [y/N] ")
            if response.lower() != 'y':
                print("Reset cancelled.")
                return 0

        # Copy template to config file
        template_path = os.path.join(os.path.dirname(CONFIG_FILE_PATH), 'config.yml.template')
        if not os.path.exists(template_path):
            print("Error: Configuration template not found")
            return 1

        import shutil
        shutil.copy2(template_path, CONFIG_FILE_PATH)
        print("Successfully reset configuration to defaults")
        return 0

    def _print_config_recursive(self, config: dict, prefix: str = '') -> None:
        """Recursively print configuration values.
        
        Args:
            config: Configuration dictionary to print
            prefix: Current key prefix
        """
        for key, value in config.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                print(f"\n{full_key}:")
                self._print_config_recursive(value, full_key)
            else:
                print(f"{full_key:40} = {value}")
