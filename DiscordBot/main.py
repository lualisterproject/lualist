import discord
from discord import app_commands
from discord.ext import commands
import discord.ui
from discord.ui import View, Button, Select
import requests
import logging
import json
import os


bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f"I am {bot.user}")

DATA_FILE = 'data.json'

def load_data():
    if not os.path.exists(DATA_FILE):
        return None
    with open(DATA_FILE, 'r') as file:
        data = json.load(file)
    return data

def save_data(data):
    with open(DATA_FILE, 'w') as file:
        json.dump(data, file, indent=4)
    logging.debug("Data saved: %s", json.dumps(data, indent=4))


# Set up

@bot.tree.command(name="SetUp", description="Set up an script")
@app_commands.describe(api_key="Api_Key")
async def script(interaction: discord.Interaction, api_key: str):
    guildid = interaction.guild_id
    data = load_data()
    setupendpoint = "http://127.0.0.1/setup"
    final_url = f"{setupendpoint}?guildid={guildid}&api_key={api_key}"
    r = requests.get(final_url)
    if r.status_code == 200:
        interaction.response.send_message(f"This server has been setted with the script", ephemeral=True)
    else:
        interaction.response.send_message("Pending", ephemeral=True)

# Whitelist

@bot.tree.command(name="whitelist")
@app_commands.describe(user="user")
@app_commands.describe(script_id="Script id")
async def whitelist(interaction: discord.Interaction, user: discord.Member, scriptid: str):
    userid = user.id
    author = interaction.user.id
    guild = interaction.guild_id
    enpoint = "http://127.0.0.1:5000/whitelist"
    finalurl = f"{enpoint}?{guild}&{userid}&{scriptid}&{author}"
    r = requests.get(finalurl)
    if r.status_code == 200:
        emb = discord.Embed(title="User whitelist", description="User whitelisted")
        await interaction.response.send_message(embed=emb)
    elif r.status_code == 408:
        emb = discord.Embed(title="User already whitelisted", description="User already whitelisted")
        await interaction.response.send_message(embed=emb)
    elif r.status_code == 403:
        emb = discord.Embed(title="Not perms", description="You dont have permissions to whitelist people")
        await interaction.response.send_message(embed=emb)
    else:
        await interaction.response.send_message("Pending")


@bot.tree.command(name="savepanel")
@app_commands.describe(scrptid="scriptid")
@app_commands.describe(panel_name="Panel name")
@app_commands.describe(description="panel description")
@app_commands.describe(script="script")
async def sendpanel(interaction: discord.Interaction, scriptid: str, panel_name: str, description: str, script: str):
    data = load_data()
    author = interaction.user.id
    guildid = interaction.guild_id
    r = requests.post(f"http://127.0.0.1:5000/check_contributors?{author}")
    if r.status_code == 200:
        new_panel = {
            "scriptid": scriptid,
            "guildid": str(guildid),
            "panelname": panel_name,
            "paneldescription": description,
            "script": script
        }
        data["panels"].append(new_panel)   
        save_data(data)
        await interaction.response.send_message("Saved", ephemeral=True)
    else:
        await interaction.response.send_message("You dont have permissions to run it", ephemeral=True)


@bot.tree.command(name="loadpanel")
@app_commands.describe(scriptid="scriptid")
async def loadpanel(interaction: discord.Interaction, scriptid: str):
    data = load_data()
    if not data:
        await interaction.response.send_message("Error: data.json file not found", ephemeral=True)
        return

    author = interaction.user.id
    r = requests.post(f"http://127.0.0.1:5000/check_contributors?userid={author}")
    if r.status_code != 200:
        await interaction.response.send_message("You are not a contributor", ephemeral=True)
        return

    if 'panels' in data:
        for panel in data['panels']:
            if panel.get('scriptid') == scriptid:
                panelname = panel.get('panelname', 'No panelname found')
                paneldescription = panel.get('paneldescription', 'No paneldescription found')
                
                emb = discord.Embed(title=panelname, description=paneldescription)
                button = Button(label="Get script", style=discord.ButtonStyle.green)
                button2 = Button(label="Reset HWID", style=discord.ButtonStyle.green)
                
                async def handle_reset_hwid(interaction):
                    user = interaction.user
                    userid = str(user.id)
                    r = requests.post(f"http://127.0.0.1:5000/reset_hwid?userid={userid}")
                    if r.status_code == 200:
                        await interaction.response.send_message("Reset HWID successfully", ephemeral=True)
                    else:
                        await interaction.response.send_message("Failed to reset HWID", ephemeral=True)
                
                async def handle_get_script(interaction):
                    user = interaction.user
                    userid = str(user.id)
                    guildid = str(interaction.guild.id)
                    r = requests.get(f"http://127.0.0.1:5000/check_whitelisted?userid={userid}&scriptid={scriptid}")
                    if r.status_code == 200:
                        data = r.json()
                        scriptkey = data.get("scriptkey")
                        loadstring = panel.get("script", "")
                        await interaction.followup.send(f"```local scriptid = '{scriptid}'\nlocal scriptkey = '{scriptkey}'\n{loadstring}```", ephemeral=True)        
                    else:
                        await interaction.response.send_message("User is not whitelisted for the provided script", ephemeral=True)
                
                button.callback = handle_get_script
                button2.callback = handle_reset_hwid
                
                view = View(timeout=None)
                view.add_item(button)
                view.add_item(button2)
                
                await interaction.response.send_message(embed=emb, view=view)
                return
        
        await interaction.response.send_message("No panel found with the provided scriptid", ephemeral=True)

@bot.tree.command(name="force-resethwid")
@app_commands.describe(user="User")
async def reset_hwid(interaction: discord.Interaction, user: discord.Member):
    authot = interaction.user
    userid = user.id
    guildid = str(interaction.guild.id)
    await interaction.response.defer()

    data = load_data()
    scriptid = None

    for guild in data.get("guilds", []):
        if guild.get("guildid") == guildid:
            scriptid = guild.get("scriptid")
            break

    if not scriptid:
        await interaction.followup.send("Error: No script found for the provided guildid.")
        return

    check_url = f"http://127.0.0.1/check_contributor?userid={authot}&scriptid={scriptid}"
    check_response = requests.post(check_url)
    
    if check_response.status_code == 200:
        reset_url = f"http://127.0.0.1/force-resethwid?userid={userid}"
        reset_response = requests.post(reset_url)
        
        if reset_response.status_code == 200:
            await interaction.followup.send("HWID reset successfully.")
        else:
            await interaction.followup.send(f"Failed to reset HWID: {reset_response.json().get('error', 'Unknown error')}")
    elif check_response.status_code == 403:
        await interaction.followup.send("Error: You do not have permission to reset the HWID for this script.")
    elif check_response.status_code == 404:
        await interaction.followup.send("Error: No script found for the provided scriptid.")
    else:
        await interaction.followup.send(f"Failed to check permissions: {check_response.json().get('error', 'Unknown error')}")

bot.run("")