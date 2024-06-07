import discord
import requests
from discord.ext import commands
from discord import app_commands
import io
from decouple import config

# Replace with your bot token
BOT_TOKEN = config('BOT_MANAGER_TOKEN')

END_POINT = "http://127.0.0.1"
# Replace with your API endpoint URL

# Additional code to insert into Lua functions

bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f"Bot is ready as {bot.user}")


@bot.tree.command(name="createscript", description="Create script")
@app_commands.describe(name="name")
async def create_script(interaction: discord.Interaction, name: str, attachment: discord.Attachment):
    url = f"{END_POINT}/create_and_obfuscate"
    owner_userid = interaction.user.id
    params = {'owner_userid': owner_userid, 'name': name}

    file_data = await file.read()
    files = {'file': (file.filename, file_data)}
    
    response = requests.post(url, data=params, files=files)
    
    if response.status_code == 200:
        json_response = response.json()
        script_id = json_response.get('script_id')
        api_key = json_response.get('api_key')
        
        obfuscated_file = response.content
        file = discord.File(io.BytesIO(obfuscated_file), filename=f"{name}.obfuscate.lua")
        
        await interaction.followup.send(
            f"Script created successfully!\nScript ID: {script_id}\nAPI Key: {api_key}",
            file=file
        )
    else:
        await interaction.followup.send("There was an error creating and obfuscating the script.")
        
@bot.tree.command(name="addcontributors")
@app_commands.describe(contributorid="contributor userid")
@app_commands.describe(scriptid="script id")
async def add_contributors(interaction: discord.Interaction, contributorid: str, scriptid: str):
    owner_userid = interaction.user.id
    await interaction.response.defer()
    url = f"{END_POINT}/add_contributors?owner_userid={owner_userid}&contributor_userid={contributorid}&scriptid={scriptid}"
    response = requests.post(url)
    if response.status_code == 200:
        await interaction.followup.send("Contributor added successfully.")
    elif response.status_code == 400:
        await interaction.followup.send("Error: owner_userid, contributor_userid, and scriptid parameters are required.")
    elif response.status_code == 409:
        await interaction.followup.send("Error: Contributor already exists for this script.")
    elif response.status_code == 404:
        await interaction.followup.send("Error: No script found for the provided scriptid and owner_userid.")
    else:
        await interaction.followup.send("An error occurred while adding the contributor.")


@bot.tree.command(name="register")
async def register(interaction: discord.Interaction):
    user = interaction.user
    userid = user.id
    url = f"{END_POINT}/register?username={user}&userid={userid}"
    r = requests.post(url)
    if r.status_code == 200:
        data = r.json()
        apikey = data.get('apikey')
        emb = discord.Embed(title="Registered succeful", description=f"Registered sucelful\nAPI KEY:{apikey}")
        await interaction.response.send_message(embed=emb)
    else:
        await interaction.response.send_message("Error Registering")


bot.run(BOT_TOKEN)
