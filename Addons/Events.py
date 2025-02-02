import asyncio
import os
import random
import re
import time

import nextcord
from nextcord.ext import commands, tasks
from ruamel.yaml import YAML

import Libs.get
from Systems.levelsys import levelling

# Reads the config file, no need for changing.
yaml = YAML()
with open("Configs/events.yml", "r", encoding="utf-8") as file:
    config = yaml.load(file)


class Events(commands.Cog):
    def __init__(self, client):
        self.client = client

def setup(client):
    client.add_cog(Events(client))


    @tasks.loop(minutes=int(config['time']))
    async def e():
        activeservers = client.guilds
        for guild in activeservers:
            event = random.choice(['reaction', 'maths', 'unscramble'])

            if event == "reaction":
                emoji = random.choice(config['reaction_emoji'])
                embed = nextcord.Embed(description=f"**Click the selected emoji in the fastest time to win!**")
                serverstats = levelling.find_one({"server": guild.id})
                channel = nextcord.utils.get(guild.channels, name="😝-fun")
                if channel is None:
                    continue
                message = await channel.send(embed=embed)
                await asyncio.sleep(4)
                for x in config['reaction_emoji']:
                    await message.add_reaction(x)
                for i in reversed(range(1, 4)):
                    await message.edit(embed=nextcord.Embed(description=str(f"**{i}**")))
                    await asyncio.sleep(1)
                await message.edit(embed=nextcord.Embed(description=f"**Click** {emoji} **NOW!**"))
                start = time.perf_counter()
                try:
                    _, user = await client.wait_for(
                        "reaction_add",
                        check=lambda _reaction, user: _reaction.message.guild == guild
                                                      and _reaction.message.channel == channel
                                                      and _reaction.message == message and str(
                            _reaction.emoji) == emoji and user != client.user
                                                      and not user.bot,
                        timeout=config['reaction_event_length'])
                    end = time.perf_counter()
                    await message.edit(embed=nextcord.Embed(
                        description=f"**{user}** clicked {emoji} in `{end - start:.3f}` seconds and earned `{config['reaction_xp']}xp`!"))
                    stats = levelling.find_one({"guildid": guild.id, "id": user.id})
                    xp = stats['xp']
                    levelling.update_one({"guildid": guild.id, "id": user.id}, {"$set": {"xp": xp + config['reaction_xp']}})

                    for x in config['reaction_emoji']:
                        await message.remove_reaction(x, client.user)
                        await message.clear_reaction(x)

                except asyncio.TimeoutError:
                    await message.edit(embed=nextcord.Embed(
                        description=f"*No one clicked the* `{emoji}` emoji!"))
                    await asyncio.sleep(5)

            elif event == "unscramble":
                word = random.choice(config['word_list'])
                scrambled = str(random.sample(word, len(word))).replace('[', '').replace(']', '').replace(',',
                                                                                                          '').replace(
                    ' ', '').replace("'", '')
                if config['case_sensitive'] is False:
                    word = word
                else:
                    word = word.lower()
                embed = nextcord.Embed(description=f"**Unscramble the word in the fastest time to win!**")
                serverstats = levelling.find_one({"server": guild.id})
                channel = nextcord.utils.get(guild.channels, name="😝-fun")
                if channel is None:
                    continue
                message = await channel.send(embed=embed)
                await asyncio.sleep(4)
                for i in reversed(range(1, 4)):
                    await message.edit(embed=nextcord.Embed(description=str(f"**{i}**")))
                    await asyncio.sleep(1)
                await message.edit(embed=nextcord.Embed(description=f"**UNSCRAMBLE THE WORD:** `{scrambled}` **NOW!**"))
                start = time.perf_counter()

                def check(m):
                    if config['case_sensitive'] is False:
                        if m.content == word and m.channel == channel:
                            return m.author
                    else:
                        if m.content == word.lower() and m.channel == channel:
                            return m.author

                try:
                    user = await client.wait_for(
                        "message",
                        check=check,
                        timeout=config['unscramble_event_length'])
                    end = time.perf_counter()
                    await user.add_reaction("✅")
                    await message.edit(embed=nextcord.Embed(
                        description="**{.author}** ".format(
                            user) + f" unscrambled `{word}` in `{end - start:.3f}` seconds and earned `{config['unscramble_xp']}xp`!"))
                    stats = levelling.find_one({"guildid": guild.id, "id": int("{.author.id}".format(user))})
                    xp = stats['xp']
                    levelling.update_one({"guildid": guild.id, "id": int("{.author.id}".format(user))},
                                         {"$set": {"xp": xp + config['unscramble_xp']}})

                except asyncio.TimeoutError:
                    await message.edit(embed=nextcord.Embed(
                        description=f"*No one got it right! The word was* `{word}!`"))
                    await asyncio.sleep(10)

            elif event == "maths":
                maths_1 = random.randint(100, 200)
                maths_2 = random.randint(1, 100)
                maths_type = random.choice(config['operators'])
                equation = f"{maths_1}{maths_type}{maths_2}"
                answer = (round(eval(equation)))
                
                embed = nextcord.Embed(description=f"**Solve the equation in the fastest time to win!**")
                
                serverstats = levelling.find_one({"server": guild.id})
                channel = nextcord.utils.get(guild.channels, name="😝-fun")
                
                if channel is None:
                    continue
                
                message = await channel.send(embed=embed)
                await asyncio.sleep(4)
                
                for i in reversed(range(1, 4)):
                    await message.edit(embed=nextcord.Embed(description=str(f"**{i}**")))
                    await asyncio.sleep(1)
                
                await message.edit(
                    embed=nextcord.Embed(description=f"**SOLVE:** `{maths_1} {maths_type} {maths_2}` **NOW!**"))
                
                start = time.perf_counter()

                def check(m):
                    if m.content == str(answer) and m.channel == channel:
                        return m.author

                try:
                    user = await client.wait_for(
                        "message",
                        check=check,
                        timeout=config['maths_event_length'])
                    end = time.perf_counter()
                    
                    await user.add_reaction("✅")
                    await message.edit(embed=nextcord.Embed(
                        description="**{.author}** ".format(
                            user) + f" Solved `{equation} = {answer}` in `{end - start:.3f}` seconds and earned `{config['maths_xp']}xp`!"))
                    
                    stats = levelling.find_one({"guildid": guild.id, "id": int("{.author.id}".format(user))})
                    xp = stats['xp']
                    levelling.update_one({"guildid": guild.id, "id": int("{.author.id}".format(user))},
                                         {"$set": {"xp": xp + config['maths_xp']}})

                except asyncio.TimeoutError:
                    await message.edit(embed=nextcord.Embed(
                        description=f"*No one got it right! The answer was* `{equation} = {answer}`"))
                    await asyncio.sleep(10)

    e.start()

