from datetime import datetime
from enum import Enum
import json
from typing import Sequence
import numpy as np
import sys
import os

# 중앙 설정 모듈 import
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
from financial_constants_2025 import KOR_2025 # type: ignore

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.shared.exceptions import McpError

from pydantic import BaseModel

# __pycache__ 폴더 생성 방지
sys.dont_write_bytecode = True

class ToojaTools(str, Enum):
    ASSESS_RISK_PROFILE = "assess_risk_profile"
    GENERATE_PORTFOLIOS = "generate_three_tier_portfolios"
    ADJUST_VOLATILITY = "adjust_portfolio_volatility"
    BUILD_IMPLEMENTATION = "build_implementation_roadmap"
    CALCULATE_ACCOUNT_ALLOCATION = "calculate_monthly_account_allocation"
    MONITOR_PERFORMANCE = "monitor_portfolio_performance"
    CALCULATE_RETIREMENT_ACHIEVEMENT = "calculate_retirement_achievement"
    COMPARE_TAX_EFFICIENCY = "compare_tax_efficiency_across_accounts"


# ========== 데이터 모델 ==========

class RiskProfile(BaseModel):
    risk_level: str
    max_equity_ratio: float
    use_tax_advantaged: bool
    special_assets_preference: list


class Portfolio(BaseModel):
    portfolio_type: str
    asset_allocation: dict
    expected_return: float
    expected_volatility: float


class VolatilityAdjustment(BaseModel):
    original_allocation: dict
    adjusted_allocation: dict
    volatility_regime: str
    adjustment_reason: str


class ImplementationPlan(BaseModel):
    account_strategy: dict
    execution_steps: list
    rebalancing_rules: dict


class AccountAllocation(BaseModel):
    monthly_investment: float
    irp_monthly: float
    isa_monthly: float
    general_monthly: float
    isa_accumulated: float
    isa_limit_reached: bool


# ========== 투자메이트 서비스 로직 (토큰 절약형) ==========

class ToojaService:

    # 계좌 한도 상수
    IRP_ANNUAL_LIMIT = 18_000_000  # 연 1,800만원
    IRP_MONTHLY_OPTIMAL = 1_500_000  # 월 150만원
    ISA_ANNUAL_LIMIT = 20_000_000  # 연 2,000만원
    ISA_MONTHLY_OPTIMAL = 1_666_667  # 월 약 166.67만원
    ISA_TOTAL_LIMIT = 100_000_000  # 총 1억원

    def __init__(self):
        self.user_risk_profile = {}
        self.base_portfolios = {}
        self.isa_accumulated = 0  # ISA 누적 입금액 추적

    def assess_risk_profile(self, demographic_info: dict, financial_capacity: dict,
                            liquidity_requirements: dict, behavioral_preferences: dict) -> dict:
        """투자성향 분석 (간소화)"""

        age = demographic_info.get('age', 40)
        retirement_age = demographic_info.get('retirement_age', 65)
        years_to_retirement = retirement_age - age
        risk_score = behavioral_preferences.get('risk_tolerance_score', 50)

        # 위험성향 분류
        if risk_score < 40:
            risk_level = 'conservative'
        elif risk_score < 70:
            risk_level = 'moderate'
        else:
            risk_level = 'aggressive'

        # 주식 상한
        max_equity = min(70, (100 - age))
        phase = self._determine_life_phase(age, years_to_retirement)
        age_based_equity = self._lifecycle_equity_allocation(age, phase, max_equity)

        self.user_risk_profile = {
            'risk_level': risk_level,
            'max_equity_ratio': round(age_based_equity, 2),
            'years_to_retirement': years_to_retirement,
            'life_phase': phase,
            'use_irp': behavioral_preferences.get('use_irp', True),
            'use_pension_savings': behavioral_preferences.get('use_pension_savings', True)
        }

        return {
            'risk_level': risk_level,
            'max_equity_ratio': round(age_based_equity * 100, 1),
            'life_phase': phase,
            'recommendation': f'{risk_level} 포트폴리오 권장'
        }


    def _determine_life_phase(self, age: int, years_to_retirement: int) -> str:
        """생애주기 단계"""
        if years_to_retirement > 15:
            return "accumulation"
        elif years_to_retirement > 5:
            return "transition"
        else:
            return "retirement"

    def _lifecycle_equity_allocation(self, age: int, phase: str, max_equity: float) -> float:
        """생애주기별 주식 배분"""
        if phase == "accumulation":
            base_eq = min(0.90, (130 - age) / 100)
        elif phase == "transition":
            base_eq = min(0.70, (120 - age) / 100)
        else:
            base_eq = min(0.60, (110 - age) / 100)
        
        return max(0.20, min(max_equity, base_eq))

    def generate_three_tier_portfolios(self, risk_constraints: dict) -> dict:
        """포트폴리오 3가지 생성 (간소화)"""

        portfolios = {}
        
        for portfolio_type in ['conservative', 'moderate', 'aggressive']:
            allocation = self._lifecycle_allocation_kor(
                risk_constraints.get('age', 40), 
                portfolio_type, 
                risk_constraints.get('life_phase', 'accumulation'), 
                risk_constraints.get('risk_score', 50)
            )
            
            portfolios[portfolio_type] = {
                'portfolio_name': f'{portfolio_type.title()}형',
                'asset_allocation': allocation,
                'expected_annual_return': self._expected_return_kor(portfolio_type),
                'expected_volatility': self._expected_volatility_kor(portfolio_type)
            }

        self.base_portfolios = portfolios

        return {
            'portfolios': portfolios,
            'recommendation': 'moderate'
        }

    def _lifecycle_allocation_kor(self, age: int, risk_level: str, phase: str, risk_score: int) -> dict:
        """자산 배분"""
        max_equity = min(70, (100 - age))
        
        if risk_level == 'conservative':
            return {'채권': 55, '주식': min(20, max_equity), '금': 10, '현금': 10, '대체투자': 5}
        elif risk_level == 'moderate':
            return {'채권': 40, '주식': min(35, max_equity), '금': 10, '현금': 10, '대체투자': 5}
        else:  # aggressive
            return {'채권': 30, '주식': min(50, max_equity), '금': 10, '현금': 5, '대체투자': 5}

    def _expected_return_kor(self, portfolio_type: str) -> float:
        """기대수익률"""
        returns = {'conservative': 4.5, 'moderate': 6.0, 'aggressive': 7.5}
        return returns[portfolio_type]

    def _expected_volatility_kor(self, portfolio_type: str) -> float:
        """기대변동성"""
        volatilities = {'conservative': 8.0, 'moderate': 12.0, 'aggressive': 16.0}
        return volatilities[portfolio_type]

    def calculate_monthly_account_allocation(self, monthly_investment: float,
                                             isa_accumulated: float = 0) -> dict:
        """월 투자금액 기반 계좌별 배분 계산"""

        self.isa_accumulated = isa_accumulated
        isa_limit_reached = self.isa_accumulated >= self.ISA_TOTAL_LIMIT

        # 1순위: IRP 계좌 (월 150만원)
        irp_monthly = min(monthly_investment, self.IRP_MONTHLY_OPTIMAL)
        remaining = monthly_investment - irp_monthly

        # 2순위: ISA 계좌 (월 166만원, 단 총 1억 한도)
        if not isa_limit_reached and remaining > 0:
            isa_available_space = max(0, self.ISA_TOTAL_LIMIT - self.isa_accumulated)
            isa_monthly = min(remaining, self.ISA_MONTHLY_OPTIMAL, isa_available_space)
        else:
            isa_monthly = 0

        # 3순위: 일반계좌 (나머지)
        general_monthly = remaining - isa_monthly

        return {
            'monthly_investment': monthly_investment,
            'account_allocation': {
                'IRP': {
                    'monthly_amount': irp_monthly,
                    'annual_limit': self.IRP_ANNUAL_LIMIT,
                    'reason': '세액공제(13.2~16.5%) + 과세이연 혜택 극대화'
                },
                'ISA': {
                    'monthly_amount': isa_monthly,
                    'annual_limit': self.ISA_ANNUAL_LIMIT,
                    'total_limit': self.ISA_TOTAL_LIMIT,
                    'accumulated': self.isa_accumulated,
                    'limit_reached': isa_limit_reached,
                    'reason': '손익통산 + 비과세(200/400만원) + 9.9% 저율과세'
                },
                'general': {
                    'monthly_amount': general_monthly,
                    'reason': '1, 2순위 한도 초과분 또는 ISA 1억 달성 후 투자'
                }
            },
            'summary': {
                'irp_monthly': irp_monthly,
                'isa_monthly': isa_monthly,
                'general_monthly': general_monthly,
                'total': monthly_investment
            },
            'warnings': self._generate_account_warnings(monthly_investment, irp_monthly, isa_monthly, isa_limit_reached)
        }

    def _generate_account_warnings(self, monthly_investment: float, irp_monthly: float,
                                   isa_monthly: float, isa_limit_reached: bool) -> list:
        """계좌 배분 경고 메시지 생성"""
        warnings = []

        if monthly_investment < self.IRP_MONTHLY_OPTIMAL:
            warnings.append('월 투자금액이 IRP 최적 금액(150만원)보다 적습니다. IRP 한도를 최대한 활용하면 절세 효과가 더 큽니다.')

        if isa_limit_reached:
            warnings.append('ISA 계좌가 총 한도(1억원)에 도달했습니다. ISA 입금이 중단되고 일반계좌로 전환됩니다.')

        return warnings

    def adjust_portfolio_volatility(self, base_portfolio: dict,
                                    market_volatility_data: dict) -> dict:
        """변동성 조정 (간소화)"""

        current_volatility = market_volatility_data.get(
            'current_volatility', KOR_2025.MKT.kospi_volatility * 100)
        historical_avg = market_volatility_data.get('historical_average', KOR_2025.MKT.kospi_volatility * 100)
        volatility_ratio = current_volatility / historical_avg

        allocation = base_portfolio.get('asset_allocation', {}).copy()

        if volatility_ratio > 1.2:
            regime = 'high_volatility'
            allocation['주식'] = max(10, allocation.get('주식', 0) - 10)
            allocation['채권'] = min(60, allocation.get('채권', 0) + 5)
            allocation['금'] = min(20, allocation.get('금', 0) + 5)
        elif volatility_ratio < 0.8:
            regime = 'low_volatility'
            allocation['주식'] = min(80, allocation.get('주식', 0) + 5)
            allocation['채권'] = max(20, allocation.get('채권', 0) - 3)
        else:
            regime = 'normal_volatility'

        return {
            'volatility_regime': regime,
            'volatility_ratio': round(volatility_ratio, 2),
            'adjusted_allocation': allocation
        }

    def build_implementation_roadmap(self, optimized_portfolio: dict,
                                     current_holdings: dict,
                                     account_info: dict) -> dict:
        """실행 계획 - 절세 최적화 버전"""

        asset_allocation = optimized_portfolio.get('asset_allocation', {})
        monthly_investment = account_info.get('monthly_investment', 0)

        # 계좌별 배분 계산
        account_allocation = None
        if monthly_investment > 0:
            isa_accumulated = account_info.get('isa_accumulated', 0)
            account_allocation = self.calculate_monthly_account_allocation(
                monthly_investment, isa_accumulated
            )

        # 자산별 계좌 배치 전략
        asset_placement_strategy = self._generate_asset_placement_strategy(asset_allocation)

        # 실행 단계
        execution_steps = self._generate_execution_steps(
            asset_allocation,
            account_info,
            monthly_investment
        )

        # 주의사항 및 경고
        warnings = self._generate_implementation_warnings()

        return {
            'account_allocation': account_allocation,
            'asset_placement_strategy': asset_placement_strategy,
            'execution_steps': execution_steps,
            'warnings': warnings,
            'rebalancing_rules': {
                'frequency': '연 1회',
                'timing': '매년 12월 또는 시장 급변동 시',
                'threshold': '목표 비중 대비 ±5% 이상 이탈 시'
            }
        }

    def _generate_asset_placement_strategy(self, asset_allocation: dict) -> dict:
        """자산별 계좌 배치 전략 생성"""

        strategy = {
            '주식': {
                'priority_order': ['IRP/연금저축', 'ISA', '일반계좌'],
                'account_details': {
                    '1순위_IRP연금저축': {
                        'products': ['해외주식 ETF (S&P 500, NASDAQ 100 등)'],
                        'reason': '양도소득세 22% + 배당소득세 15.4%가 모두 이연. 나중에 3.3~5.5% 연금소득세로 대체',
                        'tax_saving': '약 18~30% 절세'
                    },
                    '2순위_ISA': {
                        'products': ['고배당주 ETF', '해외주식 ETF'],
                        'reason': '배당소득 9.9% 저율과세 + 손익통산 가능',
                        'tax_saving': '배당소득세 15.4% → 9.9%'
                    },
                    '3순위_일반계좌': {
                        'products': ['국내 상장주식 (삼성전자, KOSPI 200 ETF 등)'],
                        'reason': '매매차익이 원래 비과세(0%)이므로 일반계좌 사용',
                        'warning': '⚠️ 절대 주의: 국내 상장주식을 IRP/연금계좌에 넣지 마세요! 비과세 혜택이 사라집니다.'
                    }
                }
            },
            '채권': {
                'priority_order': ['IRP/연금저축', 'ISA', '일반계좌'],
                'account_details': {
                    '1순위_IRP연금저축': {
                        'products': ['채권형 ETF', '채권형 펀드 (국내/해외)'],
                        'reason': '이자소득세 15.4%가 이연되어 재투자. 복리 효과 극대화',
                        'tax_saving': '약 15.4% → 3.3~5.5%'
                    },
                    '2순위_ISA': {
                        'products': ['채권형 ETF', '개별 채권'],
                        'reason': '이자소득 9.9% 저율과세 + 손익통산',
                        'tax_saving': '15.4% → 9.9%'
                    },
                    '3순위_일반계좌': {
                        'products': ['비과세 채권 (물가연동국채)', '개별 채권'],
                        'reason': '1, 2순위 한도 초과 시 사용',
                        'warning': '⚠️ 이자소득 연 2,000만원 초과 시 금융소득종합과세 대상'
                    }
                }
            },
            '금': {
                'priority_order': ['IRP/연금저축', 'ISA', '일반계좌 (KRX 금현물)'],
                'account_details': {
                    '1순위_IRP연금저축': {
                        'products': ['금(Gold) ETF'],
                        'reason': '국내 상장 금 ETF 수익은 배당소득(15.4%). 이를 이연시켜 복리 투자',
                        'tax_saving': '15.4% → 3.3~5.5%'
                    },
                    '2순위_ISA': {
                        'products': ['금(Gold) ETF'],
                        'reason': '배당소득 9.9% 저율과세 + 손익통산',
                        'tax_saving': '15.4% → 9.9%'
                    },
                    '3순위_일반계좌': {
                        'products': ['KRX 금 현물 (한국거래소 금시장)'],
                        'reason': 'KRX 금 현물 매매차익은 비과세(0%)',
                        'warning': '⚠️ 일반계좌에서는 금 ETF 대신 KRX 금 현물 권장'
                    }
                }
            },
            '대체투자': {
                'priority_order': ['IRP/연금저축', 'ISA', '일반계좌'],
                'account_details': {
                    '1순위_IRP연금저축': {
                        'products': ['리츠(REITs) ETF/펀드'],
                        'reason': '리츠의 높은 배당소득(15.4%)을 이연시켜 재투자. 복리 효과 최대',
                        'tax_saving': '15.4% → 3.3~5.5%'
                    },
                    '2순위_ISA': {
                        'products': ['리츠(REITs) ETF/펀드'],
                        'reason': '높은 배당소득을 9.9% 저율과세로 감면',
                        'tax_saving': '15.4% → 9.9%'
                    },
                    '3순위_일반계좌': {
                        'products': ['상장 리츠 ETF'],
                        'reason': '1, 2순위 한도 초과 시 사용',
                        'warning': '⚠️ 배당이 많으므로 금융소득종합과세 2,000만원 한도 유의'
                    }
                }
            }
        }

        return strategy

    def _generate_execution_steps(self, asset_allocation: dict,
                                   account_info: dict,
                                   monthly_investment: float) -> list:
        """실행 단계 가이드 생성"""

        steps = []
        current_step = 1

        if monthly_investment > 0:
            steps.append({
                'step': current_step,
                'title': '월 투자금액 계좌별 배분',
                'description': f'월 {monthly_investment:,.0f}원을 절세 계좌 우선순위에 따라 배분',
                'action': '위의 account_allocation 결과 참고'
            })
            current_step += 1

        steps.extend([
            {
                'step': current_step,
                'title': 'IRP/연금저축 계좌 우선 투자',
                'description': '세금이 많이 발생하는 상품을 최우선 배치',
                'action': '해외주식 ETF → 채권형 ETF → 리츠 ETF 순서로 투자'
            },
            {
                'step': current_step + 1,
                'title': 'ISA 계좌 투자',
                'description': 'IRP 한도 초과분을 ISA에 투자 (총 1억 한도까지)',
                'action': '고배당주 → 채권 → 금 ETF 순서로 투자'
            },
            {
                'step': current_step + 2,
                'title': '일반계좌 투자',
                'description': '세금이 원래 적거나 없는 상품 위주',
                'action': '국내 상장주식 → KRX 금 현물 → 비과세 채권 순서로 투자'
            },
            {
                'step': current_step + 3,
                'title': '연 1회 리밸런싱',
                'description': '목표 자산배분 비율 유지',
                'action': '매년 12월 또는 목표 비중 대비 ±5% 이상 이탈 시 실행'
            }
        ])

        return steps

    def _generate_implementation_warnings(self) -> list:
        """실행 시 주의사항"""

        return [
            {
                'category': '절세 함정 주의',
                'warnings': [
                    '❌ 국내 상장주식을 IRP/연금계좌에 넣지 마세요 (비과세 혜택 상실)',
                    '❌ 세금이 적은 상품(국내주식)을 세금 혜택 계좌에 넣어 한도 낭비하지 마세요',
                    '✅ 세금이 많은 상품(해외ETF, 채권, 리츠)을 절세 계좌에 우선 배치하세요'
                ]
            },
            {
                'category': '계좌 한도 관리',
                'warnings': [
                    'IRP 연 1,800만원 한도 (월 150만원 권장)',
                    'ISA 연 2,000만원 한도, 총 1억원 한도 (월 166만원 권장)',
                    'ISA 1억 달성 시 일반계좌로 자동 전환'
                ]
            },
            {
                'category': '금융소득종합과세 주의',
                'warnings': [
                    '일반계좌의 이자+배당 소득이 연 2,000만원 초과 시 종합과세 대상',
                    '고배당 상품(리츠, 배당주)은 가급적 IRP/ISA에 배치 권장',
                    '초과 시 세율이 6.6%~49.5%까지 급증할 수 있음'
                ]
            }
        ]

    def monitor_portfolio_performance(self, portfolio_returns: dict,
                                      benchmark_returns: dict,
                                      time_period: str) -> dict:
        """성과 분석 (간소화)"""

        portfolio_return = portfolio_returns.get('total_return', 0.0)
        portfolio_volatility = portfolio_returns.get('volatility', 0.0)
        benchmark_return = benchmark_returns.get('total_return', 0.0)

        risk_free_rate = KOR_2025.PERF.risk_free_rate
        if portfolio_volatility > 0:
            sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility
        else:
            sharpe_ratio = 0

        excess_return = portfolio_return - benchmark_return

        # 최대낙폭 계산
        returns_list = portfolio_returns.get('monthly_returns', [])
        if returns_list:
            cumulative = np.cumprod([1 + r for r in returns_list])
            running_max = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = np.min(drawdown) * 100
        else:
            max_drawdown = 0

        return {
            'period': time_period,
            'portfolio_return': round(portfolio_return * 100, 2),
            'benchmark_return': round(benchmark_return * 100, 2),
            'excess_return': round(excess_return * 100, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'max_drawdown': round(max_drawdown, 2)
        }

    def calculate_retirement_achievement(self, current_age: int, retirement_age: int,
                                        current_assets: float, required_retirement_assets: float,
                                        monthly_investment: float = 0) -> dict:
        """은퇴 목표 달성 여부 및 투자 전략 계산"""

        years_to_retirement = retirement_age - current_age

        if years_to_retirement <= 0:
            return {
                'error': '현재 나이가 목표 은퇴 나이보다 크거나 같습니다.'
            }

        # 목표: 필요 은퇴자산의 110%
        target_assets = required_retirement_assets * 1.1

        # 위험성향에 따른 예상 수익률 (연간)
        expected_returns = {
            'conservative': 0.045,  # 4.5%
            'moderate': 0.06,       # 6.0%
            'aggressive': 0.075     # 7.5%
        }

        # 각 시나리오별로 미래 자산 계산
        scenarios = {}
        for risk_level, annual_return in expected_returns.items():
            # 현재 자산의 미래 가치 계산
            future_value_current = current_assets * ((1 + annual_return) ** years_to_retirement)

            # 월 투자금의 미래 가치 계산 (연금의 미래가치 공식)
            if monthly_investment > 0:
                monthly_rate = annual_return / 12
                months = years_to_retirement * 12
                future_value_monthly = monthly_investment * (((1 + monthly_rate) ** months - 1) / monthly_rate)
            else:
                future_value_monthly = 0

            total_future_value = future_value_current + future_value_monthly

            # 목표 달성률 계산
            achievement_rate = (total_future_value / target_assets) * 100

            scenarios[risk_level] = {
                'expected_annual_return': round(annual_return * 100, 1),
                'future_value_current_assets': round(future_value_current),
                'future_value_monthly_investment': round(future_value_monthly),
                'total_expected_assets': round(total_future_value),
                'target_assets': round(target_assets),
                'achievement_rate': round(achievement_rate, 1),
                'achieves_110_target': achievement_rate >= 100
            }

        # 110% 목표 달성 가능한 최소 위험 포트폴리오 찾기
        recommended_strategy = None
        for risk_level in ['conservative', 'moderate', 'aggressive']:
            if scenarios[risk_level]['achieves_110_target']:
                recommended_strategy = risk_level
                break

        # 목표 달성을 위해 필요한 추가 월 투자액 계산 (moderate 기준)
        required_additional_monthly = 0
        if not scenarios['moderate']['achieves_110_target']:
            moderate_return = expected_returns['moderate']
            monthly_rate = moderate_return / 12
            months = years_to_retirement * 12
            future_value_current = current_assets * ((1 + moderate_return) ** years_to_retirement)

            # 필요한 추가 자산
            needed_from_monthly = target_assets - future_value_current

            if needed_from_monthly > 0:
                # 연금의 미래가치 공식을 역으로 계산
                required_additional_monthly = needed_from_monthly * monthly_rate / (((1 + monthly_rate) ** months - 1))

        return {
            'financial_status': {
                'current_age': current_age,
                'retirement_age': retirement_age,
                'years_to_retirement': years_to_retirement,
                'current_assets': current_assets,
                'monthly_investment': monthly_investment,
                'required_retirement_assets': required_retirement_assets,
                'target_assets_110': round(target_assets)
            },
            'scenarios': scenarios,
            'recommendation': {
                'recommended_strategy': recommended_strategy if recommended_strategy else 'aggressive',
                'message': self._generate_achievement_message(
                    scenarios,
                    recommended_strategy,
                    current_age,
                    retirement_age,
                    current_assets,
                    target_assets,
                    required_additional_monthly
                )
            }
        }

    def _generate_achievement_message(self, scenarios: dict, recommended_strategy: str,
                                     current_age: int, retirement_age: int,
                                     current_assets: float, target_assets: float,
                                     required_additional_monthly: float) -> str:
        """목표 달성 메시지 생성"""

        if recommended_strategy:
            scenario = scenarios[recommended_strategy]
            return f"""
재무 현황

현재 나이: {current_age}세 → 목표 은퇴 나이: {retirement_age}세 ({retirement_age - current_age}년 남음)

현재 투자자산: {current_assets:,.0f}원

{retirement_age}세 예상 자산: {scenario['total_expected_assets']:,.0f}원

필요 은퇴자산: {target_assets:,.0f}원 (목표 대비 110%)

결론: 목표 대비 110% 달성 예정!

권장 전략: {recommended_strategy.title()}형 포트폴리오 (연 {scenario['expected_annual_return']}% 수익률)
- 목표 달성률: {scenario['achievement_rate']}%
"""
        else:
            # 모든 시나리오가 목표 미달성
            aggressive = scenarios['aggressive']
            moderate = scenarios['moderate']

            additional_msg = ""
            if required_additional_monthly > 0:
                additional_msg = f"\n또는, 현재 투자금액 유지 시 월 {required_additional_monthly:,.0f}원 추가 투자 필요 (Moderate 기준)"

            return f"""
재무 현황

현재 나이: {current_age}세 → 목표 은퇴 나이: {retirement_age}세 ({retirement_age - current_age}년 남음)

현재 투자자산: {current_assets:,.0f}원

{retirement_age}세 예상 자산 (Aggressive): {aggressive['total_expected_assets']:,.0f}원

필요 은퇴자산: {target_assets:,.0f}원 (목표 대비 110%)

결론: 현재 계획으로는 목표 달성 어려움

권장 조치:
1. Aggressive형 포트폴리오 채택 (연 {aggressive['expected_annual_return']}% 수익률)
   - 현재 달성률: {aggressive['achievement_rate']}%
   - 부족 금액: {target_assets - aggressive['total_expected_assets']:,.0f}원{additional_msg}

2. 은퇴 시기를 조정하거나 필요 자산을 재검토하세요.
"""

    def compare_tax_efficiency_across_accounts(self, investment_period_years: int,
                                                monthly_investment: float,
                                                asset_allocation: dict,
                                                expected_returns: dict = None) -> dict:
        """일반계좌 vs 절세계좌(ISA, IRP) 세금 비교 시뮬레이션

        Args:
            investment_period_years: 투자 기간 (년)
            monthly_investment: 월 투자 금액
            asset_allocation: 자산 배분 비율 {'주식': 40, '채권': 30, '금': 10, '리츠': 10, '현금': 10}
            expected_returns: 자산별 예상 수익률 (선택, 기본값 사용 가능)

        Returns:
            계좌별 세금 비교 결과
        """

        # 기본 예상 수익률 (연간)
        if expected_returns is None:
            expected_returns = {
                '주식': 0.08,      # 국내 주식 8%
                '해외주식': 0.10,  # 해외 주식 10%
                '채권': 0.04,      # 채권 4%
                '금': 0.05,        # 금 5%
                '리츠': 0.07,      # 리츠 7%
                '현금': 0.02       # 현금 2%
            }

        # 총 투자금액
        total_investment = monthly_investment * 12 * investment_period_years

        # 자산별 투자액 계산
        asset_investments = {}
        for asset, allocation_pct in asset_allocation.items():
            asset_investments[asset] = total_investment * (allocation_pct / 100)

        # 각 계좌별 시뮬레이션
        general_account_result = self._simulate_general_account(
            asset_investments, expected_returns, investment_period_years, monthly_investment
        )

        isa_account_result = self._simulate_isa_account(
            asset_investments, expected_returns, investment_period_years, monthly_investment
        )

        irp_account_result = self._simulate_irp_account(
            asset_investments, expected_returns, investment_period_years, monthly_investment
        )

        # 절세 효과 계산
        tax_savings_vs_general = {
            'ISA_vs_일반계좌': {
                '세금_절감액': round(general_account_result['total_tax'] - isa_account_result['total_tax'], 0),
                '절감률': round((general_account_result['total_tax'] - isa_account_result['total_tax']) / general_account_result['total_tax'] * 100, 1) if general_account_result['total_tax'] > 0 else 0
            },
            'IRP_vs_일반계좌': {
                '세금_절감액': round(general_account_result['total_tax'] - irp_account_result['total_tax'], 0),
                '절감률': round((general_account_result['total_tax'] - irp_account_result['total_tax']) / general_account_result['total_tax'] * 100, 1) if general_account_result['total_tax'] > 0 else 0,
                '세액공제_추가혜택': round(irp_account_result['tax_deduction_benefit'], 0)
            }
        }

        return {
            'investment_summary': {
                '투자기간': f'{investment_period_years}년',
                '월_투자액': round(monthly_investment, 0),
                '총_투자원금': round(total_investment, 0),
                '자산배분': asset_allocation
            },
            'account_comparison': {
                '일반계좌': general_account_result,
                'ISA': isa_account_result,
                'IRP_연금저축': irp_account_result
            },
            'tax_savings_analysis': tax_savings_vs_general,
            'recommendations': self._generate_tax_efficiency_recommendations(
                tax_savings_vs_general,
                general_account_result,
                isa_account_result,
                irp_account_result,
                monthly_investment
            )
        }

    def _simulate_general_account(self, asset_investments: dict, expected_returns: dict,
                                   years: int, monthly_investment: float) -> dict:
        """일반계좌 세금 시뮬레이션"""

        total_value = 0
        total_tax = 0
        asset_details = {}

        for asset, investment_amount in asset_investments.items():
            asset_return_rate = expected_returns.get(asset, expected_returns.get('주식', 0.08))

            # 월 복리 계산
            monthly_rate = asset_return_rate / 12
            months = years * 12
            monthly_amount = investment_amount / months

            # 미래가치 계산 (연금의 미래가치)
            future_value = monthly_amount * (((1 + monthly_rate) ** months - 1) / monthly_rate)
            total_return = future_value - investment_amount

            # 자산별 세금 계산
            tax = self._calculate_general_account_tax(asset, total_return, investment_amount, years)

            asset_details[asset] = {
                '투자원금': round(investment_amount, 0),
                '최종가치': round(future_value, 0),
                '수익': round(total_return, 0),
                '세금': round(tax, 0),
                '세후가치': round(future_value - tax, 0)
            }

            total_value += future_value
            total_tax += tax

        return {
            'total_investment': round(sum(asset_investments.values()), 0),
            'total_value_before_tax': round(total_value, 0),
            'total_tax': round(total_tax, 0),
            'total_value_after_tax': round(total_value - total_tax, 0),
            'effective_tax_rate': round(total_tax / (total_value - sum(asset_investments.values())) * 100, 2) if (total_value - sum(asset_investments.values())) > 0 else 0,
            'asset_breakdown': asset_details
        }

    def _calculate_general_account_tax(self, asset: str, total_return: float,
                                        investment_amount: float, years: int) -> float:
        """일반계좌 자산별 세금 계산"""

        if asset == '주식':
            # 국내 상장주식: 매매차익 비과세
            return 0

        elif asset == '해외주식':
            # 해외주식: 양도소득세 22% (250만원 기본공제)
            capital_gain = total_return
            taxable_gain = max(0, capital_gain - 2500000)
            return taxable_gain * 0.22

        elif asset == '채권':
            # 채권: 이자소득세 15.4%
            # 매년 이자 발생하므로 연간 수익 추정
            annual_return = total_return / years
            annual_tax = annual_return * 0.154
            return annual_tax * years

        elif asset == '금':
            # 금 ETF: 배당소득세 15.4%
            # KRX 금 현물은 비과세이지만 여기서는 ETF로 가정
            return total_return * 0.154

        elif asset == '리츠':
            # 리츠: 배당소득세 15.4%
            return total_return * 0.154

        elif asset == '현금':
            # 현금: 이자소득세 15.4%
            return total_return * 0.154

        else:
            # 기타: 15.4% 적용
            return total_return * 0.154

    def _simulate_isa_account(self, asset_investments: dict, expected_returns: dict,
                               years: int, monthly_investment: float) -> dict:
        """ISA 계좌 세금 시뮬레이션"""

        total_value = 0
        total_tax = 0
        asset_details = {}

        total_return_all_assets = 0

        for asset, investment_amount in asset_investments.items():
            asset_return_rate = expected_returns.get(asset, expected_returns.get('주식', 0.08))

            # 월 복리 계산
            monthly_rate = asset_return_rate / 12
            months = years * 12
            monthly_amount = investment_amount / months

            future_value = monthly_amount * (((1 + monthly_rate) ** months - 1) / monthly_rate)
            total_return = future_value - investment_amount
            total_return_all_assets += total_return

            total_value += future_value

        # ISA 세금: 비과세 한도 200만원(일반형) / 400만원(서민형), 초과분 9.9%
        # 여기서는 일반형으로 가정
        tax_free_limit = 2000000
        taxable_return = max(0, total_return_all_assets - tax_free_limit)
        total_tax = taxable_return * 0.099

        # 자산별 상세 (비례 배분)
        for asset, investment_amount in asset_investments.items():
            asset_return_rate = expected_returns.get(asset, expected_returns.get('주식', 0.08))

            monthly_rate = asset_return_rate / 12
            months = years * 12
            monthly_amount = investment_amount / months

            future_value = monthly_amount * (((1 + monthly_rate) ** months - 1) / monthly_rate)
            total_return = future_value - investment_amount

            # 세금은 전체 수익에서 비례 배분
            asset_tax = total_tax * (total_return / total_return_all_assets) if total_return_all_assets > 0 else 0

            asset_details[asset] = {
                '투자원금': round(investment_amount, 0),
                '최종가치': round(future_value, 0),
                '수익': round(total_return, 0),
                '세금': round(asset_tax, 0),
                '세후가치': round(future_value - asset_tax, 0)
            }

        return {
            'total_investment': round(sum(asset_investments.values()), 0),
            'total_value_before_tax': round(total_value, 0),
            'total_return': round(total_return_all_assets, 0),
            'tax_free_amount': round(min(total_return_all_assets, tax_free_limit), 0),
            'taxable_amount': round(taxable_return, 0),
            'total_tax': round(total_tax, 0),
            'total_value_after_tax': round(total_value - total_tax, 0),
            'effective_tax_rate': round(total_tax / total_return_all_assets * 100, 2) if total_return_all_assets > 0 else 0,
            'asset_breakdown': asset_details,
            'note': 'ISA 비과세 한도 200만원(일반형) 적용, 초과분 9.9% 저율과세'
        }

    def _simulate_irp_account(self, asset_investments: dict, expected_returns: dict,
                               years: int, monthly_investment: float) -> dict:
        """IRP/연금저축 계좌 세금 시뮬레이션"""

        total_value = 0
        total_tax = 0
        asset_details = {}

        total_return_all_assets = 0

        for asset, investment_amount in asset_investments.items():
            asset_return_rate = expected_returns.get(asset, expected_returns.get('주식', 0.08))

            # 월 복리 계산 (과세 이연으로 복리 효과 극대화)
            monthly_rate = asset_return_rate / 12
            months = years * 12
            monthly_amount = investment_amount / months

            future_value = monthly_amount * (((1 + monthly_rate) ** months - 1) / monthly_rate)
            total_return = future_value - investment_amount
            total_return_all_assets += total_return

            total_value += future_value

        # IRP/연금저축 세금: 나중에 인출 시 연금소득세 5.5% (평균)
        # 현재는 과세 이연 효과만 계산
        # 실제 인출 시 세금은 연금소득세로 부과
        pension_tax_rate = 0.055  # 연금소득세 평균 5.5% (3.3~5.5%)
        total_tax = total_value * pension_tax_rate

        # 세액공제 혜택 계산 (연간 납입액의 13.2~16.5%)
        annual_investment = monthly_investment * 12
        # 최대 세액공제 대상: 연 900만원 (총급여 5,500만원 이하), 연 700만원 (초과)
        # 여기서는 700만원 기준, 16.5% 세액공제율 적용
        deductible_per_year = min(annual_investment, 7000000)
        tax_deduction_benefit = deductible_per_year * 0.165 * years  # 전체 기간 세액공제

        # 자산별 상세
        for asset, investment_amount in asset_investments.items():
            asset_return_rate = expected_returns.get(asset, expected_returns.get('주식', 0.08))

            monthly_rate = asset_return_rate / 12
            months = years * 12
            monthly_amount = investment_amount / months

            future_value = monthly_amount * (((1 + monthly_rate) ** months - 1) / monthly_rate)
            total_return = future_value - investment_amount

            # 세금은 전체 가치에서 비례 배분
            asset_tax = total_tax * (future_value / total_value) if total_value > 0 else 0

            asset_details[asset] = {
                '투자원금': round(investment_amount, 0),
                '최종가치': round(future_value, 0),
                '수익': round(total_return, 0),
                '연금소득세': round(asset_tax, 0),
                '세후가치': round(future_value - asset_tax, 0)
            }

        return {
            'total_investment': round(sum(asset_investments.values()), 0),
            'total_value_before_tax': round(total_value, 0),
            'total_return': round(total_return_all_assets, 0),
            'pension_income_tax': round(total_tax, 0),
            'total_value_after_tax': round(total_value - total_tax, 0),
            'effective_tax_rate': round(total_tax / total_value * 100, 2) if total_value > 0 else 0,
            'tax_deduction_benefit': round(tax_deduction_benefit, 0),
            'net_benefit_after_deduction': round(total_value - total_tax + tax_deduction_benefit - sum(asset_investments.values()), 0),
            'asset_breakdown': asset_details,
            'note': f'과세 이연 효과로 복리 극대화. 인출 시 연금소득세 {pension_tax_rate*100}% 적용. 세액공제 {years}년간 총 {round(tax_deduction_benefit, 0):,}원'
        }

    def _generate_tax_efficiency_recommendations(self, tax_savings: dict,
                                                  general: dict, isa: dict, irp: dict,
                                                  monthly_investment: float) -> list:
        """세금 효율성 권장사항 생성"""

        recommendations = []

        # 절세 효과 분석
        isa_savings = tax_savings['ISA_vs_일반계좌']['세금_절감액']
        irp_savings = tax_savings['IRP_vs_일반계좌']['세금_절감액']
        irp_deduction = tax_savings['IRP_vs_일반계좌']['세액공제_추가혜택']

        recommendations.append({
            'category': '절세 효과 요약',
            'details': [
                f'ISA 사용 시: 일반계좌 대비 {isa_savings:,.0f}원 절세 ({tax_savings["ISA_vs_일반계좌"]["절감률"]}%)',
                f'IRP/연금저축 사용 시: 일반계좌 대비 {irp_savings:,.0f}원 절세 ({tax_savings["IRP_vs_일반계좌"]["절감률"]}%)',
                f'IRP/연금저축 세액공제 추가 혜택: {irp_deduction:,.0f}원'
            ]
        })

        # 최적 전략
        if monthly_investment >= self.IRP_MONTHLY_OPTIMAL:
            recommendations.append({
                'category': '최적 투자 전략',
                'details': [
                    f'1순위: IRP/연금저축 월 150만원 (연 1,800만원 한도)',
                    f'2순위: ISA 월 {monthly_investment - self.IRP_MONTHLY_OPTIMAL:,.0f}원 (총 1억원 한도)',
                    f'3순위: 일반계좌 (한도 초과분)',
                    f'💡 세금이 많은 자산(해외주식, 채권, 리츠)을 절세 계좌에 우선 배치하세요'
                ]
            })
        else:
            recommendations.append({
                'category': '최적 투자 전략',
                'details': [
                    f'1순위: IRP/연금저축 월 {monthly_investment:,.0f}원 전액 투자',
                    f'💡 IRP 한도(월 150만원)를 최대한 활용하면 절세 효과가 더 큽니다',
                    f'⚠️ 현재 투자액이 IRP 최적 금액보다 적습니다'
                ]
            })

        # 자산 배치 전략
        recommendations.append({
            'category': '자산별 계좌 배치 가이드',
            'details': [
                '✅ IRP/연금저축: 해외주식 ETF, 채권, 리츠 (세금 많은 자산)',
                '✅ ISA: 고배당주, 채권, 금 ETF',
                '✅ 일반계좌: 국내 상장주식, KRX 금 현물 (세금 없거나 적은 자산)',
                '❌ 절대 주의: 국내 상장주식을 IRP에 넣으면 비과세 혜택 상실!'
            ]
        })

        return recommendations


# ========== MCP Server 설정 ==========

async def serve() -> None:
    server = Server("mcp-tooja")
    service = ToojaService()

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """투자메이트 도구 목록"""
        return [
            Tool(
                name=ToojaTools.ASSESS_RISK_PROFILE.value,
                description="투자 성향 분석 (간소화)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "demographic_info": {"type": "object"},
                        "financial_capacity": {"type": "object"},
                        "liquidity_requirements": {"type": "object"},
                        "behavioral_preferences": {"type": "object"}
                    },
                    "required": ["demographic_info", "behavioral_preferences"]
                }
            ),
            Tool(
                name=ToojaTools.GENERATE_PORTFOLIOS.value,
                description="포트폴리오 3가지 생성 (간소화)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "risk_constraints": {"type": "object"}
                    },
                    "required": ["risk_constraints"]
                }
            ),
            Tool(
                name=ToojaTools.ADJUST_VOLATILITY.value,
                description="변동성 조정 (간소화)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_portfolio": {"type": "object"},
                        "market_volatility_data": {"type": "object"}
                    },
                    "required": ["base_portfolio", "market_volatility_data"]
                }
            ),
            Tool(
                name=ToojaTools.BUILD_IMPLEMENTATION.value,
                description="실행 계획 수립 - 절세 최적화 버전 (자산별 계좌 배치 전략 포함)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "optimized_portfolio": {"type": "object"},
                        "current_holdings": {"type": "object"},
                        "account_info": {
                            "type": "object",
                            "properties": {
                                "monthly_investment": {"type": "number"},
                                "isa_accumulated": {"type": "number"},
                                "has_irp": {"type": "boolean"},
                                "has_pension_savings": {"type": "boolean"}
                            }
                        }
                    },
                    "required": ["optimized_portfolio", "account_info"]
                }
            ),
            Tool(
                name=ToojaTools.CALCULATE_ACCOUNT_ALLOCATION.value,
                description="월 투자금액 기반 계좌별 배분 계산 (IRP → ISA → 일반계좌 우선순위)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "monthly_investment": {
                            "type": "number",
                            "description": "월 투자 가능 금액 (원)"
                        },
                        "isa_accumulated": {
                            "type": "number",
                            "description": "ISA 계좌 누적 입금액 (원)",
                            "default": 0
                        }
                    },
                    "required": ["monthly_investment"]
                }
            ),
            Tool(
                name=ToojaTools.MONITOR_PERFORMANCE.value,
                description="포트폴리오 성과 분석 (간소화)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "portfolio_returns": {"type": "object"},
                        "benchmark_returns": {"type": "object"},
                        "time_period": {"type": "string"}
                    },
                    "required": ["portfolio_returns", "benchmark_returns", "time_period"]
                }
            ),
            Tool(
                name=ToojaTools.CALCULATE_RETIREMENT_ACHIEVEMENT.value,
                description="은퇴 목표 달성 여부 계산 및 110% 목표 달성 투자 방법 제시",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "current_age": {
                            "type": "number",
                            "description": "현재 나이"
                        },
                        "retirement_age": {
                            "type": "number",
                            "description": "목표 은퇴 나이"
                        },
                        "current_assets": {
                            "type": "number",
                            "description": "현재 투자 가능 자산 (원)"
                        },
                        "required_retirement_assets": {
                            "type": "number",
                            "description": "필요한 은퇴 자산 (원)"
                        },
                        "monthly_investment": {
                            "type": "number",
                            "description": "월 투자 가능 금액 (원, 옵션)",
                            "default": 0
                        }
                    },
                    "required": ["current_age", "retirement_age", "current_assets", "required_retirement_assets"]
                }
            ),
            Tool(
                name=ToojaTools.COMPARE_TAX_EFFICIENCY.value,
                description="일반계좌 vs 절세계좌(ISA, IRP/연금저축) 세금 비교 시뮬레이션 - 투자 기간 동안 발생하는 세금 차이와 절세 효과 계산",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "investment_period_years": {
                            "type": "number",
                            "description": "투자 기간 (년)"
                        },
                        "monthly_investment": {
                            "type": "number",
                            "description": "월 투자 금액 (원)"
                        },
                        "asset_allocation": {
                            "type": "object",
                            "description": "자산 배분 비율 (퍼센트). 예: {'주식': 40, '채권': 30, '금': 10, '리츠': 10, '현금': 10}. 합계가 100이 되어야 함."
                        },
                        "expected_returns": {
                            "type": "object",
                            "description": "자산별 예상 수익률 (소수). 선택사항, 기본값: 주식 8%, 해외주식 10%, 채권 4%, 금 5%, 리츠 7%, 현금 2%. 예: {'주식': 0.08, '채권': 0.04}"
                        }
                    },
                    "required": ["investment_period_years", "monthly_investment", "asset_allocation"]
                }
            )
        ]

    @server.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """도구 실행"""
        try:
            result = None

            match name:
                case ToojaTools.ASSESS_RISK_PROFILE.value:
                    result = service.assess_risk_profile(
                        arguments.get('demographic_info', {}),
                        arguments.get('financial_capacity', {}),
                        arguments.get('liquidity_requirements', {}),
                        arguments.get('behavioral_preferences', {})
                    )

                case ToojaTools.GENERATE_PORTFOLIOS.value:
                    result = service.generate_three_tier_portfolios(
                        arguments['risk_constraints']
                    )

                case ToojaTools.ADJUST_VOLATILITY.value:
                    result = service.adjust_portfolio_volatility(
                        arguments['base_portfolio'],
                        arguments['market_volatility_data']
                    )

                case ToojaTools.BUILD_IMPLEMENTATION.value:
                    result = service.build_implementation_roadmap(
                        arguments['optimized_portfolio'],
                        arguments.get('current_holdings', {}),
                        arguments['account_info']
                    )

                case ToojaTools.CALCULATE_ACCOUNT_ALLOCATION.value:
                    result = service.calculate_monthly_account_allocation(
                        arguments['monthly_investment'],
                        arguments.get('isa_accumulated', 0)
                    )

                case ToojaTools.MONITOR_PERFORMANCE.value:
                    result = service.monitor_portfolio_performance(
                        arguments['portfolio_returns'],
                        arguments['benchmark_returns'],
                        arguments['time_period']
                    )

                case ToojaTools.CALCULATE_RETIREMENT_ACHIEVEMENT.value:
                    result = service.calculate_retirement_achievement(
                        arguments['current_age'],
                        arguments['retirement_age'],
                        arguments['current_assets'],
                        arguments['required_retirement_assets'],
                        arguments.get('monthly_investment', 0)
                    )

                case ToojaTools.COMPARE_TAX_EFFICIENCY.value:
                    result = service.compare_tax_efficiency_across_accounts(
                        arguments['investment_period_years'],
                        arguments['monthly_investment'],
                        arguments['asset_allocation'],
                        arguments.get('expected_returns', None)
                    )

                case _:
                    raise ValueError(f"Unknown tool: {name}")

            return [
                TextContent(type="text", text=json.dumps(
                    result, ensure_ascii=False, indent=2))
            ]

        except Exception as e:
            raise ValueError(f"Error in {name}: {str(e)}")

    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options)

# 서버시작 함수
if __name__ == "__main__":
    import asyncio
    asyncio.run(serve())
