# Judgarr

A Python utility for dynamically managing Overseerr user request limits based on data usage patterns.

## Features

- Dynamic request limit adjustment based on user behavior
- Integration with Overseerr, Radarr, and Sonarr
- Customizable punishment system
- Multi-channel notifications (Discord, Email)
- Comprehensive logging and monitoring
- Command-line interface for easy management

## Requirements

- Python 3.12 or higher
- Overseerr instance
- Radarr/Sonarr instances
- SQLite3

## Installation

```bash
# Clone the repository
git clone https://github.com/engels74/judgarr-sonnet.git
cd judgarr-sonnet

# Create and activate virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .
```

## Quick Start

1. Run the setup wizard:
```bash
judgarr setup
```

2. Configure your API credentials in the generated `config.yml`

3. Start monitoring user requests:
```bash
judgarr show
```

## Available Commands

- `judgarr show`: Display user statistics and current limits
- `judgarr reset <user>`: Reset punishment for a specific user
- `judgarr punish <user>`: Manually apply punishment to a user
- `judgarr config`: View or modify configuration
- `judgarr setup`: Run the setup wizard
- `judgarr setup --advanced`: Advanced setup with custom parameters

## Configuration

The `config.yml` file contains all necessary settings:

- API credentials for Overseerr, Radarr, and Sonarr
- Punishment thresholds and durations
- Notification settings
- Logging preferences

## Development

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run linting
pylint judgarr
```

## License

[![GNU AGPLv3 Image](https://www.gnu.org/graphics/agplv3-155x51.png)](https://www.gnu.org/licenses/agpl-3.0.en.html)

This project is licensed under the AGPLv3 License - see the LICENSE file for details.