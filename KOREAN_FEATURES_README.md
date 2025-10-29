# 한국 특화 은퇴 설계 AI 에이전트

## 개요

이 프로젝트는 **한국 금융 시장과 세제 환경에 최적화된** 은퇴 설계 AI 에이전트입니다. 기존의 하드코딩된 수치값들을 제거하고, 한국의 실제 금융 환경을 반영한 중앙 설정 시스템으로 전환했습니다.

## 주요 개선사항

### 1. 중앙 설정화 (Centralized Configuration)
- **하드코딩 제거**: 모든 수치값을 `config/financial_constants_2025.py`로 이동
- **연도별 버전 관리**: 2025년 기준 설정, 향후 2026년 등 추가 가능
- **지역별 확장**: 한국(KOR) 외에 미국(USA) 등 다른 지역 추가 가능

### 2. 한국 특화 기능

#### 세제 최적화
- **연금소득세 분리과세**: 1,500만원까지 3.3% 저세율 우선 적용
- **금융소득 분리과세**: 15.4% 원천징수
- **세제혜택 계좌**: IRP(1,800만원), 연금저축(700만원) 한도 반영

#### 시장 특성 반영
- **변동성**: 코스피 22%, 국채 8% (실제 한국 시장 데이터 기반)
- **자산 배분**: 국내주식 60%, 해외주식 40% 가이드라인
- **리츠**: 5% 권장 비중

#### 생애주기 투자
- **130-나이 규칙**: 나이에 따른 주식 비중 자동 조정
- **생애주기 단계**: accumulation/transition/retirement 구분
- **위험성향**: 0-100점 기준으로 주식 상한 30-80% 조정

### 3. 서버별 주요 기능

#### 인출메이트 (mcp_server_inchul)
- **SWR 기간별 조정**: 20년 +0.5%p, 30년 기본, 40년 -0.5%p
- **한국형 가드레일**: ±25% 임계값 (한국 변동성 고려)
- **3버킷 전략**: 2-8-나머지 + 의료비 버킷 (연령 가중)
- **세금 최적화**: 연금 분리과세 → 종합과세 → 일반과세 순서

#### 적립메이트 (mcp_server_jeoklip)
- **경제 시나리오**: 보수/기준/공격 3가지 (확률 가중)
- **SWR 범위**: 기간별 동적 조정
- **의료비 준비금**: 연비 15% × 기간 × 연령 가중치
- **한국 대안**: 주택연금, 국민연금 지연 수급 등

#### 투자메이트 (mcp_server_tooja)
- **자산 배분**: 국내/해외 분할, 리츠 포함
- **변동성 조정**: 코스피 기준 실시간 조정
- **리밸런싱**: 분기별 검토, ±5% 정기, ±8% 긴급
- **성과 평가**: 한국 무위험수익률(3.2%) 기준

## 파일 구조

```
etirement-planning-mcp/
├── config/
│   └── financial_constants_2025.py    # 중앙 설정 모듈
├── mcp_server_inchul/
│   └── server.py                      # 인출메이트 (한국 특화)
├── mcp_server_jeoklip/
│   └── server.py                      # 적립메이트 (한국 특화)
├── mcp_server_tooja/
│   └── server.py                      # 투자메이트 (한국 특화)
└── tests/
    ├── test_korean_financial_constants.py
    ├── test_inchul_korean.py
    ├── test_jeoklip_korean.py
    ├── test_tooja_korean.py
    └── run_all_tests.py
```

## 사용법

### 1. 설정 모듈 사용
```python
from config.financial_constants_2025 import KOR_2025

# SWR 조정
swr_rate = KOR_2025.SWR.adjust_by_duration(30)  # 30년: 3.5%

# 세율 조회
tax_rate = KOR_2025.TAX.interest_dividend  # 15.4%

# 시장 특성
kospi_vol = KOR_2025.MKT.kospi_volatility  # 22%
```

### 2. 서버 실행
```bash
# 인출메이트
cd mcp_server_inchul
python server.py

# 적립메이트  
cd mcp_server_jeoklip
python server.py

# 투자메이트
cd mcp_server_tooja
python server.py
```

### 3. 테스트 실행
```bash
# 모든 테스트
cd tests
python run_all_tests.py

# 개별 테스트
python -m unittest test_korean_financial_constants.py
```

## 주요 수치값 (2025년 기준)

### SWR (안전인출률)
- **기본**: 3.5%
- **20년 이하**: 4.0% (+0.5%p)
- **30년**: 3.5% (기본)
- **40년 이상**: 3.0% (-0.5%p)

### 가드레일
- **상한 임계값**: +25%
- **하한 임계값**: -25%
- **최대 연간 조정**: 20%

### 세율
- **연금 분리과세**: 3.3% (1,500만원까지)
- **금융소득 분리과세**: 15.4%
- **연금 종합과세**: 3% ~ 42% (구간별)

### 시장 특성
- **코스피 변동성**: 22%
- **국채 변동성**: 8%
- **국내주식 비중**: 60%
- **해외주식 비중**: 40%
- **리츠 비중**: 5%

### 상품 한도
- **IRP**: 1,800만원/년
- **연금저축**: 700만원/년
- **주택연금**: 3억원

## 향후 계획

### 1. 연도별 업데이트
- `financial_constants_2026.py` 추가
- 세율, 금리 등 법규 변경사항 반영

### 2. 지역별 확장
- `USA_2025` 클래스 추가
- 미국 세제, 시장 특성 반영

### 3. 실시간 데이터 연동
- 시장 변동성 실시간 모니터링
- 동적 파라미터 조정

### 4. 백테스팅 강화
- 1997 외환위기, 2008 금융위기 등 충격 시나리오
- 한국 시장 데이터 기반 검증

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 기여하기

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 문의

프로젝트 관련 문의사항이 있으시면 이슈를 등록해 주세요.
