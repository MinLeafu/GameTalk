import discord
from discord.ext import commands
import requests

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

class UserBio():
    def __init__(self):
        self.user_name = None
        self.user_age = 0
        self.user_games = None
        self.location = None
        self.user_bio = None
    
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
        
        return self
    
    def get_embed(self):
        """Create a nice Discord embed to display the bio"""
        embed = discord.Embed(title=f"{self.user_name}'s Profile", color=discord.Color.blue())
        embed.add_field(name="Age", value=str(self.user_age), inline=True)
        embed.add_field(name="Location", value=self.location, inline=True)
        embed.add_field(name="Games", value=self.user_games, inline=False)
        embed.add_field(name="Bio", value=self.user_bio, inline=False)
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
        
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

# Run the bot
bot.run(os.getenv('DISCORD_TOKEN'))