# 🏦 은퇴 설계 AI Agent - MCP Server

> **Claude Desktop과 연동되는 포괄적인 은퇴 설계 지원 시스템**  
> Docker 기반 MCP 서버로 적립, 투자, 인출 전략을 한 번에!

[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-FF6B6B)](https://modelcontextprotocol.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📋 목차

- [개요](#-개요)
- [주요 기능](#-주요-기능)
- [빠른 시작](#-빠른-시작)
- [상세 설치 가이드](#-상세-설치-가이드)
- [툴 사용 가이드](#-툴-사용-가이드)
- [실전 예시](#-실전-예시)
- [문제 해결](#-문제-해결)
- [FAQ](#-faq)

---

## 🎯 개요

이 프로젝트는 **Koscom AI Agent Challenge 2025**를 위해 개발된 은퇴 설계 전문 MCP(Model Context Protocol) 서버입니다. 세 가지 핵심 서비스를 통해 은퇴 준비부터 자산 운용, 인출 전략까지 전 과정을 지원합니다.

### 🏗️ 시스템 구조

```
┌─────────────────────────────────────────┐
│         Claude Desktop (사용자)          │
└────────────────┬────────────────────────┘
                 │ MCP Protocol
        ┌────────┴────────┐
        │  Docker Engine  │
        └────────┬────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
┌───▼───┐   ┌───▼───┐   ┌───▼───┐
│적립메이트│   │투자메이트│   │인출메이트│
│Jeoklip │   │ Tooja │   │Inchul │
└────────┘   └────────┘   └────────┘
```

---

## 📦 주요 기능

### 1️⃣ 적립메이트 (Jeoklip) - 은퇴 자산 적립

**"얼마를, 어떻게 모을 것인가?"**

- ✅ 3가지 경제 시나리오 생성 (보수/기준/공격)
- ✅ 필요 은퇴자본 계산 (SWR법 + 연금현가법)
- ✅ 은퇴시점 자산 예측
- ✅ 자금격차 분석
- ✅ 최적 저축계획 수립
- ✅ 브릿지 기간 분석 (은퇴~공적연금 수령 전)

### 2️⃣ 투자메이트 (Tooja) - 은퇴 자산 투자

**"어떻게 안전하게 운용할 것인가?"**

- ✅ 리스크 프로파일 분석
- ✅ 3단계 포트폴리오 생성 (보수/중립/성장)
- ✅ 시장 변동성 기반 동적 조정
- ✅ 계좌별 실행 플랜 (IRP, ISA, 연금저축 최적화)
- ✅ 절세 전략 제시
- ✅ 성과 모니터링

### 3️⃣ 인출메이트 (Inchul) - 은퇴 후 절세 인출

**"어떻게, 언제, 얼마나 꺼내 쓸 것인가?"**

- ✅ 안전인출률(SWR) 기반 인출 설계
- ✅ Guyton-Klinger 가드레일 시스템
- ✅ 절세 인출 순서 최적화
- ✅ 3버킷 전략 (시퀀스 리스크 관리)
- ✅ 계좌별 세금 효율 비교
- ✅ 월별 실행 체크리스트

---

## 🚀 빠른 시작

### 필수 요구사항

| 항목 | 요구사항 | 확인 방법 |
|------|----------|-----------|
| **Docker** | Docker Desktop 또는 Docker Engine | `docker --version` |
| **Docker Compose** | v2.0+ | `docker compose version` |
| **Claude Desktop** | 최신 버전 | [다운로드](https://claude.ai/download) |

### ⚡ 2단계로 시작하기

```bash
# 1️⃣ Docker 이미지 다운로드 (자동)
# Claude Desktop 설정 시 자동으로 이미지가 다운로드됩니다.
# 또는 사전에 수동으로 다운로드할 수 있습니다:
docker pull silverbell0109/jeoklip_server:1.0.0
docker pull silverbell0109/tooja_server:1.0.0
docker pull silverbell0109/inchul_server:1.0.0

# 2️⃣ Claude Desktop 설정 (아래 섹션 참고)
```

---

## 📖 상세 설치 가이드

### 🪟 Windows 설치

#### Step 1: Docker Desktop 설치

1. [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) 다운로드
2. 설치 파일 실행
3. 설치 완료 후 컴퓨터 재시작
4. Docker Desktop 실행

**확인:**
```powershell
docker --version
docker compose version
```

#### Step 2: Docker 이미지 다운로드 (선택사항)

```powershell
# Claude Desktop 설정 시 자동으로 다운로드되지만,
# 사전에 다운로드하려면 아래 명령어를 실행하세요:
docker pull silverbell0109/jeoklip_server:1.0.0
docker pull silverbell0109/tooja_server:1.0.0
docker pull silverbell0109/inchul_server:1.0.0
```

⏱️ 첫 다운로드는 2-3분 소요됩니다.

#### Step 3: Claude Desktop 연동

```powershell
# 설정 파일 위치로 이동
cd $env:APPDATA\Claude

# 설정 파일 생성/편집
notepad claude_desktop_config.json
```

**claude_desktop_config.json 내용:**
```json
{
  "mcpServers": {
    "jeoklip": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "silverbell0109/jeoklip_server:1.0.0"
      ]
    },
    "tooja": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "silverbell0109/tooja_server:1.0.0"
      ]
    },
    "inchul": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "silverbell0109/inchul_server:1.0.0"
      ]
    }
  }
}
```

#### Step 4: Claude Desktop 재시작

1. Claude Desktop 완전 종료
2. Claude Desktop 재실행

---

### 🍎 macOS 설치

#### Step 1: Docker Desktop 설치

1. [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/) 다운로드
2. .dmg 파일 실행
3. Docker Desktop 실행

**확인:**
```bash
docker --version
docker compose version
```

#### Step 2: Docker 이미지 다운로드 (선택사항)

```bash
# Claude Desktop 설정 시 자동으로 다운로드되지만,
# 사전에 다운로드하려면 아래 명령어를 실행하세요:
docker pull silverbell0109/jeoklip_server:1.0.0
docker pull silverbell0109/tooja_server:1.0.0
docker pull silverbell0109/inchul_server:1.0.0
```

#### Step 3: Claude Desktop 연동

```bash
# 설정 파일 생성
mkdir -p ~/Library/Application\ Support/Claude
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**claude_desktop_config.json 내용:** (Windows와 동일)

저장: `Ctrl + O` → `Enter` → `Ctrl + X`

#### Step 4: Claude Desktop 재시작

```bash
osascript -e 'quit app "Claude"'
sleep 2
open -a Claude
```

---

### 🐧 Linux (Ubuntu 22.04) 설치

#### Step 1: Docker 설치

```bash
# 시스템 업데이트
sudo apt update
sudo apt upgrade -y

# Docker 설치
sudo apt install -y docker.io docker-compose

# Docker 서비스 시작 및 자동 시작 설정
sudo systemctl start docker
sudo systemctl enable docker

# 현재 사용자를 docker 그룹에 추가 (sudo 없이 docker 사용)
sudo usermod -aG docker $USER

# 그룹 변경 적용 (재로그인 대신)
newgrp docker
```

**확인:**
```bash
docker --version
docker compose version
docker ps
```

**⚠️ 참고:** `docker ps` 실행 시 권한 오류가 발생하면 로그아웃 후 재로그인하세요.

#### Step 2: Docker 이미지 다운로드 (선택사항)

```bash
# Claude Desktop 설정 시 자동으로 다운로드되지만,
# 사전에 다운로드하려면 아래 명령어를 실행하세요:
docker pull silverbell0109/jeoklip_server:1.0.0
docker pull silverbell0109/tooja_server:1.0.0
docker pull silverbell0109/inchul_server:1.0.0
```

⏱️ 첫 다운로드는 2-3분 소요됩니다.

#### Step 3: Claude Desktop 설치 (Linux용)

**방법 1: Snap을 통한 설치 (권장)**

```bash
# Snap이 없는 경우 설치
sudo apt install -y snapd

# Claude Desktop 설치
sudo snap install claude-desktop
```

**방법 2: AppImage 다운로드**

1. [Claude Desktop for Linux](https://claude.ai/download) 다운로드
2. AppImage 파일에 실행 권한 부여:
```bash
chmod +x Claude-*.AppImage
./Claude-*.AppImage
```

#### Step 4: Claude Desktop 연동

```bash
# 설정 디렉토리 생성
mkdir -p ~/.config/Claude

# 설정 파일 생성/편집
nano ~/.config/Claude/claude_desktop_config.json
```

**claude_desktop_config.json 내용:**
```json
{
  "mcpServers": {
    "jeoklip": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "silverbell0109/jeoklip_server:1.0.0"
      ]
    },
    "tooja": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "silverbell0109/tooja_server:1.0.0"
      ]
    },
    "inchul": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "silverbell0109/inchul_server:1.0.0"
      ]
    }
  }
}
```

저장: `Ctrl + O` → `Enter` → `Ctrl + X`

#### Step 5: Claude Desktop 재시작

```bash
# Snap으로 설치한 경우
snap restart claude-desktop

# 또는 프로세스 종료 후 재실행
pkill -f claude
sleep 2
claude-desktop &  # 또는 GUI에서 실행
```

#### 🔧 Ubuntu 전용 문제 해결

**Docker 권한 오류**
```bash
# 현재 사용자의 그룹 확인
groups

# docker 그룹이 없다면 재로그인
# 또는 다음 명령어로 임시 적용:
sudo chmod 666 /var/run/docker.sock
```

**Claude Desktop이 Docker를 찾지 못할 때**
```bash
# Docker 경로 확인
which docker
# 결과: /usr/bin/docker

# 필요시 설정 파일에서 전체 경로 사용:
"command": "/usr/bin/docker"
```

**AppImage 실행 오류**
```bash
# FUSE 라이브러리 설치
sudo apt install -y libfuse2

# 또는 AppImage 압축 해제 실행
./Claude-*.AppImage --appimage-extract
./squashfs-root/AppRun
```

---

## 🔗 연결 확인

### ✅ 체크리스트

1. **Docker 이미지 확인**
```bash
docker images | grep silverbell0109
```

2. **Claude Desktop에서 도구 확인**
   - 🔧 jeoklip
   - 🔧 tooja
   - 🔧 inchul

3. **테스트 질문**
```
40세, 월 소득 600만원입니다.
60세 은퇴를 위해 필요한 자금을 계산해주세요.
```

---

## 🛠️ 툴 사용 가이드

### 1️⃣ 적립메이트 사용법

#### 📝 질문 템플릿

```
기본 정보:
- 현재 나이: __세
- 월 소득: __만원
- 월 지출: __만원
- 월 저축액: __만원

현재 자산:
- 총 자산: __만원
  - 주식: __만원
  - 채권: __만원
  - 현금: __만원
  - 부동산: __만원
  - 기타: __만원

연금 정보:
- 기대 연금 일시불 수령액: __만원 (퇴직연금, 개인연금 등)

은퇴 목표:
- 은퇴 희망 나이: __세
- 은퇴 후 월 생활비: __만원
- 예상 국민연금: 월 __만원 (__세부터 수령)

필요한 은퇴 자금과 저축 계획을 세워주세요.
```

#### 💡 실전 예시

**질문:**
```
저는 40세이고, 월 소득 600만원입니다.
월 지출은 420만원, 매달 180만원 저축 중입니다.

현재 자산:
- 총 자산: 1억 2천만원
  - 주식: 3천만원
  - 채권: 2천만원
  - 현금: 5천만원
  - IRP/연금저축: 2천만원

연금 정보:
- 기대 연금 일시불 수령액: 약 8천만원 (퇴직연금 예상)

은퇴 목표:
- 60세 은퇴 목표
- 은퇴 후 월 생활비: 300만원
- 예상 국민연금: 월 150만원 (65세부터)

필요한 은퇴 자금과 저축 계획을 세워주세요.
```

**예상 결과:**
```
📊 은퇴 설계 분석

1. 필요 은퇴자본: 약 12억원
2. 현재 계획으로 모을 수 있는 금액:
   - 20년간 저축: 4.3억원
   - 현재 자산 운용: 2.8억원
   - 퇴직연금: 0.8억원
   - 총 예상: 약 7.9억원
3. 부족액: 약 4.1억원

권장 저축 계획:
- 방법 1: 월 저축 250만원으로 증액 (70만원 증액)
- 방법 2: 은퇴 연령 63세로 조정
- 방법 3: 적극적 자산 운용 (연 7% 목표)
```

---

### 2️⃣ 투자메이트 사용법

#### 📝 질문 템플릿

```
투자 정보:
- 나이: __세
- 투자 기간: __년 (은퇴까지 남은 기간)
- 월 투자 가능 금액: __만원

현재 자산:
- 총 투자 가능 자산: __만원
  - 주식: __만원
  - 채권: __만원
  - 현금: __만원
  - 금/원자재: __만원
  - 리츠: __만원
  - 기타: __만원

절세계좌 현황:
- IRP (개인형 퇴직연금):
  - 현재 잔액: __만원
  - 연간 납입 가능액: __만원
- 연금저축:
  - 현재 잔액: __만원
  - 연간 납입 가능액: __만원
- ISA (개인종합자산관리계좌):
  - 현재 잔액: __만원
  - 누적 납입액: __만원 (한도: 최대 2억원)
  - 타입: [일반형/서민형]

투자 성향:
- 투자 경험: [초보/중급/고급]
- 리스크 수용도: [보수적/중립적/공격적]
- 손실 감내 범위: __%까지 견딜 수 있음

보수형, 중립형, 공격형 포트폴리오를 추천하고 절세 전략도 알려주세요.
```

#### 💡 실전 예시

**질문:**
```
45세, 은퇴까지 15년 남았습니다.
월 150만원 추가 투자 가능합니다.

현재 자산:
- 총 투자 가능 자산: 1억 5천만원
  - 주식: 5천만원 (삼성전자, SK하이닉스 등)
  - 채권: 3천만원 (국고채, 회사채)
  - 현금: 5천만원
  - 금: 1천만원
  - 리츠: 1천만원

절세계좌 현황:
- IRP: 현재 3천만원, 연 900만원 납입 가능
- 연금저축: 현재 2천만원, 연 600만원 납입 가능
- ISA: 현재 4천만원, 누적 납입 5천만원 (일반형)

투자 성향:
- 투자 경험: 중급 (5년)
- 리스크 수용도: 중립적
- 손실 감내: 연 15%까지 견딜 수 있음

보수형, 중립형, 공격형 포트폴리오를 추천하고 절세 전략도 알려주세요.
```

**예상 결과:**
```
📊 포트폴리오 추천

【중립형 포트폴리오 (추천)】
자산 배분:
- 주식: 40% (6천만원)
  - 국내 주식: 25%
  - 해외 주식: 15%
- 채권: 40% (6천만원)
  - 국고채: 25%
  - 회사채: 15%
- 금/원자재: 10% (1.5천만원)
- 리츠: 5% (750만원)
- 현금: 5% (750만원)

예상 수익률: 연 6-7%
15년 후 예상 자산: 약 5.2억원

【절세 전략】
계좌별 배치 전략:
1. IRP (900만원/년):
   - 채권 ETF 100% (안정적 수익)
   - 세액공제: 연 148만원 (16.5%)

2. 연금저축 (600만원/년):
   - 혼합형 ETF 또는 TDF
   - 세액공제: 연 99만원 (16.5%)

3. ISA (연 2천만원):
   - 해외 주식 ETF (배당소득 비과세)
   - 국내 주식 (매매차익 비과세)

4. 일반 계좌:
   - 국내 주식 (양도세 없음)
   - 현금 및 금

연간 절세 효과: 약 360만원
15년 누적 절세: 약 5,400만원
```

---

### 3️⃣ 인출메이트 사용법

#### 📝 질문 템플릿

```
은퇴 정보:
- 은퇴 나이: __세
- 예상 수명: __세
- 은퇴 기간: __년
- 월 생활비: __만원

수입:
- 국민연금: 월 __만원 (__세부터)
- 사적연금: 월 __만원
- 기타 소득: 월 __만원 (임대소득 등)

보유 자산 상세:

【일반 계좌】
- 총액: __만원
  - 주식: __만원
  - 채권: __만원
  - 현금: __만원
  - 금: __만원
  - 기타: __만원

【ISA (개인종합자산관리계좌)】
- 총액: __만원
  - 주식: __만원
  - 채권: __만원
  - 현금: __만원
  - ETF: __만원

【연금계좌 (IRP + 연금저축)】
- 총액: __만원
  상세 구분:
  - 비과세재원: __만원 (본인 납입분)
  - 이연퇴직소득: __만원 (퇴직금)
  - 과세재원: __만원 (세액공제 받은 분)
  
  자산 구성:
  - 주식형 펀드: __만원
  - 채권형 펀드: __만원
  - TDF: __만원
  - 현금: __만원

절세 인출 전략을 알려주세요.
```

#### 💡 실전 예시

**질문:**
```
60세 은퇴, 90세까지 30년 생활 계획입니다.
월 생활비 350만원 필요합니다.

수입:
- 국민연금: 월 180만원 (65세부터)
- 사적연금: 월 70만원 (개인연금보험)
- 임대소득: 월 50만원

보유 자산 상세:

【일반 계좌: 2억 5천만원】
- 주식: 1억원 (삼성전자, 카카오 등)
- 채권: 8천만원 (국고채)
- 현금: 5천만원
- 금: 2천만원

【ISA: 1억 2천만원】
- 국내 주식 ETF: 5천만원
- 해외 주식 ETF: 4천만원
- 채권 ETF: 2천만원
- 현금: 1천만원

【연금계좌: 6억원】
- 비과세재원: 1억원 (본인 납입분)
- 이연퇴직소득: 2억원 (퇴직금)
- 과세재원: 3억원 (세액공제 받은 분)

자산 구성:
- TDF 2055: 3억원
- 채권형 펀드: 2억원
- 배당주 펀드: 5천만원
- 현금: 5천만원

절세 인출 전략을 알려주세요.
```

**예상 결과:**
```
📋 절세 인출 전략

【브릿지 기간 (60-65세, 5년)】
월 필요액: 350만원
월 수입: 120만원 (사적연금 70만원 + 임대소득 50만원)
월 부족액: 230만원

인출 순서:
1차: 일반 계좌 우선 인출
  - 연 2,760만원 × 5년 = 1억 3,800만원
  - 국내 주식 → 채권 → 현금 순서
  - 예상 세금: 약 420만원 (배당소득세)

2차: ISA 활용 (일반계좌 소진 후)
  - 비과세 혜택 최대 활용
  - 수익 200만원까지 비과세
  - 초과분 9.9% 분리과세

브릿지 기간 총 세금: 약 620만원

【국민연금 수령 후 (65-90세, 25년)】
월 필요액: 350만원
월 수입: 300만원 (국민연금 180만원 + 사적연금 70만원 + 임대소득 50만원)
월 부족액: 50만원

인출 전략:
1. 연금계좌 분산 인출
   - 비과세재원 우선 인출 (세금 0%)
   - 연 600만원 × 약 17년 = 1억원
   
2. 이연퇴직소득 인출
   - 퇴직소득세 적용 (일반 소득세보다 낮음)
   - 연 600만원 × 약 8년 = 2억원
   - 예상 세금: 약 2,000만원

3. 과세재원 인출 (최후)
   - 연금소득세 적용 (연령별 3.3~5.5%)
   - 예상 세금: 약 1,500만원

【3버킷 전략】
- 버킷 1 (0-5년 생활비): ISA + 일반계좌
- 버킷 2 (5-15년 생활비): 연금계좌 (비과세재원)
- 버킷 3 (15년+ 생활비): 연금계좌 (과세재원) + 남은 자산

【절세 효과】
- 일반 인출 시 예상 세금: 약 5,500만원
- 최적 인출 시 예상 세금: 약 4,120만원
- 절세 효과: 약 1,380만원 (25% 절감)

【주의사항】
✓ 연금계좌는 연 1,500만원 초과 인출 시 기타소득세 적용
✓ 55세 이전 중도 인출 시 16.5% 페널티
✓ ISA는 만기 후 연금계좌 전환 시 추가 300만원 세액공제 가능
```

---

## 🎯 통합 활용 예시

**시나리오: 45세 직장인의 완전한 은퇴 준비**

```
【1단계: 적립메이트로 목표 설정】
"45세, 월 소득 700만원, 월 지출 480만원입니다.
현재 자산 2억원 (주식 1억, 현금 1억), 월 저축 220만원입니다.
60세 은퇴 목표, 은퇴 후 월 400만원 필요합니다.
국민연금 월 200만원 예상됩니다.

필요한 은퇴 자금을 계산해주세요."

→ 결과: 약 15억원 필요, 현재 계획으로 12억원 가능, 3억원 부족

【2단계: 투자메이트로 포트폴리오 구성】
"위 상황에서 현재 자산 2억원과 월 220만원을 
어떻게 투자해야 15년 후 15억원을 만들 수 있을까요?
IRP 5천만원, ISA 3천만원 보유 중입니다.
중립적 성향이며 연 10% 손실까지 견딜 수 있습니다.

포트폴리오와 절세 전략을 알려주세요."

→ 결과: 중립형 포트폴리오 + 계좌별 최적 배치 전략

【3단계: 인출메이트로 은퇴 후 계획】
"60세에 15억원을 모았습니다.
일반계좌 5억, ISA 3억, 연금계좌 7억입니다.
90세까지 월 400만원씩 사용하려면
어떻게 인출해야 세금을 최소화할 수 있나요?"

→ 결과: 브릿지 기간 전략 + 계좌별 최적 인출 순서
```

---

## 💡 효과적인 질문 요령

### ✅ 좋은 질문의 조건

1. **구체적인 숫자 제공**
   - ❌ "은퇴 자금을 모으고 싶어요"
   - ✅ "40세, 월 소득 600만원, 현재 자산 1억원입니다"

2. **현재 상황 상세히 설명**
   - ❌ "투자를 시작하고 싶어요"
   - ✅ "현재 주식 3천만원, 현금 5천만원 보유 중이고 IRP 2천만원 있습니다"

3. **목표 명확히 제시**
   - ❌ "은퇴 준비가 되어 있나요?"
   - ✅ "60세 은퇴 목표, 은퇴 후 월 300만원 생활비가 필요합니다"

4. **절세 계좌 정보 포함**
   - ❌ "어디에 투자하면 좋을까요?"
   - ✅ "IRP 5천만원, ISA 3천만원 있고, 월 100만원 추가 투자 가능합니다"

### 📊 단계별 접근법

**초보자 (20-30대)**
1. 적립메이트로 목표 금액 파악
2. 투자메이트로 포트폴리오 추천 받기
3. 정기적으로 진행 상황 체크

**중급자 (40-50대)**
1. 적립메이트로 현재 진행 상황 점검
2. 투자메이트로 포트폴리오 재조정
3. 인출메이트로 은퇴 후 시뮬레이션

**은퇴 임박 (55-60대)**
1. 적립메이트로 최종 점검
2. 투자메이트로 보수적 조정
3. 인출메이트로 구체적 인출 계획 수립



## 🔍 문제 해결

### ❌ Docker 이미지가 없어요

```bash
# Docker Hub에서 이미지 다운로드
docker pull silverbell0109/jeoklip_server:1.0.0
docker pull silverbell0109/tooja_server:1.0.0
docker pull silverbell0109/inchul_server:1.0.0

# 이미지 확인
docker images | grep silverbell0109
```

### ❌ Claude에서 도구를 사용할 수 없어요

1. Docker Desktop 실행 중인가요?
2. 이미지가 빌드되었나요?
3. 설정 파일 위치가 맞나요?
4. Claude Desktop을 재시작했나요?

### ❌ 도구 실행이 안 돼요

**질문에 구체적인 숫자를 포함하세요:**

❌ 나쁜 예: `은퇴 계획을 세우고 싶어요`
✅ 좋은 예: `40세, 월 소득 600만원입니다. 60세 은퇴 목표입니다`

---

## ❓ FAQ

### Q1. 여러 도구를 동시에 사용 가능?

**A:** 네! Claude가 자동으로 선택합니다. 다만, 요청할 때 "00도구를 사용해줘." 라고 구체적으로 요청하면 더 자세한 결과가 나옵니다.

### Q2. 결과를 파일로 저장 가능?

**A:** 네! Claude에게 직접 요청하면 가능합니다.
```
Ex: 위의 분석 결과를 PDF로 만들어주세요.
```

### Q3. 계산이 정확한가요?

**A:** 대한민국 2025년 기준으로 한 중앙 설정 모듈을 이용하여 비교적 정확한 계산이 가능합니다.

### Q4. 개인정보가 저장되나요?

**A:** 아니요! 로컬에서만 실행되며 외부로 따로 전송하지 않습니다. 또한 컨테이너 종료 시 자동으로 삭제됩니다.


## 📊 기술 스택

| 카테고리 | 기술 |
|----------|------|
| **언어** | Python 3.11+ |
| **프레임워크** | MCP (Model Context Protocol) |
| **컨테이너** | Docker, Docker Compose |
| **라이브러리** | mcp, pydantic, numpy |

---
## 👥 개발팀

**국민대학교 - Koscom AI Agent Challenge 2025**

- 김지원
- 이유진
- 주소정
- 최종은

---

## 📞 문의

- **GitHub Issues**: [프로젝트 이슈](https://github.com/SilVerBell0109/etirement-planning-mcp/issues)
- **Email**: alex.choi@daum.net


</div>
