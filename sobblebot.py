"""
TODO list: 
hitdraft
add slabs for searcch?
error handling
have more auction settings?
improve hitdraft string comparisons
order hd results
check why my id isn't properly loaded from .env
fix heartbeat thing for spreadsheet https://stackoverflow.com/questions/65881761/discord-gateway-warning-shard-id-none-heartbeat-blocked-for-more-than-10-second
"""

import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
import asyncio
import math
import json

load_dotenv()
token = os.getenv('SOBBLE_BOT')
sobbleServerID = os.getenv('SOBBLE_SERVER_ID')
SCBServerID = os.getenv('SoCalBuddies_ID')

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
studio = discord.Object(id=sobbleServerID)

@client.event
async def on_ready():
    print('sobble is sobbing')
    await tree.sync()

@tree.command(name = "commands", description = "get a link to all of Sobble Bot's commands")
async def sendCommands(interaction: discord.Interaction):
    await interaction.response.send_message("https://docs.google.com/document/d/1SmirNxrlFgKY82UcYKx4N_gVhtkFbWUwakU1VFwvupY/edit?usp=sharing")

@tree.command(name = "kreggy", description = "craig chant", guild = discord.Object(id = SCBServerID))
async def kreggy(interaction: discord.Interaction):
    await interaction.response.send_message("If Kreggy has million number of fans I am one of them. If Kreggy has ten fans I am one of them. If Kreggy has no fans, that means I am no more on the earth. If word is against Kreggy, I am against the world. I love Kreggy till my last breath")

@tree.command(name = "auction", description = "start an auction: you have x seconds to put in a new bid, /command for full description")
async def startAuction(interaction: discord.Interaction, seconds: int, min_bid: int = 1, description: str = ""):
    from auction import Auction
    if description:
        desc_phrase = " for " + description
    else:
        desc_phrase = ""
    auction = Auction(seconds, min_bid, desc_phrase, interaction.channel, client.user)
    await interaction.response.send_message(f"The auction{auction.desc} has started. You must bid within {seconds} seconds of the last bid, else the auction ends. Enter a number to bid any amount or enter a period to bid the minimum bid")
    while auction.auctioning:
        try:
            task1 = asyncio.create_task(client.wait_for("message", check=auction.check, timeout=seconds))
            task2 = asyncio.create_task(auction.countdown(seconds))
            done, _ = await asyncio.wait({task1, task2}, return_when=asyncio.FIRST_COMPLETED)
            task2.cancel()
            for task in done:
                msg = task.result()
            if msg.content == ".":
                bid = auction.min_bid
            else:
                bid = int(msg.content)
            auction.highest_bidder = msg.author.display_name
            auction.current_bid = bid
            auction.min_bid = math.ceil(1.05 * bid)
            await interaction.channel.send(f"{auction.highest_bidder} has the highest bid (${auction.current_bid}). The minimum bid is now ${auction.min_bid}.")
            await asyncio.sleep(1)

        except asyncio.TimeoutError:
            auction.auctioning = False
            await interaction.channel.send(f"{auction.highest_bidder} has won the auction{auction.desc} with a bid of ${auction.current_bid}!")

@tree.command(name = "hitdraft", description = "start a hitdraft", guild = studio)
async def startHitDraft(interaction: discord.Interaction):
    await interaction.response.send_message("creating hitdraft")
    from hitdraft import HitDraft
    hd = HitDraft(interaction.channel)
    await hd.startup()

@tree.command(name = "tcgp", description = "lookup tcgplayer prices, /commands for full description")
async def tcgp(interaction: discord.Interaction, search: str, keywords: str = ""):
    await interaction.response.send_message("searching for price")
    from tcg import tcgpEmbed
    if not keywords:
        keywords = []
    else:
        keywords = keywords.split(', ')
    embeds = await tcgpEmbed(search, keywords)
    for embed in embeds:
        await interaction.channel.send(embed=embed)

@tree.command(name = "tcgr", description = "lookup tcgrepublic prices, /commands for full description")
async def tcgr(interaction: discord.Interaction, search: str, keywords: str = "", category: str = ""):
    await interaction.response.send_message("searching for price")
    from tcg import tcgrEmbed
    if not keywords:
        keywords = []
    else:
        keywords = keywords.split(', ')
    embeds = await tcgrEmbed(search, keywords, category)
    for embed in embeds:
        await interaction.channel.send(embed=embed)

@tree.command(name = "spreadsheet", description = "fill in spreadsheet with prices, /commands for full description")
async def sheet(interaction: discord.Interaction):
    from tcg import spreadsheet
    await interaction.response.send_message("working on it")
    await spreadsheet()
    await interaction.channel.send(f"{interaction.user.mention} done getting prices, use /resetspreadsheet when done")

@tree.command(name = "spreadsheetinput", description = "get cols A:E of spreadsheet", guild = studio)
async def getinputs(interaction: discord.Interaction):
    await interaction.response.send_message('getting spreadsheet input')
    from tcg import spreadsheetInput
    await spreadsheetInput()

@tree.command(name = "resetspreadsheet", description = "reset the price lookup google sheet, /commands for full description")
async def reset(interaction: discord.Interaction):
    await interaction.response.send_message('resetting')
    from tcg import resetSpreadsheet
    await resetSpreadsheet()
    await interaction.channel.send("spreadsheet has been reset")

@tree.command(name = "standing", description = "see your buddies points VIP standing")
async def getStanding(interaction: discord.Interaction, name: str):
    from SoCalBuddies import standing
    await standing(interaction, name)

client.run(token)