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


user_history = {}

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
        time = datetime.datetime.now().time().strftime("%H:%M:%S")
        print(time, message.author.id, message.author, "Message")
        try:
            async with message.channel.typing():
                await message.add_reaction("🕥")
                if str(message.author.id) not in user_history:
                    user_history.setdefault(str(message.author.id), Gemini(cookies=BARD_COOKIES))
                msg_content = await meta(message, bot)
                response = user_history[str(message.author.id)].generate_content(msg_content)
                await message.reply(f"{response.response_dict['candidates']['text']}")
                await message.remove_reaction("🕥", bot.user)
                await message.add_reaction("😸")
        except Exception as error:
            await message.reply(f"An error occurred: {error}.")
            traceback.print_exc()


@bot.slash_command(description="Reset your conversation.")
async def reset(ctx: discord.ApplicationContext):
    if str(ctx.user.id) not in user_history:
        await ctx.respond("Nothing to reset...", ephemeral=True)
        return
    try:
        del user_history[str(ctx.user.id)]
        await ctx.respond("Reset complete!", ephemeral=True)
    except Exception as error:
        await ctx.respond(f"An error occurred: {error}.", ephemeral=True)
    return

bot.run(bot_token)