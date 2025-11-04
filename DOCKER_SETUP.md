# Docker 설정 가이드

3개의 MCP 서버(jeoklip, tooja, inchul)를 하나의 도커 이미지로 관리하는 설정입니다.

## 📁 생성된 파일

- `Dockerfile` - 공용 도커 이미지 빌드 파일
- `entrypoint.sh` - MCP_SERVER 환경변수에 따라 서버 선택 실행
- `.dockerignore` - 도커 빌드 시 제외할 파일 목록
- `claude_desktop_config.json` - 도커 기반 Claude MCP 설정 (모든 플랫폼 공통)

## 🚀 사용 방법

### 1. 도커 이미지 빌드

프로젝트 루트 디렉토리로 이동 후:

**Windows (PowerShell):**
```powershell
cd "C:\path\to\etirement-planning-mcp"
docker build -t retirement-mcp .
```

**Mac/Linux (Terminal):**
```bash
cd ~/path/to/etirement-planning-mcp
docker build -t retirement-mcp .
```

### 2. 각 MCP 서버 테스트

#### jeoklip 서버 테스트
**Windows:**
```powershell
docker run --rm -it -e MCP_SERVER=jeoklip retirement-mcp
```

**Mac/Linux:**
```bash
docker run --rm -it -e MCP_SERVER=jeoklip retirement-mcp
```

#### tooja 서버 테스트
**Windows:**
```powershell
docker run --rm -it -e MCP_SERVER=tooja retirement-mcp
```

**Mac/Linux:**
```bash
docker run --rm -it -e MCP_SERVER=tooja retirement-mcp
```

#### inchul 서버 테스트
**Windows:**
```powershell
docker run --rm -it -e MCP_SERVER=inchul retirement-mcp
```

**Mac/Linux:**
```bash
docker run --rm -it -e MCP_SERVER=inchul retirement-mcp
```

### 3. Claude Desktop 설정

Claude Desktop 설정 파일 위치:

**Windows:**
- 경로: `%APPDATA%\Claude\claude_desktop_config.json`
- 또는: `C:\Users\[사용자명]\AppData\Roaming\Claude\claude_desktop_config.json`

**Mac:**
- 경로: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Linux:**
- 경로: `~/.config/Claude/claude_desktop_config.json`

설정 파일 내용은 프로젝트의 `claude_desktop_config.json` 파일을 복사하여 사용하세요. (모든 플랫폼에서 동일한 설정 사용)

## 🔍 동작 원리

1. **단일 이미지**: `retirement-mcp` 이미지 하나에 3개 서버 모두 포함
2. **환경변수 선택**: `MCP_SERVER` 환경변수로 실행할 서버 선택
   - `MCP_SERVER=jeoklip` → jeoklip 서버 실행
   - `MCP_SERVER=tooja` → tooja 서버 실행
   - `MCP_SERVER=inchul` → inchul 서버 실행
3. **entrypoint.sh**: 환경변수에 따라 적절한 Python 모듈 실행

## ⚠️ 주의사항

- MCP 서버는 정상 작동 시 프로세스가 계속 대기 상태로 유지됩니다.
- Claude MCP 클라이언트가 stdio로 요청을 보내는 것을 기다립니다.
- `--rm` 플래그는 컨테이너 종료 시 자동 삭제를 의미합니다.
- `-i` 플래그는 stdio 연결을 위해 필수입니다.

## 🐛 문제 해결

### 이미지 빌드 실패
- `requirements.txt`에 모든 의존성이 올바르게 나열되어 있는지 확인
- Python 3.10 호환성 확인

### 실행 시 에러
- `MCP_SERVER` 환경변수가 올바르게 설정되었는지 확인
- 로그 메시지를 확인하여 어떤 서버가 시작되는지 확인

### Claude에서 연결 실패
- Docker가 실행 중인지 확인
- `retirement-mcp` 이미지가 빌드되어 있는지 확인
- Claude Desktop을 재시작해보세요

