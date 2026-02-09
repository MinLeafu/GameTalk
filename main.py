import asyncio
import discord
from dotenv import load_dotenv
from discord.ext import commands
import os

# Store user data (in production, use a database)
user_data = {}

class Person:
    def __init__(self, name="", age=0, games=None, location="", bio=""):
        self.name = name
        self.age = age
        self.games = games if games else []
        self.location = location
        self.bio = bio

def clean_games(inp):
    return [game.lower().strip() for game in inp.split(",")]

def compare_games(a, b):
    common_games = set(a.games) & set(b.games)
    return len(common_games)

def compare_age(a, b):
    return a.age - b.age

def main():
    load_dotenv()

    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="!", intents=intents)
    
    @bot.command()
    async def profile(ctx, member: discord.Member = None):
        """Prints a user's stored info"""
        if member is None:
            member = ctx.author
        
        person = user_data.get(member.id)
        if person is None:
            await ctx.send(f"No info found for {member.display_name}.")
            return
        
        await ctx.send(
            f"**{person.name}'s Profile:**\n"
            f"Age: {person.age}\n"
            f"Games: {', '.join(person.games)}\n"
            f"Location: {person.location}"
        )
    
    # Use environment variable for token
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("Error: DISCORD_TOKEN environment variable not set")
        return
    
    bot.run(token)

if __name__ == "__main__":
    main()