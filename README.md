# LoL Player Report Generator

League of Legends 플레이어 전적 분석 도구

## 기능

- 최근 100게임 랭크 전적 다운로드
- 챔피언별, 포지션별 통계 분석
- AI 분석용 리포트 자동 생성
- Discord 봇 통합 (프로필 설정, 스카우팅, 라이브 게임 분석)

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

각 봇 폴더에 `.env` 파일 생성:

```env
RIOT_API_KEY=your_api_key_here
DISCORD_TOKEN=your_discord_token_here
RIOT_REGION=kr  # or na1
RIOT_ROUTING=asia  # or americas
```

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

### Discord 봇 실행

```bash
cd kr_bot  # or na_bot
python3 bot.py
```

## Discord 봇 명령어

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
