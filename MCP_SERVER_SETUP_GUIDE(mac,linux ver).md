# 🚀 은퇴 플래너 MCP 서버 설치 가이드 (공유 가상환경)

새로운 macOS 환경에서 은퇴 플래너(적립메이트, 인출메이트, 투자메이트) MCP 서버를 설치하고 Claude Desktop에 연동하는 가이드입니다.

**특징**: 3개 서버가 하나의 가상환경을 공유하여 간단하고 효율적으로 관리합니다.

---

## 📋 목차

1. [사전 준비 사항](#1-사전-준비-사항)
2. [프로젝트 다운로드](#2-프로젝트-다운로드)
3. [공유 가상환경 설정](#3-공유-가상환경-설정)
4. [Claude Desktop 설치 및 설정](#4-claude-desktop-설치-및-설정)
5. [연결 테스트](#5-연결-테스트)
6. [문제 해결](#6-문제-해결)

---

## 1. 사전 준비 사항

### 1.1 Homebrew 설치

macOS 패키지 관리자인 Homebrew를 설치합니다.

```bash
# Terminal 실행 (⌘ + Space → "terminal" 입력)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**M1/M2/M3 Mac의 경우** 설치 후 PATH 설정이 필요합니다:

```bash
# .zprofile에 Homebrew PATH 추가
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

**Intel Mac의 경우** 추가 설정이 필요 없습니다.

### 1.2 Git 설치

```bash
brew install git

# 설치 확인
git --version
```

### 1.3 Python 3.11+ 설치

```bash
# Python 설치
brew install python@3.11

# 설치 확인
python3 --version
# 출력 예: Python 3.11.x
```

### 1.4 UV 설치

UV는 빠른 Python 패키지 관리 도구입니다.

```bash
# UV 설치
curl -LsSf https://astral.sh/uv/install.sh | sh

# 설치 확인
uv --version
```

만약 `uv: command not found` 에러가 발생하면:

```bash
# PATH 설정 추가
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.zprofile
source ~/.zprofile
```

---

## 2. 프로젝트 다운로드

### 2.1 작업 디렉토리로 이동

```bash
cd ~/Desktop
```

### 2.2 Git 저장소 클론

**주의**: 실제 GitHub 저장소 URL로 변경하세요.

```bash
# Git 저장소에서 프로젝트 다운로드
git clone [YOUR_GITHUB_REPOSITORY_URL] etirement-planner

# 예시:
# git clone https://github.com/yourusername/etirement-planner.git etirement-planner
```

### 2.3 프로젝트 구조 확인

```bash
cd etirement-planner
ls -la
```

예상 구조:
```
etirement-planner/
├── .venv/                    ← (설치 후 생성됨) 공유 가상환경
├── etirement-planning-mcp/
│   ├── mcp_server_jeoklip/
│   ├── mcp_server_inchul/
│   └── mcp_server_tooja/
└── README.md (있을 경우)
```

**참고**: `.venv` 폴더는 3단계에서 생성됩니다.

---

## 3. 공유 가상환경 설정

3개의 MCP 서버가 하나의 가상환경을 공유합니다. **한 번만 설정하면 됩니다!**

### 3.1 프로젝트 루트로 이동

```bash
cd ~/Desktop/etirement-planner
```

### 3.2 공유 가상환경 생성

```bash
# 가상환경 생성 (프로젝트 루트에 .venv 폴더 생성)
uv venv

# 가상환경 활성화
source .venv/bin/activate
```

### 3.3 모든 MCP 서버 의존성 한 번에 설치

```bash
# 적립메이트 설치
cd etirement-planning-mcp/mcp_server_jeoklip
uv pip install -e .

# 인출메이트 설치
cd ../mcp_server_inchul
uv pip install -e .

# 투자메이트 설치
cd ../mcp_server_tooja
uv pip install -e .

# 프로젝트 루트로 돌아가기
cd ~/Desktop/etirement-planner
```

### 3.4 설치 확인

```bash
# 모든 서버가 정상 설치되었는지 확인
python -c "import mcp_server_jeoklip; print('✅ Jeoklip 설치 완료')"
python -c "import mcp_server_inchul; print('✅ Inchul 설치 완료')"
python -c "import mcp_server_tooja; print('✅ Tooja 설치 완료')"
```

모두 성공하면 다음 단계로!

### 3.5 가상환경 비활성화

```bash
# 설치 완료 후 가상환경 비활성화
deactivate
```

**참고**: UV는 자동으로 가상환경을 찾아 사용하므로, Claude Desktop에서는 별도로 활성화할 필요가 없습니다.

---

## 4. Claude Desktop 설치 및 설정

### 4.1 Claude Desktop 다운로드 및 설치

1. 웹브라우저에서 https://claude.ai/download 방문
2. macOS 버전 다운로드
3. 다운로드한 `.dmg` 파일 실행
4. Claude 아이콘을 Applications 폴더로 드래그
5. Applications에서 Claude 실행하여 로그인

또는 터미널에서:

```bash
open https://claude.ai/download
```

### 4.2 Claude Desktop 설정 디렉토리 생성

```bash
# 설정 디렉토리 생성
mkdir -p ~/Library/Application\ Support/Claude/
```

### 4.3 MCP 서버 설정 파일 생성

공유 가상환경을 사용하는 설정입니다.

```bash
# 설정 파일 생성
cat > ~/Library/Application\ Support/Claude/claude_desktop_config.json << 'EOF'
{
  "mcpServers": {
    "jeoklip": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/silverbell/Desktop/etirement-planner",
        "run",
        "mcp-server-jeoklip"
      ]
    },
    "inchul": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/silverbell/Desktop/etirement-planner",
        "run",
        "mcp-server-inchul"
      ]
    },
    "tooja": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/silverbell/Desktop/etirement-planner",
        "run",
        "mcp-server-tooja"
      ]
    }
  }
}
EOF
```

**핵심 변경사항**: 
- `--directory`가 프로젝트 루트(`/Users/silverbell/Desktop/etirement-planner`)를 가리킵니다
- UV가 자동으로 해당 디렉토리의 `.venv`를 찾아 사용합니다

### 4.4 사용자명 확인 및 경로 수정 (필요시)

만약 사용자명이 `silverbell`이 아니라면 설정 파일을 수정해야 합니다:

```bash
# 현재 사용자명 확인
whoami

# 설정 파일 열기
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json

# 또는 VS Code로 열기
code ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**수정 예시**: 사용자명이 `john`인 경우
```json
"/Users/silverbell/Desktop/..." 
→ "/Users/john/Desktop/..."
```

모든 경로에서 `silverbell`을 실제 사용자명으로 변경하세요.

### 4.5 설정 파일 유효성 검사

```bash
# JSON 문법 확인
python3 -m json.tool ~/Library/Application\ Support/Claude/claude_desktop_config.json

# 정상 출력되면 OK
```

---

## 5. 연결 테스트

### 5.1 Claude Desktop 재시작

```bash
# Claude Desktop 완전 종료
killall Claude

# 3초 대기
sleep 3

# Claude Desktop 다시 실행
open -a Claude
```

### 5.2 MCP 서버 연결 확인

Claude Desktop에서:

1. **우측 하단** 또는 **좌측 하단** 🔌 아이콘 클릭
2. **"Connected Servers"** 또는 **"MCP Servers"** 섹션 확인
3. 다음 서버들이 보이는지 확인:
   - ✅ jeoklip
   - ✅ inchul  
   - ✅ tooja

### 5.3 테스트 메시지

Claude에게 다음과 같이 입력하여 테스트:

```
적립메이트로 은퇴 계획 세워줘.

현재 나이: 35세
은퇴 나이: 65세
월 소득: 600만원
월 지출: 400만원
현재 자산: 2억원
```

정상적으로 응답하면 설치 완료! 🎉

---

## 6. 문제 해결

### 6.1 서버가 보이지 않는 경우

#### 설정 파일 확인
```bash
# 설정 파일 존재 확인
ls -la ~/Library/Application\ Support/Claude/claude_desktop_config.json

# 설정 파일 내용 출력
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

#### 경로 문제
```bash
# 프로젝트 경로가 실제로 존재하는지 확인
ls -la ~/Desktop/etirement-planner
ls -la ~/Desktop/etirement-planner/.venv

# 공유 가상환경이 생성되었는지 확인
ls -la ~/Desktop/etirement-planner/.venv/bin/python
```

경로가 다르다면 설정 파일의 경로를 수정하세요. 
**중요**: 모든 서버의 `--directory`가 프로젝트 루트(`~/Desktop/etirement-planner`)를 가리켜야 합니다.

### 6.2 UV 명령어를 찾을 수 없는 경우

```bash
# UV 경로 확인
which uv

# 출력이 없다면 PATH 추가
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.zprofile
source ~/.zprofile

# 다시 확인
uv --version
```

### 6.3 Python 모듈을 찾을 수 없는 경우

```bash
# 프로젝트 루트에서 가상환경 재설치
cd ~/Desktop/etirement-planner
source .venv/bin/activate

# 모든 서버 재설치
cd etirement-planning-mcp/mcp_server_jeoklip && uv pip install -e .
cd ../mcp_server_inchul && uv pip install -e .
cd ../mcp_server_tooja && uv pip install -e .

deactivate
```

### 6.4 로그 확인

```bash
# Claude Desktop 로그 디렉토리
cd ~/Library/Logs/Claude/

# 최근 로그 확인
ls -lart

# 특정 로그 파일 내용 확인
tail -f mcp-server-jeoklip.log
```

### 6.5 권한 문제

```bash
# Python 실행 권한 확인
ls -la ~/Desktop/etirement-planner/.venv/bin/python

# 디렉토리 권한 확인
ls -la ~/Desktop/etirement-planner/
```

### 6.6 완전 초기화 (문제 해결 안 될 시)

```bash
# 1. 공유 가상환경 삭제
rm -rf ~/Desktop/etirement-planner/.venv

# 2. Claude 설정 삭제
rm ~/Library/Application\ Support/Claude/claude_desktop_config.json

# 3. Claude Desktop 재시작
killall Claude

# 4. 다시 3단계부터 진행 (공유 가상환경 설정)
cd ~/Desktop/etirement-planner
uv venv
source .venv/bin/activate
# ... (이후 단계 반복)
```

---

## 📝 체크리스트

설치를 진행하면서 체크하세요:

- [ ] Homebrew 설치 완료
- [ ] Git 설치 완료  
- [ ] Python 3.11+ 설치 완료
- [ ] UV 설치 완료
- [ ] Git 저장소 클론 완료
- [ ] 공유 가상환경 생성 (프로젝트 루트에 .venv)
- [ ] 3개 MCP 서버 의존성 설치 완료
- [ ] Claude Desktop 설치 완료
- [ ] claude_desktop_config.json 생성
- [ ] 사용자명 경로 확인/수정
- [ ] Claude Desktop 재시작
- [ ] MCP 서버 3개 연결 확인 (🔌 아이콘)
- [ ] 테스트 메시지 성공

---

## 🔗 추가 정보

### 유용한 명령어

```bash
# 프로젝트 업데이트 (새 버전 받기)
cd ~/Desktop/etirement-planner
git pull origin main

# 업데이트 후 의존성 재설치
cd etirement-planning-mcp/mcp_server_jeoklip
source .venv/bin/activate
uv pip install -e .
deactivate
```

### 참고 링크

- [MCP 공식 문서](https://modelcontextprotocol.io)
- [Claude Desktop](https://claude.ai/download)
- [UV 문서](https://docs.astral.sh/uv/)
- [Python 공식 문서](https://www.python.org/doc/)

---

## 💡 팁

1. **가상환경 위치**: 프로젝트 루트의 `.venv` 디렉토리에 공유 가상환경이 생성됩니다.
   ```
   etirement-planner/
   ├── .venv/  ← 모든 서버가 공유
   └── etirement-planning-mcp/
       ├── mcp_server_jeoklip/
       ├── mcp_server_inchul/
       └── mcp_server_tooja/
   ```

2. **설정 파일 위치**: `~/Library/Application Support/Claude/claude_desktop_config.json`

3. **로그 위치**: `~/Library/Logs/Claude/`

4. **프로젝트 업데이트 시**: 
   ```bash
   cd ~/Desktop/etirement-planner
   git pull origin main
   
   # 의존성 업데이트가 필요한 경우에만
   source .venv/bin/activate
   cd etirement-planning-mcp/mcp_server_jeoklip && uv pip install -e .
   cd ../mcp_server_inchul && uv pip install -e .
   cd ../mcp_server_tooja && uv pip install -e .
   deactivate
   ```

5. **공유 가상환경의 장점**: 
   - 디스크 공간 절약 (1개의 .venv만 생성)
   - 설치 시간 단축
   - 의존성 버전 일관성 유지
   - 관리 용이

6. **새 라이브러리 추가 시**:
   ```bash
   cd ~/Desktop/etirement-planner
   source .venv/bin/activate
   uv pip install [새로운-패키지]
   deactivate
   ```

---

**문제가 계속되면 다음 정보와 함께 문의하세요:**
- macOS 버전 (`sw_vers`)
- Python 버전 (`python3 --version`)
- UV 버전 (`uv --version`)
- 에러 메시지 전문
- 로그 파일 내용

설치 완료를 축하합니다! 🎉
