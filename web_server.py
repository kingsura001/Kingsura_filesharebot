#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import threading
import json
import os
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from bot import Bot

class SimpleWebHandler(BaseHTTPRequestHandler):
    bot_instance = None
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path in ['/', '/health']:
            self.send_health_check()
        elif path == '/status':
            self.send_bot_status()
        elif path == '/stats':
            self.send_bot_stats()
        else:
            self.send_not_found()
    
    def send_health_check(self):
        """Send health check response"""
        response = {
            "status": "ok",
            "message": "Telegram File Sharing Bot is running",
            "timestamp": datetime.now().isoformat(),
            "uptime": self.bot_instance.get_uptime() if hasattr(self.bot_instance, 'get_uptime') else "Unknown"
        }
        self.send_json_response(response)
    
    def send_bot_status(self):
        """Send bot status response"""
        try:
            # Create a simple sync wrapper for async function
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            me = loop.run_until_complete(self.bot_instance.get_me())
            
            response = {
                "bot_info": {
                    "username": me.username,
                    "first_name": me.first_name,
                    "id": me.id
                },
                "status": "running",
                "uptime": self.bot_instance.get_uptime() if hasattr(self.bot_instance, 'get_uptime') else "Unknown",
                "timestamp": datetime.now().isoformat()
            }
            self.send_json_response(response)
        except Exception as e:
            error_response = {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.send_json_response(error_response, status=500)
    
    def send_bot_stats(self):
        """Send bot statistics response"""
        try:
            if hasattr(self.bot_instance, 'db'):
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                users_count = loop.run_until_complete(self.bot_instance.db.get_users_count())
                files_count = loop.run_until_complete(self.bot_instance.db.get_files_count())
                batch_links_count = loop.run_until_complete(self.bot_instance.db.get_batch_links_count())
                
                response = {
                    "statistics": {
                        "total_users": users_count,
                        "total_files": files_count,
                        "total_batch_links": batch_links_count,
                        "uptime": self.bot_instance.get_uptime() if hasattr(self.bot_instance, 'get_uptime') else "Unknown"
                    },
                    "timestamp": datetime.now().isoformat()
                }
                self.send_json_response(response)
            else:
                response = {
                    "message": "Database not connected",
                    "timestamp": datetime.now().isoformat()
                }
                self.send_json_response(response, status=503)
        except Exception as e:
            error_response = {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.send_json_response(error_response, status=500)
    
    def send_json_response(self, data, status=200):
        """Send JSON response"""
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def send_not_found(self):
        """Send 404 response"""
        response = {
            "status": "error",
            "message": "Not Found",
            "timestamp": datetime.now().isoformat()
        }
        self.send_json_response(response, status=404)
    
    def log_message(self, format, *args):
        """Override to reduce log noise"""
        pass

class SimpleWebServer:
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.server = None
        self.thread = None
        
    def start_server(self, host='0.0.0.0', port=None):
        """Start the web server in a separate thread"""
        if port is None:
            port = int(os.getenv('PORT', 5000))
        
        # Set bot instance for handler
        SimpleWebHandler.bot_instance = self.bot
        
        # Create and start server
        self.server = HTTPServer((host, port), SimpleWebHandler)
        
        def run_server():
            logging.info(f"Web server started on http://{host}:{port}")
            self.server.serve_forever()
        
        self.thread = threading.Thread(target=run_server, daemon=True)
        self.thread.start()
        
        return self.server
    
    def stop_server(self):
        """Stop the web server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()

async def run_bot_with_web_server():
    """Run both bot and web server"""
    # Initialize bot
    bot = Bot()
    
    # Initialize web server
    web_server = SimpleWebServer(bot)
    
    # Start bot
    await bot.start()
    
    # Start web server
    web_server.start_server()
    
    try:
        # Keep both running
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logging.info("Shutting down...")
    finally:
        # Cleanup
        web_server.stop_server()
        await bot.stop()

if __name__ == "__main__":
    asyncio.run(run_bot_with_web_server())