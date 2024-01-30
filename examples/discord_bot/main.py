import requests
import json
import time
import discord
import asyncio
from collections import deque
from pathlib import Path
import os
import io
import base64

script_dir = Path(os.path.abspath(__file__)).parent

def is_message_allowed(message):
    for server_id, channel_id in config['whitelisted_servers']:
        if server_id == message.guild.id:
            if channel_id == 0 or message.channel.id == channel_id:
                return True
    return False

class PolyMind:
    def __init__(self, base_url):
        self.base_url = base_url

    def send_message(self, message, user):
        url = f"{self.base_url}/"
        data = {'input': message, 'user': user}
        response = requests.post(url, data=data)
        return response.json()

    def upload_file(self, file_path, file_type):
        url = f"{self.base_url}/upload_file"
        file = {'file': open(file_path, 'rb')}
        data = {'content': file_type}
        response = requests.post(url, files=file, data=data)
        return response.json()


def load_config():
    try:
        with open(os.path.join(script_dir, "config.json"), 'r') as file:
            config = json.load(file)
        return config
    except FileNotFoundError:
        print(f"config.json not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding config.json.")
        return None

config = load_config()

class discordclient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message_queue = deque()
        self.is_processing = False  
        self.polyclient = PolyMind(config["URI"])

    async def on_ready(self):
        print(f'Logged in as {self.user}\n------')

    async def on_message(self, message):
        if message.author == self.user or not is_message_allowed(message):
            return

        try:
            guild = message.guild.name
        except AttributeError:
            guild = "PrivateMessage"

        if self.user in message.mentions:
            content = message.content.replace(f'<@{self.user.id}>', '')
            print(f'Message from {message.author}: {content} with {message.attachments} in {guild}')
            self.message_queue.append(message)
            if not self.is_processing:
                async with message.channel.typing():
                    await self.process_messages()

    async def process_messages(self):
        self.is_processing = True
        while len(self.message_queue) > 0:
            message = self.message_queue.popleft()
            content = message.content.replace(f'<@{self.user.id}>', '')
            response = self.polyclient.send_message(content, message.author)

            print("Response: " + response['output'])
            if "base64_image" in response:
                file = discord.File(io.BytesIO(base64.b64decode(response['base64_image_full'])), filename='img.png')
                await message.reply(response['output'], file=file)
            else:
                await message.reply(response['output'])

        self.is_processing = False

client = discordclient(intents=discord.Intents.default())
client.run(config['token'])
