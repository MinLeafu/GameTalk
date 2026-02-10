import asyncio
import discord
from dotenv import load_dotenv
from discord.ext import commands
import os
import requests
import aiohttp
from datetime import datetime, timedelta
from discord.ui import View, Button, Select

# Store user data (in production, use a database)
user_data = {}
# Store active connections with timestamps
active_connections = {}  # {(user1_id, user2_id): {'timestamp': datetime, 'user1_decision': None, 'user2_decision': None}}
# Maximum connections per user
MAX_CONNECTIONS = 5

# Singapore MRT Stations (grouped by line for easier navigation)
MRT_STATIONS = {
    "North-South Line": [
        "Jurong East", "Bukit Batok", "Bukit Gombak", "Choa Chu Kang", "Yew Tee",
        "Kranji", "Marsiling", "Woodlands", "Admiralty", "Sembawang", "Canberra",
        "Yishun", "Khatib", "Yio Chu Kang", "Ang Mo Kio", "Bishan", "Braddell",
        "Toa Payoh", "Novena", "Newton", "Orchard", "Somerset", "Dhoby Ghaut",
        "City Hall", "Raffles Place", "Marina Bay", "Marina South Pier"
    ],
    "East-West Line": [
        "Pasir Ris", "Tampines", "Simei", "Tanah Merah", "Bedok", "Kembangan",
        "Eunos", "Paya Lebar", "Aljunied", "Kallang", "Lavender", "Bugis",
        "City Hall", "Raffles Place", "Tanjong Pagar", "Outram Park", "Tiong Bahru",
        "Redhill", "Queenstown", "Commonwealth", "Buona Vista", "Dover", "Clementi",
        "Jurong East", "Chinese Garden", "Lakeside", "Boon Lay", "Pioneer",
        "Joo Koon", "Gul Circle", "Tuas Crescent", "Tuas West Road", "Tuas Link"
    ],
    "Circle Line": [
        "Dhoby Ghaut", "Bras Basah", "Esplanade", "Promenade", "Nicoll Highway",
        "Stadium", "Mountbatten", "Dakota", "Paya Lebar", "MacPherson", "Tai Seng",
        "Bartley", "Serangoon", "Lorong Chuan", "Bishan", "Marymount", "Caldecott",
        "Botanic Gardens", "Farrer Road", "Holland Village", "Buona Vista", "one-north",
        "Kent Ridge", "Haw Par Villa", "Pasir Panjang", "Labrador Park", "Telok Blangah",
        "HarbourFront", "Marina Bay"
    ],
    "Downtown Line": [
        "Bukit Panjang", "Cashew", "Hillview", "Beauty World", "King Albert Park",
        "Sixth Avenue", "Tan Kah Kee", "Botanic Gardens", "Stevens", "Newton",
        "Little India", "Rochor", "Bugis", "Promenade", "Bayfront", "Downtown",
        "Telok Ayer", "Chinatown", "Fort Canning", "Bencoolen", "Jalan Besar",
        "Bendemeer", "Geylang Bahru", "Mattar", "MacPherson", "Ubi", "Kaki Bukit",
        "Bedok North", "Bedok Reservoir", "Tampines West", "Tampines", "Tampines East",
        "Upper Changi", "Expo"
    ],
    "North-East Line": [
        "HarbourFront", "Outram Park", "Chinatown", "Clarke Quay", "Dhoby Ghaut",
        "Little India", "Farrer Park", "Boon Keng", "Potong Pasir", "Woodleigh",
        "Serangoon", "Kovan", "Hougang", "Buangkok", "Sengkang", "Punggol"
    ],
    "Thomson-East Coast Line": [
        "Woodlands North", "Woodlands", "Woodlands South", "Springleaf", "Lentor",
        "Mayflower", "Bright Hill", "Upper Thomson", "Caldecott", "Mount Pleasant",
        "Stevens", "Napier", "Orchard Boulevard", "Orchard", "Great World", "Havelock",
        "Outram Park", "Maxwell", "Shenton Way", "Marina Bay", "Marina South",
        "Gardens by the Bay", "Tanjong Rhu", "Katong Park", "Tanjong Katong",
        "Marine Parade", "Marine Terrace", "Siglap", "Bayshore", "Bedok South",
        "Sungei Bedok"
    ]
}

# Flatten all stations into a single list (removing duplicates)
ALL_MRT_STATIONS = sorted(list(set([station for stations in MRT_STATIONS.values() for station in stations])))

class MRTSelectView(View):
    """Dropdown menu for selecting MRT station"""
    def __init__(self, user_id, bot_instance):
        super().__init__(timeout=180)  # 3 minute timeout
        self.user_id = user_id
        self.bot = bot_instance
        self.selected_station = None
        
        # Create dropdown with first 25 stations (Discord limit)
        # We'll use multiple dropdowns or a different approach for all stations
        self.add_station_select()
    
    def add_station_select(self):
        # Split stations into groups of 25 (Discord limit per select menu)
        select1 = Select(
            placeholder="Choose your nearest MRT station (1)",
            options=[
                discord.SelectOption(label=station, value=station)
                for station in ALL_MRT_STATIONS[:25]
            ]
        )
        select1.callback = self.station_callback
        self.add_item(select1)
        
        if len(ALL_MRT_STATIONS) > 25:
            select2 = Select(
                placeholder="Choose your nearest MRT station (2)",
                options=[
                    discord.SelectOption(label=station, value=station)
                    for station in ALL_MRT_STATIONS[25:50]
                ]
            )
            select2.callback = self.station_callback
            self.add_item(select2)
        
        if len(ALL_MRT_STATIONS) > 50:
            select3 = Select(
                placeholder="Choose your nearest MRT station (3)",
                options=[
                    discord.SelectOption(label=station, value=station)
                    for station in ALL_MRT_STATIONS[50:75]
                ]
            )
            select3.callback = self.station_callback
            self.add_item(select3)
        
        if len(ALL_MRT_STATIONS) > 75:
            select4 = Select(
                placeholder="Choose your nearest MRT station (4)",
                options=[
                    discord.SelectOption(label=station, value=station)
                    for station in ALL_MRT_STATIONS[75:100]
                ]
            )
            select4.callback = self.station_callback
            self.add_item(select4)
        
        if len(ALL_MRT_STATIONS) > 100:
            select5 = Select(
                placeholder="Choose your nearest MRT station (5)",
                options=[
                    discord.SelectOption(label=station, value=station)
                    for station in ALL_MRT_STATIONS[100:min(125, len(ALL_MRT_STATIONS))]
                ]
            )
            select5.callback = self.station_callback
            self.add_item(select5)
    
    async def station_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This isn't your selection!", ephemeral=True)
            return
        
        self.selected_station = interaction.data['values'][0]
        await interaction.response.send_message(f"✅ You selected: **{self.selected_station}**", ephemeral=True)
        self.stop()

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

def clean_games(games_list):
    """Clean and normalize game names"""
    return [game.lower().strip() for game in games_list]

def calculate_match_score(user1, user2):
    """Calculate match score between two users based on games and age"""
    # Find common games
    common_games = set(user1.games) & set(user2.games)
    num_common_games = len(common_games)
    
    # Calculate age difference
    age_diff = abs(user1.age - user2.age)
    
    # Calculate score
    game_score = num_common_games * 10
    age_penalty = age_diff * 0.5
    
    total_score = game_score - age_penalty
    
    return {
        'score': total_score,
        'common_games': list(common_games),
        'num_common': num_common_games,
        'age_diff': age_diff
    }

def get_connection_key(user1_id, user2_id):
    """Create a unique key for a connection (order doesn't matter)"""
    return tuple(sorted([user1_id, user2_id]))

def get_user_connections(user_id):
    """Get all active connections for a user"""
    return [key for key in active_connections.keys() if user_id in key]

def get_connection_count(user_id):
    """Get number of active connections for a user"""
    return len(get_user_connections(user_id))

def can_accept_connection(user_id):
    """Check if user can accept more connections"""
    return get_connection_count(user_id) < MAX_CONNECTIONS

def get_other_user_id(connection_key, user_id):
    """Get the other user's ID from a connection key"""
    return connection_key[0] if connection_key[1] == user_id else connection_key[1]

def get_time_since_match(connection_key):
    """Get time elapsed since match was made"""
    if connection_key in active_connections:
        timestamp = active_connections[connection_key]['timestamp']
        return datetime.now() - timestamp
    return timedelta(0)

def can_make_decision(connection_key):
    """Check if 30 minutes have passed since the match"""
    time_elapsed = get_time_since_match(connection_key)
    return time_elapsed >= timedelta(minutes=30)

def is_connected(user1_id, user2_id):
    """Check if two users are connected"""
    connection_key = get_connection_key(user1_id, user2_id)
    return connection_key in active_connections

def get_connected_user_from_name(sender_id, recipient_name):
    """Find a connected user by their Discord username or display name"""
    user_connections = get_user_connections(sender_id)
    
    for connection_key in user_connections:
        other_id = get_other_user_id(connection_key, sender_id)
        if other_id in user_data:
            # Check if the recipient name matches the user's profile name or game name
            if user_data[other_id].name.lower() == recipient_name.lower():
                return other_id
    
    return None

class KeepOrReleaseView(View):
    """UI for keep/release decision"""
    def __init__(self, bot, connection_key, user_id, timeout=None):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.connection_key = connection_key
        self.user_id = user_id
    
    @discord.ui.button(label="Keep on Team", style=discord.ButtonStyle.success, emoji="✅")
    async def keep_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This isn't your decision!", ephemeral=True)
            return
        
        await handle_decision(self.bot, self.connection_key, self.user_id, "keep")
        await interaction.response.send_message("✅ You've decided to keep this teammate!", ephemeral=True)
        self.stop()
    
    @discord.ui.button(label="Let Go", style=discord.ButtonStyle.danger, emoji="👋")
    async def release_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This isn't your decision!", ephemeral=True)
            return
        
        await handle_decision(self.bot, self.connection_key, self.user_id, "release")
        await interaction.response.send_message("👋 You've decided to let this teammate go.", ephemeral=True)
        self.stop()

async def handle_decision(bot, connection_key, user_id, decision):
    """Handle keep/release decision"""
    if connection_key not in active_connections:
        return
    
    connection_data = active_connections[connection_key]
    other_user_id = get_other_user_id(connection_key, user_id)
    
    # Record decision
    if connection_key[0] == user_id:
        connection_data['user1_decision'] = decision
    else:
        connection_data['user2_decision'] = decision
    
    user1_decision = connection_data['user1_decision']
    user2_decision = connection_data['user2_decision']
    
    # Check if both users have made decisions
    if user1_decision and user2_decision:
        user1_id = connection_key[0]
        user2_id = connection_key[1]
        
        user1 = await bot.fetch_user(user1_id)
        user2 = await bot.fetch_user(user2_id)
        
        if user1_decision == "keep" and user2_decision == "keep":
            # Both want to keep - connection becomes permanent
            try:
                await user1.send(f"🎉 **Great news!** Both you and {user_data[user2_id].name} want to keep gaming together! This connection is now permanent. Use `!viewteam` to see all your teammates.")
                await user2.send(f"🎉 **Great news!** Both you and {user_data[user1_id].name} want to keep gaming together! This connection is now permanent. Use `!viewteam` to see all your teammates.")
            except:
                pass
            # Keep in active_connections but mark as permanent
            connection_data['permanent'] = True
            
        elif user1_decision == "release" or user2_decision == "release":
            # At least one wants to release - remove connection
            try:
                if user1_decision == "release" and user2_decision == "release":
                    await user1.send(f"👋 You both decided to part ways with each other. You can find new matches with `!findmatch`")
                    await user2.send(f"👋 You both decided to part ways with each other. You can find new matches with `!findmatch`")
                elif user1_decision == "release":
                    await user1.send(f"👋 You've let {user_data[user2_id].name} go. You can find new matches with `!findmatch`")
                    await user2.send(f"😔 {user_data[user1_id].name} decided to let you go. You can find new matches with `!findmatch`")
                else:
                    await user2.send(f"👋 You've let {user_data[user1_id].name} go. You can find new matches with `!findmatch`")
                    await user1.send(f"😔 {user_data[user2_id].name} decided to let you go. You can find new matches with `!findmatch`")
            except:
                pass
            
            # Remove connection
            del active_connections[connection_key]

async def send_match_dm(bot, user1_id, user2_id, match_data, user1_data, user2_data):
    """Send DM to both users about their match"""
    try:
        user1 = await bot.fetch_user(user1_id)
        user2 = await bot.fetch_user(user2_id)
        
        # Create embed for user1
        embed1 = discord.Embed(
            title="🎮 New Gaming Match Found!",
            description=f"You've been matched with **{user2_data.name}** (@{user2.name})!",
            color=discord.Color.green()
        )
        embed1.add_field(name="🎯 Match Score", value=f"**{match_data['score']:.1f}** points", inline=True)
        embed1.add_field(name="🎮 Common Games", value=", ".join(match_data['common_games']), inline=False)
        embed1.add_field(name="📍 Their Location", value=user2_data.location, inline=True)
        embed1.add_field(name="📅 Age", value=str(user2_data.age), inline=True)
        embed1.add_field(name="📝 Bio", value=user2_data.bio, inline=False)
        
        if user2_data.photo_url:
            embed1.set_thumbnail(url=user2_data.photo_url)
        
        embed1.set_footer(text="⏰ In 30 minutes, you'll decide: Keep or Release this teammate!")
        
        # Create embed for user2
        embed2 = discord.Embed(
            title="🎮 New Gaming Match Found!",
            description=f"You've been matched with **{user1_data.name}** (@{user1.name})!",
            color=discord.Color.green()
        )
        embed2.add_field(name="🎯 Match Score", value=f"**{match_data['score']:.1f}** points", inline=True)
        embed2.add_field(name="🎮 Common Games", value=", ".join(match_data['common_games']), inline=False)
        embed2.add_field(name="📍 Their Location", value=user1_data.location, inline=True)
        embed2.add_field(name="📅 Age", value=str(user1_data.age), inline=True)
        embed2.add_field(name="📝 Bio", value=user1_data.bio, inline=False)
        
        if user1_data.photo_url:
            embed2.set_thumbnail(url=user1_data.photo_url)
        
        embed2.set_footer(text="⏰ In 30 minutes, you'll decide: Keep or Release this teammate!")
        
        # Send DMs with smart formatting for names with spaces
        user1_msg_cmd = f'!msg "{user2_data.name}"' if ' ' in user2_data.name else f'!msg {user2_data.name}'
        user1_dm_cmd = f'!dm "{user2.name}"' if ' ' in user2.name else f'!dm {user2.name}'
        
        user2_msg_cmd = f'!msg "{user1_data.name}"' if ' ' in user1_data.name else f'!msg {user1_data.name}'
        user2_dm_cmd = f'!dm "{user1.name}"' if ' ' in user1.name else f'!dm {user1.name}'
        
        await user1.send(embed=embed1)
        await user1.send(f"💬 **Send messages to {user2_data.name}:**\nUse `{user1_msg_cmd} Your message here`\nOr use `{user1_dm_cmd} Your message here`")
        
        await user2.send(embed=embed2)
        await user2.send(f"💬 **Send messages to {user1_data.name}:**\nUse `{user2_msg_cmd} Your message here`\nOr use `{user2_dm_cmd} Your message here`")
        
        return True
    except discord.Forbidden:
        print(f"Cannot send DM to user - they may have DMs disabled")
        return False
    except Exception as e:
        print(f"Error sending match DM: {e}")
        return False

async def send_decision_prompt(bot, connection_key):
    """Send decision prompt after 30 minutes"""
    if connection_key not in active_connections:
        return
    
    connection_data = active_connections[connection_key]
    
    # Skip if already permanent
    if connection_data.get('permanent'):
        return
    
    user1_id = connection_key[0]
    user2_id = connection_key[1]
    
    try:
        user1 = await bot.fetch_user(user1_id)
        user2 = await bot.fetch_user(user2_id)
        
        user1_data = user_data.get(user1_id)
        user2_data = user_data.get(user2_id)
        
        if not user1_data or not user2_data:
            return
        
        # Send decision UI to user1
        embed1 = discord.Embed(
            title="⏰ Decision Time!",
            description=f"30 minutes have passed! What do you think of **{user2_data.name}**?",
            color=discord.Color.gold()
        )
        embed1.add_field(
            name="Keep on Team ✅",
            value="You enjoyed gaming together and want to keep this connection",
            inline=False
        )
        embed1.add_field(
            name="Let Go 👋",
            value="Not the right fit - find a new match",
            inline=False
        )
        
        view1 = KeepOrReleaseView(bot, connection_key, user1_id)
        await user1.send(embed=embed1, view=view1)
        
        # Send decision UI to user2
        embed2 = discord.Embed(
            title="⏰ Decision Time!",
            description=f"30 minutes have passed! What do you think of **{user1_data.name}**?",
            color=discord.Color.gold()
        )
        embed2.add_field(
            name="Keep on Team ✅",
            value="You enjoyed gaming together and want to keep this connection",
            inline=False
        )
        embed2.add_field(
            name="Let Go 👋",
            value="Not the right fit - find a new match",
            inline=False
        )
        
        view2 = KeepOrReleaseView(bot, connection_key, user2_id)
        await user2.send(embed=embed2, view=view2)
        
    except Exception as e:
        print(f"Error sending decision prompt: {e}")

def main():
    load_dotenv()

    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True  # Enable member intents for better user lookups
    bot = commands.Bot(command_prefix="!", intents=intents)
    
    # Background task for decision prompts
    @bot.event
    async def on_ready():
        print(f'{bot.user} has connected to Discord!')
        print(f'Bot is ready to match gamers!')
        bot.loop.create_task(check_decision_times())
    
    # Handle DM messages for relay
    @bot.event
    async def on_message(message):
        # Ignore messages from the bot itself
        if message.author == bot.user:
            return
        
        # Process commands first
        await bot.process_commands(message)
        
        # Check if it's a DM (not in a guild/server)
        if message.guild is None and not message.content.startswith('!'):
            sender_id = message.author.id
            
            # Check if sender has a profile
            if sender_id not in user_data:
                return
            
            # Get all connections for this user
            user_connections = get_user_connections(sender_id)
            
            if not user_connections:
                await message.channel.send("❌ You're not connected with anyone yet! Use `!findmatch` to find teammates.")
                return
            
            # If user has only one connection, auto-send to them
            if len(user_connections) == 1:
                connection_key = user_connections[0]
                recipient_id = get_other_user_id(connection_key, sender_id)
                
                try:
                    recipient = await bot.fetch_user(recipient_id)
                    sender_name = user_data[sender_id].name
                    
                    # Create message embed
                    embed = discord.Embed(
                        description=message.content,
                        color=discord.Color.blue(),
                        timestamp=datetime.utcnow()
                    )
                    embed.set_author(name=f"Message from {sender_name}", icon_url=message.author.display_avatar.url)
                    embed.set_footer(text="Reply directly or use !msg to respond")
                    
                    # Forward attachments if any
                    if message.attachments:
                        for attachment in message.attachments:
                            embed.add_field(name="📎 Attachment", value=f"[{attachment.filename}]({attachment.url})", inline=False)
                    
                    await recipient.send(embed=embed)
                    await message.add_reaction("✅")  # Confirm message sent
                    
                except Exception as e:
                    await message.channel.send(f"❌ Failed to send message: {e}")
            
            else:
                # Multiple connections - ask user to specify recipient
                await message.channel.send(
                    "❓ You have multiple connections. Please use:\n"
                    "`!msg <name> <message>` - Send to specific teammate\n"
                    "`!dm @username <message>` - Send using Discord username"
                )
    
    async def check_decision_times():
        """Background task to check if connections are ready for decisions"""
        await bot.wait_until_ready()
        while not bot.is_closed():
            current_time = datetime.now()
            connections_to_check = list(active_connections.items())
            
            for connection_key, connection_data in connections_to_check:
                # Skip if permanent or already has decisions
                if connection_data.get('permanent'):
                    continue
                if connection_data.get('user1_decision') or connection_data.get('user2_decision'):
                    continue
                
                # Check if 30 minutes have passed
                time_elapsed = current_time - connection_data['timestamp']
                if time_elapsed >= timedelta(minutes=30) and not connection_data.get('prompt_sent'):
                    await send_decision_prompt(bot, connection_key)
                    connection_data['prompt_sent'] = True
            
            await asyncio.sleep(60)  # Check every minute
    
    @bot.command()
    async def setup(ctx):
        """Interactive profile setup"""
        try:
            user_id = ctx.author.id
            
            if user_id in user_data:
                await ctx.send("⚠️ You already have a profile! Use `!update` to change it or `!delete` to remove it.")
                return
            
            await ctx.send("🎮 **Let's set up your gaming profile!**\n")
            
            await ctx.send("**What is your name?**")
            msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60.0)
            name = msg.content
            
            await ctx.send("**What is your age?**")
            msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60.0)
            try:
                age = int(msg.content)
            except ValueError:
                await ctx.send("❌ Invalid age. Please use `!setup` to try again.")
                return
            
            await ctx.send("**What games do you play?** (separate with commas)\nExample: Valorant, League of Legends, Minecraft")
            msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60.0)
            games = clean_games(msg.content.split(","))
            
            # MRT Station Selection with dropdown
            await ctx.send("🚇 **Select your nearest MRT station:**")
            mrt_view = MRTSelectView(user_id, bot)
            mrt_message = await ctx.send("Use the dropdown menus below:", view=mrt_view)
            
            # Wait for selection
            await mrt_view.wait()
            
            if mrt_view.selected_station:
                location = f"{mrt_view.selected_station} MRT, Singapore"
                await ctx.send(f"📍 Location set to: **{location}**")
            else:
                await ctx.send("⏱️ MRT selection timed out. Using default location.")
                location = "Singapore"
            
            await ctx.send("**Write something about yourself:**")
            msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60.0)
            bio = msg.content
            
            await ctx.send("**Upload a profile photo!** (attach an image or type 'skip')")
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
            
            person = Person(name=name, age=age, games=games, location=location, bio=bio, photo_url=photo_url)
            user_data[user_id] = person
            
            embed = discord.Embed(title=f"✅ {person.name}'s Profile Created!", color=discord.Color.green())
            embed.add_field(name="Age", value=str(person.age), inline=True)
            embed.add_field(name="Location", value=person.location, inline=True)
            embed.add_field(name="Games", value=", ".join(person.games), inline=False)
            embed.add_field(name="Bio", value=person.bio, inline=False)
            
            if person.photo_url:
                embed.set_thumbnail(url=person.photo_url)
            
            await ctx.send(embed=embed)
            await ctx.send("💡 **Use `!findmatch` to find gaming buddies!**")
            
        except asyncio.TimeoutError:
            await ctx.send("⏱️ Setup timed out. Please use `!setup` to try again.")
        except Exception as e:
            await ctx.send(f"❌ An error occurred: {e}")
    
    @bot.command()
    async def profile(ctx, member: discord.Member = None):
        """View a user's profile"""
        if member is None:
            member = ctx.author
        
        person = user_data.get(member.id)
        if person is None:
            await ctx.send(f"❌ No profile found for {member.display_name}. Use `!setup` to create one!")
            return
        
        embed = discord.Embed(title=f"👤 {person.name}'s Profile", color=discord.Color.blue())
        embed.add_field(name="Age", value=str(person.age), inline=True)
        embed.add_field(name="Location", value=person.location, inline=True)
        embed.add_field(name="Games", value=", ".join(person.games), inline=False)
        embed.add_field(name="Bio", value=person.bio, inline=False)
        embed.set_footer(text=f"Discord: {member.display_name}")
        
        if person.photo_url:
            embed.set_thumbnail(url=person.photo_url)
        
        await ctx.send(embed=embed)
    
    @bot.command()
    async def findmatch(ctx):
        """Find your best gaming matches"""
        user_id = ctx.author.id
        
        if user_id not in user_data:
            await ctx.send("❌ You need to create a profile first! Use `!setup`")
            return
        
        # Check connection limit
        connection_count = get_connection_count(user_id)
        if connection_count >= MAX_CONNECTIONS:
            await ctx.send(f"⚠️ **You've reached the maximum of {MAX_CONNECTIONS} active connections!**\nUse `!viewteam` to see your current team, or wait for the 30-minute decision period to free up slots.")
            return
        
        current_user = user_data[user_id]
        matches = []
        
        # Get already connected user IDs
        connected_user_ids = set()
        for connection in get_user_connections(user_id):
            connected_user_ids.add(get_other_user_id(connection, user_id))
        
        # Compare with all other users (excluding already connected)
        for other_id, other_person in user_data.items():
            if other_id == user_id or other_id in connected_user_ids:
                continue
            
            # Skip if other user is at max connections
            if not can_accept_connection(other_id):
                continue
            
            match_data = calculate_match_score(current_user, other_person)
            
            if match_data['num_common'] > 0:
                matches.append({'user_id': other_id, 'person': other_person, 'match_data': match_data})
        
        if not matches:
            await ctx.send("😔 **No new matches available!**\nEither everyone is at max connections or you're already connected with all compatible players.")
            return
        
        matches.sort(key=lambda x: x['match_data']['score'], reverse=True)
        
        embed = discord.Embed(
            title=f"🎮 Top Gaming Matches for {current_user.name}",
            description=f"Found {len(matches)} potential gaming buddies!\n**Connections: {connection_count}/{MAX_CONNECTIONS}**",
            color=discord.Color.gold()
        )
        
        for i, match in enumerate(matches[:5], 1):
            other_id = match['user_id']
            person = match['person']
            match_data = match['match_data']
            
            try:
                member = await bot.fetch_user(other_id)
                discord_name = f"@{member.name}"
            except:
                discord_name = "Unknown User"
            
            match_info = (
                f"**{discord_name}**\n"
                f"🎯 Match Score: **{match_data['score']:.1f}**\n"
                f"🎮 Common Games ({match_data['num_common']}): {', '.join(match_data['common_games'])}\n"
                f"📅 Age Difference: {match_data['age_diff']} years\n"
                f"📍 Location: {person.location}\n"
            )
            
            if i == 1:
                title = "🥇 Best Match - " + person.name
            elif i == 2:
                title = "🥈 2nd Match - " + person.name
            elif i == 3:
                title = "🥉 3rd Match - " + person.name
            else:
                title = f"#{i} - {person.name}"
            
            embed.add_field(name=title, value=match_info, inline=False)
        
        if matches[0]['person'].photo_url:
            embed.set_thumbnail(url=matches[0]['person'].photo_url)
        
        embed.set_footer(text=f"Use !connect @username to start chatting!")
        
        await ctx.send(embed=embed)
    
    @bot.command()
    async def connect(ctx, member: discord.Member):
        """Connect with a match"""
        user_id = ctx.author.id
        
        if user_id not in user_data:
            await ctx.send("❌ You need to create a profile first! Use `!setup`")
            return
        
        if member.id not in user_data:
            await ctx.send(f"❌ {member.display_name} doesn't have a profile yet!")
            return
        
        if member.id == user_id:
            await ctx.send("❌ You can't connect with yourself!")
            return
        
        # Check connection limits
        if not can_accept_connection(user_id):
            await ctx.send(f"❌ You've reached the maximum of {MAX_CONNECTIONS} active connections!")
            return
        
        if not can_accept_connection(member.id):
            await ctx.send(f"❌ {member.display_name} has reached their maximum connections!")
            return
        
        connection_key = get_connection_key(user_id, member.id)
        if connection_key in active_connections:
            await ctx.send(f"⚠️ You're already connected with {member.display_name}!")
            return
        
        user1_data = user_data[user_id]
        user2_data = user_data[member.id]
        
        match_data = calculate_match_score(user1_data, user2_data)
        
        if match_data['num_common'] == 0:
            await ctx.send(f"⚠️ You have no common games with {member.display_name}.")
            return
        
        await ctx.send(f"✅ Creating connection with {member.display_name}... Check your DMs! 📬")
        
        success = await send_match_dm(bot, user_id, member.id, match_data, user1_data, user2_data)
        
        if success:
            # Create new connection
            active_connections[connection_key] = {
                'timestamp': datetime.now(),
                'user1_decision': None,
                'user2_decision': None,
                'prompt_sent': False
            }
            
            await ctx.send(f"🎉 **Connection established!** You have 30 minutes to chat before making a decision.\n**Your connections: {get_connection_count(user_id)}/{MAX_CONNECTIONS}**")
        else:
            await ctx.send(f"⚠️ Couldn't send DM. Make sure both of you have DMs enabled!")
    
    @bot.command()
    async def msg(ctx, *, full_message: str):
        """Send a message to a connected teammate using their profile name
        Usage: !msg John Hey, want to play Valorant?
        Or for names with spaces: !msg "John Doe" Hey there!"""
        sender_id = ctx.author.id
        
        if sender_id not in user_data:
            await ctx.send("❌ You need to create a profile first! Use `!setup`")
            return
        
        # Parse the message - handle both quoted and unquoted names
        recipient_name = None
        message = None
        
        # Check if starts with a quote (for names with spaces)
        if full_message.startswith('"'):
            # Find the closing quote
            end_quote = full_message.find('"', 1)
            if end_quote != -1:
                recipient_name = full_message[1:end_quote]
                message = full_message[end_quote+1:].strip()
            else:
                await ctx.send("❌ Missing closing quote for name!")
                return
        else:
            # No quotes - take first word as name
            parts = full_message.split(None, 1)
            if len(parts) < 2:
                await ctx.send("❌ Usage: `!msg <name> <message>` or `!msg \"Name With Spaces\" <message>`")
                return
            recipient_name = parts[0]
            message = parts[1]
        
        if not message:
            await ctx.send("❌ You need to include a message!")
            return
        
        # Find the recipient among connections
        recipient_id = None
        user_connections = get_user_connections(sender_id)
        
        for connection_key in user_connections:
            other_id = get_other_user_id(connection_key, sender_id)
            if other_id in user_data:
                if user_data[other_id].name.lower() == recipient_name.lower():
                    recipient_id = other_id
                    break
        
        if not recipient_id:
            await ctx.send(f"❌ You're not connected with anyone named '{recipient_name}'.\nUse `!viewteam` to see your connections.")
            return
        
        try:
            recipient = await bot.fetch_user(recipient_id)
            sender_name = user_data[sender_id].name
            
            # Create message embed
            embed = discord.Embed(
                description=message,
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            embed.set_author(name=f"Message from {sender_name}", icon_url=ctx.author.display_avatar.url)
            
            # Smart footer - add quotes if sender name has spaces
            if ' ' in sender_name:
                embed.set_footer(text=f"Reply with: !msg \"{sender_name}\" <your message>")
            else:
                embed.set_footer(text=f"Reply with: !msg {sender_name} <your message>")
            
            await recipient.send(embed=embed)
            await ctx.send(f"✅ Message sent to {user_data[recipient_id].name}!")
            
        except Exception as e:
            await ctx.send(f"❌ Failed to send message: {e}")
    
    @bot.command()
    async def dm(ctx, *, full_message: str):
        """Send a message to a connected teammate using their Discord username
        Usage: !dm username Hey, want to play?
        Or for names with spaces: !dm "user name" Hey there!"""
        sender_id = ctx.author.id
        
        if sender_id not in user_data:
            await ctx.send("❌ You need to create a profile first! Use `!setup`")
            return
        
        # Parse the message - handle both quoted and unquoted names
        recipient_name = None
        message = None
        
        # Check if starts with a quote (for names with spaces)
        if full_message.startswith('"'):
            # Find the closing quote
            end_quote = full_message.find('"', 1)
            if end_quote != -1:
                recipient_name = full_message[1:end_quote]
                message = full_message[end_quote+1:].strip()
            else:
                await ctx.send("❌ Missing closing quote for name!")
                return
        else:
            # No quotes - take first word as name
            parts = full_message.split(None, 1)
            if len(parts) < 2:
                await ctx.send("❌ Usage: `!dm username <message>` or `!dm \"user name\" <message>`")
                return
            recipient_name = parts[0]
            message = parts[1]
        
        if not message:
            await ctx.send("❌ You need to include a message!")
            return
        
        # Find the member by Discord username among connections
        recipient_id = None
        user_connections = get_user_connections(sender_id)
        
        for connection_key in user_connections:
            other_id = get_other_user_id(connection_key, sender_id)
            if other_id in user_data:
                try:
                    member = await bot.fetch_user(other_id)
                    # Check both username and display name
                    if member.name.lower() == recipient_name.lower() or member.display_name.lower() == recipient_name.lower():
                        recipient_id = other_id
                        break
                except:
                    continue
        
        if not recipient_id:
            await ctx.send(f"❌ You're not connected with Discord user '{recipient_name}'.\nUse `!viewteam` to see your connections.")
            return
        
        try:
            member = await bot.fetch_user(recipient_id)
            sender_name = user_data[sender_id].name
            sender_discord = ctx.author.name
            
            # Create message embed
            embed = discord.Embed(
                description=message,
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            embed.set_author(name=f"Message from {sender_name}", icon_url=ctx.author.display_avatar.url)
            
            # Smart footer - add quotes if sender Discord name has spaces
            if ' ' in sender_discord:
                embed.set_footer(text=f"Reply with: !dm \"{sender_discord}\" <your message>")
            else:
                embed.set_footer(text=f"Reply with: !dm {sender_discord} <your message>")
            
            await member.send(embed=embed)
            await ctx.send(f"✅ Message sent to {user_data[recipient_id].name}!")
            
        except discord.Forbidden:
            await ctx.send(f"❌ Cannot send DM to {recipient_name}. They may have DMs disabled.")
        except Exception as e:
            await ctx.send(f"❌ Failed to send message: {e}")
    
    @bot.command()
    async def viewteam(ctx):
        """View your current active connections with detailed UI"""
        user_id = ctx.author.id
        
        if user_id not in user_data:
            await ctx.send("❌ You need to create a profile first! Use `!setup`")
            return
        
        user_connections = get_user_connections(user_id)
        
        if not user_connections:
            await ctx.send("📭 You have no active connections yet! Use `!findmatch` to find matches.")
            return
        
        embed = discord.Embed(
            title=f"🤝 Your Gaming Team",
            description=f"**Active Connections: {len(user_connections)}/{MAX_CONNECTIONS}**",
            color=discord.Color.blue()
        )
        
        for connection_key in user_connections:
            other_id = get_other_user_id(connection_key, user_id)
            
            if other_id not in user_data:
                continue
            
            other_person = user_data[other_id]
            connection_data = active_connections[connection_key]
            
            time_elapsed = get_time_since_match(connection_key)
            is_permanent = connection_data.get('permanent', False)
            
            # Get decision status
            if connection_key[0] == user_id:
                my_decision = connection_data.get('user1_decision')
                their_decision = connection_data.get('user2_decision')
            else:
                my_decision = connection_data.get('user2_decision')
                their_decision = connection_data.get('user1_decision')
            
            try:
                member = await bot.fetch_user(other_id)
                
                # Build status text
                if is_permanent:
                    status = "✅ **Permanent Teammate**"
                elif time_elapsed < timedelta(minutes=30):
                    time_remaining = timedelta(minutes=30) - time_elapsed
                    minutes_left = int(time_remaining.total_seconds() / 60)
                    status = f"⏰ Decision in **{minutes_left} minutes**"
                else:
                    if my_decision and their_decision:
                        status = f"✅ Both decided: {my_decision.title()}"
                    elif my_decision:
                        status = f"⏳ You: {my_decision.title()} | Them: Pending"
                    elif their_decision:
                        status = f"⏳ You: Pending | Them: Decided"
                    else:
                        status = "⚠️ **Decision time! Check DMs**"
                
                # Smart formatting for names with spaces
                msg_cmd = f'!msg "{other_person.name}"' if ' ' in other_person.name else f'!msg {other_person.name}'
                
                field_value = (
                    f"@{member.name}\n"
                    f"🎮 Common Games: {', '.join(calculate_match_score(user_data[user_id], other_person)['common_games'][:3])}\n"
                    f"📍 {other_person.location}\n"
                    f"{status}\n"
                    f"💬 Message: `{msg_cmd} <text>`"
                )
                
                embed.add_field(
                    name=f"{'⭐' if is_permanent else '🎮'} {other_person.name}",
                    value=field_value,
                    inline=False
                )
            except:
                pass
        
        embed.set_footer(text="Use !makedecision to keep or release teammates after 30 minutes")
        
        await ctx.send(embed=embed)
    
    @bot.command()
    async def makedecision(ctx, member: discord.Member, decision: str):
        """Manually make a keep/release decision - !makedecision @user keep/release"""
        user_id = ctx.author.id
        
        if user_id not in user_data or member.id not in user_data:
            await ctx.send("❌ Both users need profiles!")
            return
        
        connection_key = get_connection_key(user_id, member.id)
        
        if connection_key not in active_connections:
            await ctx.send(f"❌ You're not connected with {member.display_name}!")
            return
        
        if not can_make_decision(connection_key):
            time_remaining = timedelta(minutes=30) - get_time_since_match(connection_key)
            minutes_left = int(time_remaining.total_seconds() / 60)
            await ctx.send(f"⏰ You can make a decision in **{minutes_left} minutes**!")
            return
        
        decision = decision.lower()
        if decision not in ['keep', 'release']:
            await ctx.send("❌ Invalid decision! Use `keep` or `release`")
            return
        
        await handle_decision(bot, connection_key, user_id, decision)
        
        if decision == "keep":
            await ctx.send(f"✅ You've decided to keep {member.display_name} on your team!")
        else:
            await ctx.send(f"👋 You've decided to let {member.display_name} go.")
    
    @bot.command()
    async def delete(ctx):
        """Delete your profile"""
        user_id = ctx.author.id
        
        if user_id in user_data:
            for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
                filepath = f"user_photos/{user_id}{ext}"
                if os.path.exists(filepath):
                    os.remove(filepath)
            
            # Remove all connections
            connections_to_remove = [key for key in active_connections.keys() if user_id in key]
            for key in connections_to_remove:
                del active_connections[key]
            
            del user_data[user_id]
            await ctx.send("✅ Your profile and all connections have been deleted.")
        else:
            await ctx.send("❌ You don't have a profile to delete.")
    
    @bot.command()
    async def update(ctx):
        """Update your profile"""
        user_id = ctx.author.id
        
        if user_id in user_data:
            for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
                filepath = f"user_photos/{user_id}{ext}"
                if os.path.exists(filepath):
                    os.remove(filepath)
            
            del user_data[user_id]
        
        await setup(ctx)
    
    @bot.command()
    async def send(ctx):
        """Fun command for friends"""
        await ctx.send("FUCK YOU ALL")
    
    @bot.command()
    async def receive(ctx):
        """Fun command for friends"""
        await ctx.send("IM GNA POUND YOU")

    @bot.command()
    async def removemember(ctx, member: discord.Member):
        """Remove a permanent teammate from your team"""
        user_id = ctx.author.id
        
        if user_id not in user_data:
            await ctx.send("❌ You need to create a profile first! Use `!setup`")
            return
        
        if member.id not in user_data:
            await ctx.send(f"❌ {member.display_name} doesn't have a profile!")
            return
        
        connection_key = get_connection_key(user_id, member.id)
        
        if connection_key not in active_connections:
            await ctx.send(f"❌ You're not connected with {member.display_name}!")
            return
        
        connection_data = active_connections[connection_key]
        
        # Check if connection is permanent
        if not connection_data.get('permanent'):
            await ctx.send(f"⚠️ This connection isn't permanent yet! Wait for the 30-minute decision period to complete first.")
            return
        
        # Confirmation message
        embed = discord.Embed(
            title="⚠️ Remove Teammate?",
            description=f"Are you sure you want to remove **{user_data[member.id].name}** from your team?",
            color=discord.Color.orange()
        )
        embed.add_field(
            name="❗ This action cannot be undone",
            value="React with ✅ to confirm or ❌ to cancel (30 seconds)",
            inline=False
        )
        
        confirm_msg = await ctx.send(embed=embed)
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirm_msg.id
        
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == "✅":
                # Remove the connection
                del active_connections[connection_key]
                
                # Notify both users
                try:
                    other_user = await bot.fetch_user(member.id)
                    await other_user.send(f"💔 **{user_data[user_id].name}** has removed you from their team.")
                except:
                    pass
                
                await ctx.send(f"✅ You've removed **{user_data[member.id].name}** from your team.\n**Your connections: {get_connection_count(user_id)}/{MAX_CONNECTIONS}**")
            else:
                await ctx.send("❌ Removal cancelled.")
                
        except asyncio.TimeoutError:
            await ctx.send("⏱️ Removal cancelled - timed out.")
            
    @bot.command()
    async def chat(ctx, member: discord.Member = None):
        """Get DM information for your teammates"""
        user_id = ctx.author.id
        
        if user_id not in user_data:
            await ctx.send("❌ You need to create a profile first! Use `!setup`")
            return
        
        user_connections = get_user_connections(user_id)
        
        if not user_connections:
            await ctx.send("📭 You have no active connections yet! Use `!findmatch` to find matches.")
            return
        
        # If no member specified, show all connections
        if member is None:
            embed = discord.Embed(
                title="💬 Your Chat Connections",
                description="Here are all your active teammates:",
                color=discord.Color.blue()
            )
            
            for connection_key in user_connections:
                other_id = get_other_user_id(connection_key, user_id)
                
                if other_id not in user_data:
                    continue
                
                other_person = user_data[other_id]
                
                try:
                    other_user = await bot.fetch_user(other_id)
                    
                    is_permanent = active_connections[connection_key].get('permanent', False)
                    status = "⭐ Permanent" if is_permanent else "⏰ Trial"
                    
                    # Smart formatting for names with spaces
                    msg_cmd = f'!msg "{other_person.name}"' if ' ' in other_person.name else f'!msg {other_person.name}'
                    dm_cmd = f'!dm "{other_user.name}"' if ' ' in other_user.name else f'!dm {other_user.name}'
                    
                    embed.add_field(
                        name=f"{status} - {other_person.name}",
                        value=f"{other_user.mention} (`{other_user.name}`)\n💬 `{msg_cmd} <message>`\n📧 `{dm_cmd} <message>`",
                        inline=False
                    )
                except:
                    pass
            
            embed.set_footer(text="Use !chat @user to get specific DM info")
            await ctx.send(embed=embed)
            return
        
        # If member specified, show info for that specific connection
        connection_key = get_connection_key(user_id, member.id)
        
        if connection_key not in active_connections:
            await ctx.send(f"❌ You're not connected with {member.display_name}!")
            return
        
        other_person = user_data[member.id]
        is_permanent = active_connections[connection_key].get('permanent', False)
        
        # Smart formatting for names with spaces
        msg_cmd = f'!msg "{other_person.name}"' if ' ' in other_person.name else f'!msg {other_person.name}'
        dm_cmd = f'!dm "{member.name}"' if ' ' in member.name else f'!dm {member.name}'
        
        embed = discord.Embed(
            title=f"💬 Chat with {other_person.name}",
            description=f"{member.mention}",
            color=discord.Color.green()
        )
        embed.add_field(name="Username", value=f"`{member.name}`", inline=True)
        embed.add_field(name="Status", value="⭐ Permanent" if is_permanent else "⏰ Trial", inline=True)
        embed.add_field(
            name="How to Message",
            value=f"📝 `{msg_cmd} Your message here`\n📧 `{dm_cmd} Your message here`",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @bot.command()
    async def myteam(ctx):
        """View only your permanent teammates"""
        user_id = ctx.author.id
        
        if user_id not in user_data:
            await ctx.send("❌ You need to create a profile first! Use `!setup`")
            return
        
        user_connections = get_user_connections(user_id)
        
        # Filter only permanent connections
        permanent_connections = [
            key for key in user_connections 
            if active_connections[key].get('permanent', False)
        ]
        
        if not permanent_connections:
            await ctx.send("📭 You have no permanent teammates yet!\nUse `!findmatch` and `!connect` to find gaming buddies.")
            return
        
        embed = discord.Embed(
            title=f"⭐ Your Permanent Gaming Team",
            description=f"**Permanent Teammates: {len(permanent_connections)}**",
            color=discord.Color.green()
        )
        
        for connection_key in permanent_connections:
            other_id = get_other_user_id(connection_key, user_id)
            
            if other_id not in user_data:
                continue
            
            other_person = user_data[other_id]
            match_data = calculate_match_score(user_data[user_id], other_person)
            
            try:
                member = await bot.fetch_user(other_id)
                
                # Smart formatting for names with spaces
                msg_cmd = f'!msg "{other_person.name}"' if ' ' in other_person.name else f'!msg {other_person.name}'
                
                field_value = (
                    f"@{member.name}\n"
                    f"🎮 Common Games: {', '.join(match_data['common_games'])}\n"
                    f"📍 {other_person.location}\n"
                    f"📝 {other_person.bio[:50]}..." if len(other_person.bio) > 50 else other_person.bio + "\n"
                    f"💬 `{msg_cmd} <message>`"
                )
                
                embed.add_field(
                    name=f"⭐ {other_person.name}",
                    value=field_value,
                    inline=False
                )
            except:
                pass
        
        embed.set_footer(text="Use !removemember @user to remove a teammate")
        
        await ctx.send(embed=embed)

    @bot.command()
    async def bothelp(ctx):
        """Show all available commands"""
        embed = discord.Embed(
            title="🎮 GameTalk Bot - Commands",
            description="Find your perfect gaming buddy!",
            color=discord.Color.purple()
        )
        
        embed.add_field(
            name="📝 Profile Commands",
            value=(
                "`!setup` - Create your gaming profile\n"
                "`!profile [@user]` - View a profile\n"
                "`!update` - Update your profile\n"
                "`!delete` - Delete your profile"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🔍 Matching Commands",
            value=(
                "`!findmatch` - Find best matches\n"
                "`!connect @user` - Connect with a match\n"
                "`!viewteam` - View all active connections\n"
                "`!myteam` - View permanent teammates only\n"
                "`!makedecision @user keep/release` - Decide after 30min\n"
                "`!removemember @user` - Remove a permanent teammate"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💬 Messaging Commands",
            value=(
                "`!msg Name <message>` - Message by profile name\n"
                "`!msg \"Name With Spaces\" <msg>` - For spaced names\n"
                "`!dm username <message>` - Message by Discord username\n"
                "**Or just send a DM** if you have 1 connection!"
            ),
            inline=False
        )
        
        embed.add_field(
            name="ℹ️ System Info",
            value=f"• Max {MAX_CONNECTIONS} connections per user\n• 30-minute trial period\n• Keep or release teammates\n• Chat via bot relay",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("Error: DISCORD_TOKEN environment variable not set")
        return
    
    bot.run(token)

if __name__ == "__main__":
    main()
