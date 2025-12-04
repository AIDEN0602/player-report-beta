# LoL AI Analysis System

League of Legends AI 전적 분석 시스템 - Claude AI 기반

## 🌟 주요 기능

### 1. AI 전적 분석 (Discord Bot)
- **완전 분석**: 100게임 기반 심층 분석
- **빠른 분석**: 30게임 기반 즉시 분석
- Claude AI가 제공하는 프로급 인사이트

### 2. 분석 내용
- ✅ 예상 티어 (통계 기반 티어 예측)
- ✅ 플레이 스타일 분석
- ✅ 강점 & 약점
- ✅ 챔피언별 매치업 승률
- ✅ 승리 플랜 (구체적인 게임 전략)
- ✅ 즉시 개선 가능한 부분
- ✅ 장기 성장 로드맵

### 3. 프로급 통계
- 팀 조합 분석 (5vs5 풀 데이터)
- 블루/레드 사이드 승률
- 게임 길이별 퍼포먼스
- 멀티킬 & 오브젝트 통계
- 데스 타이밍 분석
- 퍼스트 블러드 참여율

## 구성

### kr_bot (한국 서버)
- 서버: KR
- Routing: Asia

### na_bot (북미 서버)
- 서버: NA
- Routing: Americas

## 설치

```bash
pip install -r requirements.txt
```

## 환경 설정

각 봇 폴더에 `.env` 파일 생성 (`.env.example` 참고):

```env
# Discord Bot Token
DISCORD_TOKEN=your_discord_bot_token_here

# Riot Games API Key
RIOT_API_KEY=your_riot_api_key_here

# Region (KR: kr/asia, NA: na1/americas, EUW: euw1/europe)
RIOT_REGION=na1
RIOT_ROUTING=americas

# Claude AI API Key (for AI analysis)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### API 키 발급

1. **Discord Bot Token**
   - https://discord.com/developers/applications
   - Bot 생성 후 TOKEN 복사
   - Bot Permissions: `Send Messages`, `Embed Links`, `Attach Files`, `Use Slash Commands`

2. **Riot API Key**
   - https://developer.riotgames.com/
   - 로그인 후 API Key 발급

3. **Anthropic API Key**
   - https://console.anthropic.com/
   - Account Settings > API Keys

## 사용법

### 전적 다운로드

**한국 서버:**
```bash
cd kr_bot
python3 generate_player_report.py
```

**북미 서버:**
```bash
cd na_bot
python3 generate_player_report.py
```

입력 형식: `GameName#TAG` (예: `Faker#KR1`)

### AI 분석 Discord 봇 실행

```bash
cd kr_bot  # or na_bot
python3 analysis_bot.py
```

## Discord 봇 명령어

### AI 전적 분석 (analysis_bot.py)
- `/analyze riot_id:Name#TAG` - **완전 AI 분석** (100게임, 2-3분 소요)
  - 예상 티어
  - 플레이 스타일
  - 강점/약점
  - 승리 플랜
  - 개선 로드맵

- `/quick_analyze riot_id:Name#TAG` - **빠른 AI 분석** (30게임, 1분 소요)
  - 기본 통계
  - 예상 티어
  - 즉시 개선 가능한 부분

- `/help_analysis` - 도움말

### 기본 봇 (bot.py)
- `/profile_setup riot_id:Name#TAG` - 프로필 설정
- `/profile_show` - 프로필 확인
- `/profile_set role:TOP` - 포지션 변경
- `/ban_suggest` - 밴 추천
- `/pick_suggest` - 픽 추천
- `/scout riot_id:Name#TAG` - 플레이어 스카우팅
- `/live_analyze` - 현재 게임 분석

## 출력 파일

- `player_report_이름_날짜.txt` - AI 분석용 상세 리포트
- `player_data_이름_날짜.json` - 원본 게임 데이터

## 라이선스

MIT
