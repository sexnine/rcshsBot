import asyncio
from typing import overload
import nextcord
from nextcord.ext import commands
from pymongo import MongoClient, collection
from ruamel.yaml import YAML
import vacefron
import os
import re

MONGODB_URI = "" # MongoDB URL
COLLECTION = "levelling"
DB_NAME = "discord"

cluster = MongoClient(MONGODB_URI)
levelling = cluster[COLLECTION][DB_NAME]

# Reads the config file
yaml = YAML()
with open("Configs/config.yml", "r", encoding="utf-8") as file:
    config = yaml.load(file)
with open("Configs/holidayconfig.yml", "r", encoding="utf-8") as file2:
    holidayconfig = yaml.load(file2)

# Vac-API
vac_api = vacefron.Client()

class levelsys(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(self, ctx):
        if not ctx.author.bot:
            stats = levelling.find_one({"guildid": ctx.guild.id, "id": ctx.author.id})
            serverstats = levelling.find_one({"server": ctx.guild.id})
            bot_stats = levelling.find_one({"bot_name": self.bot.user.name})

            # Check if prefix is in the message
            if config['Prefix'] in ctx.content:
                stats = levelling.find_one({"guildid": ctx.guild.id, "id": ctx.author.id})
                xp = stats['xp']
                levelling.update_one({"guildid": ctx.guild.id, "id": ctx.author.id}, {"$set": {"xp": xp}})
            
            else:
                user = ctx.author
                role = nextcord.utils.get(ctx.guild.roles, name=serverstats["double_xp_role"])
                
                # Check if the length of talk channels is greater than 0
                talk_channels = serverstats['ignored_channels']
                if len(talk_channels) > 0 and ctx.channel.id not in talk_channels:
                    if role in user.roles:
                        stats = levelling.find_one({"guildid": ctx.guild.id, "id": ctx.author.id})
                        xp = stats['xp'] + serverstats['xp_per_message'] * 2
                        levelling.update_one({"guildid": ctx.guild.id, "id": ctx.author.id}, {"$set": {"xp": xp}})

                    else:
                        stats = levelling.find_one({"guildid": ctx.guild.id, "id": ctx.author.id})
                        xp = stats['xp'] + serverstats['xp_per_message']
                        levelling.update_one({"guildid": ctx.guild.id, "id": ctx.author.id}, {"$set": {"xp": xp}})
                
                elif len(talk_channels) < 1 or ctx.channel.id in talk_channels:
                    if role in user.roles:
                        stats = levelling.find_one({"guildid": ctx.guild.id, "id": ctx.author.id})
                        xp = stats["xp"] + serverstats['xp_per_message'] * 2
                        levelling.update_one({"guildid": ctx.guild.id, "id": ctx.author.id}, {"$set": {"xp": xp}})
                    else:
                        stats = levelling.find_one({"guildid": ctx.guild.id, "id": ctx.author.id})
                        xp = stats["xp"]
                        levelling.update_one({"guildid": ctx.guild.id, "id": ctx.author.id}, {"$set": {"xp": xp}})
                
                elif len(talk_channels) < 1 or ctx.channel.id in talk_channels:
                    if role in user.roles:
                        stats = levelling.find_one({"guildid": ctx.guild.id, "id": ctx.author.id})
                        xp = stats["xp"] + serverstats['xp_per_message'] * 2
                        levelling.update_one({"guildid": ctx.guild.id, "id": ctx.author.id}, {"$set": {"xp": xp}})
                    else:
                        stats = levelling.find_one({"guildid": ctx.guild.id, "id": ctx.author.id})
                        xp = stats['xp'] + serverstats['xp_per_message']
                        levelling.update_one({"guildid": ctx.guild.id, "id": ctx.author.id}, {"$set": {"xp": xp}})
                
                if bot_stats['event_state'] is True:
                    stats = levelling.find_one({"guildid": ctx.guild.id, "id": ctx.author.id})
                    xp = stats['xp'] + serverstats['xp_per_message'] * holidayconfig['bonus_xp']
                    levelling.update_one({"guildid": ctx.guild.id, "id": ctx.author.id}, {"$set": {"xp": xp}})

            xp = stats['xp']
            lvl = 0
            while True:
                if xp < ((config['xp_per_level'] / 2 * (lvl ** 2)) + (config['xp_per_level'] / 2 * lvl)):
                    break
                lvl += 1
            
            xp -= ((config['xp_per_level'] / 2 * ((lvl - 1) ** 2)) + (config['xp_per_level'] / 2 * (lvl - 1)))

            if stats['xp'] < 0:
                levelling.update_one({"guildid": ctx.guild.id, "id": ctx.author.id}, {"$set": {"xp": 0}})
            
            if stats['rank'] != lvl:
                levelling.update_one({"guildid": ctx.guild.id, "id": ctx.author.id}, {"$set": {"rank": lvl + 1}})
                embed2 = nextcord.Embed(title=f":tada: **LEVEL UP!**",
                                        description=f"{ctx.author.mention} just reached Level: **{lvl}**",
                                        color=config['embed_color'])
                
                xp = stats['xp']
                levelling.update_one({"guildid": ctx.guild.id, "id": ctx.author.id},
                                        {"$set" :{"rank": lvl, "xp": xp + serverstats['xp_per_message'] * 2}})
                
                print(f"User: {ctx.author} | Leveled UP To: {lvl}")
                
                embed2.add_field(name="Next Level:",
                                value=f"`{int(config['xp_per_level'] * 2 * ((1 / 2) * lvl))}xp`")
                embed2.set_thumbnail(url=ctx.author.avatar.url)
                
                member = ctx.author
                channel = nextcord.utils.get(member.guild.channels, name=serverstats['level_channel'])
                
                if channel is None:
                    return
                
                if config['level_up_ping'] is True:
                    await channel.send(f"{ctx.author.mention},")
                
                msg = await channel.send(embed=embed2)
                level_roles = serverstats['role']
                level_roles_num = serverstats['level']
                
                for i in range(len(level_roles)):
                    if lvl == int(level_roles_num[i]):
                        await ctx.author.add_roles(nextcord.utils.get(ctx.author.guild.roles, name=level_roles[i]))
                        embed2.add_field(name="Role Unlocked", value=f"`{level_roles[i]}`")
                        
                        print(f"User: {ctx.author} | Unlocked Role: {level_roles[i]}")
                        embed2.set_thumbnail(url=ctx.author.avatar.url)
                        
                        await msg.edit(embed=embed2)
                        
                        # remove the previous role
                        if i > 0:
                            await ctx.author.remove_roles(nextcord.utils.get(ctx.author.guild.roles, name=level_roles[i - 1]))
                        
                        else:
                            continue
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await asyncio.sleep(1.5)
        serverstats = levelling.find_one({"server": guild.id})
        
        if serverstats is None:
            
            if guild.system_channel is None:
                levelchannel = "Private"
            else:
                levelchannel = guild.system_channel.name
            
            newserver = {"server": guild.id, "xp_per_message": 10, "double_xp_role": "None",
                        "level_channel": levelchannel,
                        "Antispam": False, "mutedRole": "None", "mutedTime": 300, "warningMessages": 5,
                        "muteMessages": 6,
                        "ignoredRole": "None", "event": "Ended", "ignored_channels": []}
            levelling.insert_one(newserver)

            if config['private_message'] is True:
                overwrites = {
                    guild.default_role: nextcord.PermissionOverwrite(read_messages=False),
                    guild.me: nextcord.PermissionOverwrite(read_messages=True)
                }
                
                prefix = config['Prefix']
                embed= nextcord.Embed(title=f"👋 // Greetings, {guild.name}", description=f"Thanks for inviting me, my prefix here is: `{prefix}`")
                
                if os.path.exists("Addons/Extras+.py") is True:
                    embed.add_field(name="🚀 | What's Next?",
                                    value=f"`{prefix}help` displays every command you need to know for {self.bot.user.mention}",
                                    inline=False)
                embed.add_field(name="🧭 | Important Links:",
                                value=f" - Get support for {self.bot.user.mention}")
                
                if guild.system_channel is None:
                    await guild.create_text_channel('private', overwrites=overwrites)
                    channel = nextcord.utils.get(guild.channels, name="private")
                    
                    if channel is None:
                        return
                    
                    await channel.send(embed=embed)
                
                else:
                    await guild.system_channel.send(embed=embed)
        
        # Didn't work that's why I added add_members
        for member in guild.members:
            if not member.bot:
                serverstats = levelling.find_one({"server": guild.id})
                newuser = {"guildid": member.guild.id, "id": member.id, "tag": f"<@{member.id}>",
                            "xp": serverstats['xp_per_message'],
                            "rank": 1, "background": " ", "circle": False, "xp_color": "#ffffff", "warnings": 0,
                            "name": str(member)}
                levelling.insert_one(newuser)
                print(f"User: {member.id} has been added to the database!")

    @commands.command(name="add_members")
    async def add_members(self, ctx):
        guild = ctx.guild
        for member in guild.members:
            if not member.bot:
                serverstats = levelling.find_one({"server": guild.id})
                newuser = {"guildid": member.guild.id, "id": member.id, "tag": f"<@{member.id}>",
                            "xp": serverstats['xp_per_message'],
                            "rank": 1, "background": " ", "circle": False, "xp_color": "#ffffff", "warnings": 0,
                            "name": str(member)}
                levelling.insert_one(newuser)
                print(f"User: {member.id} has been added to the database!")
        

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        # Removes the server from the database
        levelling.delete_one({"server": guild.id})

        # Deletes all users when the bot is removed from the server
        for member in guild.members:
            if not member.bot:
                levelling.delete_one({"guildid": guild.id, "id": member.id})
                print(f"User: {member.id} has been removed from the database!")
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        if not member.bot:
            await asyncio.sleep(1.5)
            
            serverstats = levelling.find_one({"server": member.guild.id})
            economy_stats = levelling.find_one({"guildid": member.guild.id, "id": member.id, "money" :{"$exists": True}})
            
            if economy_stats:
                user = f"<@{member.id}>"
                levelling.update_one({"guildid": member.guild.id, "id": member.id}, {
                    "$set": {"tag": user, "xp": serverstats['xp_per_message'], "rank": 1, "background": " ",
                             "circle": False, "xp_color": "#ffffff", "name": f"{member}", "warnings": 0}})
            
            else:
                getGuild = levelling.find_one({"server": member.guild.id})
                newuser = {
                    "guildid": member.guild.id, "id": member.id, "tag": f"<@{member.id}>",
                    "xp": getGuild['xp_per_message'],
                    "rank": 1, "background": " ", "circle": False, "xp_color": "#ffffff", "warnings": 0,
                    "name": str(member)
                }

                levelling.insert_one(newuser)

                print(f"User: {member.id} has been added to the database!")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if not member.bot:
            levelling.delete_one({"guildid": member.guild.id, "id": member.id})
            print(f"User: {member.id} has been removed from the database!")

def setup(bot):
    bot.add_cog(levelsys(bot))