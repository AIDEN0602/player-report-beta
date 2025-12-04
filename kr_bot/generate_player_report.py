"""
Player Report Generator
Downloads 100 recent ranked games and generates AI-powered player analysis
"""

import os
import asyncio
import aiohttp
from dotenv import load_dotenv
from typing import Optional, Dict, List
import json
from datetime import datetime

# Load environment
load_dotenv()
RIOT_API_KEY = os.getenv("RIOT_API_KEY")
RIOT_REGION = os.getenv("RIOT_REGION", "kr").lower()
RIOT_ROUTING = os.getenv("RIOT_ROUTING", "asia").lower()

if not RIOT_API_KEY:
    raise ValueError("❌ Missing RIOT_API_KEY in .env file!")

class RiotAPI:
    def __init__(self):
        self.api_key = RIOT_API_KEY
        self.region = RIOT_REGION
        self.routing = RIOT_ROUTING
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
                print(f"[API] {resp.status} - {url}")
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 429:
                    print("⚠️ Rate limit hit, waiting 2 seconds...")
                    await asyncio.sleep(2)
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

    async def get_match_ids(self, puuid: str, count: int = 100):
        """Get ranked match IDs"""
        url = f"https://{self.routing}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?queue=420&count={count}"
        return await self._get(url)

    async def get_match(self, match_id: str):
        url = f"https://{self.routing}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        return await self._get(url)

    async def analyze_player_detailed(self, puuid: str, count: int = 100):
        """Download and analyze 100 games with detailed stats"""
        print(f"\n📥 Downloading {count} recent ranked games...")

        match_ids = await self.get_match_ids(puuid, count)
        if not match_ids:
            return {"ok": False, "error": "No ranked games found"}

        print(f"✅ Found {len(match_ids)} match IDs")

        games_data = []
        player_stats = {
            "total_games": 0,
            "wins": 0,
            "losses": 0,
            "kills": 0,
            "deaths": 0,
            "assists": 0,
            "champion_stats": {},  # {champion: {games, wins, kills, deaths, assists}}
            "role_stats": {},      # {role: {games, wins}}
            "recent_form": [],     # Last 20 games W/L
            "player_name": "Unknown",
            "games_detail": []     # Full game details for AI
        }

        for idx, match_id in enumerate(match_ids, 1):
            print(f"⏳ Downloading game {idx}/{len(match_ids)}...", end="\r")

            match = await self.get_match(match_id)
            if not match:
                await asyncio.sleep(0.5)  # Rate limit protection
                continue

            info = match.get("info", {})
            participants = info.get("participants", [])
            player = next((p for p in participants if p.get("puuid") == puuid), None)

            if not player:
                continue

            # Basic stats
            player_stats["total_games"] += 1
            player_stats["player_name"] = player.get("riotIdGameName", "Unknown")

            won = player.get("win", False)
            kills = player.get("kills", 0)
            deaths = player.get("deaths", 0)
            assists = player.get("assists", 0)
            champion = player.get("championName", "Unknown")
            role = player.get("teamPosition", "FILL")

            # Normalize role names
            role = role.replace("MIDDLE", "MID").replace("UTILITY", "SUP").replace("JUNGLE", "JG").replace("BOTTOM", "ADC")

            # Win/Loss
            if won:
                player_stats["wins"] += 1
            else:
                player_stats["losses"] += 1

            # KDA
            player_stats["kills"] += kills
            player_stats["deaths"] += deaths
            player_stats["assists"] += assists

            # Champion stats
            if champion not in player_stats["champion_stats"]:
                player_stats["champion_stats"][champion] = {
                    "games": 0, "wins": 0, "kills": 0, "deaths": 0, "assists": 0
                }
            player_stats["champion_stats"][champion]["games"] += 1
            if won:
                player_stats["champion_stats"][champion]["wins"] += 1
            player_stats["champion_stats"][champion]["kills"] += kills
            player_stats["champion_stats"][champion]["deaths"] += deaths
            player_stats["champion_stats"][champion]["assists"] += assists

            # Role stats
            if role not in player_stats["role_stats"]:
                player_stats["role_stats"][role] = {"games": 0, "wins": 0}
            player_stats["role_stats"][role]["games"] += 1
            if won:
                player_stats["role_stats"][role]["wins"] += 1

            # Recent form (last 20 games)
            if len(player_stats["recent_form"]) < 20:
                player_stats["recent_form"].append("W" if won else "L")

            # Detailed game data for AI
            game_detail = {
                "game_number": player_stats["total_games"],
                "champion": champion,
                "role": role,
                "win": won,
                "kda": f"{kills}/{deaths}/{assists}",
                "cs": player.get("totalMinionsKilled", 0) + player.get("neutralMinionsKilled", 0),
                "gold": player.get("goldEarned", 0),
                "damage": player.get("totalDamageDealtToChampions", 0),
                "vision_score": player.get("visionScore", 0),
                "game_duration": info.get("gameDuration", 0) // 60,  # minutes
            }
            player_stats["games_detail"].append(game_detail)

            # Rate limit protection
            await asyncio.sleep(0.5)

        print(f"\n✅ Downloaded {player_stats['total_games']} games successfully!")

        return {
            "ok": True,
            "stats": player_stats
        }

def generate_ai_prompt(stats: Dict) -> str:
    """Generate prompt for AI to analyze player"""

    # Calculate aggregated stats
    total_games = stats["total_games"]
    winrate = (stats["wins"] / total_games * 100) if total_games > 0 else 0
    kda = ((stats["kills"] + stats["assists"]) / max(stats["deaths"], 1))

    # Top champions
    top_champs = sorted(
        stats["champion_stats"].items(),
        key=lambda x: x[1]["games"],
        reverse=True
    )[:5]

    # Role distribution
    role_dist = sorted(
        stats["role_stats"].items(),
        key=lambda x: x[1]["games"],
        reverse=True
    )

    prompt = f"""# Player Analysis Request

## Player: {stats['player_name']}
## Games Analyzed: {total_games} (Recent Ranked Solo/Duo)

### Overall Stats
- Win Rate: {winrate:.1f}% ({stats['wins']}W {stats['losses']}L)
- KDA: {kda:.2f} ({stats['kills']}/{stats['deaths']}/{stats['assists']})
- Recent Form (Last 20): {' '.join(stats['recent_form'])}

### Role Distribution
"""

    for role, role_stat in role_dist:
        role_wr = (role_stat["wins"] / role_stat["games"] * 100) if role_stat["games"] > 0 else 0
        prompt += f"- {role}: {role_stat['games']} games ({role_wr:.1f}% WR)\n"

    prompt += "\n### Top 5 Champions\n"
    for champ, champ_stat in top_champs:
        champ_wr = (champ_stat["wins"] / champ_stat["games"] * 100) if champ_stat["games"] > 0 else 0
        champ_kda = ((champ_stat["kills"] + champ_stat["assists"]) / max(champ_stat["deaths"], 1))
        prompt += f"- {champ}: {champ_stat['games']} games ({champ_wr:.1f}% WR, {champ_kda:.2f} KDA)\n"

    prompt += "\n### Detailed Game History\n"
    prompt += "```\n"
    for game in stats["games_detail"][:30]:  # Show first 30 games detail
        result = "WIN " if game["win"] else "LOSS"
        prompt += f"Game {game['game_number']:3d} | {result} | {game['champion']:15s} | {game['role']:3s} | {game['kda']:9s} | {game['cs']:3d}CS | {game['damage']:6d}DMG\n"
    prompt += "```\n"

    prompt += """
### Analysis Request

Based on the above data, please provide:

1. **Player Strengths**: What does this player do well?
2. **Weaknesses**: What areas need improvement?
3. **Champion Pool Analysis**: Are they a one-trick or versatile?
4. **Role Performance**: Which role do they perform best in?
5. **Recent Form Analysis**: Are they on an upswing or downswing?
6. **Recommendations**:
   - Which champions should they focus on?
   - Which champions should they avoid?
   - What skills should they work on?
7. **Overall Rating**: Rate this player from 1-10 for their elo

Please provide a comprehensive analysis in Korean (한국어).
"""

    return prompt

async def main():
    print("="*60)
    print("🎮 LoL Player Report Generator")
    print("="*60)

    # Get player info
    riot_id = input("\n📝 Enter Riot ID (GameName#TAG): ").strip()

    if "#" not in riot_id:
        print("❌ Invalid format! Use: GameName#TAG")
        return

    game_name, tag_line = riot_id.split("#", 1)

    async with RiotAPI() as api:
        # Get account
        print(f"\n🔍 Looking up account: {riot_id}")
        account = await api.get_account_by_riot_id(game_name.strip(), tag_line.strip())

        if not account:
            print(f"❌ Account not found: {riot_id}")
            return

        puuid = account["puuid"]
        print(f"✅ Account found! PUUID: {puuid[:8]}...")

        # Analyze 100 games
        result = await api.analyze_player_detailed(puuid, 100)

        if not result.get("ok"):
            print(f"❌ Error: {result.get('error')}")
            return

        stats = result["stats"]

        # Generate AI prompt
        print("\n" + "="*60)
        print("📊 Generating AI Analysis Prompt...")
        print("="*60)

        ai_prompt = generate_ai_prompt(stats)

        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"player_report_{stats['player_name']}_{timestamp}.txt"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(ai_prompt)

        # Also save raw data as JSON
        json_filename = f"player_data_{stats['player_name']}_{timestamp}.json"
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        print(f"\n✅ Analysis prompt saved to: {filename}")
        print(f"✅ Raw data saved to: {json_filename}")
        print("\n" + "="*60)
        print("📋 AI Analysis Prompt Preview:")
        print("="*60)
        print(ai_prompt[:1000] + "\n... (truncated)")
        print("\n💡 Copy the content from the file and paste it to Claude/ChatGPT!")

if __name__ == "__main__":
    asyncio.run(main())
