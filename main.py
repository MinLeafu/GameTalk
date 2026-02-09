import asyncio
import discord
from dotenv import load_dotenv
from discord.ext import commands
import os
import requests
import aiohttp

# Store user data (in production, use a database)
user_data = {}

class Person:
    def __init__(self, name="", age=0, games=None, location="", bio="", photo_url=None):
        self.name = name
        self.age = age
        self.games = games if games else []
        self.location = location
        self.bio = bio
        self.photo_url = photo_url

def get_location_by_ip():
    """Get location from IP address"""
    try:
        response = requests.get("https://ipinfo.io/json")
        data = response.json()
        
        if 'loc' in data:
            lat, lon = map(float, data['loc'].split(','))
            city = data.get('city', 'Unknown')
            country = data.get('country', 'Unknown')
            return lat, lon, city, country
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to the API: {e}")
        return None

async def download_photo(url, user_id):
    """Download and save user photo"""
    try:
        os.makedirs("user_photos", exist_ok=True)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    content_type = resp.headers.get('content-type', '')
                    ext = '.png'
                    if 'jpeg' in content_type or 'jpg' in content_type:
                        ext = '.jpg'
                    elif 'gif' in content_type:
                        ext = '.gif'
                    elif 'webp' in content_type:
                        ext = '.webp'
                    
                    filepath = f"user_photos/{user_id}{ext}"
                    with open(filepath, 'wb') as f:
                        f.write(await resp.read())
                    
                    return filepath
        return None
    except Exception as e:
        print(f"Error downloading photo: {e}")
        return None

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
    
    @bot.event
    async def on_ready():
        print(f'{bot.user} has connected to Discord!')

    @bot.command()
    async def send(ctx):
        """Send a message"""
        await ctx.send("FUCK YOU ALL")

    @bot.command()
    async def receive(ctx):
        """Send a message"""
        await ctx.send("I'm going to pound your ass")
    
    @bot.command()
    async def profile(ctx, member: discord.Member = None):
        """View a user's profile"""
        if member is None:
            member = ctx.author
        
        person = user_data.get(member.id)
        if person is None:
            await ctx.send(f"❌ No profile found for {member.display_name}. Use `!setup` or `!setprofile` to create one!")
            return
        
        # Create embed
        embed = discord.Embed(
            title=f"{person.name}'s Profile",
            color=discord.Color.blue()
        )
        embed.add_field(name="Age", value=str(person.age), inline=True)
        embed.add_field(name="Location", value=person.location, inline=True)
        embed.add_field(name="Games", value=", ".join(person.games), inline=False)
        
        if person.bio:
            embed.add_field(name="Bio", value=person.bio, inline=False)
        
        if person.photo_url:
            embed.set_thumbnail(url=person.photo_url)
        
        await ctx.send(embed=embed)
    
    @bot.command()
    async def setup(ctx):
        """Interactive profile setup - asks questions one by one"""
        try:
            await ctx.send("📝 **Let's set up your profile!**")
            
            # Ask for name
            await ctx.send("What is your name?")
            msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60.0)
            name = msg.content
            
            # Ask for age
            await ctx.send("What is your age?")
            msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60.0)
            try:
                age = int(msg.content)
            except ValueError:
                await ctx.send("Invalid age. Setting to 0.")
                age = 0
            
            # Ask for games
            await ctx.send("What games do you play? (separate with commas)")
            msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60.0)
            games = [game.strip() for game in msg.content.split(",")]
            
            # Get location
            location_data = get_location_by_ip()
            if location_data:
                location = f"{location_data[2]}, {location_data[3]}"
                await ctx.send(f"📍 Detected location: {location}")
            else:
                await ctx.send("What is your location?")
                msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60.0)
                location = msg.content
            
            # Ask for bio
            await ctx.send("Write something about yourself:")
            msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60.0)
            bio = msg.content
            
            # Ask for photo
            await ctx.send("**Upload a profile photo!** (attach an image or type 'skip' to skip)")
            msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=120.0)
            
            photo_url = None
            if msg.attachments:
                attachment = msg.attachments[0]
                if attachment.content_type and attachment.content_type.startswith('image/'):
                    saved_path = await download_photo(attachment.url, ctx.author.id)
                    if saved_path:
                        photo_url = attachment.url
                        await ctx.send("✅ Photo uploaded successfully!")
                    else:
                        await ctx.send("⚠️ Failed to save photo, continuing without it.")
                else:
                    await ctx.send("⚠️ That's not an image! Continuing without photo.")
            elif msg.content.lower() != 'skip':
                await ctx.send("⚠️ No image detected. Continuing without photo.")
            
            # Create person object
            person = Person(
                name=name,
                age=age,
                games=games,
                location=location,
                bio=bio,
                photo_url=photo_url
            )
            
            # Save to user_data
            user_data[ctx.author.id] = person
            
            # Show completed profile
            embed = discord.Embed(
                title=f"{person.name}'s Profile",
                color=discord.Color.green()
            )
            embed.add_field(name="Age", value=str(person.age), inline=True)
            embed.add_field(name="Location", value=person.location, inline=True)
            embed.add_field(name="Games", value=", ".join(person.games), inline=False)
            embed.add_field(name="Bio", value=person.bio, inline=False)
            
            if person.photo_url:
                embed.set_thumbnail(url=person.photo_url)
            
            await ctx.send("✅ **Profile setup complete!**", embed=embed)
            
        except asyncio.TimeoutError:
            await ctx.send("⏱️ Setup timed out. Please use `!setup` to try again.")
        except Exception as e:
            await ctx.send(f"❌ An error occurred: {e}")
    
    @bot.command()
    async def setprofile(ctx, name: str, age: int, location: str, *, games: str):
        """Quick profile setup: !setprofile Name Age Location Games,Separated,By,Commas"""
        games_list = [game.strip() for game in games.split(",")]
        
        person = Person(
            name=name,
            age=age,
            games=games_list,
            location=location
        )
        
        user_data[ctx.author.id] = person
        await ctx.send(f"✅ Profile created for {ctx.author.mention}!")
    
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
    async def deleteprofile(ctx):
        """Delete your profile"""
        if ctx.author.id in user_data:
            del user_data[ctx.author.id]
            await ctx.send("✅ Your profile has been deleted.")
        else:
            await ctx.send("❌ You don't have a profile to delete.")
    
    # Use environment variable for token
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("Error: DISCORD_TOKEN environment variable not set")
        return
    
    bot.run(token)

if __name__ == "__main__":
    main()