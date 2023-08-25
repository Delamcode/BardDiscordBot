import os
import io
import requests
import time
import json
import loader
import sender
import generator
import traceback
import asyncio
import random
import discord
from discord import option
from Bard import AsyncChatbot
from dotenv import load_dotenv
from keep_alive import keep_alive
import aiohttp
import BingImageCreator
import openai
import models
import psutil
import sys
import urllib.parse

load_dotenv()

STATS_FILE = 'stats.json'
SETTINGS_FILE = 'settings.json'

announce = 1099628767581831259
version = "v1b"

user_bards = {}

# --------- TOKENS ---------
bot_token = os.environ['BOT_KEY']
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
BARD_KEY = os.getenv('BARD_KEY')
BARD_KEY_TS = os.getenv('BARD_KEY_TS')
REPLICATE_TOKEN = os.getenv('REPLICATE_TOKEN')
video_settings = {}

async def get_drafts(info):
    try:
        drafts = []
        for i, choice in enumerate(info['choices'][-3:], start=1):
            draft = choice['content']
            if isinstance(draft, list):
                draft = draft[0]
            drafts.append(f"Draft {i}:\n```{draft}```")
        return '\n\n'.join(drafts)
    except Exception as error:
        return f"Error: {error}"

bot = discord.Bot(intents=discord.Intents.default())

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    await bot.change_presence(activity=discord.Game(name="Running"))
@bot.event
async def on_command(ctx):
    stats = await loader.load_file(STATS_FILE)
    if "stats" in stats:
        stats["stats"] = int(stats["stats"])
        stats["stats"] += 1
        stats["stats"] = str(stats["stats"])
    else:
        stats = {
            "stats": "1"
        }
    await loader.save_file(stats, STATS_FILE)

class DestroyItem(discord.ui.View):
    @discord.ui.button(label="Delete Item(s)", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def button_callback(self, button, interaction):
        try:
            await interaction.message.delete()
            await interaction.response.send_message("The item was (hopefully) deleted.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred. This bot needs manage messages permission. Here is the error: {e}", ephemeral=True)

class DestroyUpscale(discord.ui.View):
    @discord.ui.button(label="Delete Item(s)", style=discord.ButtonStyle.danger, emoji="🗑️", row=0)
    async def button_callback(self, button, interaction):
        try:
            await interaction.message.delete()
            await interaction.response.send_message("The item was (hopefully) deleted.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred. This bot needs manage messages permission. Here is the error: {e}", ephemeral=True)
    @discord.ui.button(label="Upscale", style=discord.ButtonStyle.primary, emoji="⏫", row=1)
    async def button_callback(self, button, interaction):
        try:
            button.disabled = True
            stats = {"stats": str(int((await loader.load_file(STATS_FILE)).get("stats", "0")) + 1)}
            await loader.save_file(stats, STATS_FILE)
            model = "xl"
            height = 576
            width = 1024
            data = {
                "version": "71996d331e8ede8ef7bd76eba9fae076d31792e4ddf4ad057779b443d6aea62f",
                "input": {
                    "prompt": video_settings[str(interaction.message.id)]["prompt"],
                    "width": width,
                    "height": height,
                    "fps": video_settings[str(interaction.message.id)]["fps"],
                    "model": model,
                    "negative_prompt": "dust, noisy, washed out, ugly, distorted, broken",
                    "num_frames": video_settings[str(interaction.message.id)]["length"],
                    "num_inference_steps": 50,
                    "init_video": video_settings[str(interaction.message.id)]["url"]
                }
            }
            headers = {
                "Authorization": f"Token {REPLICATE_TOKEN}",
                "Content-Type": "application/json"
            }
        
            async with aiohttp.ClientSession() as session:
                async with session.post("https://api.replicate.com/v1/predictions", headers=headers, json=data) as response:
                    response_data = await response.json()
                    prediction_id = response_data["id"]
                    prediction_url = f"https://api.replicate.com/v1/predictions/{prediction_id}"
                
                    while True:
                        async with session.get(prediction_url, headers=headers) as prediction_response:
                            prediction_data = await prediction_response.json()
                            if prediction_data["status"] == "succeeded":
                                output = prediction_data["output"]
                                break
                            if prediction_data["status"] == "failed":
                                logs = prediction_data["logs"]
                                error = prediction_data["error"]
                                await ctx.respond(f"The model failed generating. \n### Error: \n```{error}```")
                                return
                            await asyncio.sleep(2)
                image_url = output[0]
                async with session.get(image_url) as image_response:
                    if image_response.status == 200:
                        image_data = await image_response.read()
                        final = discord.File(io.BytesIO(image_data), filename="video.mp4")
                        await interaction.response.send_message(f"The video was upscaled for {interaction.user.mention}", file=final, view=DestroyItem())
                        await interaction.response.edit_message(view=self)
                    else:
                        await interaction.response.send_message("Failed getting video... Please try again.")
        except Exception as error:
            await interaction.response.send_message(f"Something went wrong: {error}. Please try again.", ephemeral=True)
            with open('errors.txt', 'a') as f:
                traceback.print_exc(file=f)


# --------- TEXT MODELS ---------
@bot.event
async def on_message(message):
    if bot.user in message.mentions and '@everyone' not in message.content and '@here' not in message.content:
        user_settings = await loader.load_file(SETTINGS_FILE)
        stats = {"stats": str(int((await loader.load_file(STATS_FILE)).get("stats", "0")) + 1)}
        await loader.save_file(stats, STATS_FILE)
        print(message.author)
        try:
            async with message.channel.typing():
                await message.add_reaction("🕥")
                if str(message.author.id) not in user_settings:
                    user_settings.setdefault(str(message.author.id), models.default_settings)
                await loader.save_file(user_settings, SETTINGS_FILE)
                if models.models["text_models"][user_settings[str(message.author.id)]["text_model"]]["type"] == "openai":
                    await generator.gpt(message, models.models["text_models"][user_settings[str(message.author.id)]["text_model"]]["url"], models.models["text_models"][user_settings[str(message.author.id)]["text_model"]]["key"], models.models["text_models"][user_settings[str(message.author.id)]["text_model"]]["name"], bot, SETTINGS_FILE)
                elif models.models["text_models"][user_settings[str(message.author.id)]["text_model"]]["type"] == "bard":
                    if str(message.author.id) not in user_bards:
                        user_bards[str(message.author.id)] = await AsyncChatbot.create(BARD_KEY, BARD_KEY_TS)
                    await generator.bard(message, user_bards[str(message.author.id)], bot, SETTINGS_FILE)
                elif models.models["text_models"][user_settings[str(message.author.id)]["text_model"]]["type"] == "replicate":
                    await generator.replicate(message, bot, SETTINGS_FILE)
                elif models.models["text_models"][user_settings[str(message.author.id)]["text_model"]]["type"] == "openai-completions":
                    await generator.gpt_completions(message, models.models["text_models"][user_settings[str(message.author.id)]["text_model"]]["url"], models.models["text_models"][user_settings[str(message.author.id)]["text_model"]]["key"], models.models["text_models"][user_settings[str(message.author.id)]["text_model"]]["name"], bot, SETTINGS_FILE)
                else:
                    await message.reply("The selected model is not yet supported.")
        except Exception as error:
            await message.reply(f"An error occurred: {error}.")
            with open('errors.txt', 'a') as f:
                traceback.print_exc(file=f)

# --------- FULLINFO ---------
@bot.slash_command(description="Get the full info from a response.")
async def info(ctx):
    try:
        user_settings = await loader.load_file(SETTINGS_FILE)
        if str(ctx.user.id) in user_settings:
            user_settings[str(ctx.user.id)]["last_use"] = "info"
            content = str(user_settings[str(ctx.user.id)]["last_msg"])
            if user_settings[str(ctx.user.id)]["last_msg"]:
                await sender.send(ctx, content, False, ctx.respond)
            else:
                await ctx.respond("No info to send.", ephemeral=True)
        else:
            await ctx.respond("No info to send.", ephemeral=True)
        await loader.save_file(user_settings, SETTINGS_FILE)
    except Exception as error:
        await ctx.respond(f"An error occurred: {error}.", ephemeral=True)

@bot.slash_command(description="Reset your conversation.")
@option("type", description="The model to reset", choices=["Bard", "GPT-Like models"], required=False)
async def reset(
    ctx: discord.ApplicationContext,
    type: str,
):
    user_settings = await loader.load_file(SETTINGS_FILE)
    if str(ctx.user.id) not in user_settings:
        await ctx.respond("Nothing to reset...", ephemeral=True)
        return
    if type == "Bard" or (not type and models.models["text_models"][user_settings[str(ctx.user.id)]["text_model"]]["type"] == "bard"):
        try:
            if str(ctx.user.id) in user_bards:
                user_settings[str(ctx.user.id)]["last_msg"] = None
                user_settings[str(ctx.user.id)]["last_use"] = None
                del user_bards[str(ctx.user.id)]
                await loader.save_file(user_settings, SETTINGS_FILE)
                await ctx.respond("Reset complete!", ephemeral=True)
            else:
                await ctx.respond("You do not have a saved conversation with Bard.", ephemeral=True)
        except Exception as error:
            await ctx.respond(f"An error occurred: {error}.", ephemeral=True)
        return
    elif type == "GPT-Like models" or (not type and models.models["text_models"][user_settings[str(ctx.user.id)]["text_model"]]["type"] == "openai" or models.models["text_models"][user_settings[str(ctx.user.id)]["text_model"]]["type"] == "openai-completions"):
        try:
            if str(ctx.user.id) in user_settings:
                user_settings[str(ctx.user.id)]["last_msg"] = None
                user_settings[str(ctx.user.id)]["last_use"] = None
                user_settings[str(ctx.user.id)]["context"] = []
                await loader.save_file(user_settings, SETTINGS_FILE)
                await ctx.respond("Reset complete!", ephemeral=True)
            else:
                await ctx.respond("You do not have a saved conversation with a GPT-Like model.", ephemeral=True)
        except Exception as error:
            await ctx.respond(f"An error occurred: {error}.", ephemeral=True)
    else:
        await ctx.respond("Something went wrong...", ephemeral=True)

# --------- IMAGINE---------
@bot.slash_command(description="Generate images")
@option(name="prompt", required=True, description="Prompt to generate")
@option(name="model", required=False, choices=['bing', 'kandinsky', 'if', 'stable diffusion 1.5', 'stable diffusion 2.1', 'dreamshaper', 'deliberate', 'SDXL', 'dalle'])
@option(name="num_outputs", required=False, min_value=1, max_value=10, description="Number of outputs - bing is always 4")
async def imagine(
    ctx: discord.ApplicationContext,
    prompt: str,
    model: str,
    num_outputs: int=4,
):
    try:
        user_settings = await loader.load_file(SETTINGS_FILE)
        stats = {"stats": str(int((await loader.load_file(STATS_FILE)).get("stats", "0")) + 1)}
        await loader.save_file(stats, STATS_FILE)
        print(ctx.user)
        await ctx.respond(f"Generating:\n> {prompt}", ephemeral=True)
        if str(ctx.user.id) not in user_settings:
            user_settings.setdefault(str(ctx.user.id), models.default_settings)
            await loader.save_file(user_settings, SETTINGS_FILE)
        if not model:
            model = user_settings[str(ctx.user.id)]["img_model"]
        model_id = models.models['img_models'][model]['id']
        url = "https://image-webui.hop.sh/api"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "prompt": prompt,
            "count": num_outputs,
            "size_ratio": "1:1",
            "model": model_id,
            "key": ""
        }
        encoded_data = urllib.parse.urlencode(data)

        timeout_seconds = 120

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=encoded_data, timeout=timeout_seconds) as response:
                output = await response.json()
        if "error" in output:
            await ctx.respond(f"An error occurred: {output['error']} - API error", ephemeral=True)
            return
        final = []
        for i, url in enumerate(output):
            response = requests.get(url["url"])
            image_bytes = io.BytesIO(response.content)
            final.append(discord.File(image_bytes, f'image{i+1}.jpg'))
        await ctx.respond(f"{ctx.user.mention} requested an image with these settings:\n**{prompt}** | model: **{model}**", files=final, view=DestroyItem())

    except Exception as error:
        await ctx.respond(f"An error occurred: {error}. - Bot error", ephemeral=True)
        with open('errors.txt', 'a') as f:
            traceback.print_exc(file=f)

# --------- AUDIO ---------
@bot.slash_command(description="Generate audio.")
@option(name="prompt", required=True, description="The audio prompt")
@option(name="length", min_value=1, max_value=30, required=False)
@option(name="model", required=False, description="The model used", choices=['melody', 'large', 'riffusion', 'audioldm'])
@option(name="seed", required=False, description="Seed of generated image, default random", min_value=0)
async def audio(
    ctx: discord.ApplicationContext,
    prompt: str,
    seed: int,
    length: int = 10,
    model: str = None,
):
    stats = {"stats": str(int((await loader.load_file(STATS_FILE)).get("stats", "0")) + 1)}
    await loader.save_file(stats, STATS_FILE)
    user_settings = await loader.load_file(SETTINGS_FILE)
    print(ctx.user)
    if not seed:
        seed = random.randint(0, 4294967295)
        is_random = " (random)"
    else:
        is_random = ""
    if str(ctx.user.id) not in user_settings:
        user_settings.setdefault(str(ctx.user.id), models.default_settings)
        await loader.save_file(user_settings, SETTINGS_FILE)
    if not model and str(ctx.user.id) in user_settings:
        model = user_settings[str(ctx.user.id)]["audio_model"]
    await ctx.respond(f"Generating:\n> {prompt}\n>> This will take a while.", ephemeral=True)
    try:
        if model == "melody" or model == "large":
            data = {
                "version": "7a76a8258b23fae65c5a22debb8841d1d7e816b75c2f24218cd2bd8573787906",
                "input": {
                    "prompt": prompt,
                    "model_version": model,
                    "duration": length,
                    "seed": seed,
                }
            }
            headers = {
                "Authorization": f"Token {REPLICATE_TOKEN}",
                "Content-Type": "application/json"
            }

        elif model == "audioldm":
            length = 2.5*round(length/2.5)
            if length > 20:
                length = "20.0"
            elif length < 2.5:
                length = "2.5"
            else:
                length = str(length)
                
            data = {
                "version": "b61392adecdd660326fc9cfc5398182437dbe5e97b5decfb36e1a36de68b5b95",
                "input": {
                    "text": prompt,
                    "duration": length,
                    "random_seed": seed,
                }
            }
            headers = {
                "Authorization": f"Token {REPLICATE_TOKEN}",
                "Content-Type": "application/json"
            }
        
        elif model == "riffusion":
            data = {
                "version": "8cf61ea6c56afd61d8f5b9ffd14d7c216c0a93844ce2d82ac1c9ecc9c7f24e05",
                "input": {
                    "prompt_a": prompt
                }
            }
            headers = {
                "Authorization": f"Token {REPLICATE_TOKEN}",
                "Content-Type": "application/json"
            }
        else:
            await ctx.respond("This isn't supposed to happen... Please report the settings you used to @delamcode, then try again. Thank you!")
            return
    
        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.replicate.com/v1/predictions", headers=headers, json=data) as response:
                response_data = await response.json()
                prediction_id = response_data["id"]
                prediction_url = f"https://api.replicate.com/v1/predictions/{prediction_id}"
            
                while True:
                    async with session.get(prediction_url, headers=headers) as prediction_response:
                        prediction_data = await prediction_response.json()
                        if prediction_data["status"] == "succeeded":
                            output = prediction_data["output"]
                            break
                        if prediction_data["status"] == "failed":
                            logs = prediction_data["logs"]
                            error = prediction_data["error"]
                            if len(logs) > 1500:
                                await ctx.respond(f"### The model failed generating. \n### Error: \n```{error}```\n### Settings: **{prompt}** | length: **{length}** | model: **{model}** | seed: **{seed}**{is_random}")
                            await ctx.respond(f"### The model failed generating. Here are the logs found:\n```{logs}```\n### Error: \n```{error}```")
                            return
                    await asyncio.sleep(2)
            if model != "riffusion":
                image_url = output
                async with session.get(str(image_url)) as image_response:
                    if image_response.status == 200:
                        image_data = await image_response.read()
                        final = discord.File(io.BytesIO(image_data), filename="audio.wav")
                        await ctx.respond(f"{ctx.user.mention} requested music with these settings:\n> **{prompt}** | model: **{model}** | length: **{length}** | seed: **{seed}**{is_random}", file=final)
                    else:
                        await ctx.respond("Failed getting audio... Please try again.")
            else:
                audio_url = output["audio"]
                image_url = output["spectrogram"]
                async with session.get(str(audio_url)) as audio_response:
                    if audio_response.status == 200:
                        audio_data = await audio_response.read()
                        audio = discord.File(io.BytesIO(audio_data), filename="audio.wav")
                    else:
                        await ctx.respond("Failed getting audio... Please try again.")
                    async with session.get(str(image_url)) as image_response:
                        if image_response.status == 200:
                            image_data = await image_response.read()
                            image = discord.File(io.BytesIO(image_data), filename="spectrogram.jpg")
                        else:
                            await ctx.respond("Failed getting spectrogram... Please try again.")
                    await ctx.respond(f"{ctx.user.mention} requested music with these settings:\n> **{prompt}** | model: **{model}** | length: **{length}** | seed: **{seed}**{is_random}", files=[image, audio])

            
    except Exception as error:
        await ctx.respond(f"Something went wrong: {error}. Please try again.", ephemeral=True)
        with open('errors.txt', 'a') as f:
            traceback.print_exc(file=f)


# --------- VIDEO ---------
@bot.slash_command(description="Generate video.")
@option(name="prompt", required=True, description="The video prompt")
@option(name="length", min_value=1, max_value=48, required=False, description="Length in frames")
@option(name="model", required=False, choices=["xl", "576w", "animov-512x", "potat1"], description="Model XL: Best, slow. 576w: Worst, fast, Potat1: Good, slow.")
@option(name="fps", required=False, min_value=1, max_value=48, description="Frames per Second (lower for longer more choppy video, higher for shorter and smoother video)")
@option(name="steps", required=False, description="Number of inferance steps", min_value=10, max_value=50)
@option(name="height", required=False, min_value=256)
@option(name="width", required=False, min_value=256)
@option(name="seed", min_value=0, required=False)
async def video(
    ctx: discord.ApplicationContext,
    prompt: str,
    model: str=None,
    steps: int = 40,
    length: int = 24,
    fps: int = 12,
    height: int = None,
    width: int = None,
    seed: int = None,
):
    stats = {"stats": str(int((await loader.load_file(STATS_FILE)).get("stats", "0")) + 1)}
    await loader.save_file(stats, STATS_FILE)
    print(ctx.user)

    user_settings = await loader.load_file(SETTINGS_FILE)
    if str(ctx.user.id) not in user_settings:
        user_settings.setdefault(str(ctx.user.id), models.default_settings)
        await loader.save_file(user_settings, SETTINGS_FILE)
    if not model:
        model = user_settings[str(ctx.user.id)]["video_model"]
    if not height and not width and (model == "xl"):
        height = 576
        width = 1024
    elif not height and not width and model == "576w":
        height = 320
        width = 576
    if not height:
        height = 320
    if not width:
        width = 576
    if not seed:
        seed = random.randint(0, 2147483647)
        is_random = " (random)"
    else:
        is_random = ""
    await ctx.respond(f"Generating:\n> {prompt}\n>> This will take a while.", ephemeral=True)
    try:
        data = {
            "version": "71996d331e8ede8ef7bd76eba9fae076d31792e4ddf4ad057779b443d6aea62f",
            "input": {
                "prompt": prompt,
                "width": width,
                "height": height,
                "seed": seed,
                "fps": fps,
                "model": model,
                "negative_prompt": "dust, noisy, washed out, ugly, distorted, broken",
                "num_frames": length,
                "num_inference_steps": steps
            }
        }
        headers = {
            "Authorization": f"Token {REPLICATE_TOKEN}",
            "Content-Type": "application/json"
        }
    
        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.replicate.com/v1/predictions", headers=headers, json=data) as response:
                response_data = await response.json()
                prediction_id = response_data["id"]
                prediction_url = f"https://api.replicate.com/v1/predictions/{prediction_id}"
            
                while True:
                    async with session.get(prediction_url, headers=headers) as prediction_response:
                        prediction_data = await prediction_response.json()
                        if prediction_data["status"] == "succeeded":
                            output = prediction_data["output"]
                            break
                        if prediction_data["status"] == "failed":
                            logs = prediction_data["logs"]
                            error = prediction_data["error"]
                            if len(logs) > 1500:
                                await ctx.respond(f"### The model failed generating. \n### Error: \n```{error}```\n### Settings: **{prompt}** | length: **{length}** | fps: **{fps}** | model: **{model}** | seed: **{seed}**{is_random} | steps: **{steps}**")
                            await ctx.respond(f"### The model failed generating. Here are the logs found:\n```{logs}```\n### Error: \n```{error}```")
                            return
                    await asyncio.sleep(2)
            image_url = output[0]
            async with session.get(image_url) as image_response:
                if image_response.status == 200:
                    image_data = await image_response.read()
                    final = discord.File(io.BytesIO(image_data), filename="video.mp4")
                    message = await ctx.respond(f"{ctx.user.mention} requested a video with these settings:\n> **{prompt}** | length: **{length}** | fps: **{fps}** | model: **{model}** | seed: **{seed}**{is_random} | steps: **{steps}**", file=final, view=DestroyUpscale())
                    video_settings.setdefault(str(message.id), {"prompt": prompt, "length": length, "fps": fps, "url": image_url})
                else:
                    await ctx.respond("Failed getting video... Please try again.")
    except Exception as error:
        await ctx.respond(f"Something went wrong: {error}. Please try again.", ephemeral=True)
        with open('errors.txt', 'a') as f:
            traceback.print_exc(file=f)


# --------- QR-CODES ---------
@bot.slash_command(name="qr-code", description="Generate a cool QR Code.")
@option(name="prompt", required=True, description="The prompt to guide the generation")
@option(name="content", required=True, description="URL or Content to point to")
@option(name="negative prompt", required=False, description="What to not generate")
@option(name="steps", required=False, description="Number of inferance steps", min_value=10, max_value=50)
@option(name="seed", min_value=0, required=False)
async def qr(
    ctx: discord.ApplicationContext,
    prompt: str,
    content: str,
    neg_prompt: str = "",
    steps: int = 40,
    seed: int = None,
):
    stats = {"stats": str(int((await loader.load_file(STATS_FILE)).get("stats", "0")) + 1)}
    await loader.save_file(stats, STATS_FILE)
    print(ctx.user)
    if not seed:
        seed = random.randint(0, 2147483647)
        is_random = " (random)"
    else:
        is_random = ""
    await ctx.respond(f"Generating:\n> {prompt}\n>> This will take a while.", ephemeral=True)
    try:
        data = {
            "version": "9cdabf8f8a991351960c7ce2105de2909514b40bd27ac202dba57935b07d29d4",
            "input": {
                "prompt": prompt,
                "qr_code_content": content,
                "seed": seed,
                "negative_prompt": neg_prompt,
                "num_inference_steps": steps
            }
        }
        headers = {
            "Authorization": f"Token {REPLICATE_TOKEN}",
            "Content-Type": "application/json"
        }
    
        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.replicate.com/v1/predictions", headers=headers, json=data) as response:
                response_data = await response.json()
                prediction_id = response_data["id"]
                prediction_url = f"https://api.replicate.com/v1/predictions/{prediction_id}"
            
                while True:
                    async with session.get(prediction_url, headers=headers) as prediction_response:
                        prediction_data = await prediction_response.json()
                        if prediction_data["status"] == "succeeded":
                            output = prediction_data["output"]
                            break
                        if prediction_data["status"] == "failed":
                            logs = prediction_data["logs"]
                            error = prediction_data["error"]
                            await ctx.respond(f"### The model failed generating. Here are the logs found:\n```{logs}```\n### Error: \n```{error}```")
                            return
                    await asyncio.sleep(2)
            image_url = output[0]
            async with session.get(image_url) as image_response:
                if image_response.status == 200:
                    image_data = await image_response.read()
                    final = discord.File(io.BytesIO(image_data), filename="qr_code.png")
                    await ctx.respond(f"{ctx.user.mention} requested a qr code with these settings:\n> **{prompt}** | content: **{content}** | negative prompt: **{neg_prompt}** | seed: **{seed}**{is_random} | steps: **{steps}**", file=final)
                else:
                    await ctx.respond("Failed getting image... Please try again.")
    except Exception as error:
        await ctx.respond(f"Something went wrong: {error}. Please try again.", ephemeral=True)
        with open('errors.txt', 'a') as f:
            traceback.print_exc(file=f)


# --------- UPSCALE ---------
@bot.slash_command(description="Upscale an image")
@option(name="image", required=False, description="The image to upscale")
@option(name="image_url", required=False, description="Same as image paramater, just url")
@option(name="scale", required=False, description="At what scale to upscale at", min_value=2, max_value=10)
@option(name="face_enhance", required=False, description="Enhance and fix faces")
async def upscale(
    ctx: discord.ApplicationContext,
    image: discord.Attachment,
    image_url: str = None,
    scale: int = 2,
    face_enhance: bool = False,
):
    if not image and not image_url:
        await ctx.respond("Please enter an image or image url.", ephemeral=True)
        return
    if image and image_url:
        await ctx.respond("Please only enter an image or an image url, not both.", ephemeral=True)
        return
    if image:
        image_url = image.url
    stats = {"stats": str(int((await loader.load_file(STATS_FILE)).get("stats", "0")) + 1)}
    await loader.save_file(stats, STATS_FILE)
    print(ctx.user)
    await ctx.respond("Generating...\n>> This will take a while.", ephemeral=True)
    try:
        data = {
            "version": "42fed1c4974146d4d2414e2be2c5277c7fcf05fcc3a73abf41610695738c1d7b",
            "input": {
                "image": image_url,
                "scale": scale,
                "face_enhance": face_enhance,
            }
        }
        headers = {
            "Authorization": f"Token {REPLICATE_TOKEN}",
            "Content-Type": "application/json"
        }
    
        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.replicate.com/v1/predictions", headers=headers, json=data) as response:
                response_data = await response.json()
                prediction_id = response_data["id"]
                prediction_url = f"https://api.replicate.com/v1/predictions/{prediction_id}"
            
                while True:
                    async with session.get(prediction_url, headers=headers) as prediction_response:
                        prediction_data = await prediction_response.json()
                        if prediction_data["status"] == "succeeded":
                            output = prediction_data["output"]
                            break
                        if prediction_data["status"] == "failed":
                            logs = prediction_data["logs"]
                            error = prediction_data["error"]
                            await ctx.respond(f"### The model failed generating. Here are the logs found:\n```{logs}```\n### Error: \n```{error}```")
                            return
                    await asyncio.sleep(2)
            async with session.get(image_url) as image_response:
                if image_response.status == 200:
                    image_data = await image_response.read()
                    #try:
                        #final = discord.File(io.BytesIO(image_data), filename="upscaled.png")
                        #await ctx.respond(f"{ctx.user.mention} requested an upscaled image with these settings:\n> scale: **{scale}** | face enhance: **{face_enhance}**", file=final)
                    #except discord.errors.HTTPException:
                    await ctx.respond(f"{ctx.user.mention} requested an upscaled image with these settings:\n> scale: **{scale}** | face enhance: **{face_enhance}**\n{output}")
                else:
                    await ctx.respond("Failed getting image... Please try again.")
    except Exception as error:
        await ctx.respond(f"Something went wrong: {error}. Please try again.", ephemeral=True)
        with open('errors.txt', 'a') as f:
            traceback.print_exc(file=f)

# --------- FORCE TXT ---------
@bot.slash_command(description="Get the previous response in a text file.")
async def forcetxt(ctx):
    user_settings = await loader.load_file(SETTINGS_FILE)
    if str(ctx.user.id) not in user_settings:
        await ctx.respond("There's nothing to send...", ephemeral=True)
        return
    if user_settings[str(ctx.user.id)]["last_use"] == "response":
        content = user_settings[str(ctx.user.id)]["last_msg"]['content']
        await sender.send(ctx, content, True, ctx.respond)
    elif user_settings[str(ctx.user.id)]["last_use"] == "info":
        content = user_settings[str(ctx.user.id)]["last_msg"]
        await sender.send(ctx, content, True, ctx.respond)
    elif user_settings[str(ctx.user.id)]["last_use"] == "drafts":
        drafts = await get_drafts(user_settings[str(ctx.user.id)]["last_msg"])
        await sender.send(ctx, drafts, True, ctx.respond)
    else:
        await ctx.respond("There's nothing to send...", ephemeral=True)


async def get_bard_response(chatbot):
    start_time = time.perf_counter()
    chatbot.ask("ping")
    end_time = time.perf_counter()
    bard_latency = (end_time - start_time) * 1000  # In milliseconds
    return bard_latency

# --------- BOT INFO ---------
@bot.slash_command(name="bot", description="Get bot info")
async def bot_info(ctx):
    api_latency = round(bot.latency * 1000, 2)
    stats = await loader.load_file(STATS_FILE)
    if "stats" in stats:
        stats = stats["stats"]
    else:
        stats = 0
    await ctx.respond(f"Pong! 🏓\nAPI Latency: {api_latency}ms\nBot Version: {version}\nUsages: {stats}\n\nNeed more help, want updates, or want to play with beta versions of this bot? Join the support server here: https://discord.gg/cNXUrgCDw9", ephemeral=True)

# --------- DRAFTS ---------
@bot.slash_command(description="Get Bard drafts.")
async def drafts(ctx):
    if str(ctx.user.id) in user_bards:
        user_settings = await loader.load_file(SETTINGS_FILE)
        user_settings[str(ctx.user.id)]["last_use"] = 'drafts'
        drafts = await get_drafts(user_settings[str(ctx.user.id)]["last_msg"])
        if str(ctx.user.id) not in user_settings:
            await ctx.respond("No drafts are avalible.", ephemeral=True)
            return
        if models.models["text_models"][user_settings[str(ctx.user.id)]["text_model"]]["type"] == "bard":
            await sender.send(ctx, drafts, False, ctx.respond)
        else:
            await ctx.respond("Drafts are only supported on the Bard model.", ephemeral=True)
    else:
        await ctx.respond("No drafts are avalible.", ephemeral=True)

# --------- IMAGES ---------
@bot.slash_command(name='images', description='Get images from Google Bard conversation')
async def get_images(ctx):
    try:
        user_settings = await loader.load_file(SETTINGS_FILE)
        data = user_settings[str(ctx.user.id)]["last_msg"]["images"]
        max_message_length = 2000
        if data:
            message = ""
            for url in data:
                temp_message = f"{message}\n{url}"
            
                if len(temp_message) > max_message_length:
                    await ctx.respond(message.strip())
                    message = url
                else:
                    message = temp_message
                
            if message:
                await ctx.respond(message.strip())
        else:
            await ctx.respond("No images found.", ephemeral=True)
    except Exception:
        await ctx.respond(f"No images found.", ephemeral=True)

# --------- HELP ---------
@bot.slash_command(description="Show help info.")
async def help(ctx):
    embed = discord.Embed(title="Bot Commands Help", color=0x3e9ac1)
    embed.description = (
        "**/help**: Shows this help message with information about available commands.\n"
        "\n"
        "**mention bot**: Just mention the bot using @bot_name to start talking with it.\n"
        "\n"
        "**/reset**: This command resets your conversation with the bot, "\
        "removing all context that it has remembered.\n"
        "\n"
        "**/info**: This command returns the entire API call for a given message.\n"
        "\n"
        "**/forcetxt**: Sends the previous message in a txt file.\n"
        "\n"
        "**/bot**: Get bot ping, version, and stats.\n"
        "\n"
        "**/drafts**: Get all 3 drafts.\n"
        "\n"
        "**/imagine**: Generate an image using Bing Image Creator, Kandinsky, SDXL, and more!\n"
        "\n"
        "**/audio**: Generate music with riffusion.\n"
        "\n"
        "**/upscale**: Upscale an image.\n"
        "\n"
        "**/qr-code**: Generate an AI designed QR Code.\n"
        "\n"
        "**/settings**: Change the default models for generations.\n"
        "\n"
        "**moderator commands**: /set_channel, /remove_channel. -- **WIP**"
        "\n"
        "UTF-8 encoded files can be used in chats.\n"
        "\n"
        "Need more help, want updates, or want to play with beta versions of this bot? Join the support server here: https://discord.gg/cNXUrgCDw9"
    )
    embed.set_footer(
        text="Please be careful!"
    )
    await ctx.respond("", embed=embed, ephemeral=True)


class TextSettingsView(discord.ui.View):
    @discord.ui.select(
        placeholder="Select a Text Model.",
        options=[
            discord.SelectOption(
                label=models.models["text_models"]["bard"]["showname"],
                description=models.models["text_models"]["bard"]["description"],
                value="bard"
            ),
            discord.SelectOption(
                label=models.models["text_models"]["chatgpt"]["showname"],
                description=models.models["text_models"]["chatgpt"]["description"],
                value="chatgpt"
            ),
            discord.SelectOption(
                label=models.models["text_models"]["gpt3"]["showname"],
                description=models.models["text_models"]["gpt3"]["description"],
                value="gpt3"
            ),
            discord.SelectOption(
                label=models.models["text_models"]["vicuna"]["showname"],
                description=models.models["text_models"]["vicuna"]["description"],
                value="vicuna"
            ),
            discord.SelectOption(
                label=models.models["text_models"]["alpaca"]["showname"],
                description=models.models["text_models"]["alpaca"]["description"],
                value="alpaca"
            ),
            discord.SelectOption(
                label=models.models["text_models"]["koala"]["showname"],
                description=models.models["text_models"]["koala"]["description"],
                value="koala"
            ),
            discord.SelectOption(
                label=models.models["text_models"]["llama"]["showname"],
                description=models.models["text_models"]["llama"]["description"],
                value="llama"
            ),
            discord.SelectOption(
                label=models.models["text_models"]["openAssistant"]["showname"],
                description=models.models["text_models"]["openAssistant"]["description"],
                value="openAssistant"
            ),
            discord.SelectOption(
                label=models.models["text_models"]["fastchat"]["showname"],
                description=models.models["text_models"]["fastchat"]["description"],
                value="fastchat"
            ),
            discord.SelectOption(
                label=models.models["text_models"]["claude"]["showname"],
                description=models.models["text_models"]["claude"]["description"],
                value="claude"
            ),
            discord.SelectOption(
                label=models.models["text_models"]["dolly"]["showname"],
                description=models.models["text_models"]["dolly"]["description"],
                value="dolly"
            ),
            discord.SelectOption(
                label=models.models["text_models"]["stablelm"]["showname"],
                description=models.models["text_models"]["stablelm"]["description"],
                value="stablelm"
            ),
            discord.SelectOption(
                label=models.models["text_models"]["falcon"]["showname"],
                description=models.models["text_models"]["falcon"]["description"],
                value="falcon"
            ),
        ],
    row=1)
    async def select_callback(self, select, interaction):
        user_settings = await loader.load_file(SETTINGS_FILE)
        user_settings[str(interaction.user.id)]["text_model"] = select.values[-1]
        await loader.save_file(user_settings, SETTINGS_FILE)
        await interaction.response.send_message(f"Set {models.models['text_models'][select.values[-1]]['showname']} as the default text model.", ephemeral=True)

    @discord.ui.select(
        placeholder="Select an Image Model.",
        options=[
            discord.SelectOption(
                label=models.models["img_models"]["bing"]["showname"],
                description=models.models["img_models"]["bing"]["description"],
                value="bing"
            ),
            discord.SelectOption(
                label=models.models["img_models"]["kandinsky"]["showname"],
                description=models.models["img_models"]["kandinsky"]["description"],
                value="kandinsky"
            ),
            discord.SelectOption(
                label=models.models["img_models"]["if"]["showname"],
                description=models.models["img_models"]["if"]["description"],
                value="if"
            ),
            discord.SelectOption(
                label=models.models["img_models"]["stable diffusion 1.5"]["showname"],
                description=models.models["img_models"]["stable diffusion 1.5"]["description"],
                value="firefly"
            ),
            discord.SelectOption(
                label=models.models["img_models"]["stable diffusion 2.1"]["showname"],
                description=models.models["img_models"]["stable diffusion 2.1"]["description"],
                value="stable diffusion"
            ),
            discord.SelectOption(
                label=models.models["img_models"]["dreamshaper"]["showname"],
                description=models.models["img_models"]["dreamshaper"]["description"],
                value="dreamshaper"
            ),
            discord.SelectOption(
                label=models.models["img_models"]["deliberate"]["showname"],
                description=models.models["img_models"]["deliberate"]["description"],
                value="deliberate"
            ),
            discord.SelectOption(
                label=models.models["img_models"]["SDXL"]["showname"],
                description=models.models["img_models"]["SDXL"]["description"],
                value="SDXL"
            ),
        ],
    row=2)
    async def second_select_callback(self, select, interaction):
        user_settings = await loader.load_file(SETTINGS_FILE)
        user_settings[str(interaction.user.id)]["img_model"] = select.values[-1]
        await loader.save_file(user_settings, SETTINGS_FILE)
        await interaction.response.send_message(f"Set {models.models['img_models'][select.values[-1]]['showname']} as the default image model.", ephemeral=True)
    
    @discord.ui.select(
        placeholder="Select an Audio Model.",
        options=[
            discord.SelectOption(
                label=models.models["audio_models"]["melody"]["showname"],
                description=models.models["audio_models"]["melody"]["description"],
                value="melody"
            ),
            discord.SelectOption(
                label=models.models["audio_models"]["large"]["showname"],
                description=models.models["audio_models"]["large"]["description"],
                value="large"
            ),
            discord.SelectOption(
                label=models.models["audio_models"]["riffusion"]["showname"],
                description=models.models["audio_models"]["riffusion"]["description"],
                value="riffusion"
            ),
            discord.SelectOption(
                label=models.models["audio_models"]["audioldm"]["showname"],
                description=models.models["audio_models"]["audioldm"]["description"],
                value="audioldm"
            ),
        ],
    row=3)
    async def third_select_callback(self, select, interaction):
        user_settings = await loader.load_file(SETTINGS_FILE)
        user_settings[str(interaction.user.id)]["audio_model"] = select.values[-1]
        await loader.save_file(user_settings, SETTINGS_FILE)
        await interaction.response.send_message(f"Set {models.models['audio_models'][select.values[-1]]['showname']} as the default audio model.", ephemeral=True)

    @discord.ui.select(
        placeholder="Select a Video Model.",
        options=[
            discord.SelectOption(
                label=models.models["video_models"]["567w"]["showname"],
                description=models.models["video_models"]["567w"]["description"],
                value="567w"
            ),
        ],
    row=4)
    async def fourth_select_callback(self, select, interaction):
        user_settings = await loader.load_file(SETTINGS_FILE)
        user_settings[str(interaction.user.id)]["video_model"] = select.values[-1]
        await loader.save_file(user_settings, SETTINGS_FILE)
        await interaction.response.send_message(f"Set {models.models['video_models'][select.values[-1]]['showname']} as the default audio model.", ephemeral=True)

# --------- SETTINGS ---------
@bot.slash_command(description="Change default models.")
async def settings(ctx):
    user_settings = await loader.load_file(SETTINGS_FILE)
    if str(ctx.user.id) not in user_settings:
        user_settings.setdefault(str(ctx.user.id), models.default_settings)
        await loader.save_file(user_settings, SETTINGS_FILE)
    currentText = models.models["text_models"][user_settings[str(ctx.user.id)]["text_model"]]["showname"]
    currentImg = models.models["img_models"][user_settings[str(ctx.user.id)]["img_model"]]["showname"]
    currentAudio = models.models["audio_models"][user_settings[str(ctx.user.id)]["audio_model"]]["showname"]
    currentVideo = models.models["video_models"][user_settings[str(ctx.user.id)]["video_model"]]["showname"]
    await ctx.respond(f"Feel free to click buttons\nCurrent Settings:\nText Model: **{currentText}**\nImage Model: **{currentImg}**\nAudio Model: **{currentAudio}**\nVideo Model: **{currentVideo}**", view=TextSettingsView(), ephemeral=True)

# --------- SERVERS ---------
@bot.slash_command(name="servers", description="Check what servers the bot is in. Owner only.")
@option(name='count-only')
@option(name='ephemeral')
async def servers_command(
    ctx: discord.ApplicationContext,
    count_only: bool = False,
    ephemeral: bool = False,
):
    if ctx.user.id == 775496919489052723:
        servers = list(bot.guilds)
        server_info = [
            f"{guild.name}, {guild.id}, {guild.me.nick}, {guild.member_count}"
            for guild in servers
        ]
        if count_only:
            await ctx.respond(
                embed=discord.Embed(
                    title=f"Connected on {str(len(servers))} servers",
                    color=0x3e9ac1,
            ),
            ephemeral=ephemeral,
        )
        else:
            await ctx.respond(
                embed=discord.Embed(
                    title=f"Connected on {str(len(servers))} servers",
                    description="\n".join(server_info),
                    color=0x3e9ac1,
                ),
                ephemeral=ephemeral,
            )
    else:
        await ctx.respond("You are not the owner...", ephemeral=True)

# --------- RESOURCES ---------
@bot.slash_command(name="resources", description="Check used resources. Owner only.")
@option(name='ephemeral')
async def resources(
    ctx: discord.ApplicationContext,
    ephemeral: bool=False
):
    if ctx.user.id == 775496919489052723:
        await ctx.respond(
            embed=discord.Embed(
                title="Resources Used:",
                description=f"Used CPU: {psutil.cpu_percent()}%\nUsed RAM: {psutil.virtual_memory().percent}%, {psutil.virtual_memory().used}",
                color=0x3e9ac1,
            ),
            ephemeral=ephemeral,
        )
    else:
        await ctx.respond("You are not the owner...", ephemeral=True)

# KILL
@bot.slash_command(name="kill", description="Kill bot. Owner only.")
@option(name='ephemeral')
async def kill_bot(
    ctx: discord.ApplicationContext,
    ephemeral: bool=True
):
    if ctx.user.id == 775496919489052723:
        await ctx.respond("Killing...", ephemeral=ephemeral)
        sys.exit()
    else:
        await ctx.respond("You are not the owner... why did you even try this?", ephemeral=True)

keep_alive()
bot.run(bot_token)