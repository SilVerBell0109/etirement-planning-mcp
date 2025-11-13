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
3. 하단에 🔧 아이콘 3개 확인

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
sudo apt update
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker $USER
newgrp docker
```

#### Step 2-4: macOS와 동일

설정 파일 위치: `~/.config/Claude/claude_desktop_config.json`

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
- 현재 자산: __만원
- 월 저축액: __만원

은퇴 목표:
- 은퇴 희망 나이: __세
- 은퇴 후 월 생활비: __만원
- 예상 국민연금: 월 __만원

필요한 은퇴 자금과 저축 계획을 세워주세요.
```

#### 💡 실전 예시

**질문:**
```
저는 40세이고, 월 소득 600만원입니다.
현재 자산 5천만원, 매달 150만원 저축 중입니다.
60세 은퇴 목표이고, 은퇴 후 월 300만원 필요합니다.
국민연금은 월 150만원 예상됩니다.

필요한 은퇴 자금과 저축 계획을 세워주세요.
```

**예상 결과:**
```
📊 은퇴 설계 분석

1. 필요 은퇴자본: 약 12억원
2. 현재 계획으로 모을 수 있는 금액: 약 10억원
3. 부족액: 약 2억원

권장 저축 계획:
- 방법 1: 월 저축 180만원 (30만원 증액)
- 방법 2: 은퇴 연령 62세로 조정
```

---

### 2️⃣ 투자메이트 사용법

#### 📝 질문 템플릿

```
투자 정보:
- 나이: __세
- 투자 가능 금액: __만원
- 월 추가 투자: __만원
- 투자 기간: __년

투자 성향:
- 투자 경험: [초보/중급/고급]
- 리스크 성향: [보수적/중립적/공격적]

포트폴리오를 추천하고 절세 전략도 알려주세요.
```

#### 💡 실전 예시

**질문:**
```
45세, 은퇴 자금 1억원을 투자하려고 합니다.
투자 경험 5년, 중립적 성향입니다.
투자 기간 15년, 월 100만원 추가 투자 가능합니다.

보수형, 중립형, 공격형 포트폴리오를 추천해주세요.
```

**예상 결과:**
```
📊 포트폴리오 추천

중립형 (추천):
- 주식: 40%
- 채권: 40%
- 금/리츠: 20%
- 예상 수익률: 6-7%
- 15년 후: 약 4.5억원

절세 전략:
- IRP: 월 75만원 (세액공제 16.5%)
- 연금저축: 월 50만원
- ISA: 월 50만원
- 연간 절세: 약 277만원
```

---

### 3️⃣ 인출메이트 사용법

#### 📝 질문 템플릿

```
은퇴 정보:
- 은퇴 나이: __세
- 예상 수명: __세
- 월 생활비: __만원

수입:
- 국민연금: 월 __만원 (__세부터)
- 사적연금: 월 __만원

보유 자산:
- 일반 계좌: __만원
- ISA: __만원
- 연금계좌: __만원

절세 인출 전략을 알려주세요.
```

#### 💡 실전 예시

**질문:**
```
60세 은퇴, 90세까지 생활 계획입니다.
월 생활비 300만원 필요합니다.
국민연금 월 150만원 (65세부터)
사적연금 월 50만원

보유 자산:
- 일반 계좌: 2억원
- ISA: 1억원
- 연금계좌: 5억원

절세 인출 전략을 알려주세요.
```

**예상 결과:**
```
📋 인출 전략

브릿지 기간 (60-65세):
- 일반계좌 우선 인출
- ISA 비과세 활용
- 예상 세금: 약 300만원

국민연금 수령 후 (65-90세):
- 연금계좌 분산 인출
- 절세 효과: 약 1,000만원

3버킷 전략으로 안정적 자산 관리
```

---

## 🎬 실전 시나리오

### 시나리오 A: 완전 초보 (20-30대)

```
30세, 월 소득 400만원, 저축 1천만원입니다.
60세 은퇴 목표입니다.

1. 얼마를 모아야 하나요?
2. 매달 얼마를 저축해야 하나요?
3. 어떻게 투자해야 하나요?
4. 은퇴 후 어떻게 인출해야 하나요?
```

### 시나리오 B: 중급자 (40-50대)

```
50세, 월 소득 800만원, 현재 자산 4억원입니다.
월 300만원 저축 중, IRP/ISA 보유 중입니다.

1. 10년 후 예상 자산은?
2. 은퇴 목표 (월 400만원) 달성 가능?
3. 포트폴리오 조정 필요?
```

### 시나리오 C: 은퇴 직전 (55-60대)

```
59세, 1년 후 은퇴 예정입니다.
총 자산 10억원 (일반 3억, ISA 1억, 연금 6억)
예상 국민연금 월 180만원 (65세부터)
목표 생활비 월 350만원

1. 자산 배분 조정 필요?
2. 브릿지 기간 전략은?
3. 계좌별 인출 순서는?
4. 30년 자산 유지 가능?
```

---

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

### ❌ Claude에서 도구가 안 보여요

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

**A:** 네! Claude가 자동으로 선택합니다.

### Q2. 결과를 파일로 저장 가능?

**A:** 네! Claude에게 요청하세요.
```
위의 분석 결과를 PDF로 만들어주세요.
```

### Q3. 계산이 정확한가요?

**A:** 금융 공식 기반:
- 안전인출률: 3.5%
- 인플레이션: 2%
- 기대수익률: 5-9%

### Q4. 개인정보가 저장되나요?

**A:** 아니요!
- 로컬에서만 실행
- 외부 전송 없음
- 컨테이너 종료 시 삭제

### Q5. 실제 투자에 사용 가능?

**A:** ⚠️ 교육 및 참고용입니다.
- 실제 투자 전 전문가 상담 필수
- 계산은 예측이며 보장되지 않음

---

## 📊 기술 스택

| 카테고리 | 기술 |
|----------|------|
| **언어** | Python 3.11+ |
| **프레임워크** | MCP (Model Context Protocol) |
| **컨테이너** | Docker, Docker Compose |
| **라이브러리** | mcp, pydantic, numpy |

---

## 🤝 기여

기여는 언제나 환영합니다!

1. Fork the Project
2. Create Feature Branch
3. Commit Changes
4. Push to Branch
5. Open Pull Request

---

## 📝 라이선스

MIT 라이선스 - 자세한 내용은 [LICENSE](LICENSE) 참조

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

---

## 🙏 감사의 말

- **Anthropic** - Claude 및 MCP
- **Koscom** - AI Agent Challenge
- **오픈소스 커뮤니티**

---

## ⚠️ 면책 조항

이 소프트웨어는 **교육 목적**으로만 제공됩니다.

- 실제 투자 결정 전 전문가 상담 필수
- 제공 계산은 참고용이며 보장되지 않음
- 개인 상황에 따라 결과 상이
- 개발자는 손실에 대해 책임지지 않음

---

<div align="center">

### ⭐ Star를 눌러주세요!

**Made with ❤️ for a better retirement planning**

</div>
