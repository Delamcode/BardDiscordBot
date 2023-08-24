import os
from dotenv import load_dotenv

load_dotenv()

models = {
    "text_models": {
        "bard": {
            "name": "bard",
            "showname": "Bard",
            "description": "The Google Bard model, connected to the internet.",
            "type": "bard",
            "key": os.environ['BARD_KEY'],
            "enabled": True,
        },
        "gpt3": {
            "name": "text-davinci-003",
            "showname": "GPT-3",
            "description": "OpenAI\'s older language model. Follows instructions well. Completion model only.",
            "type": "openai-completions",
            "url": "https://api.hypere.app/v1",
            "key": os.environ['FOX_KEY'],
            "enabled": True,
        },
        "chatgpt": {
            "name": "gpt-3.5-turbo",
            "showname": "ChatGPT",
            "description": "The normal and cheapest OpenAI language model.",
            "type": "openai",
            "url": "https://chimeragpt.adventblocks.cc/api/v1",
            "key": os.environ['CHIMERA_KEY'],
            "enabled": False,
        },
        "vicuna": {
            "name": "fastervicuna_13b",
            "showname": "Vicuna",
            "description": "A open-source language model with 90% of the quality of ChatGPT quality.",
            "type": "replicate",
            "url": "3a6afcc1c17c0384a559d6238b0fcac2483589aa689cee6abec98b1ddc648578",
            "key": os.environ['REPLICATE_TOKEN'],
            "enabled": True,
        },
        "alpaca": {
            "name": "alpace-13b",
            "showname": "Alpaca",
            "description": "A model fine-tuned from LLaMA on instruction-following demonstrations by Stanford.",
            "type": "openai",
            "url": "https://api.pawan.krd/v1",
            "key": os.environ['PAWAN_KEY'],
            "enabled": True,
        },
        "koala": {
            "name": "koala-13b",
            "showname": "Koala",
            "description": "A dialogue model for academic research by BAIR.",
            "type": "openai",
            "url": "https://api.pawan.krd/v1",
            "key": os.environ['PAWAN_KEY'],
            "enabled": True,
        },
        "llama": {
            "name": "llama13b-v2-chat",
            "showname": "LLaMa 2",
            "description": "A open and foundational language model by Meta, current best open source model.",
            "type": "replicate",
            "url": "df7690f1994d94e96ad9d568eac121aecf50684a0b0963b25a41cc40061269e5",
            "key": os.environ['REPLICATE_TOKEN'],
            "enabled": True,
        },
        "openAssistant": {
            "name": "oasst-pythia-12b",
            "showname": "Open Assistant",
            "description": "An Open Assistant for everyone by LAION.",
            "type": "openai",
            "url": "https://api.pawan.krd/v1",
            "key": os.environ['PAWAN_KEY'],
            "enabled": True,
        },
        "fastchat": {
            "name": "fastchat-t5-3b",
            "showname": "FastChat",
            "type": "openai",
            "description": "Another model",
            "url": "https://api.pawan.krd/v1",
            "key": os.environ['PAWAN_KEY'],
            "enabled": True,
        },
        "claude": {
            "name": "claude-2",
            "showname": "Claude 2",
            "type": "openai",
            "description": "Anthropics Claude 2 model with 100k tokens of context.",
            "url": "https://chimeragpt.adventblocks.cc/api/v1",
            "key": os.environ['CHIMERA_KEY'],
            "enabled": False,
        },
        "dolly": {
            "name": "dolly",
            "showname": "Dolly",
            "type": "replicate",
            "description": "Another model",
            "url": "ef0e1aefc61f8e096ebe4db6b2bacc297daf2ef6899f0f7e001ec445893500e5",
            "key": os.environ['REPLICATE_TOKEN'],
            "enabled": True
        },
        "stablelm": {
            "name": "stablelm",
            "showname": "StableLM",
            "type": "replicate",
            "description": "Another model",
            "url": "c49dae362cbaecd2ceabb5bd34fdb68413c4ff775111fea065d259d577757beb",
            "key": os.environ['REPLICATE_TOKEN'],
            "enabled": True,
        },
        "falcon": {
            "name": "falcon-40b-instruct",
            "showname": "Falcon 40b",
            "description": "One of the best opensource LLMs, incredibly slow.",
            "type": "replicate",
            "url": "7eb0f4b1ff770ab4f68c3a309dd4984469749b7323a3d47fd2d5e09d58836d3c",
            "key": os.environ['REPLICATE_TOKEN'],
            "enabled": True,
        },
    },

    "img_models": {
        "bing": {
            "showname": "Bing Image Creator",
            "id": "bing",
            "description": "Bing's image creator based on Dall-e 2.",
            "enabled": True,
        },
        "kandinsky": {
            "showname": "Kandinsky",
            "id": "kandinsky-r",
            "description": "A multilingual text2image latent diffusion model.",
            "enabled": True,
        },
        "if": {
            "showname": "Deepfloyd IF",
            "id": "if",
            "description": "A state-of-the-art text-to-image synthesis model, very good at text.",
            "enabled": True,
        },
        "imaginePy": {
            "showname": "ImaginePy",
            "description": "Unknown",
            "enabled": False,
        },
        "stable diffusion 1.5": {
            "showname": "Stable Diffusion 1.5",
            "id": "sd15",
            "description": "High-Resolution Image Synthesis with Latent Diffusion Models.",
            "enabled": True,
        },
        "stable diffusion 2.1": {
            "showname": "Stable Diffusion 2.1",
            "id": "sd21",
            "description": "High-Resolution Image Synthesis with Latent Diffusion Models.",
            "enabled": True,
        },
        "dreamshaper": {
            "showname": "Dreamshaper",
            "id": "dreamshaper",
            "description": "A high qaulity, stable diffusion based, model.",
            "enabled": True,
        },
        "deliberate": {
            "showname": "Deliberate",
            "id": "deliberate",
            "description": "Stable diffusion based model, good at details.",
            "enabled": True,
        },
        "SDXL": {
            "showname": "SDXL",
            "id": "sdxl",
            "description": "SDXL is a text-to-image generative AI model that creates beautiful images.",
            "enabled": True,
        },
    },
    "audio_models": {
        "riffusion": {
            "showname": "Riffusion",
            "description": "Low quality music generator using stable diffusion.",
            "enabled": True,
        },
        "audioldm": {
            "showname": "AudioLDM",
            "description": "High quality audio generator, good for SFX.",
            "enabled": True,
        },
        "melody": {
            "showname": "Meta MusicGen",
            "description": "High quality music generation model.",
            "enabled": True,
        },
        "large": {
            "showname": "Meta MusicGen Large",
            "description": "Highest quality music generation model, SLOW!",
            "enabled": True,
        },
    },
    "tts_models": {
        "elevenlabs": {
            "showname": "Eleven Labs",
            "enabled": False,
        },
        "google": {
            "showname": "Google TTS",
            "enabled": False,
        },
    },
    "video_models": {
        "xl": {
            "showname": "Zeroscope XL",
            "enabled": False,
            "description": "A txt2vid model made for upscaling. Not recommended.",
        },
        "567w": {
            "showname": "Zeroscope",
            "enabled": True,
            "description": "The best opensource txt2vid model.",
        },
        "potat1": {
            "showname": "Potat1",
            "enabled": False,
            "description": "Unknown",
        },
        "animov-512x": {
            "showname": "Animov",
            "enabled": False,
            "description": "Unknown",
        },
    },
}

default_settings = {
    "last_msg": None,
    "last_use": None,
    "img_model": "bing",
    "text_model": "bard",
    "audio_model": "melody",
    "tts_model": "google",
    "video_model": "567w",
    "context": [],
}