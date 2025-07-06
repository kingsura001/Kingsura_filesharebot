#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from typing import List, Optional

class Config:
    # Bot Configuration
    API_ID: int = int(os.getenv("API_ID", "0"))
    API_HASH: str = os.getenv("API_HASH", "")
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    # Owner and Admin Configuration
    OWNER_ID: int = int(os.getenv("OWNER_ID", "0"))
    ADMINS: List[int] = [int(admin) for admin in os.getenv("ADMINS", "").split() if admin.isdigit()]
    
    # Channel Configuration
    CHANNEL_ID: int = int(os.getenv("CHANNEL_ID", "0"))  # Database channel
    
    # Triple Force Subscription Channels
    FORCE_SUB_CHANNEL_1: int = int(os.getenv("FORCE_SUB_CHANNEL_1", "0"))
    FORCE_SUB_CHANNEL_2: int = int(os.getenv("FORCE_SUB_CHANNEL_2", "0"))
    FORCE_SUB_CHANNEL_3: int = int(os.getenv("FORCE_SUB_CHANNEL_3", "0"))
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "file_sharing_bot")
    
    # Bot Settings
    PROTECT_CONTENT: bool = os.getenv("PROTECT_CONTENT", "True").lower() == "true"
    AUTO_DELETE_TIME: int = int(os.getenv("AUTO_DELETE_TIME", "0"))  # 0 = disabled
    
    # Messages Configuration
    START_MESSAGE: str = os.getenv("START_MESSAGE", """
👋 Hello {mention}!
Bot powered by: @Anime_nexuus
""")
    
    FORCE_SUB_MESSAGE: str = os.getenv("FORCE_SUB_MESSAGE", """
🔒 **Access Restricted**

Hi {mention}! To access this file, you must join all 3 of our channels:

Please join the channels below and then click "Try Again" button.
""")
    
    CUSTOM_CAPTION: str = os.getenv("CUSTOM_CAPTION", """
📁 **{filename}**

{previouscaption}

🤖 Shared via @YourBot
""")
    
    # Auto Delete Messages
    AUTO_DELETE_MSG: str = os.getenv("AUTO_DELETE_MSG", """
⏰ **Auto Delete Enabled**

This file will be automatically deleted in {time} seconds.
""")
    
    AUTO_DEL_SUCCESS_MSG: str = os.getenv("AUTO_DEL_SUCCESS_MSG", """
🗑️ **File Deleted**

The file has been automatically deleted due to time expiry.
""")
    
    # Bot Stats Text
    BOT_STATS_TEXT: str = os.getenv("BOT_STATS_TEXT", """
📊 **Bot Statistics**

👥 Total Users: {users}
📁 Total Files: {files}
🔗 Total Batch Links: {batch_links}
⏰ Uptime: {uptime}
""")
    
    USER_REPLY_TEXT: str = os.getenv("USER_REPLY_TEXT", """
❌ **Invalid Request**

Please send me a valid file link to access the content.

For support, contact: @YourSupportGroup
""")
    
    # Feature Flags
    DISABLE_CHANNEL_BUTTON: bool = os.getenv("DISABLE_CHANNEL_BUTTON", "False").lower() == "true"
    JOIN_REQUEST_ENABLED: bool = os.getenv("JOIN_REQUEST_ENABLED", "False").lower() == "true"
    
    @property
    def FORCE_SUB_CHANNELS(self) -> List[int]:
        """Get list of force subscription channels"""
        channels = []
        if self.FORCE_SUB_CHANNEL_1:
            channels.append(self.FORCE_SUB_CHANNEL_1)
        if self.FORCE_SUB_CHANNEL_2:
            channels.append(self.FORCE_SUB_CHANNEL_2)
        if self.FORCE_SUB_CHANNEL_3:
            channels.append(self.FORCE_SUB_CHANNEL_3)
        return channels
    
    @property
    def IS_FORCE_SUB_ENABLED(self) -> bool:
        """Check if force subscription is enabled"""
        return len(self.FORCE_SUB_CHANNELS) > 0
