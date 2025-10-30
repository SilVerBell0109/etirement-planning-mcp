# config/financial_constants_2025.py
# 중앙 설정 모듈 - 대한민국 2025년 기준
import sys
from dataclasses import dataclass
from typing import Dict, Tuple

# __pycache__ 폴더 생성 방지
sys.dont_write_bytecode = True


# ========== 기본 금융 규칙 ==========

@dataclass(frozen=True)
class SWRRules:
    """안전인출률 규칙"""
    base_moderate: float = 0.035   # 3.5% 기본
    min_floor: float = 0.025       # 최소 2.5%
    by_years_delta: float = 0.005  # 20년 +0.5%p / 40년 -0.5%p

    def adjust_by_duration(self, years: int) -> float:
        """기간에 따른 SWR 조정"""
        if years <= 20:
            return min(0.06, self.base_moderate + self.by_years_delta)
        if years <= 30:
            return self.base_moderate
        return max(self.min_floor, self.base_moderate - self.by_years_delta)

@dataclass(frozen=True)
class GuardrailsKOR:
    """가드레일 규칙 (Guyton-Klinger 원칙 기반)"""
    upper_threshold: float = 0.20   # 20% (Guyton-Klinger 표준)
    lower_threshold: float = -0.20  # -20% (Guyton-Klinger 표준)
    inc_rate: float = 0.10          # 10% 증액
    dec_rate: float = 0.10          # 10% 감액
    max_adjustment_per_year: float = 0.20  # 연간 최대 20% 조정
    inflation_floor: bool = True    # 인플레이션 하한선 적용

@dataclass(frozen=True)
class EconomicScenariosKOR:
    """한국 경제 시나리오"""
    pessimistic: Dict = None
    baseline: Dict = None
    optimistic: Dict = None
    volatility: Dict = None

    def __post_init__(self):
        object.__setattr__(self, "pessimistic", {
            "inflation_rate": 0.030, "pre_ret": 0.030, "post_ret": 0.020, 
            "wage": 0.025, "real_ret": 0.000, "p": 0.20
        })
        object.__setattr__(self, "baseline", {
            "inflation_rate": 0.020, "pre_ret": 0.050, "post_ret": 0.035, 
            "wage": 0.035, "real_ret": 0.030, "p": 0.50
        })
        object.__setattr__(self, "optimistic", {
            "inflation_rate": 0.020, "pre_ret": 0.070, "post_ret": 0.050, 
            "wage": 0.045, "real_ret": 0.050, "p": 0.30
        })
        object.__setattr__(self, "volatility", {
            "equity": 0.18, "bond": 0.06, "inflation": 0.015
        })

@dataclass(frozen=True)
class TaxKOR2025:
    """한국 2025년 세제 구조"""
    
    # 금융소득 분리과세 (이자·배당)
    interest_dividend: float = 0.154  # 15.4%

    # === 연금소득 분리과세 (원천징수) - 2024년 개정 ===
    pension_separated_brackets: Tuple = (
        (14_000_000, 0.033),      # 1,400만원 이하: 3.3% (2024년 개정)
        (45_000_000, 0.044),      # 4,500만원 이하: 4.4%
        (100_000_000, 0.055),     # 1억원 이하: 5.5%
        (float("inf"), 0.055)     # 1억원 초과: 5.5%
    )
    
    # === 연금소득 종합과세 (선택시 적용) ===
    comprehensive_income_brackets: Tuple = (
        (14_000_000, 0.06),       # 1,400만원 이하: 6%
        (50_000_000, 0.15),       # 5,000만원 이하: 15%
        (88_000_000, 0.24),       # 8,800만원 이하: 24%
        (150_000_000, 0.35),      # 1.5억원 이하: 35%
        (300_000_000, 0.38),      # 3억원 이하: 38%
        (500_000_000, 0.40),      # 5억원 이하: 40%
        (1_000_000_000, 0.42),    # 10억원 이하: 42%
        (float("inf"), 0.45)      # 10억원 초과: 45%
    )
    
    # 연금소득 분리과세 한도 (2024년 개정)
    pension_separated_cap: int = 14_000_000  # 연 1,400만원 (2024년 개정)
    
    # 연금계좌 세액공제 한도
    pension_deduction_limit: int = 9_000_000  # 900만원 (2025년 상향)

@dataclass(frozen=True)
class PerformanceRulesKOR:
    """한국 성과 평가 기준"""
    risk_free_rate: float = 0.032  # 국고채 3년물 (2024년 12월 기준)
    sharpe_benchmark: Dict = None
    mdd_limits: Dict = None

    def __post_init__(self):
        object.__setattr__(self, "sharpe_benchmark", {
            "excellent": 1.0, "good": 0.7, "ok": 0.5, "weak": 0.3, "bad": 0.0
        })
        object.__setattr__(self, "mdd_limits", {
            "conservative": 0.15, "moderate": 0.20, "aggressive": 0.30
        })

@dataclass(frozen=True)
class BucketRules:
    """3버킷 전략 규칙"""
    cash_years: int = 2
    income_years: int = 8
    healthcare_base_ratio: float = 0.15  # 연비 대비 의료비
    healthcare_age_factor: Dict = None

    def __post_init__(self):
        object.__setattr__(self, "healthcare_age_factor", {
            (65, 70): 1.0, (70, 75): 1.3, (75, 80): 1.6, 
            (80, 85): 2.0, (85, 200): 2.5
        })

# ========== 한국 특화 규칙 ==========

@dataclass(frozen=True)
class KoreanPensionAccounts:
    """한국 연금계좌 한도 (2025년)"""
    # 납입 한도
    pension_savings_annual_limit: int = 18_000_000   # 1,800만원
    irp_annual_limit: int = 18_000_000              # 1,800만원
    
    # 세액공제 한도 (연금저축 + IRP 합산)
    total_deduction_limit: int = 9_000_000          # 900만원
    pension_only_deduction: int = 6_000_000         # 연금저축만: 600만원
    
    # ISA (개인종합자산관리계좌)
    isa_annual_limit: int = 20_000_000              # 2,000만원
    isa_total_limit: int = 100_000_000              # 1억원 (평생)

@dataclass(frozen=True)
class KoreanNationalPension:
    """국민연금 제도 (2025년 기준)"""
    
    # 소득대체율 (40년 가입 기준)
    income_replacement_rate: float = 0.40  # 40% (2028년까지 단계적 인하)
    
    # 기준연금액 (2024년 실제)
    max_monthly_benefit: int = 2_200_000  # 약 220만원 (2024년 실제)
    
    # 조기수령 감액률 (만 60~64세)
    early_claim: Dict = None  # 연 6% 감액 (최대 30%)
    
    # 연기수령 증액률 (만 66~70세)
    delayed_claim: Dict = None  # 연 7.2% 증액 (최대 36%)
    
    def __post_init__(self):
        object.__setattr__(self, "early_claim", {
            60: 0.70,  # 5년 조기: 30% 감액
            61: 0.76,  # 4년 조기: 24% 감액
            62: 0.82,  # 3년 조기: 18% 감액
            63: 0.88,  # 2년 조기: 12% 감액
            64: 0.94,  # 1년 조기: 6% 감액
            65: 1.00   # 정상 수령
        })
        
        object.__setattr__(self, "delayed_claim", {
            65: 1.00,   # 정상 수령
            66: 1.072,  # 1년 연기: 7.2% 증액
            67: 1.144,  # 2년 연기: 14.4% 증액
            68: 1.216,  # 3년 연기: 21.6% 증액
            69: 1.288,  # 4년 연기: 28.8% 증액
            70: 1.360   # 5년 연기: 36% 증액
        })

@dataclass(frozen=True)
class KoreanHousingPension:
    """주택연금 제도 (2025년)"""
    
    # 가입 대상 주택 공시가격 한도
    property_value_limit: int = 1_200_000_000  # 12억원
    
    # 가입 연령
    min_age: int = 55  # 만 55세 이상
    
    # 부부 기준 수령액 (대략적 계산)
    estimated_monthly_payment: Dict = None
    
    def __post_init__(self):
        # 예시: 주택가격별 월 수령액 (부부 모두 65세 기준)
        object.__setattr__(self, "estimated_monthly_payment", {
            300_000_000: 800_000,   # 3억: 약 80만원/월
            600_000_000: 1_500_000, # 6억: 약 150만원/월
            900_000_000: 2_100_000  # 9억: 약 210만원/월
        })

@dataclass(frozen=True)
class KoreanSpecificRules:
    """한국 특화 규칙 (기존 호환성 유지)"""
    # 의료비 실부담률
    medical_cost_ratio: float = 0.20

@dataclass(frozen=True)
class KoreanMarketCharacteristics:
    """한국 시장 특성"""
    kospi_volatility: float = 0.22
    kosdaq_volatility: float = 0.28
    bond_volatility: float = 0.08
    kospi_bond_correlation: float = -0.3
    gold_inflation_correlation: float = 0.4
    # 자산 배분 가이드라인
    domestic_equity_ratio: float = 0.40    # 국내 40% (글로벌 분산 권장)
    foreign_equity_ratio: float = 0.60     # 해외 60% (글로벌 분산 권장)
    reit_ratio: float = 0.05

@dataclass(frozen=True)
class RegulatoryCompliance:
    """규제 준수 사항"""
    suitability_requirements: bool = True
    risk_disclosure_required: bool = True
    data_retention_years: int = 5
    max_concentration_ratio: float = 0.30  # 단일 자산 30% 제한
    rebalancing_frequency_min: int = 1     # 최소 연 1회

# ========== 적립메이트용 설정 ==========

@dataclass(frozen=True)
class AccumulationAssetAllocation:
    """적립기 자산배분 (생애주기별)"""
    
    # 연령대별 권장 배분
    age_based_allocation: Dict = None
    
    # 위험성향별 조정
    risk_adjustment: Dict = None
    
    def __post_init__(self):
        # 나이별 기본 배분 (120-나이 규칙 기반)
        object.__setattr__(self, "age_based_allocation", {
            "20s": {  # 20대
                "equity_ratio": 0.90,      # 주식 90%
                "bond_ratio": 0.05,        # 채권 5%
                "alternative": 0.05,       # 대체투자 5%
                "domestic_foreign": (0.40, 0.60)  # 국내:해외 = 4:6
            },
            "30s": {  # 30대
                "equity_ratio": 0.85,
                "bond_ratio": 0.10,
                "alternative": 0.05,
                "domestic_foreign": (0.40, 0.60)
            },
            "40s": {  # 40대
                "equity_ratio": 0.75,
                "bond_ratio": 0.20,
                "alternative": 0.05,
                "domestic_foreign": (0.40, 0.60)
            },
            "50s_early": {  # 50대 초반 (은퇴 10년 전)
                "equity_ratio": 0.65,
                "bond_ratio": 0.30,
                "alternative": 0.05,
                "domestic_foreign": (0.40, 0.60)
            },
            "50s_late": {  # 50대 후반 (은퇴 5년 전)
                "equity_ratio": 0.55,
                "bond_ratio": 0.40,
                "alternative": 0.05,
                "domestic_foreign": (0.35, 0.65)
            }
        })
        
        # 위험성향별 조정치
        object.__setattr__(self, "risk_adjustment", {
            "conservative": -0.15,    # 주식 -15%p
            "moderate": 0.00,         # 조정 없음
            "aggressive": +0.10       # 주식 +10%p
        })

@dataclass(frozen=True)
class AccountAllocationRules:
    """계좌별 자산 배분 규칙"""
    
    # 연금계좌 vs 일반계좌 배분 기준
    pension_vs_taxable: Dict = None
    
    def __post_init__(self):
        object.__setattr__(self, "pension_vs_taxable", {
            "under_900K_monthly": {  # 월 90만원 이하
                "pension_account": 1.00,   # 100% 연금계좌
                "taxable_account": 0.00,
                "reason": "세액공제 한도 내 최대 활용"
            },
            "900K_to_2M": {  # 월 90만원 ~ 200만원
                "pension_account": 0.60,   # 60% 연금계좌
                "taxable_account": 0.40,   # 40% 일반계좌
                "reason": "세액공제 + 유동성 확보"
            },
            "above_2M": {  # 월 200만원 이상
                "pension_account": 0.40,   # 40% 연금계좌
                "taxable_account": 0.60,   # 60% 일반계좌
                "reason": "유동성 중요, 세액공제 한도 이미 채움"
            }
        })

@dataclass(frozen=True)
class ExpectedReturns:
    """자산별 기대수익률 (명목, 연율)"""
    
    returns: Dict = None
    
    def __post_init__(self):
        object.__setattr__(self, "returns", {
            # 주식
            "kospi": 0.065,               # 6.5%
            "kosdaq": 0.080,              # 8.0%
            "us_sp500": 0.090,            # 9.0%
            "us_nasdaq": 0.110,           # 11.0%
            "developed_ex_us": 0.075,     # 7.5%
            "emerging_markets": 0.095,    # 9.5%
            
            # 채권
            "korea_govt_bond": 0.035,     # 3.5%
            "korea_corp_bond": 0.045,     # 4.5%
            "us_treasury": 0.040,         # 4.0%
            
            # 대체투자
            "reit": 0.060,                # 6.0%
            "gold": 0.030,                # 3.0%
            "commodity": 0.045,           # 4.5%
            
            # 현금성
            "savings": 0.028,             # 2.8%
            "mmf": 0.030                  # 3.0%
        })

# ========== 투자메이트용 설정 ==========

@dataclass(frozen=True)
class RiskBasedAllocation:
    """위험성향별 자산배분"""
    
    allocations: Dict = None
    
    def __post_init__(self):
        object.__setattr__(self, "allocations", {
            "conservative": {
                "equity": 0.30,           # 주식 30%
                "bond": 0.55,             # 채권 55%
                "alternative": 0.10,      # 대체투자 10%
                "cash": 0.05,             # 현금 5%
                
                "equity_detail": {
                    "domestic": 0.40,     # 국내 40%
                    "foreign": 0.60,      # 해외 60%
                    
                    "domestic_breakdown": {
                        "large_cap": 0.70,      # 대형주 70%
                        "dividend": 0.30        # 배당주 30%
                    },
                    "foreign_breakdown": {
                        "us_sp500": 0.50,       # 미국 S&P500 50%
                        "developed": 0.40,      # 선진국 40%
                        "emerging": 0.10        # 신흥국 10%
                    }
                },
                
                "bond_detail": {
                    "domestic_govt": 0.50,      # 국내 국채 50%
                    "domestic_corp": 0.30,      # 국내 회사채 30%
                    "foreign_bond": 0.20        # 해외채권 20%
                },
                
                "expected_return": 0.045,       # 4.5%
                "expected_volatility": 0.08     # 8%
            },
            
            "moderate": {
                "equity": 0.50,
                "bond": 0.35,
                "alternative": 0.10,
                "cash": 0.05,
                
                "equity_detail": {
                    "domestic": 0.40,
                    "foreign": 0.60,
                    
                    "domestic_breakdown": {
                        "large_cap": 0.50,
                        "mid_small_cap": 0.30,
                        "dividend": 0.20
                    },
                    "foreign_breakdown": {
                        "us_sp500": 0.40,
                        "us_nasdaq": 0.20,
                        "developed": 0.30,
                        "emerging": 0.10
                    }
                },
                
                "bond_detail": {
                    "domestic_govt": 0.40,
                    "domestic_corp": 0.40,
                    "foreign_bond": 0.20
                },
                
                "expected_return": 0.060,       # 6.0%
                "expected_volatility": 0.12     # 12%
            },
            
            "aggressive": {
                "equity": 0.70,
                "bond": 0.15,
                "alternative": 0.10,
                "cash": 0.05,
                
                "equity_detail": {
                    "domestic": 0.40,
                    "foreign": 0.60,
                    
                    "domestic_breakdown": {
                        "large_cap": 0.30,
                        "mid_small_cap": 0.40,
                        "growth": 0.20,
                        "dividend": 0.10
                    },
                    "foreign_breakdown": {
                        "us_sp500": 0.30,
                        "us_nasdaq": 0.30,
                        "developed": 0.20,
                        "emerging": 0.20
                    }
                },
                
                "bond_detail": {
                    "domestic_corp": 0.50,
                    "foreign_bond": 0.30,
                    "high_yield": 0.20
                },
                
                "expected_return": 0.075,       # 7.5%
                "expected_volatility": 0.16     # 16%
            }
        })

@dataclass(frozen=True)
class InvestmentWeights:
    """투자 금액별 구체적 비중 (ETF 제외)"""
    
    # 자산군별 투자 비중 계산
    asset_allocation: Dict = None
    
    def __post_init__(self):
        # 자산군별 투자 비중 (ETF 상품명 제외)
        object.__setattr__(self, "asset_allocation", {
            "conservative": {
                "total": 500_000,
                "allocation": {
                    "국내_대형주": {
                        "amount": 60_000,      # 6만원
                        "percentage": 0.12,    # 12%
                        "category": "주식"
                    },
                    "해외_선진국": {
                        "amount": 90_000,      # 9만원
                        "percentage": 0.18,    # 18%
                        "category": "주식"
                    },
                    "국내_채권": {
                        "amount": 137_500,     # 13.75만원
                        "percentage": 0.275,   # 27.5%
                        "category": "채권"
                    },
                    "해외_채권": {
                        "amount": 55_000,      # 5.5만원
                        "percentage": 0.11,    # 11%
                        "category": "채권"
                    },
                    "리츠": {
                        "amount": 25_000,      # 2.5만원
                        "percentage": 0.05,    # 5%
                        "category": "대체투자"
                    },
                    "금": {
                        "amount": 25_000,      # 2.5만원
                        "percentage": 0.05,    # 5%
                        "category": "대체투자"
                    },
                    "현금": {
                        "amount": 12_500,      # 1.25만원
                        "percentage": 0.025,   # 2.5%
                        "category": "현금"
                    }
                }
            },
            "moderate": {
                "total": 500_000,
                "allocation": {
                    "국내_대형주": {
                        "amount": 100_000,     # 10만원
                        "percentage": 0.20,    # 20%
                        "category": "주식"
                    },
                    "해외_선진국": {
                        "amount": 150_000,     # 15만원
                        "percentage": 0.30,    # 30%
                        "category": "주식"
                    },
                    "국내_채권": {
                        "amount": 70_000,      # 7만원
                        "percentage": 0.14,    # 14%
                        "category": "채권"
                    },
                    "해외_채권": {
                        "amount": 35_000,      # 3.5만원
                        "percentage": 0.07,    # 7%
                        "category": "채권"
                    },
                    "리츠": {
                        "amount": 25_000,      # 2.5만원
                        "percentage": 0.05,    # 5%
                        "category": "대체투자"
                    },
                    "금": {
                        "amount": 25_000,      # 2.5만원
                        "percentage": 0.05,    # 5%
                        "category": "대체투자"
                    },
                    "현금": {
                        "amount": 12_500,      # 1.25만원
                        "percentage": 0.025,   # 2.5%
                        "category": "현금"
                    }
                }
            },
            "aggressive": {
                "total": 500_000,
                "allocation": {
                    "국내_대형주": {
                        "amount": 70_000,      # 7만원
                        "percentage": 0.14,    # 14%
                        "category": "주식"
                    },
                    "국내_중소형주": {
                        "amount": 70_000,      # 7만원
                        "percentage": 0.14,    # 14%
                        "category": "주식"
                    },
                    "해외_선진국": {
                        "amount": 105_000,     # 10.5만원
                        "percentage": 0.21,    # 21%
                        "category": "주식"
                    },
                    "해외_신흥국": {
                        "amount": 105_000,     # 10.5만원
                        "percentage": 0.21,    # 21%
                        "category": "주식"
                    },
                    "국내_채권": {
                        "amount": 37_500,      # 3.75만원
                        "percentage": 0.075,   # 7.5%
                        "category": "채권"
                    },
                    "해외_채권": {
                        "amount": 37_500,      # 3.75만원
                        "percentage": 0.075,   # 7.5%
                        "category": "채권"
                    },
                    "리츠": {
                        "amount": 25_000,      # 2.5만원
                        "percentage": 0.05,    # 5%
                        "category": "대체투자"
                    },
                    "금": {
                        "amount": 25_000,      # 2.5만원
                        "percentage": 0.05,    # 5%
                        "category": "대체투자"
                    },
                    "현금": {
                        "amount": 12_500,      # 1.25만원
                        "percentage": 0.025,   # 2.5%
                        "category": "현금"
                    }
                }
            }
        })

@dataclass(frozen=True)
class RebalancingRules:
    """리밸런싱 규칙"""
    
    rules: Dict = None
    
    def __post_init__(self):
        object.__setattr__(self, "rules", {
            "frequency": {
                "minimum": "연 1회",           # 최소 주기
                "recommended": "분기별 검토",  # 권장
                "execution": "반기별"          # 실행
            },
            
            "threshold": {
                "minor_adjustment": 0.05,      # ±5%p: 검토
                "major_adjustment": 0.10,      # ±10%p: 즉시 조정
                "emergency": 0.15              # ±15%p: 긴급
            },
            
            "method": {
                "new_money": "신규 입금으로 조정 (우선)",
                "sell_buy": "매도-매수 (필요시)",
                "tax_loss_harvest": "손실 실현 우선"
            },
            
            "constraints": {
                "transaction_cost_limit": 0.003,  # 0.3% 이상 비용시 보류
                "min_adjustment_amount": 100_000,  # 최소 10만원 이상
                "avoid_tax_event": True            # 세금 이벤트 최소화
            }
        })

@dataclass(frozen=True)
class InvestmentProducts:
    """투자 상품 정보 (ETF 제외)"""
    
    asset_categories: Dict = None
    
    def __post_init__(self):
        # 자산군별 투자 상품 카테고리 (ETF 상품명 제외)
        object.__setattr__(self, "asset_categories", {
            "국내_주식": {
                "대형주": "삼성전자, SK하이닉스, LG화학 등",
                "중소형주": "성장주, 밸류주, 테마주 등",
                "배당주": "고배당주, 배당성장주 등",
                "특징": "KOSPI, KOSDAQ 상장 종목"
            },
            "해외_주식": {
                "미국_대형주": "S&P500, 나스닥100 구성종목",
                "미국_중소형주": "러셀2000, 중소형 성장주",
                "선진국": "유럽, 일본, 캐나다 등 선진국 주식",
                "신흥국": "중국, 인도, 브라질 등 신흥국 주식",
                "특징": "해외 주식 직접투자 또는 펀드"
            },
            "국내_채권": {
                "국채": "3년, 5년, 10년 국고채",
                "회사채": "AAA, AA, A등급 회사채",
                "특징": "안정성 높은 고정수익 자산"
            },
            "해외_채권": {
                "미국_국채": "10년, 30년 미국 국채",
                "유럽_국채": "독일, 프랑스 등 유럽 국채",
                "특징": "환율 리스크 고려 필요"
            },
            "대체투자": {
                "리츠": "부동산투자신탁(REIT)",
                "금": "금 현물, 금 선물",
                "원자재": "석유, 구리, 농산물 등",
                "특징": "인플레이션 헤지 효과"
            },
            "현금성": {
                "예금": "정기예금, 적금",
                "MMF": "머니마켓펀드",
                "특징": "유동성 최우선, 수익률 낮음"
            }
        })

# ========== 통합 프로필 ==========

class KOR_2025:
    """대한민국 2025년 통합 설정"""
    SWR = SWRRules()
    GUARD = GuardrailsKOR()
    ECON = EconomicScenariosKOR()
    TAX = TaxKOR2025()
    PERF = PerformanceRulesKOR()
    BUCK = BucketRules()
    
    # 한국 특화 클래스들
    PENSION = KoreanPensionAccounts()      # 연금계좌 한도
    NPS = KoreanNationalPension()          # 국민연금
    HOUSING = KoreanHousingPension()       # 주택연금
    KR = KoreanSpecificRules()             # 기존 호환성
    MKT = KoreanMarketCharacteristics()
    REG = RegulatoryCompliance()
    
    # === 적립메이트용 ===
    ACCUM_ALLOC = AccumulationAssetAllocation()   # 적립기 자산배분
    ACCOUNT_RULES = AccountAllocationRules()      # 계좌 배분 규칙
    EXPECTED_RET = ExpectedReturns()              # 기대수익률
    
    # === 투자메이트용 ===
    RISK_ALLOC = RiskBasedAllocation()            # 위험성향별 배분
    INV_WEIGHTS = InvestmentWeights()             # 구체적 투자 비중
    REBAL = RebalancingRules()                    # 리밸런싱 규칙
    PRODUCTS = InvestmentProducts()               # ETF 상품 DB

# ========== 유틸리티 함수 ==========

def marginal_rate_from_brackets(amount: float, brackets: Tuple) -> float:
    """세율 구간에서 한계세율 계산"""
    for cap, rate in brackets:
        if amount <= cap:
            return rate
    return brackets[-1][1]

def get_healthcare_factor(age: int) -> float:
    """연령별 의료비 가중치"""
    for (min_age, max_age), factor in KOR_2025.BUCK.healthcare_age_factor.items():
        if min_age <= age < max_age:
            return factor
    return 2.5  # 85세 이상
