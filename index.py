import asyncio
import json
import logging
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.errors import FloodWait

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'bot_log_{datetime.now().strftime("%Y-%m-%d")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def log(level, message):
    logger.log(getattr(logging, level.upper()), message)

async def load_session(phone):
    try:
        with open(f'session_{phone}.json', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return ''

async def save_session(session, phone):
    with open(f'session_{phone}.json', 'w') as f:
        f.write(session)

async def initialize_client(account):
    session = await load_session(account['phone'])
    client = Client(
        session_name=f"session_{account['phone']}",
        api_id=account['api_id'],
        api_hash=account['api_hash'],
        phone_number=account['phone'],
        in_memory=True
    )

    await client.start()
    await save_session(await client.export_session_string(), account['phone'])

    log('INFO', f"Client for {account['phone']} is now connected and ready")
    return client

async def setup_channel_handlers(client, account):
    @client.on_message(filters.channel)
    async def message_handler(client, message):
        for channel in account['channels']:
            if message.chat.username == channel['username'].lstrip('@'):
                log('INFO', f"New message in channel {channel['username']}: {message.text[:30]}...")
                try:
                    await asyncio.sleep(2)  # Avoid flood wait
                    await message.reply(channel['comment'])
                    log('INFO', f"Comment posted successfully in {channel['username']}")
                except FloodWait as e:
                    log('WARNING', f"FloodWait: sleeping for {e.x} seconds")
                    await asyncio.sleep(e.x)
                except Exception as e:
                    log('ERROR', f"Failed to post comment in {channel['username']}: {e}")

    log('INFO', f"Handler set up for {account['phone']}")

async def main():
    with open('config.json', 'r') as f:
        config = json.load(f)

    clients = []

    for account in config['accounts']:
        try:
            client = await initialize_client(account)
            await setup_channel_handlers(client, account)
            clients.append(client)
        except Exception as e:
            log('ERROR', f"Failed to initialize client for {account['phone']}: {e}")

    if not clients:
        log('ERROR', 'No clients were initialized successfully')
        return

    log('INFO', f"Bot is running with {len(clients)} clients")
    print(f"Bot is running with {len(clients)} clients. Press Ctrl+C to stop.")

    # Keep the script running
    await asyncio.gather(*[client.run() for client in clients])

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        log('ERROR', f"Fatal error: {e}")