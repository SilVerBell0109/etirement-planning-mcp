# 은퇴 설계 AI Agent - MCP Server

Claude Desktop과 연동되는 포괄적인 은퇴 설계 지원 시스템입니다.

## 🎯 개요

이 프로젝트는 **Koscom AI Agent Challenge**를 위해 개발된 은퇴 설계 전문 MCP(Model Context Protocol) 서버입니다. 세 가지 핵심 서비스를 통해 은퇴 준비부터 자산 운용, 인출 전략까지 전 과정을 지원합니다.

## 📦 주요 서비스

### 1. 적립메이트 (Jeoklip) - 은퇴 자산 적립
**"얼마를, 어떻게 모을 것인가?"**

- ✅ 3가지 경제 시나리오 생성 (보수/기준/공격)
- ✅ 필요 은퇴자본 계산 (SWR법 + 연금현가법)
- ✅ 은퇴시점 자산 예측
- ✅ 자금격차 분석
- ✅ 최적 저축계획 수립
- ✅ 대안 시나리오 비교

### 2. 투자메이트 (Tooja) - 은퇴 자산 투자
**"어떻게 안전하게 운용할 것인가?"**

- ✅ 리스크 프로파일 분석
- ✅ 3단계 포트폴리오 생성 (보수/중립/성장)
- ✅ 시장 변동성 기반 동적 조정
- ✅ 계좌별 실행 플랜 (IRP, 연금저축 최적화)
- ✅ 성과 모니터링 (샤프비율, MDD 등)

### 3. 인출메이트 (Inchul) - 은퇴 후 절세 인출
**"어떻게, 언제, 얼마나 꺼내 쓸 것인가?"**

- ✅ 안전인출률(SWR) 기반 인출 설계
- ✅ Guyton-Klinger 가드레일 시스템
- ✅ 절세 인출 순서 최적화
- ✅ 3버킷 전략 (시퀀스 리스크 관리)
- ✅ 브릿지 기간 분석
- ✅ 월별 실행 체크리스트

## 🚀 빠른 시작

### 필요 환경
- Python 3.11+
- Claude Desktop

### 설치

```bash
# 1. 프로젝트 클론
git clone [repository-url]
cd retirement-planning-mcp

# 2. 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 테스트 실행
python tests/test_jeoklip.py
python tests/test_tooja.py
python tests/test_inchul.py
```

### Claude Desktop 연동

`claude_desktop_config.json` 파일에 추가:

```json
{
  "mcpServers": {
    "jeoklip": {
      "command": "python",
      "args": ["-m", "mcp_server_jeoklip"],
      "cwd": "/your/project/path"
    },
    "tooja": {
      "command": "python",
      "args": ["-m", "mcp_server_tooja"],
      "cwd": "/your/project/path"
    },
    "inchul": {
      "command": "python",
      "args": ["-m", "mcp_server_inchul"],
      "cwd": "/your/project/path"
    }
  }
}
```

자세한 설치 방법은 [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)를 참조하세요.

## 📖 사용 예시

### 적립메이트 사용

```
40세, 월 소득 500만원, 현재 자산 1억원입니다.
65세에 은퇴하려면 얼마를 저축해야 하나요?
```

### 투자메이트 사용

```
45세이고 은퇴 자금 1억원을 투자하려고 합니다.
보수적, 중립적, 공격적 포트폴리오를 각각 추천해주세요.
```

### 인출메이트 사용

```
65세 은퇴, 자산 10억원입니다.
월 250만원 생활비가 필요한데 어떻게 인출해야
세금을 최소화하면서 자산을 오래 유지할 수 있나요?
```

## 🏗️ 프로젝트 구조

```
retirement-planning-mcp/
├── mcp_server_jeoklip/       # 적립메이트
│   ├── __init__.py
│   ├── __main__.py
│   └── server.py              # 6개 Tools
├── mcp_server_tooja/          # 투자메이트
│   ├── __init__.py
│   ├── __main__.py
│   └── server.py              # 5개 Tools
├── mcp_server_inchul/         # 인출메이트
│   ├── __init__.py
│   ├── __main__.py
│   └── server.py              # 6개 Tools
├── tests/
│   ├── test_jeoklip.py
│   ├── test_tooja.py
│   └── test_inchul.py
├── requirements.txt
├── INSTALLATION_GUIDE.md
└── README.md
```

## 🔧 기술 스택

- **프레임워크**: Model Context Protocol (MCP)
- **언어**: Python 3.11+
- **주요 라이브러리**:
  - `mcp` - MCP 서버 구현
  - `pydantic` - 데이터 검증
  - `numpy` - 금융 계산

## 📊 주요 기능

### 금융 계산 엔진
- 복리 계산 (FV, PV)
- 연금 계산 (Annuity)
- PMT 계산 (정기 저축액)
- 인플레이션 조정
- 세금 효과 반영

### 시나리오 분석
- 보수/기준/공격 3가지 시나리오
- 대안 비교 (은퇴연령, 목표지출, 주택연금 등)
- 민감도 분석

### 위험 관리
- 안전인출률(SWR) 3.0~3.5%
- Guyton-Klinger 가드레일
- 3버킷 전략 (시퀀스 리스크 완화)
- 변동성 타겟팅

## 🎓 설계 원칙

### 1. 투명성
- 모든 계산 과정 공개
- 가정값 명시
- 출처 제공

### 2. 보안
- 로컬 데이터 저장
- 개인정보 암호화
- 외부 전송 없음

### 3. 실행 가능성
- 구체적인 실행 계획
- 월별 체크리스트
- 자동화 가이드

### 4. 사용자 중심
- 자연어 인터페이스
- 최소 입력
- 명확한 결과

## 📈 기대 효과

- **개인화**: 맞춤형 은퇴 설계
- **최적화**: 세제 혜택 극대화
- **리스크 관리**: 변동성 대응
- **장기 안정성**: 자산 지속 가능성 향상

## ⚠️ 면책 조항

이 소프트웨어는 **교육 및 정보 제공 목적**으로만 제공됩니다.

- 실제 투자 결정 전 반드시 전문가와 상담하세요
- 제공된 계산은 참고용이며 보장되지 않습니다
- 개인의 재무 상황에 따라 결과가 다를 수 있습니다
- 개발자는 사용으로 인한 손실에 대해 책임지지 않습니다

## 🤝 기여

기여는 언제나 환영합니다!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 👥 팀

**국민대학교**
- 김지원
- 이유진
- 주소정
- 최종은

**Koscom AI Agent Challenge 2025**

## 📞 문의

- GitHub Issues: [프로젝트 이슈 페이지]
- Email: [연락처]

## 🙏 감사의 말

- Anthropic - Claude 및 MCP 프로토콜
- Koscom - AI Agent Challenge 주최
- 모든 오픈소스 기여자들

---

**Made with ❤️ for a better retirement planning**