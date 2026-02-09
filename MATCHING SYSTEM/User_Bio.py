import discord
from discord.ext import commands
import requests
import os
import aiohttp
import asyncio

def get_location_by_ip():
    try:
        # Send a request to an IP geolocation API
        response = requests.get("https://ipinfo.io/json")
        data = response.json()

        if 'loc' in data:
            # Extract latitude and longitude
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
        # Create directory if it doesn't exist
        os.makedirs("user_photos", exist_ok=True)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    # Get file extension from content type
                    content_type = resp.headers.get('content-type', '')
                    ext = '.png'
                    if 'jpeg' in content_type or 'jpg' in content_type:
                        ext = '.jpg'
                    elif 'gif' in content_type:
                        ext = '.gif'
                    elif 'webp' in content_type:
                        ext = '.webp'
                    
                    # Save file
                    filepath = f"user_photos/{user_id}{ext}"
                    with open(filepath, 'wb') as f:
                        f.write(await resp.read())
                    
                    return filepath
        return None
    except Exception as e:
        print(f"Error downloading photo: {e}")
        return None

class UserBio():
    def __init__(self):
        self.user_name = None
        self.user_age = 0
        self.user_games = None
        self.location = None
        self.user_bio = None
        self.photo_url = None  # New field for photo
    
    async def setdata(self, ctx, bot):
        """Interactive setup using Discord messages"""
        
        # Ask for name
        await ctx.send("What is your name?")
        msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60.0)
        self.user_name = msg.content
        
        # Ask for age
        await ctx.send("What is your age?")
        msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60.0)
        try:
            self.user_age = int(msg.content)
        except ValueError:
            await ctx.send("Invalid age. Setting to 0.")
            self.user_age = 0
        
        # Ask for games
        await ctx.send("What games do you play? (separate with ',')")
        msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60.0)
        self.user_games = msg.content
        
        # Get location
        location = get_location_by_ip()
        if location:
            self.location = location[2]
        else:
            self.location = "Unknown"
        
        # Ask for bio
        await ctx.send("Write something about yourself:")
        msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60.0)
        self.user_bio = msg.content
        
        # Ask for photo
        await ctx.send("**Upload a profile photo!** (attach an image or type 'skip' to skip)")
        msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=120.0)
        
        if msg.attachments:
            # User uploaded an image
            attachment = msg.attachments[0]
            if attachment.content_type and attachment.content_type.startswith('image/'):
                # Download and save the photo
                saved_path = await download_photo(attachment.url, ctx.author.id)
                if saved_path:
                    self.photo_url = attachment.url  # Store the Discord CDN URL
                    await ctx.send("✅ Photo uploaded successfully!")
                else:
                    await ctx.send("⚠️ Failed to save photo, continuing without it.")
            else:
                await ctx.send("⚠️ That's not an image! Continuing without photo.")
        elif msg.content.lower() != 'skip':
            await ctx.send("⚠️ No image detected. Continuing without photo.")
        
        return self
    
    def get_embed(self):
        """Create a nice Discord embed to display the bio"""
        embed = discord.Embed(title=f"{self.user_name}'s Profile", color=discord.Color.blue())
        embed.add_field(name="Age", value=str(self.user_age), inline=True)
        embed.add_field(name="Location", value=self.location, inline=True)
        embed.add_field(name="Games", value=self.user_games, inline=False)
        embed.add_field(name="Bio", value=self.user_bio, inline=False)
        
        # Add photo to embed if available
        if self.photo_url:
            embed.set_thumbnail(url=self.photo_url)
        
        return embed

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command(name='setup_bio')
async def setup_bio(ctx):
    """Command to set up user bio"""
    try:
        user = UserBio()
        await user.setdata(ctx, bot)
        
        # Display the completed bio
        embed = user.get_embed()
        await ctx.send("✅ Bio setup complete!", embed=embed)
        
    except asyncio.TimeoutError:
        await ctx.send("Setup timed out. Please use `!setup_bio` to try again.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

# Run the bot
bot.run(os.getenv('DISCORD_TOKEN'))