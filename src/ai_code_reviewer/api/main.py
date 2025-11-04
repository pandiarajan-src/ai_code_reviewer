"""Application entry point."""

import logging

import uvicorn
from dotenv import load_dotenv

from ai_code_reviewer.api.app import create_app
from ai_code_reviewer.api.core.config import Config


# Load environment variables BEFORE importing config-dependent modules
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL), format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = create_app()


def main():
    """Start the application server"""
    try:
        # Validate configuration on startup
        Config.validate_config()
        logger.info("Configuration validated successfully")

        # Start the server
        uvicorn.run(
            "ai_code_reviewer.api.main:app",
            host=Config.HOST,
            port=Config.BACKEND_PORT,
            reload=False,
            log_level=Config.LOG_LEVEL.lower(),
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
