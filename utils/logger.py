#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import sys
from datetime import datetime
from pathlib import Path

def setup_logger(name: str = "file_sharing_bot", level: int = logging.INFO) -> logging.Logger:
    """Setup and configure logger"""
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional - creates logs directory if it doesn't exist)
    try:
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        log_file = logs_dir / f"bot_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    except Exception as e:
        logger.warning(f"Could not create file logger: {e}")
    
    # Suppress pyrogram info logs unless debug mode
    if level != logging.DEBUG:
        logging.getLogger("pyrogram").setLevel(logging.WARNING)
        logging.getLogger("pyrogram.session.session").setLevel(logging.WARNING)
        logging.getLogger("pyrogram.connection.connection").setLevel(logging.WARNING)
    
    return logger

class BotLogger:
    """Custom logger class for the bot with additional features"""
    
    def __init__(self, name: str = "file_sharing_bot"):
        self.logger = setup_logger(name)
        self.start_time = datetime.now()
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def critical(self, message: str):
        """Log critical message"""
        self.logger.critical(message)
    
    def log_user_action(self, user_id: int, action: str, details: str = ""):
        """Log user action"""
        message = f"User {user_id} - {action}"
        if details:
            message += f" - {details}"
        self.logger.info(message)
    
    def log_admin_action(self, admin_id: int, action: str, target: str = "", details: str = ""):
        """Log admin action"""
        message = f"Admin {admin_id} - {action}"
        if target:
            message += f" - Target: {target}"
        if details:
            message += f" - Details: {details}"
        self.logger.info(message)
    
    def log_file_access(self, user_id: int, file_id: str, file_name: str = ""):
        """Log file access"""
        message = f"File Access - User: {user_id}, File: {file_id}"
        if file_name:
            message += f", Name: {file_name}"
        self.logger.info(message)
    
    def log_batch_access(self, user_id: int, batch_id: str, file_count: int):
        """Log batch access"""
        message = f"Batch Access - User: {user_id}, Batch: {batch_id}, Files: {file_count}"
        self.logger.info(message)
    
    def log_subscription_check(self, user_id: int, channels_joined: int, total_channels: int):
        """Log subscription check"""
        message = f"Subscription Check - User: {user_id}, Joined: {channels_joined}/{total_channels}"
        self.logger.info(message)
    
    def log_broadcast_start(self, admin_id: int, total_users: int):
        """Log broadcast start"""
        message = f"Broadcast Started - Admin: {admin_id}, Target Users: {total_users}"
        self.logger.info(message)
    
    def log_broadcast_complete(self, admin_id: int, successful: int, failed: int, blocked: int):
        """Log broadcast completion"""
        message = f"Broadcast Complete - Admin: {admin_id}, Success: {successful}, Failed: {failed}, Blocked: {blocked}"
        self.logger.info(message)
    
    def log_auto_delete(self, chat_id: int, message_id: int, scheduled_time: str):
        """Log auto-delete scheduling"""
        message = f"Auto Delete Scheduled - Chat: {chat_id}, Message: {message_id}, Time: {scheduled_time}"
        self.logger.info(message)
    
    def log_database_operation(self, operation: str, collection: str, success: bool, details: str = ""):
        """Log database operations"""
        status = "SUCCESS" if success else "FAILED"
        message = f"Database {operation} - Collection: {collection}, Status: {status}"
        if details:
            message += f", Details: {details}"
        
        if success:
            self.logger.info(message)
        else:
            self.logger.error(message)
    
    def log_error_with_context(self, error: Exception, context: str, user_id: int = None):
        """Log error with additional context"""
        message = f"Error in {context}: {str(error)}"
        if user_id:
            message += f" - User: {user_id}"
        self.logger.error(message, exc_info=True)
    
    def get_uptime(self) -> str:
        """Get bot uptime"""
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
    
    def log_system_stats(self, stats: dict):
        """Log system statistics"""
        message = "System Stats - "
        message += ", ".join([f"{k}: {v}" for k, v in stats.items()])
        self.logger.info(message)
    
    def set_level(self, level: str):
        """Set logging level"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        if level.upper() in level_map:
            self.logger.setLevel(level_map[level.upper()])
        else:
            self.logger.warning(f"Invalid log level: {level}")

# Create a global logger instance
bot_logger = BotLogger()

# Convenience functions
def log_info(message: str):
    bot_logger.info(message)

def log_warning(message: str):
    bot_logger.warning(message)

def log_error(message: str):
    bot_logger.error(message)

def log_debug(message: str):
    bot_logger.debug(message)

def log_user_action(user_id: int, action: str, details: str = ""):
    bot_logger.log_user_action(user_id, action, details)

def log_admin_action(admin_id: int, action: str, target: str = "", details: str = ""):
    bot_logger.log_admin_action(admin_id, action, target, details)

def log_file_access(user_id: int, file_id: str, file_name: str = ""):
    bot_logger.log_file_access(user_id, file_id, file_name)

def log_error_with_context(error: Exception, context: str, user_id: int = None):
    bot_logger.log_error_with_context(error, context, user_id)
