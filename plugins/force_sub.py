#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Dict, List, Any
from pyrogram import Client
from pyrogram.errors import UserNotParticipant, ChatAdminRequired, ChannelPrivate
from config import Config
import logging

logger = logging.getLogger(__name__)

async def check_force_subscription(client: Client, user_id: int) -> Dict[str, Any]:
    """
    Check if user has joined all required force subscription channels
    Returns dict with subscription status and channel information
    """
    if not Config.IS_FORCE_SUB_ENABLED():
        return {"all_joined": True, "channels": []}
    
    subscription_status = {
        "all_joined": True,
        "channels": []
    }
    
    for channel_id in Config.FORCE_SUB_CHANNELS():
        channel_info = await check_channel_subscription(client, user_id, channel_id)
        subscription_status["channels"].append(channel_info)
        
        if not channel_info["joined"]:
            subscription_status["all_joined"] = False
    
    return subscription_status

async def check_channel_subscription(client: Client, user_id: int, channel_id: int) -> Dict[str, Any]:
    """
    Check if user has joined a specific channel
    Returns dict with join status and channel information
    """
    channel_info = {
        "channel_id": channel_id,
        "joined": False,
        "username": None,
        "title": "Unknown Channel",
        "invite_link": None,
        "error": None
    }
    
    try:
        # Get channel information
        chat = await client.get_chat(channel_id)
        channel_info["title"] = chat.title
        channel_info["username"] = chat.username
        
        # Get invite link if channel has no username
        if not chat.username:
            try:
                invite_link = await client.export_chat_invite_link(channel_id)
                channel_info["invite_link"] = invite_link
            except Exception as e:
                logger.warning(f"Could not get invite link for channel {channel_id}: {e}")
                channel_info["invite_link"] = f"https://t.me/c/{str(channel_id)[4:]}"
        
        # Check if user is a member
        try:
            member = await client.get_chat_member(channel_id, user_id)
            if member.status not in ["left", "kicked"]:
                channel_info["joined"] = True
        except UserNotParticipant:
            channel_info["joined"] = False
        except Exception as e:
            logger.error(f"Error checking membership for user {user_id} in channel {channel_id}: {e}")
            channel_info["error"] = str(e)
            channel_info["joined"] = False
    
    except ChannelPrivate:
        logger.error(f"Channel {channel_id} is private or bot is not admin")
        channel_info["error"] = "Channel is private or bot lacks admin privileges"
    except ChatAdminRequired:
        logger.error(f"Bot needs admin privileges in channel {channel_id}")
        channel_info["error"] = "Bot needs admin privileges in this channel"
    except Exception as e:
        logger.error(f"Error accessing channel {channel_id}: {e}")
        channel_info["error"] = str(e)
    
    return channel_info

async def get_force_sub_message_text(user) -> str:
    """Get formatted force subscription message"""
    return Config.FORCE_SUB_MESSAGE.format(
        first=user.first_name or "",
        last=user.last_name or "",
        id=user.id,
        mention=user.mention,
        username=user.username or ""
    )

async def verify_all_channels(client: Client) -> Dict[str, List[Dict[str, Any]]]:
    """
    Verify all force subscription channels are accessible
    Returns dict with accessible and inaccessible channels
    """
    verification_result = {
        "accessible": [],
        "inaccessible": []
    }
    
    for channel_id in Config.FORCE_SUB_CHANNELS():
        channel_status = await verify_channel_access(client, channel_id)
        
        if channel_status["accessible"]:
            verification_result["accessible"].append(channel_status)
        else:
            verification_result["inaccessible"].append(channel_status)
    
    return verification_result

async def verify_channel_access(client: Client, channel_id: int) -> Dict[str, Any]:
    """
    Verify if bot can access and manage a specific channel
    Returns dict with channel status and information
    """
    channel_status = {
        "channel_id": channel_id,
        "accessible": False,
        "title": "Unknown Channel",
        "username": None,
        "member_count": 0,
        "bot_is_admin": False,
        "can_invite_users": False,
        "error": None
    }
    
    try:
        # Get channel information
        chat = await client.get_chat(channel_id)
        channel_status["title"] = chat.title
        channel_status["username"] = chat.username
        channel_status["member_count"] = chat.members_count or 0
        channel_status["accessible"] = True
        
        # Check bot's admin status
        try:
            bot_member = await client.get_chat_member(channel_id, "me")
            if bot_member.status == "administrator":
                channel_status["bot_is_admin"] = True
                # Check specific permissions
                if hasattr(bot_member, 'privileges') and bot_member.privileges:
                    channel_status["can_invite_users"] = bot_member.privileges.can_invite_users
            elif bot_member.status == "creator":
                channel_status["bot_is_admin"] = True
                channel_status["can_invite_users"] = True
        except Exception as e:
            logger.warning(f"Could not check bot admin status in channel {channel_id}: {e}")
    
    except ChannelPrivate:
        channel_status["error"] = "Channel is private or bot is not a member"
    except ChatAdminRequired:
        channel_status["error"] = "Bot needs admin privileges"
    except Exception as e:
        channel_status["error"] = str(e)
        logger.error(f"Error verifying channel {channel_id}: {e}")
    
    return channel_status

def get_channel_join_button_text(channel_number: int) -> str:
    """Get join button text for a specific channel"""
    return f"📢 Join Channel {channel_number}"

def get_channel_url(channel_info: Dict[str, Any]) -> str:
    """Get URL for joining a channel"""
    if channel_info.get("username"):
        return f"https://t.me/{channel_info['username']}"
    elif channel_info.get("invite_link"):
        return channel_info["invite_link"]
    else:
        # Fallback to channel ID based URL
        channel_id = str(channel_info["channel_id"])
        if channel_id.startswith("-100"):
            return f"https://t.me/c/{channel_id[4:]}"
        else:
            return f"https://t.me/c/{channel_id}"

async def handle_join_request(client: Client, user_id: int, channel_id: int) -> bool:
    """
    Handle join request if JOIN_REQUEST_ENABLED is True
    Returns True if join request was sent successfully
    """
    if not Config.JOIN_REQUEST_ENABLED:
        return False
    
    try:
        # This would require the user to send a join request
        # Implementation depends on how you want to handle join requests
        # For now, we'll just return False as join requests are automatically handled by Telegram
        return False
    except Exception as e:
        logger.error(f"Error handling join request for user {user_id} in channel {channel_id}: {e}")
        return False

class ForceSubscriptionManager:
    """Manager class for force subscription functionality"""
    
    def __init__(self, client: Client):
        self.client = client
        self.cache = {}  # Simple cache for subscription status
        self.cache_timeout = 300  # 5 minutes
    
    async def check_user_subscriptions(self, user_id: int, use_cache: bool = True) -> Dict[str, Any]:
        """
        Check user subscriptions with optional caching
        """
        cache_key = f"sub_status_{user_id}"
        
        if use_cache and cache_key in self.cache:
            cached_data = self.cache[cache_key]
            # Check if cache is still valid (5 minutes)
            if (datetime.now() - cached_data["timestamp"]).seconds < self.cache_timeout:
                return cached_data["data"]
        
        # Get fresh subscription status
        subscription_status = await check_force_subscription(self.client, user_id)
        
        # Cache the result
        if use_cache:
            self.cache[cache_key] = {
                "data": subscription_status,
                "timestamp": datetime.now()
            }
        
        return subscription_status
    
    def clear_user_cache(self, user_id: int):
        """Clear cached subscription status for a user"""
        cache_key = f"sub_status_{user_id}"
        if cache_key in self.cache:
            del self.cache[cache_key]
    
    def clear_all_cache(self):
        """Clear all cached subscription data"""
        self.cache.clear()
