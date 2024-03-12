from dotenv import load_dotenv
from gemini import Gemini
import discord
import os
import traceback
import ast
import datetime

load_dotenv()

version = "v2"

# --------- TOKENS ---------
bot_token = os.environ['BOT_KEY']
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
BARD_COOKIES = os.getenv('BARD_COOKIES')
REPLICATE_TOKEN = os.getenv('REPLICATE_TOKEN')
BARD_COOKIES = ast.literal_eval(BARD_COOKIES)
PROXY_TOKEN = os.getenv('PROXY_TOKEN')


user_history = {}

GeminiClient = Gemini(cookies=BARD_COOKIES, proxies={"http": f"http://{PROXY_TOKEN}:@smartproxy.crawlbase.com:8012", "https": f"http://{PROXY_TOKEN}:@smartproxy.crawlbase.com:8012"}, timeout=30)

bot = discord.Bot(intents=discord.Intents.default())



async def meta(message, bot):
    attached_all = ""
    attachments = []
    if message.attachments:
        for attachment in message.attachments:
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as response:
                    if response.status == 200:
                        attached = await response.read()
                    else:
                        attached =  None
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
        time = datetime.datetime.now().time().strftime("%H:%M:%S")
        print(time, message.author.id, message.author, "Message")
        try:
            async with message.channel.typing():
                await message.add_reaction("🕥")
                msg_content = await meta(message, bot)
                response = await GeminiClient.generate_content(msg_content)
                await message.reply(f"{response.response_dict['candidates']['text']}")
                await message.remove_reaction("🕥", bot.user)
                await message.add_reaction("😸")
        except Exception as error:
            await message.reply(f"An error occurred: {error}.")
            traceback.print_exc()

bot.run(bot_token)