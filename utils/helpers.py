#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
import secrets
import string
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from pyrogram.types import User
from config import Config

def is_user_admin(user_id: int) -> bool:
    """Check if user is an admin or owner"""
    return user_id in Config.ADMINS() or user_id == Config.OWNER_ID

def generate_file_id() -> str:
    """Generate a unique file ID"""
    # Generate a random string and encode it
    random_str = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))
    timestamp = str(int(datetime.now().timestamp()))
    return base64.b64encode(f"{timestamp}_{random_str}".encode()).decode()

def generate_batch_id() -> str:
    """Generate a unique batch ID"""
    random_str = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
    timestamp = str(int(datetime.now().timestamp()))
    return f"batch_{base64.b64encode(f'{timestamp}_{random_str}'.encode()).decode()}"

def get_file_id(encoded_id: str) -> Optional[str]:
    """Decode and validate file ID"""
    try:
        if encoded_id.startswith("batch_"):
            return None  # This is a batch ID, not a file ID
        
        decoded = base64.b64decode(encoded_id.encode()).decode()
        # Validate format: timestamp_randomstring
        parts = decoded.split('_')
        if len(parts) >= 2:
            return encoded_id
        return None
    except Exception:
        return None

def get_batch_id(encoded_id: str) -> Optional[str]:
    """Extract and validate batch ID"""
    try:
        if not encoded_id.startswith("batch_"):
            return None
        
        batch_part = encoded_id[6:]  # Remove "batch_" prefix
        decoded = base64.b64decode(batch_part.encode()).decode()
        # Validate format
        parts = decoded.split('_')
        if len(parts) >= 2:
            return encoded_id
        return None
    except Exception:
        return None

def format_message(template: str, user: User) -> str:
    """Format message template with user information"""
    if not template:
        return ""
    
    formatted = template.format(
        first=user.first_name or "",
        last=user.last_name or "",
        id=user.id,
        mention=user.mention,
        username=user.username or ""
    )
    
    return formatted

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

def format_duration(seconds: int) -> str:
    """Format duration in human readable format"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        remaining_seconds = seconds % 60
        return f"{hours}h {remaining_minutes}m {remaining_seconds}s"

def get_current_time() -> datetime:
    """Get current datetime"""
    return datetime.now()

def add_time_delta(base_time: datetime, seconds: int) -> datetime:
    """Add seconds to a datetime object"""
    return base_time + timedelta(seconds=seconds)

def is_time_passed(target_time: datetime) -> bool:
    """Check if target time has passed"""
    return datetime.now() >= target_time

def validate_channel_id(channel_id: str) -> bool:
    """Validate channel ID format"""
    try:
        channel_int = int(channel_id)
        # Channel IDs are typically negative and start with -100
        return channel_int < 0
    except ValueError:
        return False

def extract_channel_username(channel_link: str) -> Optional[str]:
    """Extract username from channel link"""
    try:
        if "t.me/" in channel_link:
            return channel_link.split("t.me/")[-1].strip()
        return None
    except Exception:
        return None

def generate_random_string(length: int = 10) -> str:
    """Generate a random string of specified length"""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))

def create_deep_link(bot_username: str, parameter: str) -> str:
    """Create a deep link for the bot"""
    return f"https://t.me/{bot_username}?start={parameter}"

def parse_time_string(time_str: str) -> int:
    """Parse time string to seconds (e.g., '1h', '30m', '5d')"""
    try:
        if time_str.endswith('s'):
            return int(time_str[:-1])
        elif time_str.endswith('m'):
            return int(time_str[:-1]) * 60
        elif time_str.endswith('h'):
            return int(time_str[:-1]) * 3600
        elif time_str.endswith('d'):
            return int(time_str[:-1]) * 86400
        else:
            return int(time_str)  # Assume seconds if no unit
    except ValueError:
        return 0

def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    try:
        return filename.split('.')[-1].lower()
    except Exception:
        return ""

def is_media_file(filename: str) -> bool:
    """Check if file is a media file based on extension"""
    media_extensions = {
        'video': ['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', 'm4v'],
        'audio': ['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a', 'wma'],
        'image': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'],
        'document': ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt']
    }
    
    extension = get_file_extension(filename)
    for category, extensions in media_extensions.items():
        if extension in extensions:
            return True
    return False

def get_file_category(filename: str) -> str:
    """Get file category based on extension"""
    extension = get_file_extension(filename)
    
    video_ext = ['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', 'm4v']
    audio_ext = ['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a', 'wma']
    image_ext = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg']
    document_ext = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt']
    archive_ext = ['zip', 'rar', '7z', 'tar', 'gz', 'bz2']
    
    if extension in video_ext:
        return "Video"
    elif extension in audio_ext:
        return "Audio"
    elif extension in image_ext:
        return "Image"
    elif extension in document_ext:
        return "Document"
    elif extension in archive_ext:
        return "Archive"
    else:
        return "Other"

class ProgressTracker:
    """Simple progress tracker for operations"""
    
    def __init__(self, total: int):
        self.total = total
        self.current = 0
        self.start_time = datetime.now()
    
    def update(self, increment: int = 1):
        """Update progress"""
        self.current += increment
    
    def get_percentage(self) -> float:
        """Get completion percentage"""
        if self.total == 0:
            return 100.0
        return (self.current / self.total) * 100
    
    def get_elapsed_time(self) -> timedelta:
        """Get elapsed time"""
        return datetime.now() - self.start_time
    
    def get_eta(self) -> Optional[timedelta]:
        """Get estimated time of completion"""
        if self.current == 0:
            return None
        
        elapsed = self.get_elapsed_time()
        rate = self.current / elapsed.total_seconds()
        remaining = self.total - self.current
        
        if rate > 0:
            eta_seconds = remaining / rate
            return timedelta(seconds=eta_seconds)
        
        return None
    
    def is_complete(self) -> bool:
        """Check if progress is complete"""
        return self.current >= self.total
    
    def get_progress_bar(self, length: int = 20) -> str:
        """Get visual progress bar"""
        percentage = self.get_percentage()
        filled = int((percentage / 100) * length)
        bar = "█" * filled + "░" * (length - filled)
        return f"[{bar}] {percentage:.1f}%"

def create_pagination_keyboard(current_page: int, total_pages: int, callback_prefix: str):
    """Create pagination keyboard for long lists"""
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = []
    
    if total_pages > 1:
        buttons = []
        
        # Previous button
        if current_page > 1:
            buttons.append(InlineKeyboardButton("◀️ Previous", callback_data=f"{callback_prefix}_page_{current_page - 1}"))
        
        # Page indicator
        buttons.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="page_info"))
        
        # Next button
        if current_page < total_pages:
            buttons.append(InlineKeyboardButton("Next ▶️", callback_data=f"{callback_prefix}_page_{current_page + 1}"))
        
        keyboard.append(buttons)
    
    return InlineKeyboardMarkup(keyboard) if keyboard else None
