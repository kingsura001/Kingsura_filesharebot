#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from config import Config

logger = logging.getLogger(__name__)

class AutoDeleteManager:
    """Manages automatic deletion of messages"""
    
    def __init__(self, client):
        self.client = client
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
    
    async def start(self):
        """Start the auto-delete manager"""
        if Config.AUTO_DELETE_TIME > 0:
            self.scheduler.start()
            self.is_running = True
            
            # Start periodic cleanup task
            self.scheduler.add_job(
                self._cleanup_expired_messages,
                'interval',
                minutes=1,  # Check every minute
                id='cleanup_expired_messages'
            )
            
            logger.info("Auto-delete manager started")
        else:
            logger.info("Auto-delete is disabled")
    
    async def stop(self):
        """Stop the auto-delete manager"""
        if self.is_running:
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            logger.info("Auto-delete manager stopped")
    
    async def schedule_delete(self, chat_id: int, message_id: int, delay_seconds: int):
        """Schedule a message for deletion"""
        if not self.is_running or delay_seconds <= 0:
            return
        
        delete_time = datetime.now() + timedelta(seconds=delay_seconds)
        
        # Add to database queue
        await self.client.db.add_to_delete_queue(chat_id, message_id, delete_time)
        
        # Schedule the deletion job
        job_id = f"delete_{chat_id}_{message_id}"
        
        self.scheduler.add_job(
            self._delete_message,
            DateTrigger(run_date=delete_time),
            args=[chat_id, message_id],
            id=job_id,
            replace_existing=True
        )
        
        logger.info(f"Scheduled deletion for message {message_id} in chat {chat_id} at {delete_time}")
    
    async def cancel_delete(self, chat_id: int, message_id: int):
        """Cancel scheduled deletion for a message"""
        job_id = f"delete_{chat_id}_{message_id}"
        
        try:
            self.scheduler.remove_job(job_id)
            await self.client.db.remove_from_delete_queue(chat_id, message_id)
            logger.info(f"Cancelled deletion for message {message_id} in chat {chat_id}")
        except Exception as e:
            logger.error(f"Error cancelling deletion: {e}")
    
    async def _delete_message(self, chat_id: int, message_id: int):
        """Delete a specific message"""
        try:
            # Delete the message
            await self.client.delete_messages(chat_id, message_id)
            
            # Remove from database queue
            await self.client.db.remove_from_delete_queue(chat_id, message_id)
            
            # Send deletion notification if configured
            if Config.AUTO_DEL_SUCCESS_MSG:
                try:
                    await self.client.send_message(
                        chat_id,
                        Config.AUTO_DEL_SUCCESS_MSG
                    )
                except Exception as e:
                    logger.error(f"Error sending deletion notification: {e}")
            
            logger.info(f"Successfully deleted message {message_id} from chat {chat_id}")
            
        except Exception as e:
            logger.error(f"Error deleting message {message_id} from chat {chat_id}: {e}")
            
            # Remove from queue even if deletion failed
            try:
                await self.client.db.remove_from_delete_queue(chat_id, message_id)
            except Exception as e2:
                logger.error(f"Error removing from delete queue: {e2}")
    
    async def _cleanup_expired_messages(self):
        """Cleanup messages that should have been deleted but weren't"""
        try:
            expired_messages = await self.client.db.get_messages_to_delete()
            
            for msg_data in expired_messages:
                chat_id = msg_data["chat_id"]
                message_id = msg_data["message_id"]
                
                # Delete the message
                await self._delete_message(chat_id, message_id)
                
                # Small delay to prevent flooding
                await asyncio.sleep(0.1)
            
            if expired_messages:
                logger.info(f"Cleaned up {len(expired_messages)} expired messages")
                
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
    
    async def schedule_batch_delete(self, chat_id: int, message_ids: List[int], delay_seconds: int):
        """Schedule multiple messages for deletion"""
        for message_id in message_ids:
            await self.schedule_delete(chat_id, message_id, delay_seconds)
    
    async def get_pending_deletions(self, chat_id: Optional[int] = None) -> List[Dict]:
        """Get list of pending deletions"""
        try:
            if chat_id:
                # Get deletions for specific chat
                return await self.client.db.auto_delete_queue.find({
                    "chat_id": chat_id,
                    "delete_at": {"$gt": datetime.now()}
                }).to_list(length=None)
            else:
                # Get all pending deletions
                return await self.client.db.auto_delete_queue.find({
                    "delete_at": {"$gt": datetime.now()}
                }).to_list(length=None)
        except Exception as e:
            logger.error(f"Error getting pending deletions: {e}")
            return []
    
    async def get_deletion_stats(self) -> Dict[str, int]:
        """Get auto-deletion statistics"""
        try:
            total_pending = await self.client.db.auto_delete_queue.count_documents({
                "delete_at": {"$gt": datetime.now()}
            })
            
            total_expired = await self.client.db.auto_delete_queue.count_documents({
                "delete_at": {"$lte": datetime.now()}
            })
            
            return {
                "pending": total_pending,
                "expired": total_expired,
                "total": total_pending + total_expired
            }
        except Exception as e:
            logger.error(f"Error getting deletion stats: {e}")
            return {"pending": 0, "expired": 0, "total": 0}
    
    def is_auto_delete_enabled(self) -> bool:
        """Check if auto-delete is enabled"""
        return Config.AUTO_DELETE_TIME > 0 and self.is_running
    
    def get_auto_delete_time(self) -> int:
        """Get configured auto-delete time in seconds"""
        return Config.AUTO_DELETE_TIME
    
    async def send_delete_warning(self, chat_id: int, message_id: int, seconds_remaining: int):
        """Send warning message before deletion"""
        try:
            warning_text = f"⚠️ **Auto-Delete Warning**\n\nThis message will be deleted in {seconds_remaining} seconds."
            
            await self.client.send_message(chat_id, warning_text)
            
        except Exception as e:
            logger.error(f"Error sending delete warning: {e}")
    
    async def schedule_with_warning(self, chat_id: int, message_id: int, delay_seconds: int, warning_seconds: int = 60):
        """Schedule deletion with warning message"""
        if delay_seconds <= warning_seconds:
            # If delay is less than warning time, just schedule normal deletion
            await self.schedule_delete(chat_id, message_id, delay_seconds)
            return
        
        # Schedule warning
        warning_time = datetime.now() + timedelta(seconds=delay_seconds - warning_seconds)
        warning_job_id = f"warning_{chat_id}_{message_id}"
        
        self.scheduler.add_job(
            self.send_delete_warning,
            DateTrigger(run_date=warning_time),
            args=[chat_id, message_id, warning_seconds],
            id=warning_job_id,
            replace_existing=True
        )
        
        # Schedule actual deletion
        await self.schedule_delete(chat_id, message_id, delay_seconds)
    
    async def extend_deletion_time(self, chat_id: int, message_id: int, additional_seconds: int):
        """Extend deletion time for a message"""
        try:
            # Cancel current deletion
            await self.cancel_delete(chat_id, message_id)
            
            # Schedule new deletion with extended time
            await self.schedule_delete(chat_id, message_id, additional_seconds)
            
            logger.info(f"Extended deletion time for message {message_id} by {additional_seconds} seconds")
            
        except Exception as e:
            logger.error(f"Error extending deletion time: {e}")
    
    async def delete_immediately(self, chat_id: int, message_id: int):
        """Delete a message immediately and remove from queue"""
        await self._delete_message(chat_id, message_id)
