#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
from bot import Bot
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """Main function to start the bot"""
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
