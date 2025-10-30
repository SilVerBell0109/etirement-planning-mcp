# 🚀 은퇴 플래너 MCP 서버 설치 가이드 (Windows)

Windows 환경에서 은퇴 플래너(적립메이트, 인출메이트, 투자메이트) MCP 서버를 설치하고 Claude Desktop에 연동하는 가이드입니다.

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

### 1.1 PowerShell 관리자 권한으로 실행

1. **Windows 키** 누르기
2. "PowerShell" 입력
3. **Windows PowerShell**에서 **우클릭** → **관리자 권한으로 실행**

### 1.2 실행 정책 변경 (처음 한 번만)

```powershell
# 스크립트 실행 허용
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
```

### 1.3 Python 3.11+ 설치

#### Option 1: Microsoft Store에서 설치 (권장)
1. **Microsoft Store** 실행
2. "Python 3.11" 또는 "Python 3.12" 검색
3. **설치** 클릭

#### Option 2: 공식 웹사이트에서 설치
1. https://www.python.org/downloads/ 방문
2. **Download Python 3.11.x** 클릭
3. 설치 시 **"Add Python to PATH"** 체크 필수! ✅

#### 설치 확인
```powershell
# 새 PowerShell 창 열고 확인
python --version
# 출력 예: Python 3.11.x

# pip 확인
pip --version
```

### 1.4 Git 설치

#### Git for Windows 다운로드
1. https://git-scm.com/download/win 방문
2. **64-bit Git for Windows Setup** 다운로드
3. 설치 시 기본 옵션으로 진행

#### 설치 확인
```powershell
git --version
# 출력 예: git version 2.x.x
```

### 1.5 UV 설치

```powershell
# UV 설치 (Python 패키지 관리자)
pip install uv

# 설치 확인
uv --version
```

---

## 2. 프로젝트 다운로드

### 2.1 작업 디렉토리로 이동

```powershell
# 바탕화면으로 이동
cd $env:USERPROFILE\Desktop
```

### 2.2 Git 저장소 클론

**주의**: 실제 GitHub 저장소 URL로 변경하세요.

```powershell
# Git 저장소에서 프로젝트 다운로드
git clone [YOUR_GITHUB_REPOSITORY_URL] etirement-planner

# 예시:
# git clone https://github.com/yourusername/etirement-planner.git etirement-planner
```

### 2.3 프로젝트 구조 확인

```powershell
cd etirement-planner
dir
```

예상 구조:
```
etirement-planner\
├── .venv\                    ← (설치 후 생성됨) 공유 가상환경
├── etirement-planning-mcp\
│   ├── mcp_server_jeoklip\
│   ├── mcp_server_inchul\
│   └── mcp_server_tooja\
└── README.md (있을 경우)
```

**참고**: `.venv` 폴더는 3단계에서 생성됩니다.

---

## 3. 공유 가상환경 설정

3개의 MCP 서버가 하나의 가상환경을 공유합니다. **한 번만 설정하면 됩니다!**

### 3.1 프로젝트 루트로 이동

```powershell
cd $env:USERPROFILE\Desktop\etirement-planner
```

### 3.2 공유 가상환경 생성

```powershell
# 가상환경 생성 (프로젝트 루트에 .venv 폴더 생성)
uv venv

# 가상환경 활성화
.\.venv\Scripts\Activate.ps1
```

**참고**: 만약 활성화 시 오류가 발생하면:
```powershell
# 실행 정책 확인
Get-ExecutionPolicy
# "RemoteSigned" 또는 "Unrestricted"가 아니면 1.2 단계 다시 실행
```

### 3.3 모든 MCP 서버 의존성 한 번에 설치

```powershell
# 적립메이트 설치
cd etirement-planning-mcp\mcp_server_jeoklip
uv pip install -e .

# 인출메이트 설치
cd ..\mcp_server_inchul
uv pip install -e .

# 투자메이트 설치
cd ..\mcp_server_tooja
uv pip install -e .

# 프로젝트 루트로 돌아가기
cd $env:USERPROFILE\Desktop\etirement-planner
```

### 3.4 설치 확인

```powershell
# 모든 서버가 정상 설치되었는지 확인
python -c "import mcp_server_jeoklip; print('✅ Jeoklip 설치 완료')"
python -c "import mcp_server_inchul; print('✅ Inchul 설치 완료')"
python -c "import mcp_server_tooja; print('✅ Tooja 설치 완료')"
```

모두 성공하면 다음 단계로!

### 3.5 가상환경 비활성화

```powershell
# 설치 완료 후 가상환경 비활성화
deactivate
```

**참고**: UV는 자동으로 가상환경을 찾아 사용하므로, Claude Desktop에서는 별도로 활성화할 필요가 없습니다.

---

## 4. Claude Desktop 설치 및 설정

### 4.1 Claude Desktop 다운로드 및 설치

1. 웹브라우저에서 https://claude.ai/download 방문
2. **Windows** 버전 다운로드
3. 다운로드한 설치 파일 실행
4. 설치 완료 후 Claude 실행하여 로그인

### 4.2 Claude Desktop 설정 디렉토리 확인

```powershell
# 설정 디렉토리 생성 (없는 경우)
New-Item -Path "$env:APPDATA\Claude" -ItemType Directory -Force
```

### 4.3 MCP 서버 설정 파일 생성

#### 현재 사용자명 확인
```powershell
# 사용자명 확인
$env:USERNAME
# 예: john
```

#### 설정 파일 생성

**주의**: `YOUR_USERNAME`을 실제 사용자명으로 변경하세요!

```powershell
# 설정 파일 생성
@"
{
  "mcpServers": {
    "jeoklip": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\YOUR_USERNAME\\Desktop\\etirement-planner",
        "run",
        "mcp-server-jeoklip"
      ]
    },
    "inchul": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\YOUR_USERNAME\\Desktop\\etirement-planner",
        "run",
        "mcp-server-inchul"
      ]
    },
    "tooja": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\YOUR_USERNAME\\Desktop\\etirement-planner",
        "run",
        "mcp-server-tooja"
      ]
    }
  }
}
"@ | Out-File -FilePath "$env:APPDATA\Claude\claude_desktop_config.json" -Encoding UTF8
```

#### 또는 수동으로 생성

1. **파일 탐색기** 열기
2. 주소창에 `%APPDATA%\Claude` 입력하고 Enter
3. 새 파일 만들기: `claude_desktop_config.json`
4. 메모장으로 열고 다음 내용 붙여넣기 (**사용자명 변경 필수!**)

```json
{
  "mcpServers": {
    "jeoklip": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\YOUR_USERNAME\\Desktop\\etirement-planner",
        "run",
        "mcp-server-jeoklip"
      ]
    },
    "inchul": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\YOUR_USERNAME\\Desktop\\etirement-planner",
        "run",
        "mcp-server-inchul"
      ]
    },
    "tooja": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\YOUR_USERNAME\\Desktop\\etirement-planner",
        "run",
        "mcp-server-tooja"
      ]
    }
  }
}
```

**핵심 변경사항**: 
- Windows 경로는 `\` 또는 `\\` 사용 (JSON에서는 `\\` 필수)
- 예: `C:\\Users\\john\\Desktop\\etirement-planner`

### 4.4 설정 파일 유효성 검사

```powershell
# Python으로 JSON 유효성 검사
python -m json.tool "$env:APPDATA\Claude\claude_desktop_config.json"

# 정상 출력되면 OK
```

---

## 5. 연결 테스트

### 5.1 Claude Desktop 재시작

```powershell
# Claude Desktop 완전 종료
taskkill /F /IM "Claude.exe"

# 3초 대기
Start-Sleep -Seconds 3

# Claude Desktop 다시 실행
Start-Process "Claude"
```

또는 수동으로:
1. Claude Desktop 완전 종료 (시스템 트레이에서도 종료)
2. Claude Desktop 다시 실행

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
```powershell
# 설정 파일 존재 확인
Test-Path "$env:APPDATA\Claude\claude_desktop_config.json"

# 설정 파일 내용 출력
Get-Content "$env:APPDATA\Claude\claude_desktop_config.json"
```

#### 경로 문제
```powershell
# 프로젝트 경로가 실제로 존재하는지 확인
Test-Path "$env:USERPROFILE\Desktop\etirement-planner"
Test-Path "$env:USERPROFILE\Desktop\etirement-planner\.venv"

# 공유 가상환경이 생성되었는지 확인
Test-Path "$env:USERPROFILE\Desktop\etirement-planner\.venv\Scripts\python.exe"
```

경로가 다르다면 설정 파일의 경로를 수정하세요. 
**중요**: 
- 모든 서버의 `--directory`가 프로젝트 루트를 가리켜야 합니다
- Windows 경로에서는 `\`를 `\\`로 표기 (JSON 규칙)

### 6.2 UV 명령어를 찾을 수 없는 경우

```powershell
# UV 재설치
pip install --upgrade uv

# UV 경로 확인
where.exe uv

# PATH 새로고침 (PowerShell 재시작)
```

### 6.3 Python 모듈을 찾을 수 없는 경우

```powershell
# 프로젝트 루트에서 가상환경 재설치
cd $env:USERPROFILE\Desktop\etirement-planner
.\.venv\Scripts\Activate.ps1

# 모든 서버 재설치
cd etirement-planning-mcp\mcp_server_jeoklip
uv pip install -e .
cd ..\mcp_server_inchul
uv pip install -e .
cd ..\mcp_server_tooja
uv pip install -e .

deactivate
```

### 6.4 로그 확인

```powershell
# Claude Desktop 로그 디렉토리로 이동
cd "$env:APPDATA\Claude\logs"

# 로그 파일 목록 확인
dir

# 특정 로그 파일 내용 확인
Get-Content -Path "mcp-server-jeoklip.log" -Tail 50
```

### 6.5 PowerShell 실행 정책 오류

```powershell
# 현재 실행 정책 확인
Get-ExecutionPolicy

# RemoteSigned로 변경
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

# 확인
Get-ExecutionPolicy
```

### 6.6 완전 초기화 (문제 해결 안 될 시)

```powershell
# 1. 공유 가상환경 삭제
Remove-Item -Path "$env:USERPROFILE\Desktop\etirement-planner\.venv" -Recurse -Force

# 2. Claude 설정 삭제
Remove-Item -Path "$env:APPDATA\Claude\claude_desktop_config.json" -Force

# 3. Claude Desktop 재시작
taskkill /F /IM "Claude.exe"

# 4. 다시 3단계부터 진행 (공유 가상환경 설정)
cd $env:USERPROFILE\Desktop\etirement-planner
uv venv
.\.venv\Scripts\Activate.ps1
# ... (이후 단계 반복)
```

---

## 📝 체크리스트

설치를 진행하면서 체크하세요:

- [ ] PowerShell 관리자 권한 실행
- [ ] 실행 정책 변경 (RemoteSigned)
- [ ] Python 3.11+ 설치 완료 ("Add to PATH" 체크)
- [ ] Git 설치 완료
- [ ] UV 설치 완료
- [ ] Git 저장소 클론 완료
- [ ] 공유 가상환경 생성 (프로젝트 루트에 .venv)
- [ ] 3개 MCP 서버 의존성 설치 완료
- [ ] Claude Desktop 설치 완료
- [ ] claude_desktop_config.json 생성
- [ ] 사용자명 경로 확인/수정 (\\로 표기)
- [ ] Claude Desktop 재시작
- [ ] MCP 서버 3개 연결 확인 (🔌 아이콘)
- [ ] 테스트 메시지 성공

---

## 🔗 추가 정보

### 유용한 명령어

```powershell
# 프로젝트 업데이트 (새 버전 받기)
cd $env:USERPROFILE\Desktop\etirement-planner
git pull origin main

# 업데이트 후 의존성 재설치 (필요시)
.\.venv\Scripts\Activate.ps1
cd etirement-planning-mcp\mcp_server_jeoklip
uv pip install -e .
cd ..\mcp_server_inchul
uv pip install -e .
cd ..\mcp_server_tooja
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
   etirement-planner\
   ├── .venv\  ← 모든 서버가 공유
   └── etirement-planning-mcp\
       ├── mcp_server_jeoklip\
       ├── mcp_server_inchul\
       └── mcp_server_tooja\
   ```

2. **설정 파일 위치**: `%APPDATA%\Claude\claude_desktop_config.json`
   - 실제 경로: `C:\Users\[사용자명]\AppData\Roaming\Claude\claude_desktop_config.json`

3. **로그 위치**: `%APPDATA%\Claude\logs\`

4. **Windows 경로 표기법**:
   - PowerShell: `C:\Users\john\Desktop\etirement-planner`
   - JSON 파일: `C:\\Users\\john\\Desktop\\etirement-planner` (백슬래시 2개!)

5. **공유 가상환경의 장점**: 
   - 디스크 공간 절약 (1개의 .venv만 생성)
   - 설치 시간 단축
   - 의존성 버전 일관성 유지
   - 관리 용이

6. **새 라이브러리 추가 시**:
   ```powershell
   cd $env:USERPROFILE\Desktop\etirement-planner
   .\.venv\Scripts\Activate.ps1
   uv pip install [새로운-패키지]
   deactivate
   ```

7. **VS Code 사용자**: VS Code에서 프로젝트를 열면 자동으로 가상환경을 인식합니다.

8. **Windows Defender**: 처음 실행 시 Windows Defender가 경고할 수 있습니다. "추가 정보" → "실행"을 클릭하세요.

---

## 🔒 보안 참고사항

- PowerShell 실행 정책을 `RemoteSigned`로 설정하면 로컬 스크립트는 실행되지만, 인터넷에서 다운로드한 스크립트는 서명이 필요합니다.
- 이는 보안과 편의성의 균형을 맞춘 설정입니다.
- `Unrestricted`는 보안에 취약할 수 있으므로 권장하지 않습니다.

---

**문제가 계속되면 다음 정보와 함께 문의하세요:**
- Windows 버전 (`winver` 명령어로 확인)
- Python 버전 (`python --version`)
- UV 버전 (`uv --version`)
- PowerShell 버전 (`$PSVersionTable.PSVersion`)
- 에러 메시지 전문
- 로그 파일 내용

설치 완료를 축하합니다! 🎉
