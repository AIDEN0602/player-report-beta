# Discord Bot 설정 가이드

## 📋 준비물
- Discord 계정
- Python 3.9 이상
- Riot API Key
- Claude API Key (AI 분석용)

---

## 1. Discord Bot 생성

### 1-1. Discord Developer Portal 접속
1. https://discord.com/developers/applications 접속
2. "New Application" 클릭
3. 봇 이름 입력 (예: "LoL AI Coach")
4. 약관 동의 후 "Create"

### 1-2. Bot 설정
1. 왼쪽 메뉴에서 **"Bot"** 클릭
2. "Add Bot" 버튼 클릭
3. **"Reset Token"** 클릭하여 토큰 발급
4. **토큰 복사** (⚠️ 절대 공유하지 마세요!)

### 1-3. Bot 권한 설정
**Privileged Gateway Intents**에서 다음 활성화:
- ✅ MESSAGE CONTENT INTENT

**Bot Permissions**:
Bot 메뉴 아래에서 다음 권한 부여:
- ✅ Send Messages
- ✅ Embed Links
- ✅ Attach Files
- ✅ Read Message History
- ✅ Use Slash Commands

## 2. Bot Permissions 계산

### 방법 1: 권한 계산기 사용
1. 왼쪽 메뉴에서 **"OAuth2"** → **"URL Generator"** 클릭
2. **SCOPES** 선택:
   - ✅ `bot`
   - ✅ `applications.commands`

3. **BOT PERMISSIONS** 선택:
   ```
   Text Permissions:
   ✅ Send Messages
   ✅ Send Messages in Threads
   ✅ Create Public Threads
   ✅ Create Private Threads
   ✅ Embed Links
   ✅ Attach Files
   ✅ Read Message History
   ✅ Mention Everyone (optional)
   ✅ Use External Emojis
   ✅ Add Reactions
   ```

4. 생성된 URL 복사

### 방법 2: 직접 URL 만들기
```
https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=534723950656&scope=bot%20applications.commands
```
- `YOUR_CLIENT_ID`를 실제 Client ID로 교체
- Client ID는 "General Information" 메뉴에서 확인

### 권한 정수 계산
스크린샷의 권한 계산기 사용:
- 필요한 권한 모두 체크
- 하단의 정수값 복사 (예: `534723950656`)

## 3. 서버에 봇 초대

1. 2단계에서 복사한 URL을 브라우저에 붙여넣기
2. 봇을 추가할 서버 선택
3. "승인" 클릭
4. reCAPTCHA 완료

✅ 봇이 서버에 추가되었습니다!

## 4. 환경 설정

### 4-1. API 키 발급

#### Discord Bot Token
- 이미 1-2 단계에서 발급 완료

#### Riot API Key
1. https://developer.riotgames.com/ 접속
2. 로그인
3. Dashboard에서 API Key 발급
4. ⚠️ Development API Key는 24시간마다 갱신 필요
5. Production API Key가 필요하면 신청 가능

#### Claude API Key (AI 분석용)
1. https://console.anthropic.com/ 접속
2. "Get API Keys" 클릭
3. "Create Key" 클릭
4. 키 이름 입력 후 생성
5. API Key 복사 (⚠️ 한 번만 표시됨!)

### 4-2. .env 파일 생성

프로젝트 루트에 `.env` 파일 생성:

```env
# Discord Bot Token
DISCORD_TOKEN=your_discord_bot_token_here

# Riot Games API Key
RIOT_API_KEY=RGAPI-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# Anthropic Claude API Key
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxx
```

## 5. 봇 실행

### 5-1. 패키지 설치
```bash
pip install discord.py python-dotenv aiohttp anthropic
```

또는:
```bash
pip install -r requirements.txt
```

### 5-2. 봇 실행
```bash
python3 unified_bot.py
```

성공 메시지 예시:
```
============================================================
✅ Bot Online: LoL AI Coach#1234
🌍 Multi-Region Support: KR, NA, EUW, EUNE, BR, LAN, LAS, OCE, JP, SG
🤖 AI Analysis: Enabled
============================================================

✅ Synced 5 commands
```

## 6. Discord에서 사용하기

### 6-1. 명령어 확인
Discord 채팅창에서:
```
/help
```

### 6-2. 지역 설정
```
/region
```
드롭다운에서 지역 선택 (KR, NA, EUW 등)

### 6-3. 전적 분석
```
/analyze riot_id:Faker#KR1
```

또는 빠른 분석:
```
/quick riot_id:Hide on bush#KR1
```

## 7. 문제 해결

### 봇이 온라인이 안 돼요
1. `.env` 파일의 `DISCORD_TOKEN` 확인
2. Bot 권한에서 MESSAGE CONTENT INTENT 활성화 확인
3. 토큰 재발급 후 다시 시도

### Slash 명령어가 안 보여요
1. 봇에게 `applications.commands` 권한이 있는지 확인
2. 봇을 서버에서 제거 후 올바른 권한으로 재초대
3. Discord 앱 재시작

### API 에러가 나요
1. **Riot API Key 만료**:
   - Development Key는 24시간마다 갱신
   - https://developer.riotgames.com/ 에서 새 키 발급

2. **Rate Limit**:
   - 너무 많은 요청
   - 잠시 후 다시 시도

3. **계정을 찾을 수 없음**:
   - Riot ID 형식 확인: `게임이름#태그`
   - 올바른 지역 설정 확인

### AI 분석이 안 돼요
1. `.env` 파일의 `ANTHROPIC_API_KEY` 확인
2. API 크레딧이 남아있는지 확인
3. 인터넷 연결 확인

## 8. 권장 설정

### 봇 역할 설정
서버에서 봇에게 적절한 역할 부여:
1. 서버 설정 → 역할
2. 봇 역할 생성 (예: "AI Coach")
3. 권한 설정:
   - 메시지 전송
   - 임베드 링크
   - 파일 첨부
   - 슬래시 명령어 사용

### 채널 권한
특정 채널에서만 봇 사용:
1. 채널 설정 → 권한
2. 봇 역할 추가
3. 필요한 권한만 부여

## 9. 보안 주의사항

⚠️ **절대로 공유하면 안 되는 것들:**
- Discord Bot Token
- Riot API Key
- Claude API Key
- `.env` 파일

✅ **안전한 보관:**
- `.gitignore`에 `.env` 추가
- GitHub에 업로드하지 않기
- 주기적으로 키 갱신

## 10. 추가 리소스

- [Discord Developer Portal](https://discord.com/developers/docs)
- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [Riot Games API](https://developer.riotgames.com/)
- [Anthropic API Docs](https://docs.anthropic.com/)

---

## 요약 체크리스트

- [ ] Discord Bot 생성 및 토큰 발급
- [ ] Bot Permissions 설정 (Send Messages, Embed Links, etc.)
- [ ] MESSAGE CONTENT INTENT 활성화
- [ ] 서버에 봇 초대 (올바른 권한 URL 사용)
- [ ] Riot API Key 발급
- [ ] Claude API Key 발급 (AI 분석용)
- [ ] `.env` 파일 생성 및 모든 키 입력
- [ ] 패키지 설치 (`pip install -r requirements.txt`)
- [ ] 봇 실행 (`python3 unified_bot.py`)
- [ ] Discord에서 `/help` 명령어로 테스트

성공! 🎉
