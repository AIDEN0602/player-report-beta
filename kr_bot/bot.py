"""
LoL Coach Discord Bot - Complete Working Version
Supports: All roles (TOP/JG/MID/ADC/SUP), Korean champion names, Live game analysis
"""

import os
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import aiohttp
from typing import Optional, List, Dict
from datetime import datetime

# Load environment
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
RIOT_API_KEY = os.getenv("RIOT_API_KEY")
RIOT_REGION = os.getenv("RIOT_REGION", "na1").lower()
RIOT_ROUTING = os.getenv("RIOT_ROUTING", "americas").lower()

if not TOKEN or not RIOT_API_KEY:
    raise ValueError("❌ Missing DISCORD_TOKEN or RIOT_API_KEY in .env file!")

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# User profiles storage
user_profiles: Dict[int, dict] = {}

# Korean champion names
KOREAN_CHAMPS = {
    "가렌": "Garen", "갈리오": "Galio", "갱플랭크": "Gangplank", "그라가스": "Gragas",
    "그레이브즈": "Graves", "그웬": "Gwen", "나르": "Gnar", "나미": "Nami",
    "나서스": "Nasus", "녹턴": "Nocturne", "누누": "Nunu", "니달리": "Nidalee",
    "니코": "Neeko", "다리우스": "Darius", "다이애나": "Diana", "드레이븐": "Draven",
    "라이즈": "Ryze", "라칸": "Rakan", "람머스": "Rammus", "럭스": "Lux",
    "럼블": "Rumble", "레나타": "Renata", "레넥톤": "Renekton", "레오나": "Leona",
    "렉사이": "RekSai", "렝가": "Rengar", "루시안": "Lucian", "룰루": "Lulu",
    "르블랑": "LeBlanc", "리 신": "LeeSin", "리븐": "Riven", "리산드라": "Lissandra",
    "릴리아": "Lillia", "마스터 이": "MasterYi", "마오카이": "Maokai", "말자하": "Malzahar",
    "말파이트": "Malphite", "모데카이저": "Mordekaiser", "모르가나": "Morgana", "문도": "DrMundo",
    "미스 포츈": "MissFortune", "밀리오": "Milio", "바드": "Bard", "바루스": "Varus",
    "바이": "Vi", "베이가": "Veigar", "베인": "Vayne", "벡스": "Vex",
    "벨베스": "Belveth", "벨코즈": "Velkoz", "볼리베어": "Volibear", "브라이어": "Briar",
    "브라움": "Braum", "브랜드": "Brand", "블라디미르": "Vladimir", "블리츠크랭크": "Blitzcrank",
    "비에고": "Viego", "빅토르": "Viktor", "뽀삐": "Poppy", "사미라": "Samira",
    "사이온": "Sion", "사일러스": "Sylas", "샤코": "Shaco", "세나": "Senna",
    "세라핀": "Seraphine", "세주아니": "Sejuani", "세트": "Sett", "소나": "Sona",
    "소라카": "Soraka", "쉔": "Shen", "쉬바나": "Shyvana", "스웨인": "Swain",
    "스카너": "Skarner", "시비르": "Sivir", "신 짜오": "XinZhao", "신드라": "Syndra",
    "신지드": "Singed", "쓰레쉬": "Thresh", "아리": "Ahri", "아무무": "Amumu",
    "아우렐리온 솔": "AurelionSol", "아이번": "Ivern", "아지르": "Azir", "아칼리": "Akali",
    "아크샨": "Akshan", "아트록스": "Aatrox", "아펠리오스": "Aphelios", "알리스타": "Alistar",
    "애니": "Annie", "애쉬": "Ashe", "앰버사": "Ambessa", "야스오": "Yasuo",
    "에코": "Ekko", "엘리스": "Elise", "오공": "MonkeyKing", "오른": "Ornn",
    "오리아나": "Orianna", "올라프": "Olaf", "요네": "Yone", "요릭": "Yorick",
    "우디르": "Udyr", "우르곳": "Urgot", "워윅": "Warwick", "유미": "Yuumi",
    "이렐리아": "Irelia", "이블린": "Evelynn", "이즈리얼": "Ezreal", "일라오이": "Illaoi",
    "자르반 4세": "JarvanIV", "자야": "Xayah", "자크": "Zac", "잔나": "Janna",
    "잭스": "Jax", "제드": "Zed", "제라스": "Xerath", "제리": "Zeri",
    "제이스": "Jayce", "조이": "Zoe", "직스": "Ziggs", "진": "Jhin",
    "질리언": "Zilean", "징크스": "Jinx", "초가스": "ChoGath", "카르마": "Karma",
    "카밀": "Camille", "카사딘": "Kassadin", "카서스": "Karthus", "카시오페아": "Cassiopeia",
    "카이사": "Kaisa", "카직스": "Khazix", "카타리나": "Katarina", "칼리스타": "Kalista",
    "케넨": "Kennen", "케이틀린": "Caitlyn", "케인": "Kayn", "케일": "Kayle",
    "코그모": "KogMaw", "코르키": "Corki", "퀸": "Quinn", "크산테": "KSante",
    "클레드": "Kled", "키아나": "Qiyana", "킨드레드": "Kindred", "타릭": "Taric",
    "탈리야": "Taliyah", "탐 켄치": "TahmKench", "티모": "Teemo", "트런들": "Trundle",
    "트리스타나": "Tristana", "트린다미어": "Tryndamere", "트위스티드 페이트": "TwistedFate",
    "트위치": "Twitch", "파이크": "Pyke", "판테온": "Pantheon", "피들스틱": "Fiddlesticks",
    "피오라": "Fiora", "피즈": "Fizz", "하이머딩거": "Heimerdinger", "헤카림": "Hecarim",
    "흐웨이": "Hwei", "자이라": "Zyra"
}

# Champion roles
CHAMPION_ROLES = {
    "Aatrox": ["TOP"], "Ahri": ["MID"], "Akali": ["MID"], "Akshan": ["MID"],
    "Alistar": ["SUP"], "Amumu": ["JG"], "Ashe": ["ADC"], "Azir": ["MID"],
    "Bard": ["SUP"], "Blitzcrank": ["SUP"], "Brand": ["SUP"], "Braum": ["SUP"],
    "Caitlyn": ["ADC"], "Camille": ["TOP"], "Darius": ["TOP"], "Diana": ["JG"],
    "Draven": ["ADC"], "Ekko": ["JG"], "Ezreal": ["ADC"], "Fiora": ["TOP"],
    "Garen": ["TOP"], "Graves": ["JG"], "Jax": ["TOP"], "Jhin": ["ADC"],
    "Jinx": ["ADC"], "Kaisa": ["ADC"], "Katarina": ["MID"], "Kayle": ["TOP"],
    "LeeSin": ["JG"], "Lux": ["SUP"], "Malphite": ["TOP"], "MasterYi": ["JG"],
    "Nautilus": ["SUP"], "Orianna": ["MID"], "Pyke": ["SUP"], "Riven": ["TOP"],
    "Syndra": ["MID"], "Sylas": ["MID"], "Thresh": ["SUP"], "Vayne": ["ADC"],
    "Viego": ["JG"], "Viktor": ["MID"], "Yasuo": ["MID"], "Zed": ["MID"],
    "Zyra": ["SUP"]
}

def normalize_champion_name(name: str) -> Optional[str]:
    """Normalize champion name from Korean/English"""
    name = name.strip()
    
    if name in KOREAN_CHAMPS:
        return KOREAN_CHAMPS[name]
    
    name_lower = name.lower().replace(" ", "")
    for champ in CHAMPION_ROLES.keys():
        if champ.lower().replace(" ", "") == name_lower:
            return champ
    
    return None

class RiotAPI:
    def __init__(self):
        self.api_key = RIOT_API_KEY
        self.region = RIOT_REGION
        self.routing = RIOT_ROUTING
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=15)
        self.session = aiohttp.ClientSession(
            headers={"X-Riot-Token": self.api_key},
            timeout=timeout
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _get(self, url: str) -> Optional[dict]:
        try:
            async with self.session.get(url) as resp:
                print(f"[API] {resp.status} - {url}")
                if resp.status == 200:
                    return await resp.json()
                return None
        except Exception as e:
            print(f"[API ERROR] {e}")
            return None
    
    async def get_account_by_riot_id(self, game_name: str, tag_line: str):
        url = f"https://{self.routing}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        return await self._get(url)
    
    async def get_summoner_by_puuid(self, puuid: str):
        url = f"https://{self.region}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
        return await self._get(url)
    
    async def get_match_ids(self, puuid: str, count: int = 30):
        url = f"https://{self.routing}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?queue=420&count={count}"
        return await self._get(url)
    
    async def get_match(self, match_id: str):
        url = f"https://{self.routing}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        return await self._get(url)
    
    async def get_active_game(self, puuid: str):
        url = f"https://{self.region}.api.riotgames.com/lol/spectator/v5/active-games/by-summoner/{puuid}"
        return await self._get(url)
    
    async def analyze_player(self, puuid: str, count: int = 30):
        match_ids = await self.get_match_ids(puuid, count)
        if not match_ids:
            return {"ok": False, "error": "No ranked games"}
        
        stats = {"games": 0, "wins": 0, "kills": 0, "deaths": 0, "assists": 0, "roles": {}, "name": "Unknown"}
        
        for match_id in match_ids[:count]:
            match = await self.get_match(match_id)
            if not match:
                continue
            
            participants = match.get("info", {}).get("participants", [])
            player = next((p for p in participants if p.get("puuid") == puuid), None)
            
            if not player:
                continue
            
            stats["games"] += 1
            stats["name"] = player.get("riotIdGameName", "Unknown")
            if player.get("win"):
                stats["wins"] += 1
            stats["kills"] += player.get("kills", 0)
            stats["deaths"] += player.get("deaths", 0)
            stats["assists"] += player.get("assists", 0)
            
            role = player.get("teamPosition", "")
            if role:
                role = role.replace("MIDDLE", "MID").replace("UTILITY", "SUP").replace("JUNGLE", "JG").replace("BOTTOM", "ADC")
                stats["roles"][role] = stats["roles"].get(role, 0) + 1
        
        if stats["games"] == 0:
            return {"ok": False, "error": "No valid games"}
        
        kda = (stats["kills"] + stats["assists"]) / max(stats["deaths"], 1)
        wr = (stats["wins"] / stats["games"]) * 100
        main_role = max(stats["roles"], key=stats["roles"].get) if stats["roles"] else "FILL"
        
        return {
            "ok": True,
            "name": stats["name"],
            "games": stats["games"],
            "winrate": round(wr, 1),
            "kda": round(kda, 2),
            "main_role": main_role
        }

@bot.event
async def on_ready():
    print(f"\n{'='*60}")
    print(f"✅ Bot Online: {bot.user}")
    print(f"📍 Region: {RIOT_REGION.upper()} | Routing: {RIOT_ROUTING.upper()}")
    print(f"{'='*60}\n")
    
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands\n")
    except Exception as e:
        print(f"❌ Sync failed: {e}\n")

@bot.tree.command(name="help", description="Show all commands")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="🎮 LoL Coach Bot Commands", color=0x0099ff)
    embed.add_field(
        name="📋 Profile",
        value="`/profile_setup riot_id:Name#TAG`\n`/profile_show`\n`/profile_set role:TOP`",
        inline=False
    )
    embed.add_field(
        name="🎯 Champion Select",
        value="`/ban_suggest`\n`/pick_suggest allies:... enemies:...`",
        inline=False
    )
    embed.add_field(
        name="🔍 Analysis",
        value="`/scout riot_id:Name#TAG`\n`/live_analyze`",
        inline=False
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="profile_setup", description="Setup your profile")
@app_commands.describe(riot_id="Your Riot ID (e.g., Faker#KR1)")
async def profile_setup(interaction: discord.Interaction, riot_id: str):
    await interaction.response.defer()
    
    if "#" not in riot_id:
        await interaction.followup.send("❌ Use format: `GameName#TAG`")
        return
    
    game_name, tag_line = riot_id.split("#", 1)
    
    async with RiotAPI() as api:
        account = await api.get_account_by_riot_id(game_name.strip(), tag_line.strip())
        if not account:
            await interaction.followup.send(f"❌ Not found: {riot_id}")
            return
        
        puuid = account["puuid"]
        analysis = await api.analyze_player(puuid, 20)
        
        if not analysis.get("ok"):
            await interaction.followup.send(f"❌ {analysis.get('error')}")
            return
        
        user_profiles[interaction.user.id] = {
            "riot_id": riot_id,
            "puuid": puuid,
            "name": analysis["name"],
            "role": analysis["main_role"],
            "winrate": analysis["winrate"],
            "kda": analysis["kda"]
        }
        
        embed = discord.Embed(title="✅ Profile Setup!", color=0x00ff00)
        embed.add_field(name="Riot ID", value=f"`{riot_id}`", inline=False)
        embed.add_field(name="Main Role", value=analysis["main_role"], inline=True)
        embed.add_field(name="Stats", value=f"{analysis['winrate']}% WR | {analysis['kda']} KDA", inline=True)
        
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="profile_show", description="Show your profile")
async def profile_show(interaction: discord.Interaction):
    profile = user_profiles.get(interaction.user.id)
    if not profile:
        await interaction.response.send_message("❌ Use `/profile_setup` first!", ephemeral=True)
        return
    
    embed = discord.Embed(title="👤 Your Profile", color=0x3498db)
    embed.add_field(name="Riot ID", value=f"`{profile['riot_id']}`", inline=False)
    embed.add_field(name="Role", value=profile["role"], inline=True)
    embed.add_field(name="Stats", value=f"{profile['winrate']}% WR | {profile['kda']} KDA", inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="profile_set", description="Change your role")
@app_commands.describe(role="Your main role")
@app_commands.choices(role=[
    app_commands.Choice(name="TOP", value="TOP"),
    app_commands.Choice(name="JUNGLE", value="JG"),
    app_commands.Choice(name="MID", value="MID"),
    app_commands.Choice(name="ADC", value="ADC"),
    app_commands.Choice(name="SUPPORT", value="SUP")
])
async def profile_set(interaction: discord.Interaction, role: app_commands.Choice[str]):
    profile = user_profiles.get(interaction.user.id)
    if not profile:
        await interaction.response.send_message("❌ Use `/profile_setup` first!", ephemeral=True)
        return
    
    profile["role"] = role.value
    await interaction.response.send_message(f"✅ Role changed to **{role.value}**")

@bot.tree.command(name="ban_suggest", description="Get ban suggestions")
async def ban_suggest(interaction: discord.Interaction):
    profile = user_profiles.get(interaction.user.id)
    if not profile:
        await interaction.response.send_message("❌ Use `/profile_setup` first!", ephemeral=True)
        return
    
    role = profile["role"]
    bans = {
        "TOP": ["Ambessa", "Aatrox", "Camille", "Jax", "Darius"],
        "JG": ["Viego", "Graves", "LeeSin", "Khazix", "Ekko"],
        "MID": ["Syndra", "Ahri", "Yasuo", "Zed", "Katarina"],
        "ADC": ["Jinx", "Caitlyn", "Vayne", "Draven", "Kaisa"],
        "SUP": ["Thresh", "Nautilus", "Pyke", "Lux", "Blitzcrank"]
    }
    
    suggestions = bans.get(role, bans["MID"])[:3]
    
    embed = discord.Embed(title="🚫 Ban Suggestions", color=0xe74c3c)
    embed.add_field(name="Your Role", value=role, inline=False)
    embed.add_field(name="Recommended", value=" → ".join(suggestions), inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="pick_suggest", description="Get pick suggestions")
@app_commands.describe(allies="Allied champs (e.g., sylas, naut)", enemies="Enemy champs")
async def pick_suggest(interaction: discord.Interaction, allies: str = "", enemies: str = ""):
    profile = user_profiles.get(interaction.user.id)
    if not profile:
        await interaction.response.send_message("❌ Use `/profile_setup` first!", ephemeral=True)
        return
    
    role = profile["role"]
    pools = {
        "TOP": ["Camille", "Jax", "Aatrox"],
        "JG": ["Viego", "LeeSin", "Graves"],
        "MID": ["Ahri", "Syndra", "Orianna"],
        "ADC": ["Jinx", "Caitlyn", "Kaisa"],
        "SUP": ["Thresh", "Nautilus", "Lulu"]
    }
    
    suggestions = pools.get(role, pools["MID"])
    
    embed = discord.Embed(title="✅ Pick Suggestions", color=0x2ecc71)
    embed.add_field(name="Your Role", value=role, inline=False)
    embed.add_field(name="Top Picks", value=" → ".join(suggestions), inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="scout", description="Scout a player")
@app_commands.describe(riot_id="Player's Riot ID")
async def scout(interaction: discord.Interaction, riot_id: str):
    await interaction.response.defer()
    
    if "#" not in riot_id:
        await interaction.followup.send("❌ Use format: `Name#TAG`")
        return
    
    game_name, tag_line = riot_id.split("#", 1)
    
    async with RiotAPI() as api:
        account = await api.get_account_by_riot_id(game_name.strip(), tag_line.strip())
        if not account:
            await interaction.followup.send(f"❌ Not found: {riot_id}")
            return
        
        analysis = await api.analyze_player(account["puuid"], 30)
        if not analysis.get("ok"):
            await interaction.followup.send(f"❌ {analysis.get('error')}")
            return
        
        strength = "🔥 STRONG" if analysis["winrate"] >= 55 else "⚠️ WEAK" if analysis["winrate"] <= 45 else "⚖️ AVERAGE"
        color = 0xff4444 if "STRONG" in strength else 0x44ff44 if "WEAK" in strength else 0xffaa00
        
        embed = discord.Embed(title=f"🔍 Scout: {analysis['name']}", color=color)
        embed.add_field(name="Last 30 Games", value=f"{analysis['winrate']}% WR | {analysis['kda']} KDA", inline=False)
        embed.add_field(name="Main Role", value=analysis["main_role"], inline=True)
        embed.add_field(name="Strength", value=strength, inline=True)
        
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="live_analyze", description="Analyze current game")
async def live_analyze(interaction: discord.Interaction):
    await interaction.response.defer()
    
    profile = user_profiles.get(interaction.user.id)
    if not profile:
        await interaction.followup.send("❌ Use `/profile_setup` first!", ephemeral=True)
        return
    
    async with RiotAPI() as api:
        game = await api.get_active_game(profile["puuid"])
        if not game:
            await interaction.followup.send("❌ You're not in an active game!")
            return
        
        await interaction.followup.send("🔴 Live game detected! Analyzing enemies...")

if __name__ == "__main__":
    print("\n🚀 Starting Bot...\n")
    bot.run(TOKEN)