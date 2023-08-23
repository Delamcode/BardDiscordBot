import discord, io

async def send(message, response, force_text, respond):
    response = str(response)
    if len(response) <= 2000 and force_text == False:
        await respond(f"{response}")
    elif len(response)<= 4000 and force_text == False:
        embed = discord.Embed(title="AI Response", color=0x3e9ac1)
        embed.description = (response)
        embed.set_footer(text="This message was sent in an embed as it was too long.")
        await respond("", embed=embed)
    else:
        if force_text == True:
            error = "You have asked for a text file, so it is attached."
        else:
            error = "The response is too long, so I've attached it as a text file."
        try:
            file = io.StringIO(response)
            filetxt = discord.File(file, filename='response.txt')
            await respond(f"{error}", file=filetxt)
            file.close()
        except Exception:
            await respond("Something went wrong when attaching a file. Please try again.")