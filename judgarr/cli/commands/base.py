"""Base command class for all CLI commands."""

from abc import ABC, abstractmethod
from argparse import ArgumentParser, Namespace
from typing import Optional

class BaseCommand(ABC):
    """Base class for all CLI commands."""

    def __init__(self) -> None:
        """Initialize the command."""
        self.name: str = self.__class__.__name__.lower().replace('command', '')
        self.help: str = self.__doc__ or ''
        self.parser: Optional[ArgumentParser] = None

    @abstractmethod
    def setup_parser(self, parser: ArgumentParser) -> None:
        """Set up the argument parser for this command.
        
        Args:
            parser: The argument parser to configure
        """
        raise NotImplementedError

    @abstractmethod
    def execute(self, args: Namespace) -> int:
        """Execute the command with the given arguments.
        
        Args:
            args: The parsed command line arguments
            
        Returns:
            int: The exit code (0 for success, non-zero for failure)
        """
        raise NotImplementedError

    def __call__(self, args: Namespace) -> int:
        """Execute the command when called.
        
        Args:
            args: The parsed command line arguments
            
        Returns:
            int: The exit code (0 for success, non-zero for failure)
        """
        return self.execute(args)
