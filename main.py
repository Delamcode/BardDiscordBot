from dotenv import load_dotenv
from gemini import Gemini
import discord
import os
import traceback
import ast

load_dotenv()

version = "v2"

# --------- TOKENS ---------
bot_token = os.environ['BOT_KEY']
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
BARD_COOKIES = os.getenv('BARD_COOKIES')
REPLICATE_TOKEN = os.getenv('REPLICATE_TOKEN')
BARD_COOKIES = ast.literal_eval(BARD_COOKIES)

bot = discord.Bot(intents=discord.Intents.default())



async def meta(message, bot):
    attached_all = ""
    attachments = []
    if message.attachments:
        for attachment in message.attachments:
            attached = requests.get(attachment.url)
            try:
                decoded = attached.content.decode('utf-8')
                attachments.append(f"File \"{attachment.filename}\" is attached: {decoded} End of file \"{attachment.filename}\"")
            except UnicodeDecodeError:
                pass
        attached_all = ''.join(attachments)
    mention = f'<@{bot.user.id}>'
    if message.content == mention:
        msg_content = 'Hi Bard! Introduce yourself! Mention that you are a discord bot. Do not make stuff up about your capabillites as a discord bot. Only say that you are an AI powered bot'
    else:
        msg_content = message.content.replace(mention, '').strip()
    if attached_all:
        msg_content = f"{msg_content} ATTACHMENTS: {attached_all}"
    return msg_content


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    await bot.change_presence(activity=discord.Game(name="Running"))


# --------- TEXT MODELS ---------
@bot.event
async def on_message(message):
    if bot.user in message.mentions and '@everyone' not in message.content and '@here' not in message.content:
        print(message.author)
        try:
            async with message.channel.typing():
                await message.add_reaction("🕥")
                GeminiClient = Gemini(cookies=BARD_COOKIES)
                msg_content = await meta(message, bot)
                response = GeminiClient.generate_content(msg_content)
                await message.reply(f"{response.response_dict['candidates']['text']}")
                await message.remove_reaction("🕥", bot.user)
                await message.add_reaction("😸")
        except Exception as error:
            await message.reply(f"An error occurred: {error}.")
            traceback.print_exc()

bot.run(bot_token)