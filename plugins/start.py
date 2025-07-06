#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from utils.helpers import get_file_id, format_message, is_user_admin
from plugins.force_sub import check_force_subscription

@Client.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    """Handle /start command"""
    user_id = message.from_user.id
    
    # Add user to database
    user_data = {
        "first_name": message.from_user.first_name or "",
        "last_name": message.from_user.last_name or "",
        "username": message.from_user.username or ""
    }
    await client.db.add_user(user_id, user_data)
    
    # Check if there's a file/batch parameter
    if len(message.command) > 1:
        parameter = message.command[1]
        
        # Handle batch links
        if parameter.startswith("batch_"):
            await handle_batch_request(client, message, parameter)
            return
        
        # Handle single file links
        file_id = get_file_id(parameter)
        if file_id:
            await handle_file_request(client, message, file_id)
            return
    
    # Send welcome message
    welcome_text = format_message(Config.START_MESSAGE, message.from_user)
    
    # Create welcome keyboard
    keyboard = []
    if not Config.DISABLE_CHANNEL_BUTTON and Config.CHANNEL_ID:
        try:
            chat = await client.get_chat(Config.CHANNEL_ID)
            keyboard.append([InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{chat.username}")])
        except:
            pass
    
    keyboard.append([InlineKeyboardButton("ℹ️ Help", callback_data="help")])
    keyboard.append([InlineKeyboardButton("📊 Stats", callback_data="stats")])
    
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    
    await message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )

async def handle_file_request(client: Client, message: Message, file_id: str):
    """Handle single file access request"""
    user_id = message.from_user.id
    
    # Check force subscription first
    if Config.IS_FORCE_SUB_ENABLED:
        subscription_status = await check_force_subscription(client, user_id)
        if not subscription_status["all_joined"]:
            await send_force_sub_message(client, message, subscription_status)
            return
    
    # Get file from database
    file_data = await client.db.get_file(file_id)
    if not file_data:
        await message.reply_text("❌ **File Not Found**\n\nThe requested file was not found or has been removed.")
        return
    
    try:
        # Send the file
        sent_message = await client.copy_message_with_retry(
            chat_id=message.chat.id,
            from_chat_id=Config.CHANNEL_ID,
            message_id=file_data["message_id"],
            caption=format_file_caption(file_data),
            protect_content=Config.PROTECT_CONTENT
        )
        
        # Increment counters
        await client.db.increment_file_access(file_id)
        await client.db.increment_user_file_access(user_id)
        
        # Add to auto-delete queue if enabled
        if Config.AUTO_DELETE_TIME > 0:
            await client.auto_delete.schedule_delete(
                sent_message.chat.id,
                sent_message.id,
                Config.AUTO_DELETE_TIME
            )
            
            # Send auto-delete notification
            delete_msg = Config.AUTO_DELETE_MSG.format(time=Config.AUTO_DELETE_TIME)
            await message.reply_text(delete_msg)
        
    except Exception as e:
        await message.reply_text(f"❌ **Error**\n\nFailed to send file: {str(e)}")

async def handle_batch_request(client: Client, message: Message, batch_id: str):
    """Handle batch file access request"""
    user_id = message.from_user.id
    
    # Check force subscription first
    if Config.IS_FORCE_SUB_ENABLED:
        subscription_status = await check_force_subscription(client, user_id)
        if not subscription_status["all_joined"]:
            await send_force_sub_message(client, message, subscription_status)
            return
    
    # Get batch data from database
    batch_data = await client.db.get_batch_link(batch_id)
    if not batch_data:
        await message.reply_text("❌ **Batch Not Found**\n\nThe requested batch was not found or has been removed.")
        return
    
    try:
        # Send batch info
        batch_info = f"📁 **{batch_data.get('title', 'File Collection')}**\n\n"
        if batch_data.get('description'):
            batch_info += f"{batch_data['description']}\n\n"
        batch_info += f"📊 Files: {len(batch_data['file_ids'])}\n"
        batch_info += f"👁‍🗨 Views: {batch_data.get('access_count', 0)}"
        
        await message.reply_text(batch_info)
        
        # Send all files in the batch
        sent_count = 0
        for file_id in batch_data['file_ids']:
            file_data = await client.db.get_file(file_id)
            if file_data:
                try:
                    sent_message = await client.copy_message_with_retry(
                        chat_id=message.chat.id,
                        from_chat_id=Config.CHANNEL_ID,
                        message_id=file_data["message_id"],
                        caption=format_file_caption(file_data),
                        protect_content=Config.PROTECT_CONTENT
                    )
                    
                    sent_count += 1
                    
                    # Add to auto-delete queue if enabled
                    if Config.AUTO_DELETE_TIME > 0:
                        await client.auto_delete.schedule_delete(
                            sent_message.chat.id,
                            sent_message.id,
                            Config.AUTO_DELETE_TIME
                        )
                
                except Exception as e:
                    client.logger.error(f"Failed to send file {file_id}: {e}")
                    continue
        
        # Increment batch access counter
        await client.db.increment_batch_access(batch_id)
        await client.db.increment_user_file_access(user_id)
        
        # Send completion message
        completion_msg = f"✅ **Batch Complete**\n\nSent {sent_count} out of {len(batch_data['file_ids'])} files."
        if Config.AUTO_DELETE_TIME > 0:
            completion_msg += f"\n\n⏰ Files will be auto-deleted in {Config.AUTO_DELETE_TIME} seconds."
        
        await message.reply_text(completion_msg)
        
    except Exception as e:
        await message.reply_text(f"❌ **Error**\n\nFailed to send batch: {str(e)}")

async def send_force_sub_message(client: Client, message: Message, subscription_status: dict):
    """Send force subscription message with join buttons"""
    force_sub_text = format_message(Config.FORCE_SUB_MESSAGE, message.from_user)
    
    # Create join buttons for unjoined channels
    keyboard = []
    for i, channel_info in enumerate(subscription_status["channels"], 1):
        if not channel_info["joined"]:
            button_text = f"📢 Join Channel {i}"
            if channel_info["username"]:
                keyboard.append([InlineKeyboardButton(button_text, url=f"https://t.me/{channel_info['username']}")])
            else:
                keyboard.append([InlineKeyboardButton(button_text, url=channel_info["invite_link"])])
    
    keyboard.append([InlineKeyboardButton("🔄 Try Again", callback_data="check_subscription")])
    
    await message.reply_text(
        force_sub_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )

def format_file_caption(file_data: dict) -> str:
    """Format file caption with custom template"""
    if not Config.CUSTOM_CAPTION:
        return file_data.get("caption", "")
    
    caption = Config.CUSTOM_CAPTION
    caption = caption.replace("{filename}", file_data.get("file_name", "Unknown"))
    caption = caption.replace("{previouscaption}", file_data.get("caption", ""))
    
    return caption

@Client.on_message(filters.private & ~filters.command(["start", "batch", "genlink", "users", "broadcast", "stats"]))
async def handle_private_message(client: Client, message: Message):
    """Handle other private messages"""
    user_id = message.from_user.id
    
    # Check if user is admin
    if is_user_admin(user_id):
        return  # Let admin commands handle this
    
    # Send user reply message
    if Config.USER_REPLY_TEXT:
        await message.reply_text(Config.USER_REPLY_TEXT)
    
    # Update user activity
    await client.db.update_user_activity(user_id)
