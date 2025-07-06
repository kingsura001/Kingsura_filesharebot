#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from utils.helpers import is_user_admin, generate_batch_id

# Admin filter
admin_filter = filters.user(Config.ADMINS() + [Config.OWNER_ID])

@Client.on_message(filters.command("batch") & admin_filter & filters.private)
async def batch_handler(client: Client, message: Message):
    """Handle batch link creation"""
    
    if len(message.command) < 2:
        await message.reply_text("""
❌ **Invalid Usage**

**Usage:** `/batch <start_message_id> <end_message_id>`
**Example:** `/batch 100 150`

**Note:** Make sure the message IDs are from the database channel.
""")
        return
    
    try:
        start_id = int(message.command[1])
        end_id = int(message.command[2]) if len(message.command) > 2 else start_id
        
        if start_id > end_id:
            start_id, end_id = end_id, start_id
        
        # Validate message range
        if end_id - start_id > 100:
            await message.reply_text("❌ Maximum 100 files allowed in a single batch.")
            return
        
        # Create batch
        await create_batch_link(client, message, start_id, end_id)
        
    except ValueError:
        await message.reply_text("❌ Invalid message IDs. Please provide valid numbers.")
    except Exception as e:
        await message.reply_text(f"❌ Error creating batch: {str(e)}")

@Client.on_message(filters.command("batch_files") & admin_filter & filters.private)
async def batch_files_handler(client: Client, message: Message):
    """Create batch from multiple individual files"""
    
    # Start interactive batch creation
    await message.reply_text("""
📁 **Interactive Batch Creation**

Please forward the files you want to include in the batch to this chat.
Send /done when you're finished adding files.
Send /cancel to cancel the batch creation.

**Note:** You can add up to 50 files in a batch.
""")
    
    # Store batch creation session
    user_id = message.from_user.id
    batch_session = {
        "user_id": user_id,
        "files": [],
        "start_time": datetime.now()
    }
    
    # Store session in client (you might want to use a proper session manager)
    if not hasattr(client, 'batch_sessions'):
        client.batch_sessions = {}
    
    client.batch_sessions[user_id] = batch_session

@Client.on_message(filters.command("done") & admin_filter & filters.private)
async def batch_done_handler(client: Client, message: Message):
    """Complete interactive batch creation"""
    
    user_id = message.from_user.id
    
    if not hasattr(client, 'batch_sessions') or user_id not in client.batch_sessions:
        await message.reply_text("❌ No active batch session found.")
        return
    
    session = client.batch_sessions[user_id]
    
    if not session['files']:
        await message.reply_text("❌ No files added to the batch.")
        return
    
    try:
        # Create batch from collected files
        await create_batch_from_files(client, message, session['files'])
        
        # Clean up session
        del client.batch_sessions[user_id]
        
    except Exception as e:
        await message.reply_text(f"❌ Error creating batch: {str(e)}")

@Client.on_message(filters.command("cancel") & admin_filter & filters.private)
async def batch_cancel_handler(client: Client, message: Message):
    """Cancel interactive batch creation"""
    
    user_id = message.from_user.id
    
    if hasattr(client, 'batch_sessions') and user_id in client.batch_sessions:
        del client.batch_sessions[user_id]
        await message.reply_text("✅ Batch creation cancelled.")
    else:
        await message.reply_text("❌ No active batch session found.")

@Client.on_message(filters.private & admin_filter & filters.media)
async def collect_batch_files(client: Client, message: Message):
    """Collect files for interactive batch creation"""
    
    user_id = message.from_user.id
    
    # Check if user has an active batch session
    if not hasattr(client, 'batch_sessions') or user_id not in client.batch_sessions:
        return
    
    session = client.batch_sessions[user_id]
    
    # Check file limit
    if len(session['files']) >= 50:
        await message.reply_text("❌ Maximum 50 files allowed in a batch.")
        return
    
    try:
        # Forward file to database channel
        forwarded_msg = await message.forward(Config.CHANNEL_ID)
        
        # Add file info to session
        file_info = {
            "message_id": forwarded_msg.id,
            "file_name": get_file_name(message),
            "file_size": get_file_size(message),
            "file_type": get_file_type(message)
        }
        
        session['files'].append(file_info)
        
        await message.reply_text(f"✅ File added to batch ({len(session['files'])}/50)\n\nSend /done to complete or continue adding files.")
        
    except Exception as e:
        await message.reply_text(f"❌ Error adding file to batch: {str(e)}")

async def create_batch_link(client: Client, message: Message, start_id: int, end_id: int):
    """Create batch link from message ID range"""
    
    status_msg = await message.reply_text("⏳ Creating batch link...")
    
    try:
        file_ids = []
        processed = 0
        skipped = 0
        
        for msg_id in range(start_id, end_id + 1):
            try:
                # Get message from database channel
                channel_msg = await client.get_messages(Config.CHANNEL_ID, msg_id)
                
                if channel_msg and (channel_msg.document or channel_msg.video or 
                                  channel_msg.photo or channel_msg.audio or 
                                  channel_msg.voice or channel_msg.video_note):
                    
                    # Generate file ID and save to database
                    from utils.helpers import generate_file_id
                    file_id = generate_file_id()
                    
                    file_data = {
                        "file_id": file_id,
                        "message_id": msg_id,
                        "uploaded_by": message.from_user.id
                    }
                    
                    # Extract file information
                    file_data.update(extract_file_info(channel_msg))
                    
                    # Save to database
                    saved_file_id = await client.db.save_file(file_data)
                    if saved_file_id:
                        file_ids.append(file_id)
                        processed += 1
                    else:
                        skipped += 1
                else:
                    skipped += 1
                    
            except Exception as e:
                client.logger.error(f"Error processing message {msg_id}: {e}")
                skipped += 1
        
        if not file_ids:
            await status_msg.edit_text("❌ No valid files found in the specified range.")
            return
        
        # Create batch link
        batch_id = generate_batch_id()
        batch_data = {
            "batch_id": batch_id,
            "file_ids": file_ids,
            "title": f"Batch {start_id}-{end_id}",
            "description": f"Files from message {start_id} to {end_id}",
            "created_by": message.from_user.id
        }
        
        saved_batch_id = await client.db.create_batch_link(batch_data)
        
        if saved_batch_id:
            # Generate shareable link
            bot_info = await client.get_me()
            share_link = f"https://t.me/{bot_info.username}?start=batch_{batch_id}"
            
            response_text = f"""
✅ **Batch Created Successfully!**

📁 **Files:** {processed}
⚠️ **Skipped:** {skipped}
🔗 **Link:** `{share_link}`

👥 **Share this link with your users!**
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Share Batch", url=share_link)]
            ])
            
            await status_msg.edit_text(response_text, reply_markup=keyboard)
        else:
            await status_msg.edit_text("❌ Failed to create batch link.")
    
    except Exception as e:
        await status_msg.edit_text(f"❌ Error creating batch: {str(e)}")

async def create_batch_from_files(client: Client, message: Message, files: list):
    """Create batch link from collected files"""
    
    status_msg = await message.reply_text("⏳ Creating batch from collected files...")
    
    try:
        file_ids = []
        
        for file_info in files:
            # Generate file ID
            from utils.helpers import generate_file_id
            file_id = generate_file_id()
            
            file_data = {
                "file_id": file_id,
                "message_id": file_info["message_id"],
                "file_name": file_info["file_name"],
                "file_size": file_info["file_size"],
                "file_type": file_info["file_type"],
                "uploaded_by": message.from_user.id
            }
            
            # Save to database
            saved_file_id = await client.db.save_file(file_data)
            if saved_file_id:
                file_ids.append(file_id)
        
        if not file_ids:
            await status_msg.edit_text("❌ Failed to save files to database.")
            return
        
        # Create batch link
        batch_id = generate_batch_id()
        batch_data = {
            "batch_id": batch_id,
            "file_ids": file_ids,
            "title": f"Custom Batch ({len(file_ids)} files)",
            "description": f"Batch created with {len(file_ids)} files",
            "created_by": message.from_user.id
        }
        
        saved_batch_id = await client.db.create_batch_link(batch_data)
        
        if saved_batch_id:
            # Generate shareable link
            bot_info = await client.get_me()
            share_link = f"https://t.me/{bot_info.username}?start=batch_{batch_id}"
            
            response_text = f"""
✅ **Custom Batch Created!**

📁 **Files:** {len(file_ids)}
🔗 **Link:** `{share_link}`

👥 **Share this link with your users!**
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Share Batch", url=share_link)]
            ])
            
            await status_msg.edit_text(response_text, reply_markup=keyboard)
        else:
            await status_msg.edit_text("❌ Failed to create batch link.")
    
    except Exception as e:
        await status_msg.edit_text(f"❌ Error creating batch: {str(e)}")

def extract_file_info(message: Message) -> dict:
    """Extract file information from message"""
    file_info = {}
    
    if message.document:
        file_info.update({
            "file_name": message.document.file_name or "Unknown",
            "file_size": message.document.file_size,
            "file_type": "document",
            "mime_type": message.document.mime_type or ""
        })
    elif message.video:
        file_info.update({
            "file_name": message.video.file_name or "Video",
            "file_size": message.video.file_size,
            "file_type": "video",
            "mime_type": message.video.mime_type or ""
        })
    elif message.photo:
        file_info.update({
            "file_name": "Photo",
            "file_size": message.photo.file_size,
            "file_type": "photo",
            "mime_type": "image/jpeg"
        })
    elif message.audio:
        file_info.update({
            "file_name": message.audio.file_name or "Audio",
            "file_size": message.audio.file_size,
            "file_type": "audio",
            "mime_type": message.audio.mime_type or ""
        })
    elif message.voice:
        file_info.update({
            "file_name": "Voice Message",
            "file_size": message.voice.file_size,
            "file_type": "voice",
            "mime_type": message.voice.mime_type or ""
        })
    elif message.video_note:
        file_info.update({
            "file_name": "Video Note",
            "file_size": message.video_note.file_size,
            "file_type": "video_note",
            "mime_type": "video/mp4"
        })
    
    if message.caption:
        file_info["caption"] = message.caption
    
    return file_info

def get_file_name(message: Message) -> str:
    """Get file name from message"""
    if message.document:
        return message.document.file_name or "Unknown"
    elif message.video:
        return message.video.file_name or "Video"
    elif message.photo:
        return "Photo"
    elif message.audio:
        return message.audio.file_name or "Audio"
    elif message.voice:
        return "Voice Message"
    elif message.video_note:
        return "Video Note"
    return "Unknown"

def get_file_size(message: Message) -> int:
    """Get file size from message"""
    if message.document:
        return message.document.file_size
    elif message.video:
        return message.video.file_size
    elif message.photo:
        return message.photo.file_size
    elif message.audio:
        return message.audio.file_size
    elif message.voice:
        return message.voice.file_size
    elif message.video_note:
        return message.video_note.file_size
    return 0

def get_file_type(message: Message) -> str:
    """Get file type from message"""
    if message.document:
        return "document"
    elif message.video:
        return "video"
    elif message.photo:
        return "photo"
    elif message.audio:
        return "audio"
    elif message.voice:
        return "voice"
    elif message.video_note:
        return "video_note"
    return "unknown"
