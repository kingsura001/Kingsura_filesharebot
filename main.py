#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import os
from bot import Bot
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """Main function to start the bot"""
    # Check if we need to run with web server (for Render deployment)
    run_with_web = os.getenv("RUN_WITH_WEB", "false").lower() == "true"
    
    if run_with_web:
        # Import web server only when needed
        from web_server import run_bot_with_web_server
        logging.info("Starting bot with web server for Render deployment...")
        await run_bot_with_web_server()
    else:
        # Regular bot mode
        try:
            # Initialize and start the bot
            bot = Bot()
            await bot.start()
            print("Bot started successfully!")
            
            # Keep the bot running
            await asyncio.Event().wait()
            
        except Exception as e:
            logging.error(f"Failed to start bot: {e}")
        finally:
            if 'bot' in locals():
                await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())
