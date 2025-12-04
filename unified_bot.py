"""
Unified Discord Bot with Multi-Region Support and AI Analysis
Supports KR, NA, EUW, and other regions
"""

import os
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import aiohttp
from typing import Optional, Dict
from datetime import datetime
import sys

# Load environment
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
RIOT_API_KEY = os.getenv("RIOT_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not TOKEN or not RIOT_API_KEY:
    raise ValueError("❌ Missing DISCORD_TOKEN or RIOT_API_KEY in .env file!")

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# User settings storage
user_settings: Dict[int, dict] = {}

# Region configurations
REGIONS = {
    "kr": {"platform": "kr", "routing": "asia", "name": "한국 (KR)"},
    "na": {"platform": "na1", "routing": "americas", "name": "북미 (NA)"},
    "euw": {"platform": "euw1", "routing": "europe", "name": "유럽 서부 (EUW)"},
    "eune": {"platform": "eun1", "routing": "europe", "name": "유럽 북동부 (EUNE)"},
    "br": {"platform": "br1", "routing": "americas", "name": "브라질 (BR)"},
    "lan": {"platform": "la1", "routing": "americas", "name": "라틴 북부 (LAN)"},
    "las": {"platform": "la2", "routing": "americas", "name": "라틴 남부 (LAS)"},
    "oce": {"platform": "oc1", "routing": "americas", "name": "오세아니아 (OCE)"},
    "jp": {"platform": "jp1", "routing": "asia", "name": "일본 (JP)"},
    "sg": {"platform": "sg2", "routing": "asia", "name": "싱가포르 (SG)"},
}

# Try to import analyzer
try:
    # Add current directory to path for imports
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(current_dir, "na_bot")):
        sys.path.insert(0, os.path.join(current_dir, "na_bot"))

    from generate_player_report import RiotAPI as BaseRiotAPI
    from ai_analyzer import PlayerAnalyzer

    has_analyzer = bool(ANTHROPIC_API_KEY)
    analyzer = PlayerAnalyzer() if has_analyzer else None
except ImportError as e:
    print(f"⚠️  Warning: Could not import analysis modules: {e}")
    has_analyzer = False
    analyzer = None
    BaseRiotAPI = None

# Enhanced RiotAPI with region support
class MultiRegionRiotAPI:
    def __init__(self, region_code: str):
        self.api_key = RIOT_API_KEY
        region_info = REGIONS.get(region_code.lower(), REGIONS["na"])
        self.region = region_info["platform"]
        self.routing = region_info["routing"]
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=30)
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
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 429:
                    await asyncio.sleep(2)
                return None
        except Exception as e:
            print(f"[API ERROR] {e}")
            return None

    async def get_account_by_riot_id(self, game_name: str, tag_line: str):
        url = f"https://{self.routing}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        return await self._get(url)

    async def analyze_player_detailed(self, puuid: str, count: int = 100):
        """Use the imported RiotAPI if available"""
        if BaseRiotAPI:
            # Create temporary RiotAPI instance with our session
            api = BaseRiotAPI()
            api.api_key = self.api_key
            api.region = self.region
            api.routing = self.routing
            api.session = self.session
            return await api.analyze_player_detailed(puuid, count)
        else:
            return {"ok": False, "error": "Analysis module not available"}

@bot.event
async def on_ready():
    print(f"\n{'='*60}")
    print(f"✅ Bot Online: {bot.user}")
    print(f"🌍 Multi-Region Support: {', '.join(REGIONS.keys()).upper()}")
    print(f"🤖 AI Analysis: {'Enabled' if has_analyzer else 'Disabled'}")
    print(f"{'='*60}\n")

    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands\n")
    except Exception as e:
        print(f"❌ Sync failed: {e}\n")

@bot.tree.command(name="help", description="Show all available commands")
async def help_command(interaction: discord.Interaction):
    """Complete help menu"""

    # Check if user has set region
    user_region = user_settings.get(interaction.user.id, {}).get("region", None)

    embed = discord.Embed(
        title="🎮 LoL AI Analysis Bot",
        description="Claude AI 기반 전적 분석 시스템",
        color=0x5865f2
    )

    # Region status
    if user_region:
        region_name = REGIONS[user_region]["name"]
        embed.add_field(
            name="🌍 현재 지역 설정",
            value=f"**{region_name}** ({user_region.upper()})",
            inline=False
        )
    else:
        embed.add_field(
            name="⚠️ 지역 미설정",
            value="먼저 `/region` 명령어로 지역을 설정하세요!",
            inline=False
        )

    # Setup commands
    embed.add_field(
        name="⚙️ 설정",
        value="`/region` - 지역 설정 (KR, NA, EUW 등)\n"
              "`/myinfo` - 내 설정 정보 확인",
        inline=False
    )

    # Analysis commands
    if has_analyzer:
        embed.add_field(
            name="🤖 AI 전적 분석",
            value="`/analyze riot_id:이름#태그` - **완전 분석** (100게임, 2-3분)\n"
                  "  • 예상 티어, 플레이 스타일, 강점/약점\n"
                  "  • 승리 플랜, 개선 로드맵\n\n"
                  "`/quick riot_id:이름#태그` - **빠른 분석** (30게임, 1분)\n"
                  "  • 기본 통계, 예상 티어, 즉시 개선",
            inline=False
        )
    else:
        embed.add_field(
            name="📊 기본 분석",
            value="`/stats riot_id:이름#태그` - 기본 통계 확인\n"
                  "⚠️ AI 분석은 현재 비활성화 상태",
            inline=False
        )

    # Example
    embed.add_field(
        name="💡 사용 예시",
        value="1️⃣ `/region` 선택 → **KR** 선택\n"
              "2️⃣ `/analyze riot_id:Faker#KR1`\n"
              "3️⃣ AI 분석 결과 확인!",
        inline=False
    )

    # Tips
    embed.add_field(
        name="📌 팁",
        value="• Riot ID 형식: `게임이름#태그` (예: `Hide on bush#KR1`)\n"
              "• 지역은 한 번만 설정하면 자동 저장됩니다\n"
              "• 분석은 최근 랭크 게임 기준입니다",
        inline=False
    )

    embed.set_footer(text=f"Powered by Claude AI | 지원 지역: {len(REGIONS)}개")

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="region", description="Set your region (KR, NA, EUW, etc.)")
async def set_region(interaction: discord.Interaction):
    """Region selection with dropdown"""

    class RegionSelect(discord.ui.Select):
        def __init__(self):
            options = [
                discord.SelectOption(
                    label=info["name"],
                    value=code,
                    description=f"{code.upper()} - {info['platform']}",
                    emoji="🌍"
                )
                for code, info in sorted(REGIONS.items(), key=lambda x: x[1]["name"])
            ]

            super().__init__(
                placeholder="지역을 선택하세요...",
                min_values=1,
                max_values=1,
                options=options
            )

        async def callback(self, interaction: discord.Interaction):
            selected = self.values[0]
            region_name = REGIONS[selected]["name"]

            # Save user setting
            if interaction.user.id not in user_settings:
                user_settings[interaction.user.id] = {}
            user_settings[interaction.user.id]["region"] = selected

            embed = discord.Embed(
                title="✅ 지역 설정 완료",
                description=f"**{region_name}** ({selected.upper()})로 설정되었습니다!",
                color=0x00ff00
            )
            embed.add_field(
                name="다음 단계",
                value="이제 `/analyze` 명령어로 전적 분석을 시작하세요!",
                inline=False
            )

            await interaction.response.edit_message(embed=embed, view=None)

    class RegionView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            self.add_item(RegionSelect())

    embed = discord.Embed(
        title="🌍 지역 선택",
        description="분석할 서버 지역을 선택해주세요",
        color=0x3498db
    )
    embed.add_field(
        name="지원 지역",
        value="\n".join([f"• {info['name']}" for info in REGIONS.values()]),
        inline=False
    )

    await interaction.response.send_message(embed=embed, view=RegionView(), ephemeral=True)

@bot.tree.command(name="myinfo", description="Show your current settings")
async def my_info(interaction: discord.Interaction):
    """Display user settings"""

    settings = user_settings.get(interaction.user.id, {})

    embed = discord.Embed(
        title=f"⚙️ {interaction.user.display_name}의 설정",
        color=0x9b59b6
    )

    if "region" in settings:
        region_code = settings["region"]
        region_name = REGIONS[region_code]["name"]
        embed.add_field(
            name="🌍 지역 설정",
            value=f"**{region_name}** ({region_code.upper()})",
            inline=False
        )
    else:
        embed.add_field(
            name="⚠️ 지역 미설정",
            value="`/region` 명령어로 지역을 설정하세요",
            inline=False
        )

    embed.set_footer(text="설정을 변경하려면 /region을 사용하세요")

    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="analyze", description="Complete AI analysis (100 games)")
@app_commands.describe(riot_id="Riot ID (e.g., Faker#KR1)")
async def analyze_full(interaction: discord.Interaction, riot_id: str):
    """Full AI analysis"""

    # Check region
    user_region = user_settings.get(interaction.user.id, {}).get("region")
    if not user_region:
        await interaction.response.send_message(
            "⚠️ 먼저 `/region` 명령어로 지역을 설정해주세요!",
            ephemeral=True
        )
        return

    if not has_analyzer:
        await interaction.response.send_message(
            "❌ AI 분석 기능이 현재 비활성화 상태입니다.",
            ephemeral=True
        )
        return

    if "#" not in riot_id:
        await interaction.response.send_message(
            "❌ 잘못된 형식입니다! 형식: `게임이름#태그`",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    try:
        game_name, tag_line = riot_id.split("#", 1)
        region_name = REGIONS[user_region]["name"]

        status_msg = await interaction.followup.send(
            f"📥 **[{region_name}]** {riot_id}의 전적을 다운로드 중...\n"
            f"⏳ 100게임 분석 (약 2-3분 소요)"
        )

        async with MultiRegionRiotAPI(user_region) as api:
            account = await api.get_account_by_riot_id(game_name.strip(), tag_line.strip())
            if not account:
                await status_msg.edit(content=f"❌ 계정을 찾을 수 없습니다: **{riot_id}**")
                return

            result = await api.analyze_player_detailed(account["puuid"], 100)

            if not result.get("ok"):
                await status_msg.edit(content=f"❌ 오류: {result.get('error')}")
                return

            stats = result["stats"]

        await status_msg.edit(
            content=f"📥 ✅ {stats['total_games']}게임 다운로드 완료\n"
                    f"🤖 AI가 데이터를 분석 중..."
        )

        analysis = analyzer.analyze_player(stats)

        if "error" in analysis:
            await status_msg.edit(content=f"❌ 분석 오류: {analysis['error']}")
            return

        await status_msg.delete()

        # Send results
        embeds = analyzer.format_for_discord(analysis)

        await interaction.followup.send(
            content=f"## 🎮 [{region_name}] {analysis['player_name']} 전적 분석 완료!\n"
                    f"분석된 게임: {stats['total_games']}개",
            embed=embeds[0] if embeds else None
        )

        for embed in embeds[1:]:
            await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"❌ 오류 발생: {str(e)}")
        print(f"Error in analyze: {e}")
        import traceback
        traceback.print_exc()

@bot.tree.command(name="quick", description="Quick analysis (30 games, faster)")
@app_commands.describe(riot_id="Riot ID (e.g., Faker#KR1)")
async def analyze_quick(interaction: discord.Interaction, riot_id: str):
    """Quick AI analysis"""

    user_region = user_settings.get(interaction.user.id, {}).get("region")
    if not user_region:
        await interaction.response.send_message(
            "⚠️ 먼저 `/region` 명령어로 지역을 설정해주세요!",
            ephemeral=True
        )
        return

    if not has_analyzer:
        await interaction.response.send_message(
            "❌ AI 분석 기능이 현재 비활성화 상태입니다.",
            ephemeral=True
        )
        return

    if "#" not in riot_id:
        await interaction.response.send_message(
            "❌ 잘못된 형식입니다! 형식: `게임이름#태그`",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    try:
        game_name, tag_line = riot_id.split("#", 1)
        region_name = REGIONS[user_region]["name"]

        status_msg = await interaction.followup.send(
            f"⚡ **[{region_name}]** {riot_id}의 빠른 분석 중... (30게임)"
        )

        async with MultiRegionRiotAPI(user_region) as api:
            account = await api.get_account_by_riot_id(game_name.strip(), tag_line.strip())
            if not account:
                await status_msg.edit(content=f"❌ 계정을 찾을 수 없습니다: **{riot_id}**")
                return

            result = await api.analyze_player_detailed(account["puuid"], 30)

            if not result.get("ok"):
                await status_msg.edit(content=f"❌ 오류: {result.get('error')}")
                return

            stats = result["stats"]

        await status_msg.edit(content=f"🤖 AI 분석 중... ({stats['total_games']}게임)")

        analysis = analyzer.analyze_player(stats)

        if "error" in analysis:
            await status_msg.edit(content=f"❌ 분석 오류: {analysis['error']}")
            return

        await status_msg.delete()

        # Quick summary
        embed = discord.Embed(
            title=f"⚡ [{region_name}] {analysis['player_name']} 빠른 분석",
            description=f"**{stats['total_games']}게임 기반**",
            color=0x00ff00 if analysis['winrate'] >= 50 else 0xff0000
        )

        embed.add_field(
            name="📊 통계",
            value=f"승률: **{analysis['winrate']}%**\nKDA: **{analysis['kda']}**",
            inline=True
        )

        if "predicted_tier" in analysis:
            embed.add_field(
                name="🎯 예상 티어",
                value=analysis["predicted_tier"][:200],
                inline=False
            )

        if "immediate_improvements" in analysis:
            embed.add_field(
                name="⚡ 즉시 개선 가능",
                value=analysis["immediate_improvements"][:1000],
                inline=False
            )

        await interaction.followup.send(
            content=f"## ⚡ {riot_id} 빠른 분석 완료!",
            embed=embed
        )

    except Exception as e:
        await interaction.followup.send(f"❌ 오류 발생: {str(e)}")
        print(f"Error in quick analyze: {e}")

if __name__ == "__main__":
    print("\n🚀 Starting Unified LoL AI Analysis Bot...\n")
    print("📁 Make sure generate_player_report.py and ai_analyzer.py are in na_bot/ or kr_bot/\n")
    bot.run(TOKEN)
