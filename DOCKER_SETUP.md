# Docker 설정 가이드

3개의 MCP 서버(jeoklip, tooja, inchul)를 하나의 도커 이미지로 관리하는 설정입니다.

## 📁 생성된 파일

- `Dockerfile` - 공용 도커 이미지 빌드 파일
- `compose.yml` - Docker Compose 설정 파일 (여러 서비스 관리)
- `entrypoint.sh` - MCP_SERVER 환경변수에 따라 서버 선택 실행
- `.dockerignore` - 도커 빌드 시 제외할 파일 목록
- `claude_desktop_config.json` - 도커 기반 Claude MCP 설정

---

## 🚀 빠른 시작: Claude Desktop 사용하기

### 전체 워크플로우

#### Windows 환경

**1단계: 이미지 빌드**
```cmd
cd "C:\path\to\etirement-planning-mcp"
docker compose build
```

**2단계: 이미지 빌드 확인**
```powershell
docker images | Select-String "retirement-mcp"
```

**3단계: Claude Desktop 설정 파일 복사**
```powershell
# PowerShell에서 실행
cd $env:APPDATA\Claude

# 기존 설정 파일 백업 (있는 경우)
if (Test-Path claude_desktop_config.json) {
    Copy-Item claude_desktop_config.json claude_desktop_config.json.backup
}

# 프로젝트의 설정 파일 복사
Copy-Item "C:\path\to\etirement-planning-mcp\claude_desktop_config.json" .

# 설정 파일 내용 확인
Get-Content claude_desktop_config.json
```

**4단계: Claude Desktop 재시작**
- Claude Desktop 완전히 종료 (시스템 트레이 아이콘도 확인)
- Claude Desktop 다시 실행

**5단계: 연결 확인**
- Claude Desktop에서 "+" 버튼 클릭
- "연구" 메뉴에서 `jeoklip`, `tooja`, `inchul` 커넥터가 표시되고 ON 상태인지 확인

---

#### Mac 환경

**1단계: 이미지 빌드**
```bash
cd ~/path/to/etirement-planning-mcp
docker compose build
```

**2단계: 이미지 빌드 확인**
```bash
docker images | grep retirement-mcp
```

**3단계: Claude Desktop 설정 파일 복사**
```bash
# Claude Desktop 설정 디렉토리 생성 (없는 경우)
mkdir -p ~/Library/Application\ Support/Claude

# 기존 설정 파일 백업 (있는 경우)
cp ~/Library/Application\ Support/Claude/claude_desktop_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json.backup 2>/dev/null || true

# 프로젝트의 설정 파일 복사
cp claude_desktop_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json

# 설정 파일 내용 확인
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**4단계: Claude Desktop 재시작**
- Claude Desktop 완전히 종료
- Claude Desktop 다시 실행

**5단계: 연결 확인**
- Claude Desktop에서 "+" 버튼 클릭
- "연구" 메뉴에서 `jeoklip`, `tooja`, `inchul` 커넥터가 표시되고 ON 상태인지 확인

---

#### Linux (Ubuntu 22.04 포함) 환경

**1단계: 이미지 빌드**
```bash
cd ~/path/to/etirement-planning-mcp
docker compose build
```

**2단계: 이미지 빌드 확인**
```bash
docker images | grep retirement-mcp
```

**3단계: Claude Desktop 설정 파일 복사**
```bash
# Claude Desktop 설정 디렉토리 생성 (없는 경우)
mkdir -p ~/.config/Claude

# 기존 설정 파일 백업 (있는 경우)
cp ~/.config/Claude/claude_desktop_config.json ~/.config/Claude/claude_desktop_config.json.backup 2>/dev/null || true

# 프로젝트의 설정 파일 복사
cp claude_desktop_config.json ~/.config/Claude/claude_desktop_config.json

# 설정 파일 내용 확인
cat ~/.config/Claude/claude_desktop_config.json
```

**4단계: Claude Desktop 재시작**
- Claude Desktop 완전히 종료
- Claude Desktop 다시 실행

**5단계: 연결 확인**
- Claude Desktop에서 "+" 버튼 클릭
- "연구" 메뉴에서 `jeoklip`, `tooja`, `inchul` 커넥터가 표시되고 ON 상태인지 확인

---

### ⚠️ 중요 설명

- **`docker compose up --build`는 개발/테스트용입니다**
  - 서버를 직접 실행하여 테스트할 때 사용
  - Claude Desktop과는 별개로 작동
  
- **Claude Desktop 사용 시에는 이미지 빌드만 하면 됩니다**
  - `claude_desktop_config.json`에 `docker run` 명령이 설정되어 있음
  - Claude Desktop이 필요할 때마다 자동으로 컨테이너를 실행
  - **별도로 `docker compose up`을 실행할 필요 없음**

---

## 🔧 상세 설정 가이드

### 1. 도커 이미지 빌드

프로젝트 루트 디렉토리로 이동 후:

**Windows (PowerShell 또는 CMD):**
```powershell
cd "C:\path\to\etirement-planning-mcp"
docker build -t retirement-mcp .
```

**Mac/Linux (Terminal):**
```bash
cd ~/path/to/etirement-planning-mcp
docker build -t retirement-mcp .
```

또는 Docker Compose를 사용하여 빌드:

**Windows:**
```powershell
docker compose build
```

**Mac/Linux:**
```bash
docker compose build
```

### 2. Claude Desktop 설정 파일 위치

**Windows:**
- 경로: `%APPDATA%\Claude\claude_desktop_config.json`
- 또는: `C:\Users\[사용자명]\AppData\Roaming\Claude\claude_desktop_config.json`

**Mac:**
- 경로: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Linux (Ubuntu 22.04 포함):**
- 경로: `~/.config/Claude/claude_desktop_config.json`

---

## 🛠️ 개발/테스트용: 서버 직접 실행

### 방법 1: Docker Compose 사용 (권장)

**⚠️ 중요: Docker Compose 명령어를 실행하기 전에 반드시 프로젝트 루트 디렉토리(`compose.yml` 파일이 있는 디렉토리)로 이동해야 합니다!**

**Windows:**
```powershell
cd "C:\path\to\etirement-planning-mcp"
```

**Mac/Linux:**
```bash
cd ~/path/to/etirement-planning-mcp
```

#### 모든 서비스 한 번에 실행

**Windows (PowerShell):**
```powershell
# 이미지 빌드와 함께 모든 서비스 실행
docker compose up --build

# 백그라운드에서 실행
docker compose up --build -d

# 실행 중인 서비스 상태 확인
docker compose ps

# 로그 확인
docker compose logs
docker compose logs -f  # 실시간 로그 보기

# 모든 서비스 중지
docker compose down
```

**Mac/Linux (Terminal):**
```bash
# 이미지 빌드와 함께 모든 서비스 실행
docker compose up --build

# 백그라운드에서 실행
docker compose up --build -d

# 실행 중인 서비스 상태 확인
docker compose ps

# 로그 확인
docker compose logs
docker compose logs -f  # 실시간 로그 보기

# 모든 서비스 중지
docker compose down
```

#### 개별 서비스 실행

**Windows/Mac/Linux (공통):**
```bash
# 특정 서버만 실행
docker compose run --rm jeoklip
docker compose run --rm tooja
docker compose run --rm inchul
```

### 방법 2: Docker run 사용

#### 각 MCP 서버 개별 실행

**Windows (PowerShell):**
```powershell
# jeoklip 서버 실행
docker run --rm -it -e MCP_SERVER=jeoklip retirement-mcp

# tooja 서버 실행
docker run --rm -it -e MCP_SERVER=tooja retirement-mcp

# inchul 서버 실행
docker run --rm -it -e MCP_SERVER=inchul retirement-mcp
```

**Mac/Linux (Terminal):**
```bash
# jeoklip 서버 실행
docker run --rm -it -e MCP_SERVER=jeoklip retirement-mcp

# tooja 서버 실행
docker run --rm -it -e MCP_SERVER=tooja retirement-mcp

# inchul 서버 실행
docker run --rm -it -e MCP_SERVER=inchul retirement-mcp
```

---

## 🔍 동작 원리

1. **단일 이미지**: `retirement-mcp` 이미지 하나에 3개 서버 모두 포함
2. **환경변수 선택**: `MCP_SERVER` 환경변수로 실행할 서버 선택
   - `MCP_SERVER=jeoklip` → jeoklip 서버 실행
   - `MCP_SERVER=tooja` → tooja 서버 실행
   - `MCP_SERVER=inchul` → inchul 서버 실행
3. **entrypoint.sh**: 환경변수에 따라 적절한 Python 모듈 실행

---

## ⚠️ 주의사항

- MCP 서버는 stdio 통신을 사용하므로, stdin이 연결되어 있을 때만 실행됩니다.
- MCP 서버는 정상 작동 시 프로세스가 계속 대기 상태로 유지됩니다.
- Claude MCP 클라이언트가 stdio로 요청을 보내는 것을 기다립니다.
- `--rm` 플래그는 컨테이너 종료 시 자동 삭제를 의미합니다.
- `-i` 플래그는 stdio 연결을 위해 필수입니다.

---

## 🐛 문제 해결

### 이미지 빌드 실패
- `requirements.txt`에 모든 의존성이 올바르게 나열되어 있는지 확인
- Python 3.10 호환성 확인
- Docker가 실행 중인지 확인

### 실행 시 에러
- `MCP_SERVER` 환경변수가 올바르게 설정되었는지 확인
- 로그 메시지를 확인하여 어떤 서버가 시작되는지 확인

### Claude Desktop에서 연결 실패
- Docker가 실행 중인지 확인
- `retirement-mcp` 이미지가 빌드되어 있는지 확인
- Claude Desktop 설정 파일 경로가 올바른지 확인
- Claude Desktop을 완전히 종료 후 재시작
- Claude Desktop에서 "+" 버튼 → "연구" 메뉴에서 커넥터 상태 확인
