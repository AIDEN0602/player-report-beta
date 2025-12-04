"""
AI-Powered Player Analysis using Claude API
Analyzes player data and provides detailed insights
"""

import os
from anthropic import Anthropic
from typing import Dict
from dotenv import load_dotenv

load_dotenv()

class PlayerAnalyzer:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def analyze_player(self, player_stats: Dict) -> Dict[str, str]:
        """
        Analyze player statistics using Claude AI
        Returns: Dict with analysis sections
        """

        # Build analysis prompt
        prompt = self._build_analysis_prompt(player_stats)

        # Call Claude API
        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4000,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Parse response
            analysis_text = message.content[0].text
            return self._parse_analysis(analysis_text, player_stats)

        except Exception as e:
            return {
                "error": f"Analysis failed: {str(e)}",
                "player_name": player_stats.get("player_name", "Unknown")
            }

    def _build_analysis_prompt(self, stats: Dict) -> str:
        """Build detailed prompt for Claude"""

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

        prompt = f"""당신은 프로 레벨의 롤(League of Legends) 분석가입니다. 아래 플레이어의 전적을 분석하고 상세한 리포트를 작성해주세요.

## 플레이어: {stats['player_name']}
## 분석 게임 수: {total_games}게임 (최근 랭크 게임)

### 전체 통계
- 승률: {winrate:.1f}% ({stats['wins']}승 {stats['losses']}패)
- KDA: {kda:.2f} ({stats['kills']}/{stats['deaths']}/{stats['assists']})
- 최근 20게임: {' '.join(stats['recent_form'])}

### 포지션 분포
"""

        for role, role_stat in role_dist:
            role_wr = (role_stat["wins"] / role_stat["games"] * 100) if role_stat["games"] > 0 else 0
            prompt += f"- {role}: {role_stat['games']}게임 ({role_wr:.1f}% 승률)\n"

        prompt += "\n### 주요 챔피언 (Top 5)\n"
        for champ, champ_stat in top_champs:
            champ_wr = (champ_stat["wins"] / champ_stat["games"] * 100) if champ_stat["games"] > 0 else 0
            champ_kda = ((champ_stat["kills"] + champ_stat["assists"]) / max(champ_stat["deaths"], 1))
            prompt += f"- {champ}: {champ_stat['games']}게임 ({champ_wr:.1f}% 승률, {champ_kda:.2f} KDA)\n"

            # Matchups
            if champ_stat.get("vs_champions"):
                matchups = sorted(
                    champ_stat["vs_champions"].items(),
                    key=lambda x: x[1]["games"],
                    reverse=True
                )[:3]
                if matchups:
                    prompt += "  주요 매치업:\n"
                    for vs_champ, vs_stat in matchups:
                        vs_wr = (vs_stat["wins"] / vs_stat["games"] * 100) if vs_stat["games"] > 0 else 0
                        prompt += f"    vs {vs_champ}: {vs_stat['games']}게임 ({vs_wr:.1f}% 승률)\n"

        # Game timing
        prompt += "\n### 게임 길이별 승률\n"
        for time_cat in ["early", "mid", "late"]:
            time_stat = stats["time_stats"][time_cat]
            if time_stat["games"] > 0:
                time_wr = (time_stat["wins"] / time_stat["games"] * 100)
                time_label = "초반 (0-20분)" if time_cat == "early" else "중반 (20-30분)" if time_cat == "mid" else "후반 (30분+)"
                prompt += f"- {time_label}: {time_stat['games']}게임 ({time_wr:.1f}% 승률)\n"

        # Side performance
        blue_wr = (stats["side_stats"]["blue"]["wins"] / stats["side_stats"]["blue"]["games"] * 100) if stats["side_stats"]["blue"]["games"] > 0 else 0
        red_wr = (stats["side_stats"]["red"]["wins"] / stats["side_stats"]["red"]["games"] * 100) if stats["side_stats"]["red"]["games"] > 0 else 0
        prompt += f"\n### 사이드별 승률\n"
        prompt += f"- 블루 사이드: {stats['side_stats']['blue']['games']}게임 ({blue_wr:.1f}% 승률)\n"
        prompt += f"- 레드 사이드: {stats['side_stats']['red']['games']}게임 ({red_wr:.1f}% 승률)\n"

        # Multi-kills
        prompt += f"\n### 멀티킬\n"
        prompt += f"- 펜타킬: {stats['pentakills']}회\n"
        prompt += f"- 쿼드라킬: {stats['quadrakills']}회\n"
        prompt += f"- 트리플킬: {stats['triplekills']}회\n"

        # Objectives
        prompt += f"\n### 오브젝트 관여\n"
        prompt += f"- 바론: {stats['objective_stats']['baron_kills']}회\n"
        prompt += f"- 드래곤: {stats['objective_stats']['dragon_kills']}회\n"
        prompt += f"- 전령: {stats['objective_stats']['herald_kills']}회\n"

        # Death timing
        if stats["deaths"] > 0:
            early_death_pct = (stats["death_analysis"]["early_deaths"] / stats["deaths"] * 100)
            mid_death_pct = (stats["death_analysis"]["mid_deaths"] / stats["deaths"] * 100)
            late_death_pct = (stats["death_analysis"]["late_deaths"] / stats["deaths"] * 100)
            prompt += f"\n### 데스 타이밍\n"
            prompt += f"- 초반 (0-15분): {early_death_pct:.1f}%\n"
            prompt += f"- 중반 (15-25분): {mid_death_pct:.1f}%\n"
            prompt += f"- 후반 (25분+): {late_death_pct:.1f}%\n"

        prompt += """

## 분석 요청사항

다음 항목들을 **반드시 명확하게 구분**하여 분석해주세요:

### 1. 예상 티어
현재 통계로 예상되는 티어 범위 (예: 골드 3 ~ 플래티넘 4)

### 2. 플레이 스타일
이 플레이어의 전반적인 플레이 스타일과 특징

### 3. 강점
- 가장 잘하는 챔피언과 이유
- 뛰어난 플레이 요소
- 강한 게임 구간

### 4. 약점
- 피해야 할 챔피언
- 개선이 필요한 영역
- 취약한 게임 구간

### 5. 승리 플랜
구체적인 게임 플랜 (3-5가지)
- 챔피언 픽 전략
- 게임 운영 방향
- 포커스해야 할 요소

### 6. 즉시 개선 가능한 부분
당장 다음 게임부터 적용할 수 있는 실용적인 조언 (3가지)

### 7. 장기 성장 로드맵
티어 상승을 위한 단계별 계획

---

**응답 형식:** 각 섹션을 명확히 구분하고, 구체적이고 실행 가능한 조언을 제공해주세요.
이모지는 사용하지 말고, 전문적이면서도 친근한 톤으로 작성해주세요.
"""

        return prompt

    def _parse_analysis(self, analysis_text: str, stats: Dict) -> Dict[str, str]:
        """Parse Claude's response into structured sections"""

        sections = {
            "player_name": stats.get("player_name", "Unknown"),
            "total_games": stats.get("total_games", 0),
            "winrate": round((stats["wins"] / stats["total_games"] * 100) if stats["total_games"] > 0 else 0, 1),
            "kda": round((stats["kills"] + stats["assists"]) / max(stats["deaths"], 1), 2),
            "full_analysis": analysis_text
        }

        # Try to extract specific sections
        lines = analysis_text.split('\n')
        current_section = None
        section_content = []

        section_keywords = {
            "예상 티어": "predicted_tier",
            "플레이 스타일": "playstyle",
            "강점": "strengths",
            "약점": "weaknesses",
            "승리 플랜": "win_plan",
            "즉시 개선": "immediate_improvements",
            "장기 성장": "long_term_plan"
        }

        for line in lines:
            # Check if this line starts a new section
            for keyword, section_key in section_keywords.items():
                if keyword in line and line.startswith('#'):
                    # Save previous section
                    if current_section and section_content:
                        sections[current_section] = '\n'.join(section_content).strip()

                    # Start new section
                    current_section = section_key
                    section_content = []
                    break
            else:
                if current_section:
                    section_content.append(line)

        # Save last section
        if current_section and section_content:
            sections[current_section] = '\n'.join(section_content).strip()

        return sections

    def format_for_discord(self, analysis: Dict) -> List[discord.Embed]:
        """Format analysis into Discord embeds"""
        import discord

        embeds = []

        # Main stats embed
        main_embed = discord.Embed(
            title=f"📊 {analysis['player_name']} 전적 분석",
            description=f"**{analysis['total_games']}게임 분석 결과**",
            color=0x00ff00 if analysis['winrate'] >= 50 else 0xff0000
        )

        main_embed.add_field(
            name="기본 통계",
            value=f"승률: **{analysis['winrate']}%**\nKDA: **{analysis['kda']}**",
            inline=True
        )

        if "predicted_tier" in analysis:
            main_embed.add_field(
                name="예상 티어",
                value=analysis["predicted_tier"][:200],
                inline=False
            )

        embeds.append(main_embed)

        # Strengths & Weaknesses
        if "strengths" in analysis or "weaknesses" in analysis:
            swot_embed = discord.Embed(
                title="💪 강점과 약점",
                color=0x3498db
            )

            if "strengths" in analysis:
                swot_embed.add_field(
                    name="✅ 강점",
                    value=analysis["strengths"][:1000],
                    inline=False
                )

            if "weaknesses" in analysis:
                swot_embed.add_field(
                    name="⚠️ 약점",
                    value=analysis["weaknesses"][:1000],
                    inline=False
                )

            embeds.append(swot_embed)

        # Win Plan
        if "win_plan" in analysis:
            plan_embed = discord.Embed(
                title="🎯 승리 플랜",
                description=analysis["win_plan"][:2000],
                color=0xe67e22
            )
            embeds.append(plan_embed)

        # Immediate improvements
        if "immediate_improvements" in analysis:
            improve_embed = discord.Embed(
                title="⚡ 즉시 개선 가능한 부분",
                description=analysis["immediate_improvements"][:2000],
                color=0x9b59b6
            )
            embeds.append(improve_embed)

        return embeds
