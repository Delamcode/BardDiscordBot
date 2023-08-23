import asyncio, requests, dotenv
from concurrent.futures import Future
from dotenv import load_dotenv
import os
import openai
from Bard import AsyncChatbot
import sender
import loader
import models
import aiohttp

load_dotenv()

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
        msg_content = 'Hi Bard! Introduce yourself! Mention that you are a discord bot, and all your commands are in the </help:1131396431194902559> (help) command. Do not make stuff up about your capabillites as a discord bot. Only say that you are an AI powered bot with commands, as shown in </help:1131396431194902559>.'
    else:
        msg_content = message.content.replace(mention, '').strip()
    if attached_all:
        msg_content = f"{msg_content} ATTACHMENTS: {attached_all}"
    return msg_content

async def bard(message, user_bard, bot, SETTINGS_FILE):
    msg_content = await meta(message, bot)
    fullinfo = await user_bard.ask(msg_content)
    response = fullinfo['content']
    await message.remove_reaction("🕥", bot.user)
    await message.add_reaction("😸")
    user_settings = await loader.load_file(SETTINGS_FILE)
    user_settings[str(message.author.id)]["last_msg"] = fullinfo
    user_settings[str(message.author.id)]["last_use"] = "response"
    await loader.save_file(user_settings, SETTINGS_FILE)
    await sender.send(message, response, False, message.reply)

async def gpt(message, url, key, model, bot, SETTINGS_FILE):
    user_settings = await loader.load_file(SETTINGS_FILE)
    openai.api_key = key
    openai.api_base = url
    msg_content = await meta(message, bot)
    user_settings[str(message.author.id)]["context"].append({"role": "user", "content": msg_content})
    await loader.save_file(user_settings, SETTINGS_FILE)
    fullinfo = await openai.ChatCompletion.acreate(
        model=model,
        messages=user_settings[str(message.author.id)]["context"]
    )
    response = fullinfo.choices[0].message.content
    await message.remove_reaction("🕥", bot.user)
    await message.add_reaction("😸")
    user_settings = await loader.load_file(SETTINGS_FILE)
    user_settings[str(message.author.id)]["last_msg"] = fullinfo
    user_settings[str(message.author.id)]["last_use"] = "response"
    user_settings[str(message.author.id)]["context"].append(fullinfo.choices[0].message)
    await loader.save_file(user_settings, SETTINGS_FILE)
    await sender.send(message, response, False, message.reply)

async def gpt_completions(message, url, key, model, bot, SETTINGS_FILE):
    openai.api_key = key
    openai.api_base = url
    msg_content = await meta(message, bot)
    user_settings = await loader.load_file(SETTINGS_FILE)
    user_settings[str(message.author.id)]["context"].append({"role": "user", "content": msg_content})
    await loader.save_file(user_settings, SETTINGS_FILE)
    context=""
    for item in user_settings[str(message.author.id)]["context"]:
        role = item["role"]
        content = item["content"]
        context += f"{role.capitalize()}: {content}\n"
    fullinfo = await openai.Completion.acreate(
        model=model,
        max_tokens=500,
        prompt=f"System: You are a chatbot based on GPT-3.\n{context}\nAssistant:",
        stop="User:"
    )
    response = fullinfo.choices[0].text
    await message.remove_reaction("🕥", bot.user)
    await message.add_reaction("😸")
    user_settings = await loader.load_file(SETTINGS_FILE)
    user_settings[str(message.author.id)]["last_msg"] = fullinfo
    user_settings[str(message.author.id)]["last_use"] = "response"
    user_settings[str(message.author.id)]["context"].append({"role": "assistant", "content": response})
    await loader.save_file(user_settings, SETTINGS_FILE)
    await sender.send(message, response, False, message.reply)

async def replicate(message, bot, SETTINGS_FILE):
    user_settings = await loader.load_file(SETTINGS_FILE)
    msg_content = await meta(message, bot)
    data = {
        "version": models.models["text_models"][user_settings[str(message.author.id)]["text_model"]]["url"],
        "input": {
            "prompt": msg_content,
        }
    }
    headers = {
        "Authorization": f"Token {models.models['text_models'][user_settings[str(message.author.id)]['text_model']]['key']}",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.replicate.com/v1/predictions", headers=headers, json=data) as response:
            response_data = await response.json()
            prediction_id = response_data["id"]
            prediction_url = f"https://api.replicate.com/v1/predictions/{prediction_id}"
        
            while True:
                async with session.get(prediction_url, headers=headers) as prediction_response:
                    fullinfo = await prediction_response.json()
                    if fullinfo["status"] == "succeeded":
                        response = fullinfo["output"]
                        response = ''.join(response)
                        break
                    if fullinfo["status"] == "failed":
                        logs = fullinfo["logs"]
                        error = fullinfo["error"]
                        await message.reply(f"### The model failed generating. Here are the logs found:\n```{logs}```\n### Error: \n```{error}```")
                        return
                await asyncio.sleep(2)
            await message.remove_reaction("🕥", bot.user)
            await message.add_reaction("😸")
            user_settings = await loader.load_file(SETTINGS_FILE)
            user_settings[str(message.author.id)]["last_msg"] = fullinfo
            user_settings[str(message.author.id)]["last_use"] = "response"
            await loader.save_file(user_settings, SETTINGS_FILE)
            await sender.send(message, response, False, message.reply)