import asyncio
import json
import logging
from pyrogram import Client, filters
from pyrogram.errors import SessionPasswordNeeded

# Configure logging
logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configuration file
CONFIG_FILE = 'config.json'

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        return {"accounts": []}

async def setup_client(account):
    client = Client(
        f"session_{account['phone']}",
        api_id=account['api_id'],
        api_hash=account['api_hash'],
        phone_number=account['phone']
    )
    
    await client.start()
    
    if not await client.is_initialized:
        logging.info(f"Authorizing {account['phone']}...")
        try:
            code = await client.ask("Enter the code: ")
            await client.sign_in(account['phone'], code.text)
            logging.info(f"Authorized {account['phone']}")
        except SessionPasswordNeeded:
            password = await client.ask("Two-step verification required. Enter your password: ")
            await client.check_password(password.text)
            logging.info(f"Two-step verification successful for {account['phone']}")
        except Exception as e:
            logging.error(f"Failed to authorize {account['phone']}: {e}")
    
    return client

async def handle_new_message(client, channel_username, comment):
    @client.on_message(filters.chat(channel_username) & filters.incoming)
    async def auto_comment(client, message):
        try:
            await message.reply(comment)
            logging.info(f"Commented on {channel_username}: {comment}")
        except Exception as e:
            logging.error(f"Error commenting on {channel_username}: {e}")

async def main():
    config = load_config()
    
    if not config['accounts']:
        logging.info("No accounts found in config.")
        print("No accounts configured. Please update config.json.")
        return
    
    clients = []
    
    for account in config['accounts']:
        client = await setup_client(account)
        clients.append(client)
        for channel in account['channels']:
            handle_new_message(client, channel['username'], channel['comment'])
    
    logging.info("Bot is running.")
    print("Bot is running. Press Ctrl+C to exit.")
    
    try:
        await asyncio.gather(*(client.idle() for client in clients))
    except KeyboardInterrupt:
        logging.info("Shutting down bots...")
        for client in clients:
            await client.stop()
        logging.info("Bots shut down successfully.")
        print("Bot has been stopped.")

if __name__ == "__main__":
    asyncio.run(main())