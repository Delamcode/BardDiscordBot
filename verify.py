import set, openai, os
from dotenv import load_dotenv
load_dotenv()
openai.api_key = os.environ['OPENAI_KEY']

async def verify(message, bot, allowed_guild_ids, allowed_channels, config,
                 filename):
    if message.author == bot.user or not message.guild:
        return False
    is_owner = await bot.is_owner(message.author)
    is_admin = message.channel.permissions_for(message.author).manage_channels
    x = await moderation(message)
    if x == True:
        return False
    if str(message.guild.id) in allowed_guild_ids and str(message.channel.id) in allowed_channels[str(message.guild.id)]:
        if message.content.startswith(("!set", "!remove_")):
            await message.reply("This guild and channel is already set!")
            return False
        return True
    elif not is_owner or not is_admin:
        if message.content.startswith(("!set", "!remove_")):
            await message.reply("You are not a admin or bot owner...")
        return False
    if (is_admin and message.content.startswith(
        ("!set_channel",
         "!remove_channel"))) or (is_owner and message.content.startswith(
             ("!set", "!remove_"))):
        ctx = await bot.get_context(message)
        if message.content.startswith("!set_channel"):
            await set.set_channel(ctx, allowed_guild_ids, allowed_channels, config, filename)
            return False
        elif message.content.startswith("!remove_channel"):
            await set.remove_set_channel(ctx, config)
            return False
        elif message.content.startswith(
                "!set"
        ) and is_owner and not message.content.startswith("!set_channel"):
            await set.set(ctx, allowed_guild_ids, config, filename)
            return False
        elif message.content.startswith("!remove_set") and is_owner:
            await set.remove_set(ctx, allowed_guild_ids, config)
            return False
        else:
            return False
    else:
        return False

async def moderation(message):
    y = await openai.Moderation.acreate(input=message.content)
    if y["results"][0]["flagged"] == True:
        await message.reply("This message violates our policies")
        return True