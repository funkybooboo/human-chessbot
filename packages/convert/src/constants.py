"""Constants and configuration values for the convert package."""

from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Currently, the convert package uses command-line arguments for configuration
# No environment variables are needed at this time
# This file is here for consistency and future expansion
