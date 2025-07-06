#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
from datetime import datetime
from pyrogram import Client, idle
from pyrogram.errors import FloodWait
from config import Config
from database.database import Database
from utils.auto_delete import AutoDeleteManager
from utils.logger import setup_logger

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="file_sharing_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            plugins=dict(root="plugins"),
            workers=50
        )
        
        # Initialize components
        self.db = Database()
        self.auto_delete = AutoDeleteManager(self)
        self.start_time = datetime.now()
        self.logger = setup_logger()
        
    async def start(self):
        """Start the bot"""
        try:
            await super().start()
            
            # Initialize database
            await self.db.connect()
            
            # Start auto-delete manager
            await self.auto_delete.start()
            
            # Log bot information
            me = await self.get_me()
            self.logger.info(f"Bot started: @{me.username}")
            
            # Verify channels
            await self._verify_channels()
            
        except Exception as e:
            self.logger.error(f"Failed to start bot: {e}")
            raise
    
    async def stop(self):
        """Stop the bot"""
        try:
            # Stop auto-delete manager
            await self.auto_delete.stop()
            
            # Close database connection
            await self.db.close()
            
            await super().stop()
            self.logger.info("Bot stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping bot: {e}")
    
    async def _verify_channels(self):
        """Verify that all configured channels are accessible"""
        channels_to_verify = [Config.CHANNEL_ID] + Config.FORCE_SUB_CHANNELS
        
        for channel_id in channels_to_verify:
            if channel_id == 0:
                continue
                
            try:
                chat = await self.get_chat(channel_id)
                self.logger.info(f"Verified channel: {chat.title} ({channel_id})")
            except Exception as e:
                self.logger.warning(f"Could not verify channel {channel_id}: {e}")
    
    async def send_message_with_retry(self, chat_id, text, **kwargs):
        """Send message with automatic retry on flood wait"""
        try:
            return await self.send_message(chat_id, text, **kwargs)
        except FloodWait as e:
            self.logger.warning(f"FloodWait: sleeping for {e.value} seconds")
            await asyncio.sleep(e.value)
            return await self.send_message(chat_id, text, **kwargs)
    
    async def copy_message_with_retry(self, chat_id, from_chat_id, message_id, **kwargs):
        """Copy message with automatic retry on flood wait"""
        try:
            return await self.copy_message(chat_id, from_chat_id, message_id, **kwargs)
        except FloodWait as e:
            self.logger.warning(f"FloodWait: sleeping for {e.value} seconds")
            await asyncio.sleep(e.value)
            return await self.copy_message(chat_id, from_chat_id, message_id, **kwargs)
    
    def get_uptime(self) -> str:
        """Get bot uptime as formatted string"""
        uptime = datetime.now() - self.start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days:
            return f"{days}d {hours}h {minutes}m {seconds}s"
        elif hours:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
