#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
from datetime import datetime
from aiohttp import web, web_runner
from aiohttp.web import Response
import json
import os
from bot import Bot

class WebServer:
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.app = web.Application()
        self.setup_routes()
        
    def setup_routes(self):
        """Setup web server routes"""
        self.app.router.add_get('/', self.health_check)
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/status', self.bot_status)
        self.app.router.add_get('/stats', self.bot_stats)
        
    async def health_check(self, request):
        """Health check endpoint"""
        return Response(
            text=json.dumps({
                "status": "ok",
                "message": "Telegram File Sharing Bot is running",
                "timestamp": datetime.now().isoformat(),
                "uptime": self.bot.get_uptime() if hasattr(self.bot, 'get_uptime') else "Unknown"
            }),
            content_type='application/json'
        )
        
    async def bot_status(self, request):
        """Bot status endpoint"""
        try:
            me = await self.bot.get_me()
            return Response(
                text=json.dumps({
                    "bot_info": {
                        "username": me.username,
                        "first_name": me.first_name,
                        "id": me.id
                    },
                    "status": "running",
                    "uptime": self.bot.get_uptime() if hasattr(self.bot, 'get_uptime') else "Unknown",
                    "timestamp": datetime.now().isoformat()
                }),
                content_type='application/json'
            )
        except Exception as e:
            return Response(
                text=json.dumps({
                    "status": "error",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                }),
                content_type='application/json',
                status=500
            )
            
    async def bot_stats(self, request):
        """Bot statistics endpoint"""
        try:
            if hasattr(self.bot, 'db'):
                users_count = await self.bot.db.get_users_count()
                files_count = await self.bot.db.get_files_count()
                batch_links_count = await self.bot.db.get_batch_links_count()
                
                return Response(
                    text=json.dumps({
                        "statistics": {
                            "total_users": users_count,
                            "total_files": files_count,
                            "total_batch_links": batch_links_count,
                            "uptime": self.bot.get_uptime() if hasattr(self.bot, 'get_uptime') else "Unknown"
                        },
                        "timestamp": datetime.now().isoformat()
                    }),
                    content_type='application/json'
                )
            else:
                return Response(
                    text=json.dumps({
                        "message": "Database not connected",
                        "timestamp": datetime.now().isoformat()
                    }),
                    content_type='application/json',
                    status=503
                )
        except Exception as e:
            return Response(
                text=json.dumps({
                    "status": "error",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                }),
                content_type='application/json',
                status=500
            )
    
    async def start_server(self, host='0.0.0.0', port=None):
        """Start the web server"""
        if port is None:
            port = int(os.getenv('PORT', 5000))
            
        runner = web_runner.AppRunner(self.app)
        await runner.setup()
        
        site = web_runner.TCPSite(runner, host, port)
        await site.start()
        
        logging.info(f"Web server started on http://{host}:{port}")
        return runner

async def run_bot_with_web_server():
    """Run both bot and web server"""
    # Initialize bot
    bot = Bot()
    
    # Initialize web server
    web_server = WebServer(bot)
    
    # Start bot
    await bot.start()
    
    # Start web server
    runner = await web_server.start_server()
    
    try:
        # Keep both running
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logging.info("Shutting down...")
    finally:
        # Cleanup
        await runner.cleanup()
        await bot.stop()

if __name__ == "__main__":
    asyncio.run(run_bot_with_web_server())