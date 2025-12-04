"""
Discord Bot with AI-Powered Player Analysis
Complete analysis system with Claude integration
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

# Import our analysis modules
sys.path.append(os.path.dirname(__file__))
from generate_player_report import RiotAPI
from ai_analyzer import PlayerAnalyzer

# Load environment
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
RIOT_API_KEY = os.getenv("RIOT_API_KEY")
RIOT_REGION = os.getenv("RIOT_REGION", "na1").lower()
RIOT_ROUTING = os.getenv("RIOT_ROUTING", "americas").lower()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not TOKEN or not RIOT_API_KEY:
    raise ValueError("❌ Missing DISCORD_TOKEN or RIOT_API_KEY in .env file!")

if not ANTHROPIC_API_KEY:
    print("⚠️  Warning: ANTHROPIC_API_KEY not found. AI analysis will be disabled.")

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize analyzer
analyzer = PlayerAnalyzer() if ANTHROPIC_API_KEY else None

@bot.event
async def on_ready():
    print(f"\n{'='*60}")
    print(f"✅ Bot Online: {bot.user}")
    print(f"📍 Region: {RIOT_REGION.upper()} | Routing: {RIOT_ROUTING.upper()}")
    print(f"🤖 AI Analysis: {'Enabled' if analyzer else 'Disabled'}")
    print(f"{'='*60}\n")

    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands\n")
    except Exception as e:
        print(f"❌ Sync failed: {e}\n")

@bot.tree.command(name="analyze", description="AI-powered player analysis (100 games)")
@app_commands.describe(riot_id="Riot ID (e.g., Faker#KR1)")
async def analyze_player(interaction: discord.Interaction, riot_id: str):
    """
    Complete AI analysis of a player based on 100 recent games
    """

    if not analyzer:
        await interaction.response.send_message(
            "❌ AI analysis is currently disabled. Please configure ANTHROPIC_API_KEY.",
            ephemeral=True
        )
        return

    # Validate format
    if "#" not in riot_id:
        await interaction.response.send_message(
            "❌ Invalid format! Use: `GameName#TAG`",
            ephemeral=True
        )
        return

    # Defer response (this will take a while)
    await interaction.response.defer()

    try:
        game_name, tag_line = riot_id.split("#", 1)

        # Step 1: Download data
        status_msg = await interaction.followup.send(
            f"📥 **Step 1/3:** Downloading 100 games for **{riot_id}**...\n"
            f"⏳ This may take 1-2 minutes..."
        )

        async with RiotAPI() as api:
            # Get account
            account = await api.get_account_by_riot_id(game_name.strip(), tag_line.strip())
            if not account:
                await status_msg.edit(content=f"❌ Account not found: **{riot_id}**")
                return

            puuid = account["puuid"]

            # Analyze 100 games
            result = await api.analyze_player_detailed(puuid, 100)

            if not result.get("ok"):
                await status_msg.edit(content=f"❌ Error: {result.get('error')}")
                return

            stats = result["stats"]

        # Step 2: AI Analysis
        await status_msg.edit(
            content=f"📥 **Step 1/3:** ✅ Downloaded {stats['total_games']} games\n"
                    f"🤖 **Step 2/3:** AI is analyzing the data...\n"
                    f"⏳ Please wait..."
        )

        analysis = analyzer.analyze_player(stats)

        if "error" in analysis:
            await status_msg.edit(content=f"❌ Analysis error: {analysis['error']}")
            return

        # Step 3: Format and send
        await status_msg.edit(
            content=f"📥 **Step 1/3:** ✅ Downloaded {stats['total_games']} games\n"
                    f"🤖 **Step 2/3:** ✅ Analysis complete\n"
                    f"📊 **Step 3/3:** Generating report..."
        )

        # Delete status message
        await status_msg.delete()

        # Send analysis embeds
        embeds = analyzer.format_for_discord(analysis)

        # Send first embed with content
        await interaction.followup.send(
            content=f"## 🎮 {analysis['player_name']} 전적 분석 완료!\n분석된 게임: {stats['total_games']}개",
            embed=embeds[0] if embeds else None
        )

        # Send remaining embeds
        for embed in embeds[1:]:
            await interaction.followup.send(embed=embed)

        # Optionally send full analysis as file
        if "full_analysis" in analysis and len(analysis["full_analysis"]) > 3000:
            with open(f"temp_analysis_{interaction.user.id}.txt", "w", encoding="utf-8") as f:
                f.write(f"# {analysis['player_name']} 전적 분석\n\n")
                f.write(analysis["full_analysis"])

            with open(f"temp_analysis_{interaction.user.id}.txt", "rb") as f:
                await interaction.followup.send(
                    content="📄 전체 분석 리포트 (텍스트 파일)",
                    file=discord.File(f, filename=f"{analysis['player_name']}_analysis.txt")
                )

            # Cleanup
            os.remove(f"temp_analysis_{interaction.user.id}.txt")

    except Exception as e:
        await interaction.followup.send(f"❌ Error occurred: {str(e)}")
        print(f"Error in analyze command: {e}")
        import traceback
        traceback.print_exc()

@bot.tree.command(name="quick_analyze", description="Quick player analysis (30 games, faster)")
@app_commands.describe(riot_id="Riot ID (e.g., Faker#KR1)")
async def quick_analyze(interaction: discord.Interaction, riot_id: str):
    """
    Faster analysis with 30 games
    """

    if not analyzer:
        await interaction.response.send_message(
            "❌ AI analysis is currently disabled. Please configure ANTHROPIC_API_KEY.",
            ephemeral=True
        )
        return

    if "#" not in riot_id:
        await interaction.response.send_message(
            "❌ Invalid format! Use: `GameName#TAG`",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    try:
        game_name, tag_line = riot_id.split("#", 1)

        status_msg = await interaction.followup.send(
            f"📥 Downloading 30 games for **{riot_id}**...",
        )

        async with RiotAPI() as api:
            account = await api.get_account_by_riot_id(game_name.strip(), tag_line.strip())
            if not account:
                await status_msg.edit(content=f"❌ Account not found: **{riot_id}**")
                return

            result = await api.analyze_player_detailed(account["puuid"], 30)

            if not result.get("ok"):
                await status_msg.edit(content=f"❌ Error: {result.get('error')}")
                return

            stats = result["stats"]

        await status_msg.edit(content=f"🤖 Analyzing {stats['total_games']} games...")

        analysis = analyzer.analyze_player(stats)

        if "error" in analysis:
            await status_msg.edit(content=f"❌ Analysis error: {analysis['error']}")
            return

        await status_msg.delete()

        # Send quick summary
        embed = discord.Embed(
            title=f"⚡ {analysis['player_name']} 빠른 분석",
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
        await interaction.followup.send(f"❌ Error occurred: {str(e)}")
        print(f"Error in quick_analyze: {e}")

@bot.tree.command(name="help_analysis", description="Show analysis commands help")
async def help_analysis(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎮 LoL AI Analysis Bot",
        description="Claude AI를 활용한 전적 분석 시스템",
        color=0x5865f2
    )

    embed.add_field(
        name="/analyze",
        value="**완전 분석** (100게임)\n"
              "- 예상 티어\n"
              "- 플레이 스타일 분석\n"
              "- 강점/약점\n"
              "- 승리 플랜\n"
              "- 개선 로드맵\n"
              "⏱️ 약 2-3분 소요",
        inline=False
    )

    embed.add_field(
        name="/quick_analyze",
        value="**빠른 분석** (30게임)\n"
              "- 기본 통계\n"
              "- 예상 티어\n"
              "- 즉시 개선 가능한 부분\n"
              "⏱️ 약 1분 소요",
        inline=False
    )

    embed.add_field(
        name="사용 예시",
        value="`/analyze riot_id:Faker#KR1`\n"
              "`/quick_analyze riot_id:Hide on bush#KR1`",
        inline=False
    )

    embed.set_footer(text=f"Region: {RIOT_REGION.upper()} | Powered by Claude AI")

    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    print("\n🚀 Starting AI Analysis Bot...\n")
    bot.run(TOKEN)
