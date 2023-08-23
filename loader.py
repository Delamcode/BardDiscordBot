import json, requests

async def load_file(filename):
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

async def save_file(dict, filename):
    with open(filename, 'w') as file:
        json.dump(dict, file)

async def attach_get(message):
    attached_all = ""
    attachments = []
    # Add images
    if message.attachments:
        for attachment in message.attachments:
            attached = requests.get(attachment.url)
            try:
                decoded = attached.content.decode('utf-8')
                attachments.append(f"File \"{attachment.filename}\" is attached: {decoded} End of file \"{attachment.filename}\"")
            except UnicodeDecodeError:
                pass
        attached_all = ''.join(attachments)
        return attached_all