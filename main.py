import asyncio
import discord
from dotenv import load_dotenv
from discord.ext import commands
import os
import requests
import aiohttp
from datetime import datetime, timedelta
from discord.ui import View, Button, Select
from math import radians, cos, sin, asin, sqrt

# Store user data (in production, use a database)
user_data = {}
# Store active connections with timestamps
active_connections = {}  # {(user1_id, user2_id): {'timestamp': datetime, 'user1_decision': None, 'user2_decision': None}}
# Maximum connections per user
MAX_CONNECTIONS = 5

# Singapore MRT Stations with approximate coordinates (latitude, longitude)
MRT_COORDINATES = {
    # North-South Line
    "Jurong East": (1.3333, 103.7422),
    "Bukit Batok": (1.3490, 103.7497),
    "Bukit Gombak": (1.3587, 103.7518),
    "Choa Chu Kang": (1.3854, 103.7443),
    "Yew Tee": (1.3970, 103.7472),
    "Kranji": (1.4250, 103.7619),
    "Marsiling": (1.4327, 103.7740),
    "Woodlands": (1.4370, 103.7868),
    "Admiralty": (1.4406, 103.8009),
    "Sembawang": (1.4491, 103.8202),
    "Canberra": (1.4430, 103.8297),
    "Yishun": (1.4296, 103.8350),
    "Khatib": (1.4172, 103.8329),
    "Yio Chu Kang": (1.3818, 103.8450),
    "Ang Mo Kio": (1.3700, 103.8495),
    "Bishan": (1.3510, 103.8484),
    "Braddell": (1.3405, 103.8468),
    "Toa Payoh": (1.3326, 103.8476),
    "Novena": (1.3204, 103.8438),
    "Newton": (1.3127, 103.8383),
    "Orchard": (1.3044, 103.8318),
    "Somerset": (1.3007, 103.8390),
    "Dhoby Ghaut": (1.2990, 103.8455),
    "City Hall": (1.2932, 103.8519),
    "Raffles Place": (1.2837, 103.8512),
    "Marina Bay": (1.2762, 103.8541),
    "Marina South Pier": (1.2712, 103.8633),
    
    # East-West Line
    "Pasir Ris": (1.3730, 103.9493),
    "Tampines": (1.3536, 103.9456),
    "Simei": (1.3434, 103.9533),
    "Tanah Merah": (1.3275, 103.9464),
    "Bedok": (1.3240, 103.9300),
    "Kembangan": (1.3210, 103.9130),
    "Eunos": (1.3196, 103.9034),
    "Paya Lebar": (1.3177, 103.8926),
    "Aljunied": (1.3164, 103.8826),
    "Kallang": (1.3114, 103.8714),
    "Lavender": (1.3075, 103.8631),
    "Bugis": (1.3006, 103.8560),
    "Tanjong Pagar": (1.2765, 103.8457),
    "Outram Park": (1.2803, 103.8395),
    "Tiong Bahru": (1.2862, 103.8269),
    "Redhill": (1.2896, 103.8172),
    "Queenstown": (1.2942, 103.8060),
    "Commonwealth": (1.3025, 103.7980),
    "Buona Vista": (1.3071, 103.7904),
    "Dover": (1.3113, 103.7786),
    "Clementi": (1.3150, 103.7652),
    "Chinese Garden": (1.3425, 103.7325),
    "Lakeside": (1.3444, 103.7210),
    "Boon Lay": (1.3389, 103.7058),
    "Pioneer": (1.3375, 103.6974),
    "Joo Koon": (1.3276, 103.6782),
    "Gul Circle": (1.3194, 103.6606),
    "Tuas Crescent": (1.3209, 103.6493),
    "Tuas West Road": (1.3300, 103.6394),
    "Tuas Link": (1.3404, 103.6367),
    
    # Circle Line
    "Bras Basah": (1.2969, 103.8509),
    "Esplanade": (1.2936, 103.8555),
    "Promenade": (1.2930, 103.8610),
    "Nicoll Highway": (1.2999, 103.8634),
    "Stadium": (1.3031, 103.8754),
    "Mountbatten": (1.3063, 103.8822),
    "Dakota": (1.3082, 103.8881),
    "MacPherson": (1.3267, 103.8902),
    "Tai Seng": (1.3357, 103.8882),
    "Bartley": (1.3425, 103.8793),
    "Serangoon": (1.3496, 103.8734),
    "Lorong Chuan": (1.3516, 103.8636),
    "Marymount": (1.3487, 103.8394),
    "Caldecott": (1.3378, 103.8394),
    "Botanic Gardens": (1.3225, 103.8155),
    "Farrer Road": (1.3172, 103.8075),
    "Holland Village": (1.3120, 103.7963),
    "one-north": (1.2996, 103.7875),
    "Kent Ridge": (1.2935, 103.7845),
    "Haw Par Villa": (1.2823, 103.7818),
    "Pasir Panjang": (1.2762, 103.7912),
    "Labrador Park": (1.2722, 103.8030),
    "Telok Blangah": (1.2704, 103.8096),
    "HarbourFront": (1.2653, 103.8220),
    
    # Downtown Line
    "Bukit Panjang": (1.3787, 103.7619),
    "Cashew": (1.3693, 103.7646),
    "Hillview": (1.3625, 103.7676),
    "Beauty World": (1.3415, 103.7757),
    "King Albert Park": (1.3353, 103.7832),
    "Sixth Avenue": (1.3306, 103.7969),
    "Tan Kah Kee": (1.3256, 103.8072),
    "Stevens": (1.3199, 103.8256),
    "Little India": (1.3066, 103.8552),
    "Rochor": (1.3038, 103.8524),
    "Bayfront": (1.2822, 103.8593),
    "Downtown": (1.2796, 103.8538),
    "Telok Ayer": (1.2824, 103.8485),
    "Chinatown": (1.2844, 103.8437),
    "Fort Canning": (1.2935, 103.8444),
    "Bencoolen": (1.2988, 103.8504),
    "Jalan Besar": (1.3055, 103.8554),
    "Bendemeer": (1.3137, 103.8622),
    "Geylang Bahru": (1.3213, 103.8712),
    "Mattar": (1.3267, 103.8831),
    "Ubi": (1.3300, 103.8996),
    "Kaki Bukit": (1.3348, 103.9082),
    "Bedok North": (1.3348, 103.9182),
    "Bedok Reservoir": (1.3365, 103.9334),
    "Tampines West": (1.3455, 103.9383),
    "Tampines East": (1.3564, 103.9555),
    "Upper Changi": (1.3418, 103.9612),
    "Expo": (1.3350, 103.9614),
    
    # North-East Line
    "Clarke Quay": (1.2886, 103.8467),
    "Farrer Park": (1.3122, 103.8540),
    "Boon Keng": (1.3193, 103.8615),
    "Potong Pasir": (1.3315, 103.8687),
    "Woodleigh": (1.3398, 103.8707),
    "Kovan": (1.3605, 103.8850),
    "Hougang": (1.3712, 103.8926),
    "Buangkok": (1.3828, 103.8927),
    "Sengkang": (1.3916, 103.8955),
    "Punggol": (1.4054, 103.9022),
    
    # Thomson-East Coast Line
    "Woodlands North": (1.4483, 103.7861),
    "Woodlands South": (1.4276, 103.7943),
    "Springleaf": (1.3977, 103.8175),
    "Lentor": (1.3847, 103.8358),
    "Mayflower": (1.3658, 103.8367),
    "Bright Hill": (1.3619, 103.8328),
    "Upper Thomson": (1.3546, 103.8341),
    "Mount Pleasant": (1.3263, 103.8348),
    "Napier": (1.3040, 103.8131),
    "Orchard Boulevard": (1.3017, 103.8244),
    "Great World": (1.2934, 103.8324),
    "Havelock": (1.2875, 103.8351),
    "Maxwell": (1.2805, 103.8442),
    "Shenton Way": (1.2788, 103.8495),
    "Marina South": (1.2711, 103.8637),
    "Gardens by the Bay": (1.2789, 103.8649),
    "Tanjong Rhu": (1.2934, 103.8774),
    "Katong Park": (1.3014, 103.8866),
    "Tanjong Katong": (1.3050, 103.8962),
    "Marine Parade": (1.3021, 103.9058),
    "Marine Terrace": (1.3051, 103.9153),
    "Siglap": (1.3132, 103.9266),
    "Bayshore": (1.3216, 103.9325),
    "Bedok South": (1.3210, 103.9439),
    "Sungei Bedok": (1.3239, 103.9485),
}

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

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees).
    Returns distance in kilometers.
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    
    return round(c * r, 1)

def get_mrt_distance(station1, station2):
    """
    Calculate distance between two MRT stations.
    Returns distance in km or None if station not found.
    """
    if station1 not in MRT_COORDINATES or station2 not in MRT_COORDINATES:
        return None
    
    lat1, lon1 = MRT_COORDINATES[station1]
    lat2, lon2 = MRT_COORDINATES[station2]
    
    return haversine_distance(lat1, lon1, lat2, lon2)

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
    except Exception as e:
        print(f"Error downloading photo: {e}")
    return None

def calculate_match_score(person1, person2):
    """Calculate how well two people match based on games and location"""
    common_games = list(set(person1.games) & set(person2.games))
    match_score = len(common_games) * 20
    
    # Calculate MRT distance if both have MRT locations
    distance_km = None
    if person1.location in MRT_COORDINATES and person2.location in MRT_COORDINATES:
        distance_km = get_mrt_distance(person1.location, person2.location)
        
        # Bonus points for being closer (max 30 points)
        if distance_km is not None:
            if distance_km < 2:
                match_score += 30
            elif distance_km < 5:
                match_score += 20
            elif distance_km < 10:
                match_score += 10
    
    return {
        'score': match_score,
        'common_games': common_games,
        'distance_km': distance_km
    }

def get_connection_key(user1_id, user2_id):
    """Generate a consistent connection key"""
    return tuple(sorted([user1_id, user2_id]))

def get_user_connections(user_id):
    """Get all connections for a user"""
    return [key for key in active_connections.keys() if user_id in key]

def get_other_user_id(connection_key, user_id):
    """Get the other user's ID from a connection key"""
    return connection_key[0] if connection_key[1] == user_id else connection_key[1]

def main():
    load_dotenv()
    
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    
    bot = commands.Bot(command_prefix='!', intents=intents)
    
    @bot.event
    async def on_ready():
        print(f'{bot.user} has connected to Discord!')
        print(f'Bot is in {len(bot.guilds)} server(s)')

    @bot.command()
    async def setup(ctx):
        """Create a gaming profile"""
        user_id = ctx.author.id
        
        if user_id in user_data:
            await ctx.send("❌ You already have a profile! Use `!update` to modify it or `!delete` to start over.")
            return
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        
        try:
            # Step 1: Name
            await ctx.send("🎮 **Let's set up your gaming profile!**\n\n**Step 1/5:** What's your name?")
            name_msg = await bot.wait_for('message', check=check, timeout=60.0)
            name = name_msg.content.strip()
            
            # Step 2: Age
            await ctx.send(f"**Step 2/5:** How old are you, {name}? (Enter a number)")
            age_msg = await bot.wait_for('message', check=check, timeout=60.0)
            try:
                age = int(age_msg.content.strip())
                if age < 1:
                    await ctx.send("❌ Please enter a valid age.")
                    return
            except ValueError:
                await ctx.send("❌ Please enter a valid number for age.")
                return
            
            # Step 3: Games
            await ctx.send(
                "**Step 3/5:** What games do you play?\n"
                "Please enter them separated by commas (e.g., `Valorant, League of Legends, Minecraft`)"
            )
            games_msg = await bot.wait_for('message', check=check, timeout=60.0)
            games = [game.strip() for game in games_msg.content.split(',')]
            
            # Step 4: MRT Location
            await ctx.send("**Step 4/5:** Select your nearest MRT station from the dropdown below:")
            
            view = MRTSelectView(user_id, bot)
            location_msg = await ctx.send("Choose your MRT station:", view=view)
            
            await view.wait()
            
            if view.selected_station is None:
                await ctx.send("❌ Setup timed out. Please try again with `!setup`")
                return
            
            location = view.selected_station
            
            # Step 5: Bio
            await ctx.send(
                "**Step 5/5:** Tell us a bit about yourself!\n"
                "What's your gaming style, when do you play, or anything else you'd like to share?"
            )
            bio_msg = await bot.wait_for('message', check=check, timeout=120.0)
            bio = bio_msg.content.strip()
            
            # Optional: Photo
            await ctx.send(
                "**Optional:** Want to add a profile photo? Upload an image now or type `skip`.\n"
                "(You can use your Discord avatar or upload a custom image)"
            )
            
            photo_url = None
            photo_response = await bot.wait_for('message', check=check, timeout=60.0)
            
            if photo_response.content.lower() != 'skip':
                if photo_response.attachments:
                    photo_url = photo_response.attachments[0].url
                    await download_photo(photo_url, user_id)
                elif ctx.author.avatar:
                    photo_url = ctx.author.avatar.url
                    await download_photo(photo_url, user_id)
            elif ctx.author.avatar:
                photo_url = ctx.author.avatar.url
                await download_photo(photo_url, user_id)
            
            # Create person object
            person = Person(name, age, games, location, bio, photo_url)
            user_data[user_id] = person
            
            # Create confirmation embed
            embed = discord.Embed(
                title="✅ Profile Created Successfully!",
                description=f"Welcome to the gaming community, {name}!",
                color=discord.Color.green()
            )
            embed.add_field(name="Name", value=name, inline=True)
            embed.add_field(name="Age", value=str(age), inline=True)
            embed.add_field(name="Games", value=", ".join(games), inline=False)
            embed.add_field(name="📍 Nearest MRT", value=location, inline=True)
            embed.add_field(name="Bio", value=bio, inline=False)
            
            if photo_url:
                embed.set_thumbnail(url=photo_url)
            
            embed.set_footer(text="Use !findmatch to find gaming buddies!")
            
            await ctx.send(embed=embed)
            
        except asyncio.TimeoutError:
            await ctx.send("❌ Setup timed out. Please try again with `!setup`")

    @bot.command()
    async def profile(ctx, member: discord.Member = None):
        """View a user's profile"""
        target = member or ctx.author
        user_id = target.id
        
        if user_id not in user_data:
            if member:
                await ctx.send(f"❌ {member.display_name} doesn't have a profile yet!")
            else:
                await ctx.send("❌ You don't have a profile! Create one with `!setup`")
            return
        
        person = user_data[user_id]
        
        embed = discord.Embed(
            title=f"🎮 {person.name}'s Gaming Profile",
            color=discord.Color.blue()
        )
        embed.add_field(name="Name", value=person.name, inline=True)
        embed.add_field(name="Age", value=str(person.age), inline=True)
        embed.add_field(name="Games", value=", ".join(person.games) if person.games else "None", inline=False)
        embed.add_field(name="📍 Nearest MRT", value=person.location, inline=True)
        embed.add_field(name="Bio", value=person.bio, inline=False)
        
        if person.photo_url:
            embed.set_thumbnail(url=person.photo_url)
        
        # Show connections count
        connections = get_user_connections(user_id)
        permanent_count = sum(1 for key in connections if active_connections[key].get('permanent', False))
        embed.set_footer(text=f"Permanent Teammates: {permanent_count}/{MAX_CONNECTIONS}")
        
        await ctx.send(embed=embed)

    @bot.command()
    async def findmatch(ctx):
        """Find best gaming matches"""
        user_id = ctx.author.id
        
        if user_id not in user_data:
            await ctx.send("❌ You need to create a profile first! Use `!setup`")
            return
        
        current_person = user_data[user_id]
        user_connections = get_user_connections(user_id)
        permanent_connections = [key for key in user_connections if active_connections[key].get('permanent', False)]
        
        if len(permanent_connections) >= MAX_CONNECTIONS:
            await ctx.send(f"❌ You've reached the maximum of {MAX_CONNECTIONS} permanent teammates!\nUse `!removemember @user` to make space.")
            return
        
        # Find potential matches (excluding self and existing connections)
        matches = []
        for other_id, other_person in user_data.items():
            if other_id == user_id:
                continue
            
            connection_key = get_connection_key(user_id, other_id)
            if connection_key in active_connections:
                continue
            
            match_data = calculate_match_score(current_person, other_person)
            if match_data['score'] > 0:
                matches.append((other_id, match_data))
        
        if not matches:
            await ctx.send("😔 No matches found! Try updating your profile or check back later.")
            return
        
        # Sort by match score
        matches.sort(key=lambda x: x[1]['score'], reverse=True)
        top_matches = matches[:5]
        
        embed = discord.Embed(
            title="🎯 Your Top Gaming Matches",
            description=f"Found {len(matches)} potential teammates!",
            color=discord.Color.gold()
        )
        
        for other_id, match_data in top_matches:
            other_person = user_data[other_id]
            
            try:
                member = await bot.fetch_user(other_id)
                
                # Build match field value with distance
                field_value = (
                    f"@{member.name}\n"
                    f"Match Score: {match_data['score']}%\n"
                    f"🎮 Common Games: {', '.join(match_data['common_games'])}\n"
                    f"📍 {other_person.location}"
                )
                
                # Add distance if available
                if match_data['distance_km'] is not None:
                    field_value += f" ({match_data['distance_km']} km away)"
                
                field_value += f"\n📝 {other_person.bio[:80]}..." if len(other_person.bio) > 80 else f"\n📝 {other_person.bio}"
                
                embed.add_field(
                    name=f"⭐ {other_person.name}",
                    value=field_value,
                    inline=False
                )
            except:
                pass
        
        embed.set_footer(text="Use !connect @user to team up with a match!")
        await ctx.send(embed=embed)

    @bot.command()
    async def connect(ctx, member: discord.Member):
        """Connect with a matched user"""
        user_id = ctx.author.id
        other_id = member.id
        
        if user_id not in user_data or other_id not in user_data:
            await ctx.send("❌ Both users need profiles to connect!")
            return
        
        if user_id == other_id:
            await ctx.send("❌ You can't connect with yourself!")
            return
        
        user_connections = get_user_connections(user_id)
        other_connections = get_user_connections(other_id)
        
        permanent_user = [key for key in user_connections if active_connections[key].get('permanent', False)]
        permanent_other = [key for key in other_connections if active_connections[key].get('permanent', False)]
        
        if len(permanent_user) >= MAX_CONNECTIONS:
            await ctx.send(f"❌ You've reached the maximum of {MAX_CONNECTIONS} permanent teammates!")
            return
        
        if len(permanent_other) >= MAX_CONNECTIONS:
            await ctx.send(f"❌ {member.display_name} has reached their maximum teammates!")
            return
        
        connection_key = get_connection_key(user_id, other_id)
        
        if connection_key in active_connections:
            await ctx.send(f"❌ You're already connected with {member.display_name}!")
            return
        
        # Create trial connection
        active_connections[connection_key] = {
            'timestamp': datetime.now(),
            'user1_decision': None,
            'user2_decision': None,
            'permanent': False
        }
        
        # Calculate match info including distance
        match_data = calculate_match_score(user_data[user_id], user_data[other_id])
        
        # Notify both users
        embed = discord.Embed(
            title="🎉 New Connection!",
            description=f"{ctx.author.mention} and {member.mention} are now connected!",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Trial Period",
            value="You have 30 minutes to chat. After that, use `!makedecision @user keep` to make this permanent!",
            inline=False
        )
        embed.add_field(name="Match Score", value=f"{match_data['score']}%", inline=True)
        embed.add_field(name="Common Games", value=", ".join(match_data['common_games']), inline=True)
        
        # Add distance info
        if match_data['distance_km'] is not None:
            embed.add_field(
                name="📍 Distance", 
                value=f"{match_data['distance_km']} km between {user_data[user_id].location} and {user_data[other_id].location}",
                inline=False
            )
        
        embed.set_footer(text="Start chatting with !msg or send a DM to the bot!")
        
        await ctx.send(embed=embed)
        
        # Send DMs to both users
        try:
            await ctx.author.send(f"✅ You're now connected with {user_data[other_id].name}! Send messages using `!msg {user_data[other_id].name} <message>`")
        except:
            pass
        
        try:
            await member.send(f"✅ You're now connected with {user_data[user_id].name}! Send messages using `!msg {user_data[user_id].name} <message>`")
        except:
            pass

    @bot.command()
    async def makedecision(ctx, member: discord.Member, decision: str):
        """Decide to keep or release a teammate after trial period"""
        user_id = ctx.author.id
        other_id = member.id
        
        if user_id not in user_data or other_id not in user_data:
            await ctx.send("❌ Invalid connection!")
            return
        
        connection_key = get_connection_key(user_id, other_id)
        
        if connection_key not in active_connections:
            await ctx.send(f"❌ You're not connected with {member.display_name}!")
            return
        
        connection = active_connections[connection_key]
        
        if connection.get('permanent', False):
            await ctx.send("✅ This connection is already permanent!")
            return
        
        # Check if 30 minutes have passed
        time_elapsed = datetime.now() - connection['timestamp']
        if time_elapsed < timedelta(minutes=30):
            remaining = timedelta(minutes=30) - time_elapsed
            minutes_left = int(remaining.total_seconds() / 60)
            await ctx.send(f"⏰ Trial period not over yet! {minutes_left} minutes remaining.")
            return
        
        decision = decision.lower()
        if decision not in ['keep', 'release']:
            await ctx.send("❌ Decision must be either `keep` or `release`")
            return
        
        # Determine which user is making the decision
        if user_id == connection_key[0]:
            connection['user1_decision'] = decision
        else:
            connection['user2_decision'] = decision
        
        # Check if both users have decided
        if connection['user1_decision'] and connection['user2_decision']:
            if connection['user1_decision'] == 'keep' and connection['user2_decision'] == 'keep':
                connection['permanent'] = True
                await ctx.send(f"⭐ **Connection is now permanent!** You and {member.display_name} are now permanent teammates!")
                
                # Notify the other user
                try:
                    await member.send(f"⭐ Your connection with {user_data[user_id].name} is now permanent!")
                except:
                    pass
            else:
                # Remove connection
                del active_connections[connection_key]
                await ctx.send(f"👋 Connection with {member.display_name} has been released.")
                
                try:
                    await member.send(f"👋 Your connection with {user_data[user_id].name} has been released.")
                except:
                    pass
        else:
            await ctx.send(f"✅ Your decision has been recorded. Waiting for {member.display_name}'s decision...")
            
            try:
                await member.send(f"⏰ {user_data[user_id].name} has made their decision. Use `!makedecision @{ctx.author.name} keep/release` to decide!")
            except:
                pass

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
        """Remove a permanent teammate"""
        user_id = ctx.author.id
        other_id = member.id
        
        connection_key = get_connection_key(user_id, other_id)
        
        if connection_key not in active_connections:
            await ctx.send(f"❌ You're not connected with {member.display_name}!")
            return
        
        if not active_connections[connection_key].get('permanent', False):
            await ctx.send("❌ This is a trial connection! Use `!makedecision` instead.")
            return
        
        # Remove connection
        del active_connections[connection_key]
        
        await ctx.send(f"✅ Removed {member.display_name} from your team.")
        
        try:
            await member.send(f"👋 {user_data[user_id].name} has removed you from their team.")
        except:
            pass

    @bot.command()
    async def msg(ctx, *, args: str):
        """Send a message to a connected user by their profile name"""
        user_id = ctx.author.id
        
        if user_id not in user_data:
            await ctx.send("❌ You need a profile to send messages!")
            return
        
        # Parse target name and message
        # Handle quoted names: !msg "Name With Spaces" message here
        # Handle unquoted names: !msg SingleName message here
        target_name = None
        message = None
        
        if args.startswith('"'):
            # Find closing quote
            end_quote = args.find('"', 1)
            if end_quote == -1:
                await ctx.send('❌ Missing closing quote for name. Use: `!msg "Name" message`')
                return
            target_name = args[1:end_quote]
            message = args[end_quote+1:].strip()
        else:
            # No quotes - split on first space
            parts = args.split(None, 1)
            if len(parts) < 2:
                await ctx.send("❌ Usage: `!msg Name message` or `!msg \"Name With Spaces\" message`")
                return
            target_name = parts[0]
            message = parts[1]
        
        if not message:
            await ctx.send("❌ Please include a message to send!")
            return
        
        # Find user by profile name
        target_id = None
        for uid, person in user_data.items():
            if person.name.lower() == target_name.lower():
                target_id = uid
                break
        
        if target_id is None:
            await ctx.send(f"❌ No user found with name '{target_name}'")
            return
        
        connection_key = get_connection_key(user_id, target_id)
        
        if connection_key not in active_connections:
            await ctx.send(f"❌ You're not connected with {target_name}!")
            return
        
        # Send message
        try:
            target_user = await bot.fetch_user(target_id)
            sender_name = user_data[user_id].name
            
            await target_user.send(f"💬 **Message from {sender_name}:**\n{message}")
            await ctx.send(f"✅ Message sent to {target_name}!")
        except Exception as e:
            await ctx.send(f"❌ Failed to send message: {str(e)}")

    @bot.command()
    async def dm(ctx, *, args: str):
        """Send a message to a connected user by their Discord username"""
        user_id = ctx.author.id
        
        if user_id not in user_data:
            await ctx.send("❌ You need a profile to send messages!")
            return
        
        # Parse target username and message
        # Handle quoted usernames: !dm "Username With Spaces" message here
        # Handle unquoted usernames: !dm Username message here
        target_username = None
        message = None
        
        if args.startswith('"'):
            # Find closing quote
            end_quote = args.find('"', 1)
            if end_quote == -1:
                await ctx.send('❌ Missing closing quote for username. Use: `!dm "Username" message`')
                return
            target_username = args[1:end_quote]
            message = args[end_quote+1:].strip()
        else:
            # No quotes - split on first space
            parts = args.split(None, 1)
            if len(parts) < 2:
                await ctx.send("❌ Usage: `!dm Username message` or `!dm \"Username With Spaces\" message`")
                return
            target_username = parts[0]
            message = parts[1]
        
        if not message:
            await ctx.send("❌ Please include a message to send!")
            return
        
        # Find user by Discord username
        target_id = None
        for guild in bot.guilds:
            for member in guild.members:
                if member.name.lower() == target_username.lower():
                    if member.id in user_data:
                        target_id = member.id
                        break
            if target_id:
                break
        
        if target_id is None:
            await ctx.send(f"❌ No connected user found with username '{target_username}'")
            return
        
        connection_key = get_connection_key(user_id, target_id)
        
        if connection_key not in active_connections:
            await ctx.send(f"❌ You're not connected with @{target_username}!")
            return
        
        # Send message
        try:
            target_user = await bot.fetch_user(target_id)
            sender_name = user_data[user_id].name
            
            await target_user.send(f"💬 **Message from {sender_name}:**\n{message}")
            await ctx.send(f"✅ Message sent to @{target_username}!")
        except Exception as e:
            await ctx.send(f"❌ Failed to send message: {str(e)}")

    @bot.event
    async def on_message(message):
        """Handle direct messages to the bot"""
        # Process commands first
        await bot.process_commands(message)
        
        # Ignore bot's own messages
        if message.author.bot:
            return
        
        # Check if it's a DM
        if isinstance(message.channel, discord.DMChannel):
            user_id = message.author.id
            
            if user_id not in user_data:
                return
            
            # Find all connections
            user_connections = get_user_connections(user_id)
            
            if len(user_connections) == 0:
                await message.channel.send("❌ You're not connected with anyone! Use `!findmatch` to find teammates.")
                return
            
            if len(user_connections) == 1:
                # Auto-send to the only connection
                connection_key = user_connections[0]
                other_id = get_other_user_id(connection_key, user_id)
                
                try:
                    other_user = await bot.fetch_user(other_id)
                    sender_name = user_data[user_id].name
                    
                    await other_user.send(f"💬 **Message from {sender_name}:**\n{message.content}")
                    await message.channel.send(f"✅ Message sent to {user_data[other_id].name}!")
                except Exception as e:
                    await message.channel.send(f"❌ Failed to send message: {str(e)}")
            else:
                # Multiple connections - ask user to specify
                names = []
                for key in user_connections:
                    other_id = get_other_user_id(key, user_id)
                    if other_id in user_data:
                        names.append(user_data[other_id].name)
                
                await message.channel.send(
                    f"You have multiple connections! Please use:\n"
                    f"`!msg <name> <message>` to specify who to message.\n\n"
                    f"Your connections: {', '.join(names)}"
                )

    @bot.command()
    async def update(ctx):
        """Update your profile"""
        user_id = ctx.author.id
        
        if user_id not in user_data:
            await ctx.send("❌ You don't have a profile! Create one with `!setup`")
            return
        
        await ctx.send("🔄 Profile update coming soon! For now, use `!delete` then `!setup` to recreate your profile.")

    @bot.command()
    async def delete(ctx):
        """Delete your profile"""
        user_id = ctx.author.id
        
        if user_id not in user_data:
            await ctx.send("❌ You don't have a profile!")
            return
        
        # Remove all connections
        connections_to_remove = get_user_connections(user_id)
        for key in connections_to_remove:
            other_id = get_other_user_id(key, user_id)
            del active_connections[key]
            
            # Notify the other user
            try:
                other_user = await bot.fetch_user(other_id)
                await other_user.send(f"👋 {user_data[user_id].name} has deleted their profile. Your connection has been removed.")
            except:
                pass
        
        del user_data[user_id]
        await ctx.send("✅ Your profile has been deleted along with all connections.")

    @bot.command()
    async def viewteam(ctx, member: discord.Member = None):
        """View all your active connections or get info about a specific one"""
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
                    
                    # Calculate distance
                    match_data = calculate_match_score(user_data[user_id], other_person)
                    distance_text = f" ({match_data['distance_km']} km away)" if match_data['distance_km'] else ""
                    
                    # Smart formatting for names with spaces
                    msg_cmd = f'!msg "{other_person.name}"' if ' ' in other_person.name else f'!msg {other_person.name}'
                    dm_cmd = f'!dm "{other_user.name}"' if ' ' in other_user.name else f'!dm {other_user.name}'
                    
                    embed.add_field(
                        name=f"{status} - {other_person.name}",
                        value=f"{other_user.mention} (`{other_user.name}`)\n📍 {other_person.location}{distance_text}\n💬 `{msg_cmd} <message>`\n📧 `{dm_cmd} <message>`",
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
        
        # Calculate distance
        match_data = calculate_match_score(user_data[user_id], other_person)
        distance_text = f"{match_data['distance_km']} km away" if match_data['distance_km'] else "Distance unavailable"
        
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
        embed.add_field(name="📍 Distance", value=distance_text, inline=True)
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
                
                # Add distance to field
                distance_text = f" ({match_data['distance_km']} km away)" if match_data['distance_km'] else ""
                
                field_value = (
                    f"@{member.name}\n"
                    f"🎮 Common Games: {', '.join(match_data['common_games'])}\n"
                    f"📍 {other_person.location}{distance_text}\n"
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
                "`!msg \"Name With Spaces\" <message>` - For names with spaces\n"
                "`!dm Username <message>` - Message by Discord username\n"
                "`!dm \"Username With Spaces\" <message>` - For usernames with spaces\n"
                "**Or just send a DM** if you have 1 connection!"
            ),
            inline=False
        )
        
        embed.add_field(
            name="ℹ️ System Info",
            value=f"• Max {MAX_CONNECTIONS} connections per user\n• 30-minute trial period\n• Keep or release teammates\n• Chat via bot relay\n• See distance between MRT stations!",
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
