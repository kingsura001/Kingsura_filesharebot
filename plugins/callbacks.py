#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import MessageNotModified, QueryIdInvalid
from config import Config
from plugins.force_sub import check_force_subscription
from utils.helpers import is_user_admin, format_message

@Client.on_callback_query()
async def callback_handler(client: Client, callback_query: CallbackQuery):
    """Handle all callback queries"""
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    try:
        # Update user activity
        await client.db.update_user_activity(user_id)
        
        if data == "check_subscription":
            await handle_subscription_check(client, callback_query)
        elif data == "help":
            await handle_help_callback(client, callback_query)
        elif data == "stats":
            await handle_stats_callback(client, callback_query)
        elif data == "close":
            await handle_close_callback(client, callback_query)
        elif data == "confirm_broadcast" and is_user_admin(user_id):
            await handle_broadcast_confirm(client, callback_query)
        elif data == "cancel_broadcast" and is_user_admin(user_id):
            await handle_broadcast_cancel(client, callback_query)
        elif data.startswith("delete_"):
            await handle_delete_callback(client, callback_query)
        else:
            await callback_query.answer("❌ Unknown command!", show_alert=True)
            
    except Exception as e:
        client.logger.error(f"Error in callback handler: {e}")
        try:
            await callback_query.answer("❌ An error occurred!", show_alert=True)
        except:
            pass

async def handle_subscription_check(client: Client, callback_query: CallbackQuery):
    """Handle subscription verification callback"""
    user_id = callback_query.from_user.id
    
    if not Config.IS_FORCE_SUB_ENABLED:
        await callback_query.answer("✅ No subscription required!", show_alert=True)
        return
    
    # Check subscription status
    subscription_status = await check_force_subscription(client, user_id)
    
    if subscription_status["all_joined"]:
        # User has joined all channels
        await callback_query.answer("✅ All channels joined! You can now access files.", show_alert=True)
        
        # Update the message to show success
        success_text = "✅ **Verification Successful!**\n\nYou have joined all required channels. You can now access files by clicking on file links."
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh", callback_data="check_subscription")],
            [InlineKeyboardButton("❌ Close", callback_data="close")]
        ])
        
        try:
            await callback_query.edit_message_text(success_text, reply_markup=keyboard)
        except MessageNotModified:
            pass
    else:
        # User still needs to join some channels
        unjoined_channels = [ch for ch in subscription_status["channels"] if not ch["joined"]]
        
        await callback_query.answer(
            f"❌ Please join {len(unjoined_channels)} more channel(s) first!",
            show_alert=True
        )
        
        # Update force sub message with current status
        force_sub_text = format_message(Config.FORCE_SUB_MESSAGE, callback_query.from_user)
        force_sub_text += f"\n\n**Status:** {len(subscription_status['channels']) - len(unjoined_channels)}/{len(subscription_status['channels'])} channels joined"
        
        # Create updated keyboard
        keyboard = []
        for i, channel_info in enumerate(subscription_status["channels"], 1):
            if not channel_info["joined"]:
                button_text = f"📢 Join Channel {i}"
                if channel_info.get("username"):
                    keyboard.append([InlineKeyboardButton(button_text, url=f"https://t.me/{channel_info['username']}")])
                elif channel_info.get("invite_link"):
                    keyboard.append([InlineKeyboardButton(button_text, url=channel_info["invite_link"])])
        
        keyboard.append([InlineKeyboardButton("🔄 Try Again", callback_data="check_subscription")])
        
        try:
            await callback_query.edit_message_text(
                force_sub_text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except MessageNotModified:
            pass

async def handle_help_callback(client: Client, callback_query: CallbackQuery):
    """Handle help callback"""
    help_text = """
🤖 **Bot Help**

**For Users:**
• Send me a file link to access shared content
• Make sure you've joined all required channels
• Files may auto-delete after a certain time

**Features:**
• 🔒 Triple force subscription system
• 📁 Single and batch file sharing
• 🛡️ Content protection
• ⏰ Auto-delete functionality

**Support:** Contact our support group for assistance.
"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Stats", callback_data="stats")],
        [InlineKeyboardButton("❌ Close", callback_data="close")]
    ])
    
    try:
        await callback_query.edit_message_text(help_text, reply_markup=keyboard)
    except MessageNotModified:
        await callback_query.answer()

async def handle_stats_callback(client: Client, callback_query: CallbackQuery):
    """Handle stats callback"""
    try:
        total_users = await client.db.get_users_count()
        total_files = await client.db.get_files_count()
        total_batches = await client.db.get_batch_links_count()
        
        stats_text = f"""
📊 **Bot Statistics**

👥 **Users:** {total_users:,}
📁 **Files:** {total_files:,}
🔗 **Batches:** {total_batches:,}
⏰ **Uptime:** {client.get_uptime()}

🤖 **Features:**
• Force Sub Channels: {len(Config.FORCE_SUB_CHANNELS)}
• Auto Delete: {'Enabled' if Config.AUTO_DELETE_TIME > 0 else 'Disabled'}
• Content Protection: {'Enabled' if Config.PROTECT_CONTENT else 'Disabled'}
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("ℹ️ Help", callback_data="help")],
            [InlineKeyboardButton("❌ Close", callback_data="close")]
        ])
        
        await callback_query.edit_message_text(stats_text, reply_markup=keyboard)
        
    except Exception as e:
        await callback_query.answer(f"Error getting stats: {str(e)}", show_alert=True)

async def handle_close_callback(client: Client, callback_query: CallbackQuery):
    """Handle close callback"""
    try:
        await callback_query.message.delete()
    except Exception:
        await callback_query.answer("❌ Cannot delete this message!", show_alert=True)

async def handle_broadcast_confirm(client: Client, callback_query: CallbackQuery):
    """Handle broadcast confirmation"""
    if not callback_query.message.reply_to_message:
        await callback_query.answer("❌ Original message not found!", show_alert=True)
        return
    
    await callback_query.answer("✅ Starting broadcast...", show_alert=True)
    
    # Start broadcast process
    asyncio.create_task(
        start_broadcast(client, callback_query.message.reply_to_message, callback_query.from_user.id)
    )
    
    # Update message
    await callback_query.edit_message_text(
        "⏳ **Broadcasting Started**\n\nBroadcast is now in progress. You'll receive a summary when it's complete."
    )

async def handle_broadcast_cancel(client: Client, callback_query: CallbackQuery):
    """Handle broadcast cancellation"""
    await callback_query.edit_message_text("❌ **Broadcast Cancelled**\n\nThe broadcast has been cancelled.")

async def handle_delete_callback(client: Client, callback_query: CallbackQuery):
    """Handle auto-delete callback"""
    try:
        # Extract message info from callback data
        _, chat_id, message_id = callback_query.data.split("_")
        chat_id = int(chat_id)
        message_id = int(message_id)
        
        # Delete the message
        await client.delete_messages(chat_id, message_id)
        
        # Remove from delete queue
        await client.db.remove_from_delete_queue(chat_id, message_id)
        
        await callback_query.answer("✅ Message deleted successfully!")
        
    except Exception as e:
        client.logger.error(f"Error in delete callback: {e}")
        await callback_query.answer("❌ Failed to delete message!", show_alert=True)

async def start_broadcast(client: Client, message, admin_id: int):
    """Start the broadcast process"""
    try:
        # Get all users
        users = await client.db.get_all_users()
        
        total_users = len(users)
        successful = 0
        blocked = 0
        failed = 0
        
        # Send initial status
        status_msg = await client.send_message(
            admin_id,
            f"📡 **Broadcasting to {total_users} users...**\n\n⏳ Starting broadcast..."
        )
        
        # Broadcast to all users
        for i, user in enumerate(users):
            try:
                await client.copy_message_with_retry(
                    chat_id=user["user_id"],
                    from_chat_id=message.chat.id,
                    message_id=message.id
                )
                successful += 1
                
            except Exception as e:
                if "blocked" in str(e).lower() or "user is deactivated" in str(e).lower():
                    blocked += 1
                else:
                    failed += 1
                
                client.logger.error(f"Broadcast error for user {user['user_id']}: {e}")
            
            # Update status every 100 users
            if (i + 1) % 100 == 0:
                try:
                    await status_msg.edit_text(
                        f"📡 **Broadcasting Progress**\n\n"
                        f"✅ Successful: {successful}\n"
                        f"🚫 Blocked: {blocked}\n"
                        f"❌ Failed: {failed}\n"
                        f"📊 Progress: {i + 1}/{total_users}"
                    )
                except:
                    pass
        
        # Send final summary
        summary_text = f"""
📡 **Broadcast Complete**

📊 **Summary:**
• Total Users: {total_users}
• ✅ Successful: {successful}
• 🚫 Blocked: {blocked}
• ❌ Failed: {failed}

⏰ **Completed at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        await status_msg.edit_text(summary_text)
        
    except Exception as e:
        client.logger.error(f"Broadcast error: {e}")
        try:
            await client.send_message(admin_id, f"❌ **Broadcast Failed**\n\nError: {str(e)}")
        except:
            pass
