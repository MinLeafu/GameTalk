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
    
    @bot.command()
    async def send(ctx):
        """Send a message"""
        await ctx.send("FUCK YOU ALL")
    
    @bot.command()
    async def compare(ctx, member: discord.Member):
        """Compare your profile with another user"""
        user1 = user_data.get(ctx.author.id)
        user2 = user_data.get(member.id)
        
        if not user1 or not user2:
            await ctx.send("❌ Both users need profiles to compare!")
            return
        
        common_games = set(user1.games) & set(user2.games)
        age_diff = abs(user1.age - user2.age)
        
        embed = discord.Embed(
            title=f"Comparison: {user1.name} vs {user2.name}",
            color=discord.Color.purple()
        )
        embed.add_field(name="Common Games", value=", ".join(common_games) if common_games else "None", inline=False)
        embed.add_field(name="Age Difference", value=f"{age_diff} years", inline=True)
        
        await ctx.send(embed=embed)
    
    @bot.command()
    async def setprofile(ctx, name: str, age: int, location: str, *, games: str):
        """Set your profile: !setprofile Name Age Location Games,Separated,By,Commas"""
        games_list = [game.strip() for game in games.split(",")]
        
        person = Person(
            name=name,
            age=age,
            games=games_list,
            location=location
        )
        
        user_data[ctx.author.id] = person
        await ctx.send(f"✅ Profile created for {ctx.author.mention}!")
    
    # Use environment variable for token
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("Error: DISCORD_TOKEN environment variable not set")
        return
    
    bot.run(token)

if __name__ == "__main__":
    main()