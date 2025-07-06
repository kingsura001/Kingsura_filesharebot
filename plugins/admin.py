#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import base64
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, UserIsBlocked
from config import Config
from utils.helpers import is_user_admin, generate_file_id, format_message

# Admin checker function
def is_admin_or_owner(user_id: int) -> bool:
    return user_id in Config.ADMINS() or user_id == Config.OWNER_ID

@Client.on_message(filters.command("genlink") & filters.private)
async def generate_link_handler(client: Client, message: Message):
    """Generate link for a single file"""
    # Check if user is admin
    if not is_admin_or_owner(message.from_user.id):
        return
    
    if message.reply_to_message is None:
        await message.reply_text("❌ Please reply to a file to generate a link.")
        return
    
    replied_msg = message.reply_to_message
    
    # Check if the replied message contains media
    if not (replied_msg.document or replied_msg.video or replied_msg.photo or replied_msg.audio or replied_msg.voice or replied_msg.video_note):
        await message.reply_text("❌ Please reply to a media file.")
        return
    
    try:
        # Forward the file to database channel
        forwarded_msg = await replied_msg.forward(Config.CHANNEL_ID)
        
        # Generate file ID
        file_id = generate_file_id()
        
        # Prepare file data
        file_data = {
            "file_id": file_id,
            "message_id": forwarded_msg.id,
            "uploaded_by": message.from_user.id
        }
        
        # Extract file information
        if replied_msg.document:
            file_data.update({
                "file_name": replied_msg.document.file_name or "Unknown",
                "file_size": replied_msg.document.file_size,
                "file_type": "document",
                "mime_type": replied_msg.document.mime_type or ""
            })
        elif replied_msg.video:
            file_data.update({
                "file_name": replied_msg.video.file_name or "Video",
                "file_size": replied_msg.video.file_size,
                "file_type": "video",
                "mime_type": replied_msg.video.mime_type or ""
            })
        elif replied_msg.photo:
            file_data.update({
                "file_name": "Photo",
                "file_size": replied_msg.photo.file_size,
                "file_type": "photo",
                "mime_type": "image/jpeg"
            })
        elif replied_msg.audio:
            file_data.update({
                "file_name": replied_msg.audio.file_name or "Audio",
                "file_size": replied_msg.audio.file_size,
                "file_type": "audio",
                "mime_type": replied_msg.audio.mime_type or ""
            })
        elif replied_msg.voice:
            file_data.update({
                "file_name": "Voice Message",
                "file_size": replied_msg.voice.file_size,
                "file_type": "voice",
                "mime_type": replied_msg.voice.mime_type or ""
            })
        elif replied_msg.video_note:
            file_data.update({
                "file_name": "Video Note",
                "file_size": replied_msg.video_note.file_size,
                "file_type": "video_note",
                "mime_type": "video/mp4"
            })
        
        # Add caption if available
        if replied_msg.caption:
            file_data["caption"] = replied_msg.caption
        
        # Save to database
        saved_file_id = await client.db.save_file(file_data)
        
        if saved_file_id:
            # Generate shareable link
            bot_info = await client.get_me()
            share_link = f"https://t.me/{bot_info.username}?start={file_id}"
            
            response_text = f"""
✅ **Link Generated Successfully!**

📁 **File:** {file_data['file_name']}
📊 **Size:** {format_file_size(file_data['file_size'])}
🔗 **Link:** `{share_link}`

👥 **Share this link with your users!**
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Share Link", url=share_link)]
            ])
            
            await message.reply_text(response_text, reply_markup=keyboard)
        else:
            await message.reply_text("❌ Failed to save file to database.")
    
    except Exception as e:
        await message.reply_text(f"❌ Error generating link: {str(e)}")

@Client.on_message(filters.command("users") & filters.private)
async def users_stats_handler(client: Client, message: Message):
    """Show user statistics"""
    # Check if user is admin
    if not is_admin_or_owner(message.from_user.id):
        return
    
    try:
        total_users = await client.db.get_users_count()
        total_files = await client.db.get_files_count()
        total_batches = await client.db.get_batch_links_count()
        
        stats_text = f"""
📊 **Bot Statistics**

👥 **Total Users:** {total_users:,}
📁 **Total Files:** {total_files:,}
🔗 **Total Batches:** {total_batches:,}
⏰ **Uptime:** {client.get_uptime()}

🤖 **Bot Information:**
• **Force Sub Channels:** {len(Config.FORCE_SUB_CHANNELS())}
• **Auto Delete:** {'Enabled' if Config.AUTO_DELETE_TIME > 0 else 'Disabled'}
• **Content Protection:** {'Enabled' if Config.PROTECT_CONTENT else 'Disabled'}
"""
        
        await message.reply_text(stats_text)
        
    except Exception as e:
        await message.reply_text(f"❌ Error getting statistics: {str(e)}")

@Client.on_message(filters.command("broadcast") & filters.private)
async def broadcast_handler(client: Client, message: Message):
    """Broadcast message to all users"""
    # Check if user is admin
    if not is_admin_or_owner(message.from_user.id):
        return
    
    if message.reply_to_message is None:
        await message.reply_text("❌ Please reply to a message to broadcast.")
        return
    
    # Confirm broadcast
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm Broadcast", callback_data="confirm_broadcast")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_broadcast")]
    ])
    
    await message.reply_text(
        "⚠️ **Broadcast Confirmation**\n\nAre you sure you want to broadcast this message to all users?",
        reply_markup=keyboard
    )

@Client.on_message(filters.command("stats") & filters.private)
async def detailed_stats_handler(client: Client, message: Message):
    """Show detailed bot statistics"""
    # Check if user is admin
    if not is_admin_or_owner(message.from_user.id):
        return
    
    try:
        # Get comprehensive stats
        total_users = await client.db.get_users_count()
        total_files = await client.db.get_files_count()
        total_batches = await client.db.get_batch_links_count()
        
        # Format stats using custom template if available
        if Config.BOT_STATS_TEXT:
            stats_text = Config.BOT_STATS_TEXT.format(
                users=total_users,
                files=total_files,
                batch_links=total_batches,
                uptime=client.get_uptime()
            )
        else:
            stats_text = f"""
📈 **Detailed Bot Statistics**

👥 **Users:** {total_users:,}
📁 **Files:** {total_files:,}
🔗 **Batch Links:** {total_batches:,}
⏰ **Uptime:** {client.get_uptime()}

⚙️ **Configuration:**
• **API ID:** {Config.API_ID}
• **Force Sub Channels:** {len(Config.FORCE_SUB_CHANNELS())}
• **Auto Delete Time:** {Config.AUTO_DELETE_TIME}s
• **Protect Content:** {Config.PROTECT_CONTENT}
• **Database:** {Config.DATABASE_NAME}

🔧 **System Info:**
• **Started:** {client.start_time.strftime('%Y-%m-%d %H:%M:%S')}
• **Admin Count:** {len(Config.ADMINS())}
"""
        
        await message.reply_text(stats_text)
        
    except Exception as e:
        await message.reply_text(f"❌ Error getting detailed statistics: {str(e)}")

@Client.on_message(filters.command("settings") & filters.user(Config.OWNER_ID) & filters.private)
async def settings_handler(client: Client, message: Message):
    """Show bot settings (owner only)"""
    settings_text = f"""
⚙️ **Bot Settings**

🔑 **API Configuration:**
• API ID: {Config.API_ID}
• Channel ID: {Config.CHANNEL_ID}

📢 **Force Subscription:**
• Channel 1: {Config.FORCE_SUB_CHANNEL_1}
• Channel 2: {Config.FORCE_SUB_CHANNEL_2}
• Channel 3: {Config.FORCE_SUB_CHANNEL_3}

🛡️ **Security:**
• Protect Content: {Config.PROTECT_CONTENT}
• Auto Delete: {Config.AUTO_DELETE_TIME}s

👑 **Administration:**
• Owner ID: {Config.OWNER_ID}
• Admins: {len(Config.ADMINS())}

🗄️ **Database:**
• URL: {Config.DATABASE_URL[:50]}...
• Name: {Config.DATABASE_NAME}
"""
    
    await message.reply_text(settings_text)

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

@Client.on_message(filters.command("ban") & filters.private)
async def ban_user_handler(client: Client, message: Message):
    """Ban a user (admin only)"""
    # Check if user is admin
    if not is_admin_or_owner(message.from_user.id):
        return
    
    if len(message.command) < 2:
        await message.reply_text("❌ Usage: `/ban <user_id>`")
        return
    
    try:
        user_id = int(message.command[1])
        
        # Update user ban status in database
        await client.db.users.update_one(
            {"user_id": user_id},
            {"$set": {"is_banned": True, "banned_date": datetime.now()}}
        )
        
        await message.reply_text(f"✅ User {user_id} has been banned.")
        
    except ValueError:
        await message.reply_text("❌ Invalid user ID.")
    except Exception as e:
        await message.reply_text(f"❌ Error banning user: {str(e)}")

@Client.on_message(filters.command("unban") & filters.private)
async def unban_user_handler(client: Client, message: Message):
    """Unban a user (admin only)"""
    # Check if user is admin
    if not is_admin_or_owner(message.from_user.id):
        return
    
    if len(message.command) < 2:
        await message.reply_text("❌ Usage: `/unban <user_id>`")
        return
    
    try:
        user_id = int(message.command[1])
        
        # Update user ban status in database
        await client.db.users.update_one(
            {"user_id": user_id},
            {"$set": {"is_banned": False}, "$unset": {"banned_date": ""}}
        )
        
        await message.reply_text(f"✅ User {user_id} has been unbanned.")
        
    except ValueError:
        await message.reply_text("❌ Invalid user ID.")
    except Exception as e:
        await message.reply_text(f"❌ Error unbanning user: {str(e)}")
