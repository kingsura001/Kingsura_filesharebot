#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError
from config import Config
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.users = None
        self.files = None
        self.batch_links = None
        self.admin_settings = None
        self.auto_delete_queue = None
    
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(Config.DATABASE_URL)
            self.db = self.client[Config.DATABASE_NAME]
            
            # Initialize collections
            self.users = self.db.users
            self.files = self.db.files
            self.batch_links = self.db.batch_links
            self.admin_settings = self.db.admin_settings
            self.auto_delete_queue = self.db.auto_delete_queue
            
            # Create indexes
            await self._create_indexes()
            
            logger.info("Connected to MongoDB successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")
    
    async def _create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # User indexes
            await self.users.create_index("user_id", unique=True)
            
            # File indexes
            await self.files.create_index("file_id", unique=True)
            await self.files.create_index("message_id")
            
            # Batch link indexes
            await self.batch_links.create_index("batch_id", unique=True)
            
            # Auto delete queue indexes
            await self.auto_delete_queue.create_index("delete_at")
            await self.auto_delete_queue.create_index([("chat_id", 1), ("message_id", 1)])
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Failed to create some indexes: {e}")
    
    # User Management
    async def add_user(self, user_id: int, user_data: Dict[str, Any]) -> bool:
        """Add a new user to the database"""
        try:
            user_doc = {
                "user_id": user_id,
                "first_name": user_data.get("first_name", ""),
                "last_name": user_data.get("last_name", ""),
                "username": user_data.get("username", ""),
                "joined_date": datetime.now(),
                "last_activity": datetime.now(),
                "files_accessed": 0,
                "is_banned": False
            }
            
            await self.users.insert_one(user_doc)
            return True
            
        except DuplicateKeyError:
            # User already exists, update last activity
            await self.update_user_activity(user_id)
            return False
        except Exception as e:
            logger.error(f"Failed to add user {user_id}: {e}")
            return False
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user information"""
        try:
            return await self.users.find_one({"user_id": user_id})
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            return None
    
    async def update_user_activity(self, user_id: int):
        """Update user's last activity timestamp"""
        try:
            await self.users.update_one(
                {"user_id": user_id},
                {"$set": {"last_activity": datetime.now()}}
            )
        except Exception as e:
            logger.error(f"Failed to update user activity for {user_id}: {e}")
    
    async def increment_user_file_access(self, user_id: int):
        """Increment user's file access counter"""
        try:
            await self.users.update_one(
                {"user_id": user_id},
                {"$inc": {"files_accessed": 1}}
            )
        except Exception as e:
            logger.error(f"Failed to increment file access for {user_id}: {e}")
    
    async def get_users_count(self) -> int:
        """Get total number of users"""
        try:
            return await self.users.count_documents({})
        except Exception as e:
            logger.error(f"Failed to get users count: {e}")
            return 0
    
    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users for broadcasting"""
        try:
            cursor = self.users.find({}, {"user_id": 1})
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Failed to get all users: {e}")
            return []
    
    # File Management
    async def save_file(self, file_data: Dict[str, Any]) -> str:
        """Save file information and return file_id"""
        try:
            file_doc = {
                "file_id": file_data["file_id"],
                "message_id": file_data["message_id"],
                "file_name": file_data.get("file_name", ""),
                "file_size": file_data.get("file_size", 0),
                "file_type": file_data.get("file_type", ""),
                "mime_type": file_data.get("mime_type", ""),
                "caption": file_data.get("caption", ""),
                "uploaded_by": file_data["uploaded_by"],
                "upload_date": datetime.now(),
                "access_count": 0
            }
            
            await self.files.insert_one(file_doc)
            return file_data["file_id"]
            
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            return ""
    
    async def get_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get file information"""
        try:
            return await self.files.find_one({"file_id": file_id})
        except Exception as e:
            logger.error(f"Failed to get file {file_id}: {e}")
            return None
    
    async def increment_file_access(self, file_id: str):
        """Increment file access counter"""
        try:
            await self.files.update_one(
                {"file_id": file_id},
                {"$inc": {"access_count": 1}}
            )
        except Exception as e:
            logger.error(f"Failed to increment file access for {file_id}: {e}")
    
    async def get_files_count(self) -> int:
        """Get total number of files"""
        try:
            return await self.files.count_documents({})
        except Exception as e:
            logger.error(f"Failed to get files count: {e}")
            return 0
    
    # Batch Link Management
    async def create_batch_link(self, batch_data: Dict[str, Any]) -> str:
        """Create a new batch link"""
        try:
            batch_doc = {
                "batch_id": batch_data["batch_id"],
                "file_ids": batch_data["file_ids"],
                "title": batch_data.get("title", ""),
                "description": batch_data.get("description", ""),
                "created_by": batch_data["created_by"],
                "created_date": datetime.now(),
                "access_count": 0,
                "is_active": True
            }
            
            await self.batch_links.insert_one(batch_doc)
            return batch_data["batch_id"]
            
        except Exception as e:
            logger.error(f"Failed to create batch link: {e}")
            return ""
    
    async def get_batch_link(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get batch link information"""
        try:
            return await self.batch_links.find_one({"batch_id": batch_id, "is_active": True})
        except Exception as e:
            logger.error(f"Failed to get batch link {batch_id}: {e}")
            return None
    
    async def increment_batch_access(self, batch_id: str):
        """Increment batch link access counter"""
        try:
            await self.batch_links.update_one(
                {"batch_id": batch_id},
                {"$inc": {"access_count": 1}}
            )
        except Exception as e:
            logger.error(f"Failed to increment batch access for {batch_id}: {e}")
    
    async def get_batch_links_count(self) -> int:
        """Get total number of batch links"""
        try:
            return await self.batch_links.count_documents({"is_active": True})
        except Exception as e:
            logger.error(f"Failed to get batch links count: {e}")
            return 0
    
    # Auto Delete Queue Management
    async def add_to_delete_queue(self, chat_id: int, message_id: int, delete_at: datetime):
        """Add message to auto-delete queue"""
        try:
            delete_doc = {
                "chat_id": chat_id,
                "message_id": message_id,
                "delete_at": delete_at,
                "created_at": datetime.now()
            }
            
            await self.auto_delete_queue.insert_one(delete_doc)
            
        except Exception as e:
            logger.error(f"Failed to add message to delete queue: {e}")
    
    async def get_messages_to_delete(self) -> List[Dict[str, Any]]:
        """Get messages that should be deleted now"""
        try:
            cursor = self.auto_delete_queue.find({"delete_at": {"$lte": datetime.now()}})
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Failed to get messages to delete: {e}")
            return []
    
    async def remove_from_delete_queue(self, chat_id: int, message_id: int):
        """Remove message from delete queue"""
        try:
            await self.auto_delete_queue.delete_one({
                "chat_id": chat_id,
                "message_id": message_id
            })
        except Exception as e:
            logger.error(f"Failed to remove message from delete queue: {e}")
    
    # Admin Settings
    async def get_admin_setting(self, key: str, default=None) -> Any:
        """Get admin setting value"""
        try:
            setting = await self.admin_settings.find_one({"key": key})
            return setting["value"] if setting else default
        except Exception as e:
            logger.error(f"Failed to get admin setting {key}: {e}")
            return default
    
    async def set_admin_setting(self, key: str, value: Any):
        """Set admin setting value"""
        try:
            await self.admin_settings.update_one(
                {"key": key},
                {"$set": {"value": value, "updated_at": datetime.now()}},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Failed to set admin setting {key}: {e}")
