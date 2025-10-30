from datetime import datetime
from enum import Enum
import json
from typing import Sequence
import numpy as np
import sys
import os

# 중앙 설정 모듈 import
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
from financial_constants_2025 import KOR_2025, marginal_rate_from_brackets, get_healthcare_factor # type: ignore

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.shared.exceptions import McpError

from pydantic import BaseModel

# __pycache__ 폴더 생성 방지
sys.dont_write_bytecode = True
class InchulTools(str, Enum):
    ANALYZE_ASSET_STRUCTURE = "analyze_retirement_asset_structure"
    OPTIMIZE_BASELINE = "optimize_withdrawal_baseline"
    MANAGE_GUARDRAILS = "manage_guardrail_system"
    OPTIMIZE_TAX_SEQUENCE = "optimize_tax_efficient_sequence"
    MANAGE_BUCKETS = "manage_three_bucket_strategy"
    CREATE_EXECUTION = "create_execution_plan"


# ========== 데이터 모델 ==========

class AssetStructure(BaseModel):
    liquid_assets: dict
    investment_accounts: dict
    pension_accounts: dict
    total_assets: float


class WithdrawalBaseline(BaseModel):
    annual_withdrawal: float
    monthly_withdrawal: float
    withdrawal_period: int
    method: str


class GuardrailAdjustment(BaseModel):
    current_status: str
    adjustment_action: str
    new_withdrawal_amount: float


class TaxSequence(BaseModel):
    withdrawal_order: list
    annual_tax_estimate: float
    account_breakdown: dict


# ========== 금융 계산 엔진 ==========

class WithdrawalCalculator:

    @staticmethod
    def calculate_swr(portfolio_value: float, swr_rate: float = None) -> float:
        """안전인출률(SWR) 기반 연간 인출액 계산"""
        if swr_rate is None:
            swr_rate = KOR_2025.SWR.base_moderate  # 3.5%
        return portfolio_value * swr_rate

    @staticmethod
    def calculate_bridge_gap(annual_expense: float, guaranteed_income: float,
                             bridge_years: int, discount_rate: float) -> float:
        """브릿지 기간 부족분 현가 계산"""
        annual_gap = annual_expense - guaranteed_income

        pv = 0
        for year in range(1, bridge_years + 1):
            pv += annual_gap / ((1 + discount_rate) ** year)

        return pv

    @staticmethod
    def apply_guardrails(init_port_val: float, cur_port_val: float, 
                        cur_withdrawal: float, threshold: float = None,
                        inc_rate: float = None, dec_rate: float = None) -> dict:
        """가드레일 적용"""
        if threshold is None:
            threshold = KOR_2025.GUARD.upper_threshold  # 25%
        if inc_rate is None:
            inc_rate = KOR_2025.GUARD.inc_rate  # 10%
        if dec_rate is None:
            dec_rate = KOR_2025.GUARD.dec_rate  # 10%
            
        drift = (cur_port_val - init_port_val) / max(1e-9, init_port_val)
        out = cur_withdrawal

        if drift >= threshold:
            out *= (1 + inc_rate)
            adjustment = 'increase'
        elif drift <= -threshold:
            out *= (1 - dec_rate)
            adjustment = 'decrease'
        else:
            adjustment = 'maintain'

        return {
            'adjustment': adjustment,
            'new_withdrawal': out,
            'variance': drift
        }


# ========== 인출메이트 서비스 로직 ==========

class InchulService:

    def __init__(self):
        self.calculator = WithdrawalCalculator()
        self.asset_structure = {}
        self.baseline = {}

    def analyze_retirement_asset_structure(self, liquid_assets: dict,
                                           investment_accounts: dict,
                                           pension_accounts: dict,
                                           real_estate_assets: dict,
                                           guaranteed_income: dict,
                                           essential_expenses: dict) -> dict:
        """은퇴 시작시점의 자산 및 소득 구조 분석"""

        total_liquid = sum(liquid_assets.values())
        total_investment = sum(investment_accounts.values())
        total_pension = sum(pension_accounts.values())
        total_real_estate = sum(real_estate_assets.values())

        total_assets = total_liquid + total_investment + total_pension + total_real_estate

        total_guaranteed = sum(guaranteed_income.values())
        total_essential = sum(essential_expenses.values())

        annual_gap = max(0, total_essential - total_guaranteed)

        self.asset_structure = {
            'total_assets': total_assets,
            'guaranteed_income': total_guaranteed,
            'essential_expenses': total_essential,
            'annual_gap': annual_gap
        }

        return {
            'asset_summary': {
                '유동자산': round(total_liquid, 0),
                '투자계좌': round(total_investment, 0),
                '연금계좌': round(total_pension, 0),
                '부동산': round(total_real_estate, 0),
                '총자산': round(total_assets, 0)
            },
            'income_expense_analysis': {
                '보장소득_연간': round(total_guaranteed, 0),
                '필수지출_연간': round(total_essential, 0),
                '연간부족분': round(annual_gap, 0),
                '월부족분': round(annual_gap / 12, 0)
            },
            'sufficiency_ratio': round(total_guaranteed / total_essential * 100, 1) if total_essential > 0 else 100,
            'note': f"보장소득으로 필수지출의 {round(total_guaranteed / total_essential * 100, 1) if total_essential > 0 else 100}%를 충당할 수 있습니다."
        }

    def optimize_withdrawal_baseline(self, annual_cash_requirement: float,
                                     total_portfolio_value: float,
                                     bridge_period_years: int,
                                     retirement_period: int,
                                     withdrawal_method: str = "fixed_real") -> dict:
        """SWR 기반 인출 기본선 설정 (한국 특화)"""

        # 기간별 SWR 조정
        swr_conservative = KOR_2025.SWR.adjust_by_duration(retirement_period) - 0.005
        swr_moderate = KOR_2025.SWR.adjust_by_duration(retirement_period)
        swr_aggressive = KOR_2025.SWR.adjust_by_duration(retirement_period) + 0.005

        conservative_result = self.calculator.calculate_swr_amount(
            total_portfolio_value, retirement_period, swr_conservative)
        moderate_result = self.calculator.calculate_swr_amount(
            total_portfolio_value, retirement_period, swr_moderate)
        aggressive_result = self.calculator.calculate_swr_amount(
            total_portfolio_value, retirement_period, swr_aggressive)

        recommended_annual = moderate_result['annual']
        recommended_monthly = recommended_annual / 12

        if bridge_period_years > 0:
            bridge_gap = self.calculator.calculate_bridge_gap(
                annual_cash_requirement, 0, bridge_period_years, 0.025
            )
        else:
            bridge_gap = 0

        self.baseline = {
            'annual_withdrawal': recommended_annual,
            'monthly_withdrawal': recommended_monthly,
            'retirement_period': retirement_period,
            'withdrawal_method': withdrawal_method
        }

        return {
            'withdrawal_scenarios': {
                '보수적': {
                    '연간': round(conservative_result['annual'], 0),
                    '월간': round(conservative_result['annual'] / 12, 0),
                    '인출률': f"{conservative_result['rate']*100:.2f}%"
                },
                '균형적': {
                    '연간': round(moderate_result['annual'], 0),
                    '월간': round(moderate_result['annual'] / 12, 0),
                    '인출률': f"{moderate_result['rate']*100:.2f}%"
                },
                '적극적': {
                    '연간': round(aggressive_result['annual'], 0),
                    '월간': round(aggressive_result['annual'] / 12, 0),
                    '인출률': f"{aggressive_result['rate']*100:.2f}%"
                }
            },
            'recommended': {
                '연간인출액': round(recommended_annual, 0),
                '월인출액': round(recommended_monthly, 0),
                '인출률': f"{moderate_result['rate']*100:.2f}%",
                '예상지속기간': f"{retirement_period}년"
            },
            'bridge_period_analysis': {
                '브릿지기간': f"{bridge_period_years}년",
                '추가필요자금': round(bridge_gap, 0)
            } if bridge_period_years > 0 else None,
            'note': f'기간 {retirement_period}년에 맞춘 {moderate_result["rate"]*100:.2f}% 인출률을 기본으로 권장합니다.'
        }

    def manage_guardrail_system(self, current_portfolio_value: float,
                                target_portfolio_value: float,
                                current_withdrawal: float,
                                essential_expenses: float,
                                inflation_rate: float = 0.0) -> dict:
        """한국형 가드레일 규칙 적용"""

        adjustment = self.calculator.apply_guardrails_kor(
            target_portfolio_value,  # 초기 목표값
            current_portfolio_value,  # 현재값
            current_withdrawal,
            inflation_rate
        )

        new_withdrawal = adjustment['new_withdrawal']
        if new_withdrawal < essential_expenses:
            warning = True
            warning_message = '조정된 인출액이 필수지출보다 적습니다. 지출 조정 또는 자산 활용 방안이 필요합니다.'
        else:
            warning = False
            warning_message = None

        return {
            'current_portfolio': round(current_portfolio_value, 0),
            'target_portfolio': round(target_portfolio_value, 0),
            'variance_from_target': f"{adjustment['variance'] * 100:.1f}%",
            'adjustment_action': adjustment['adjustment'],
            'current_withdrawal': round(current_withdrawal, 0),
            'adjusted_withdrawal': round(new_withdrawal, 0),
            'change_amount': round(new_withdrawal - current_withdrawal, 0),
            'change_percentage': round((new_withdrawal - current_withdrawal) / current_withdrawal * 100, 1) if current_withdrawal > 0 else 0,
            'essential_expenses_check': {
                'essential_expenses': round(essential_expenses, 0),
                'sufficient': new_withdrawal >= essential_expenses,
                'warning': warning_message
            },
            'message': adjustment['message'],
            'next_review_date': '1년 후',
            'inflation_adjustment': f"인플레이션 {inflation_rate*100:.1f}% 반영" if inflation_rate > 0 else "인플레이션 미반영"
        }

    def optimize_tax_efficient_sequence(self, annual_withdrawal_need: float,
                                        account_balances: dict,
                                        guaranteed_income: float,
                                        tax_brackets: list = None) -> dict:
        """한국 세제 최적화 인출 순서 및 금액 결정"""

        remaining_need = annual_withdrawal_need - guaranteed_income

        if remaining_need <= 0:
            return {
                'total_need': round(annual_withdrawal_need, 0),
                'guaranteed_income': round(guaranteed_income, 0),
                'additional_withdrawal_needed': 0,
                'message': '보장소득만으로 충분합니다.'
            }

        # 한국 세제 최적화 로직
        result = self._optimal_withdrawal_split_kor(
            account_balances.get('일반과세계좌', 0),
            account_balances.get('연금계좌', 0),
            remaining_need
        )

        withdrawal_sequence = []

        # 1) 연금 분리과세 우선
        if result['pension_separated'] > 0:
            withdrawal_sequence.append({
                'order': 1,
                'account': '연금계좌 (분리과세)',
                'amount': round(result['pension_separated'], 0),
                'tax_amount': round(result['pension_separated'] * 0.033, 0),
                'tax_rate': '3.3%',
                'reason': '분리과세 한도 내 저세율 적용'
            })

        # 2) 연금 종합과세
        if result['pension_comprehensive'] > 0:
            comp_tax = result['pension_comprehensive'] * marginal_rate_from_brackets(
                result['pension_comprehensive'], KOR_2025.TAX.comprehensive_income_brackets)
            withdrawal_sequence.append({
                'order': 2,
                'account': '연금계좌 (종합과세)',
                'amount': round(result['pension_comprehensive'], 0),
                'tax_amount': round(comp_tax, 0),
                'tax_rate': f"{marginal_rate_from_brackets(result['pension_comprehensive'], KOR_2025.TAX.comprehensive_income_brackets)*100:.1f}%",
                'reason': '분리과세 초과분 종합과세'
            })

        # 3) 일반과세계좌
        if result['taxable'] > 0:
            withdrawal_sequence.append({
                'order': 3,
                'account': '일반과세계좌',
                'amount': round(result['taxable'], 0),
                'tax_amount': round(result['taxable'] * KOR_2025.TAX.interest_dividend, 0),
                'tax_rate': f"{KOR_2025.TAX.interest_dividend*100:.1f}%",
                'reason': '금융소득 분리과세'
            })

        total_withdrawal = result['pension_separated'] + result['pension_comprehensive'] + result['taxable']
        total_tax = result['estimated_tax']

        return {
            'annual_withdrawal_need': round(annual_withdrawal_need, 0),
            'guaranteed_income': round(guaranteed_income, 0),
            'additional_withdrawal_needed': round(remaining_need, 0),
            'withdrawal_sequence': withdrawal_sequence,
            'total_withdrawal_from_accounts': round(total_withdrawal, 0),
            'estimated_annual_tax': round(total_tax, 0),
            'after_tax_amount': round(total_withdrawal - total_tax, 0),
            'effective_tax_rate': f"{round(total_tax / total_withdrawal * 100, 2) if total_withdrawal > 0 else 0}%",
            'recommendations': [
                '연금 1,500만원까지 분리과세 우선 활용',
                '일반과세계좌는 15.4% 원천징수 적용',
                '세율 구간을 초과하지 않도록 주의'
            ]
        }

    def _optimal_withdrawal_split_kor(self, taxable_balance: float, 
                                     pension_balance: float, 
                                     annual_need: float) -> dict:
        """한국 세제 최적화 인출 분배"""
        T = KOR_2025.TAX
        
        # 1) 연금 분리과세 한도 우선
        pension_sep_take = min(T.pension_separated_cap, pension_balance, annual_need)
        pension_sep_tax = pension_sep_take * 0.033  # 3.3% 가정
        
        remaining = annual_need - pension_sep_take
        
        # 2) 나머지는 연금 종합 vs 과세계좌 중 최적 조합
        pension_comp_take = min(remaining, max(0, pension_balance - pension_sep_take))
        pension_comp_tax = pension_comp_take * marginal_rate_from_brackets(
            pension_comp_take, T.comprehensive_income_brackets)
        
        rem2 = remaining - pension_comp_take
        taxable_take = min(rem2, taxable_balance)
        taxable_tax = taxable_take * T.interest_dividend
        
        total_tax = pension_sep_tax + pension_comp_tax + taxable_tax
        
        return {
            'pension_separated': pension_sep_take,
            'pension_comprehensive': pension_comp_take,
            'taxable': taxable_take,
            'estimated_tax': total_tax
        }

    def manage_three_bucket_strategy(self, total_portfolio: float,
                                     annual_withdrawal: float,
                                     market_condition: str,
                                     age: int = 65) -> dict:
        """한국형 3버킷 전략 (2-8-나머지 + 의료비)"""

        # 한국형 버킷 구조
        bucket_plan = self._bucket_plan_kor(annual_withdrawal, age, 30)  # 30년 가정

        bucket1_amount = bucket_plan['cash']
        bucket2_amount = bucket_plan['income'] 
        bucket3_amount = total_portfolio - bucket1_amount - bucket2_amount
        healthcare_amount = bucket_plan['healthcare']

        if market_condition == 'bear':
            strategy = {
                'current_condition': '하락장',
                'action': 'bucket1, bucket2에서 생활비 충당. bucket3 매도 지연',
                'bucket1_usage': '우선 사용',
                'bucket2_usage': 'bucket1 소진시 사용',
                'bucket3_action': '매도 지연, 회복 대기',
                'rebalancing': '중단 (회복시까지)'
            }
        elif market_condition == 'bull':
            strategy = {
                'current_condition': '상승장',
                'action': 'bucket3에서 일부 매도하여 bucket1, 2 재충전',
                'bucket1_usage': '정상 사용',
                'bucket2_usage': '정상 대기',
                'bucket3_action': '이익 실현하여 버킷 재충전',
                'rebalancing': '실시 (목표 배분 복원)'
            }
        else:
            strategy = {
                'current_condition': '보합장',
                'action': '정상적인 버킷 순환 운영',
                'bucket1_usage': '정상 사용',
                'bucket2_usage': '정상 대기',
                'bucket3_action': '정상 유지',
                'rebalancing': '연 1회 실시'
            }

        return {
            'bucket_allocation': {
                'bucket1_현금단기채': {
                    '금액': round(bucket1_amount, 0),
                    '기간': f'{KOR_2025.BUCK.cash_years}년분',
                    '자산': '현금, MMF, 단기채권',
                    '목적': '즉시 인출 가능, 생활비 1순위'
                },
                'bucket2_중기채배당': {
                    '금액': round(bucket2_amount, 0),
                    '기간': f'{KOR_2025.BUCK.income_years}년분',
                    '자산': '중기채권, 배당주, 리츠',
                    '목적': '하락장 완충, bucket1 보충'
                },
                'bucket3_장기성장': {
                    '금액': round(bucket3_amount, 0),
                    '기간': '나머지',
                    '자산': '주식, 성장형 ETF',
                    '목적': '장기 성장, 회복기 활용'
                },
                '의료비_버킷': {
                    '금액': round(healthcare_amount, 0),
                    '기간': '30년분 (연령 가중)',
                    '자산': '의료비 전용 저축',
                    '목적': '고령화 대비 의료비'
                }
            },
            'market_strategy': strategy,
            'bucket1_depletion_months': round(bucket1_amount / (annual_withdrawal / 12), 0) if annual_withdrawal > 0 else 0,
            'healthcare_ratio': f"{KOR_2025.BUCK.healthcare_base_ratio*100:.1f}%",
            'recommendations': [
                'bucket1이 1년치 미만으로 줄면 즉시 보충',
                '하락장에서는 bucket3 매도를 최대한 지연',
                '상승장에서는 적극적으로 이익 실현',
                '의료비 버킷은 연령별 가중치 적용'
            ]
        }

    def _bucket_plan_kor(self, annual_expense: float, age: int, horizon_years: int) -> dict:
        """한국형 버킷 계획"""
        b = KOR_2025.BUCK
        cash_amt = annual_expense * b.cash_years
        income_amt = annual_expense * b.income_years
        growth_amt = max(0, annual_expense * max(0, horizon_years - (b.cash_years + b.income_years)))

        # 의료비: 연비 15% 기본 × 은퇴기간 × 연령 가중치
        base_med = annual_expense * b.healthcare_base_ratio
        age_factor = get_healthcare_factor(age)
        med_total = base_med * min(30, horizon_years) * age_factor

        return {
            'cash': cash_amt,
            'income': income_amt, 
            'growth': growth_amt,
            'healthcare': med_total
        }

    def create_execution_plan(self, withdrawal_strategy: dict,
                              account_details: dict) -> dict:
        """실행 가능한 월별 인출 계획 및 체크리스트 생성"""

        annual_withdrawal = withdrawal_strategy.get('annual_withdrawal', 0)
        monthly_withdrawal = annual_withdrawal / 12

        monthly_schedule = []
        for month in range(1, 13):
            monthly_schedule.append({
                'month': f'{month}월',
                'withdrawal_amount': round(monthly_withdrawal, 0),
                'source_account': 'bucket1 (현금/MMF)',
                'transfer_date': '매월 1일',
                'tax_withholding': '원천징수 자동 처리'
            })

        quarterly_checklist = [
            {
                'quarter': 'Q1 (1-3월)',
                'tasks': [
                    'bucket1 잔액 확인 (2년분 유지되는지)',
                    '전년도 세금 정산',
                    '포트폴리오 밸런스 확인'
                ]
            },
            {
                'quarter': 'Q2 (4-6월)',
                'tasks': [
                    'bucket2 → bucket1 보충 필요 여부 확인',
                    '상반기 수익률 점검',
                    '대형 지출 예정 확인'
                ]
            },
            {
                'quarter': 'Q3 (7-9월)',
                'tasks': [
                    'bucket3 수익률 점검',
                    '시장 상황 평가',
                    '가드레일 점검'
                ]
            },
            {
                'quarter': 'Q4 (10-12월)',
                'tasks': [
                    '연간 리밸런싱 실시',
                    '다음연도 인출 계획 수립',
                    '세금 납부 준비'
                ]
            }
        ]

        alternative_scenarios = {
            '목표지출_10%감소': {
                'new_monthly_withdrawal': round(monthly_withdrawal * 0.9, 0),
                'annual_savings': round(annual_withdrawal * 0.1, 0),
                'portfolio_longevity': '+2년 연장 예상'
            },
            '공적연금_1년_늦춤': {
                'additional_bridge_cost': round(monthly_withdrawal * 12, 0),
                'increased_pension': '+6% 증액',
                'net_benefit': '장기적으로 유리'
            },
            '주택연금_도입': {
                'estimated_monthly_income': '주택가격 및 연령에 따라 상이',
                'withdrawal_reduction': '월 인출액 감소 가능',
                'consideration': '상속 계획 고려 필요'
            }
        }

        return {
            'monthly_withdrawal_schedule': monthly_schedule,
            'quarterly_checklist': quarterly_checklist,
            'annual_tasks': [
                '1월: 전년도 결산 및 세금 정산',
                '6월: 상반기 점검 및 중간 조정',
                '12월: 리밸런싱 및 다음연도 계획 수립'
            ],
            'alternative_scenarios': alternative_scenarios,
            'emergency_procedures': {
                '시장_급락시': [
                    'bucket1, 2에서만 인출',
                    'bucket3 매도 중단',
                    '필수지출만 유지'
                ],
                '예상외_대형지출': [
                    '2-3년 분산 인출 검토',
                    '세율 급등 방지',
                    '부동산 활용 고려'
                ]
            },
            'automation_setup': {
                '자동이체': '매월 1일 bucket1 → 생활비 계좌',
                '자동리밸런싱': '연 1회 12월 자동 실행 (옵션)',
                '알림설정': 'bucket1 1년분 미만시 알림'
            }
        }


# ========== MCP Server 설정 ==========

async def serve() -> None:
    server = Server("mcp-inchul")
    service = InchulService()

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """인출메이트 도구 목록"""
        return [
            Tool(
                name=InchulTools.ANALYZE_ASSET_STRUCTURE.value,
                description="은퇴 시작시점의 자산 및 소득 구조를 분석합니다",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "liquid_assets": {"type": "object"},
                        "investment_accounts": {"type": "object"},
                        "pension_accounts": {"type": "object"},
                        "real_estate_assets": {"type": "object"},
                        "guaranteed_income": {"type": "object"},
                        "essential_expenses": {"type": "object"}
                    },
                    "required": ["liquid_assets", "guaranteed_income", "essential_expenses"]
                }
            ),
            Tool(
                name=InchulTools.OPTIMIZE_BASELINE.value,
                description="안전인출률 기반 인출 기본선을 설정합니다",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "annual_cash_requirement": {"type": "number"},
                        "total_portfolio_value": {"type": "number"},
                        "bridge_period_years": {"type": "integer"},
                        "retirement_period": {"type": "integer"},
                        "withdrawal_method": {"type": "string"}
                    },
                    "required": ["annual_cash_requirement", "total_portfolio_value", "retirement_period"]
                }
            ),
            Tool(
                name=InchulTools.MANAGE_GUARDRAILS.value,
                description="가드레일 시스템으로 인출액을 동적 조정합니다",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "current_portfolio_value": {"type": "number"},
                        "target_portfolio_value": {"type": "number"},
                        "current_withdrawal": {"type": "number"},
                        "essential_expenses": {"type": "number"}
                    },
                    "required": ["current_portfolio_value", "target_portfolio_value", "current_withdrawal"]
                }
            ),
            Tool(
                name=InchulTools.OPTIMIZE_TAX_SEQUENCE.value,
                description="세금 효율적인 계좌별 인출 순서를 결정합니다",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "annual_withdrawal_need": {"type": "number"},
                        "account_balances": {"type": "object"},
                        "guaranteed_income": {"type": "number"},
                        "tax_brackets": {"type": "array"}
                    },
                    "required": ["annual_withdrawal_need", "account_balances"]
                }
            ),
            Tool(
                name=InchulTools.MANAGE_BUCKETS.value,
                description="3버킷 전략으로 시퀀스 리스크를 관리합니다",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "total_portfolio": {"type": "number"},
                        "annual_withdrawal": {"type": "number"},
                        "market_condition": {"type": "string"}
                    },
                    "required": ["total_portfolio", "annual_withdrawal", "market_condition"]
                }
            ),
            Tool(
                name=InchulTools.CREATE_EXECUTION.value,
                description="월별 인출 계획 및 실행 체크리스트를 생성합니다",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "withdrawal_strategy": {"type": "object"},
                        "account_details": {"type": "object"}
                    },
                    "required": ["withdrawal_strategy"]
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
                case InchulTools.ANALYZE_ASSET_STRUCTURE.value:
                    result = service.analyze_retirement_asset_structure(
                        arguments.get('liquid_assets', {}),
                        arguments.get('investment_accounts', {}),
                        arguments.get('pension_accounts', {}),
                        arguments.get('real_estate_assets', {}),
                        arguments.get('guaranteed_income', {}),
                        arguments.get('essential_expenses', {})
                    )

                case InchulTools.OPTIMIZE_BASELINE.value:
                    result = service.optimize_withdrawal_baseline(
                        arguments['annual_cash_requirement'],
                        arguments['total_portfolio_value'],
                        arguments.get('bridge_period_years', 0),
                        arguments['retirement_period'],
                        arguments.get('withdrawal_method', 'fixed_real')
                    )

                case InchulTools.MANAGE_GUARDRAILS.value:
                    result = service.manage_guardrail_system(
                        arguments['current_portfolio_value'],
                        arguments['target_portfolio_value'],
                        arguments['current_withdrawal'],
                        arguments.get('essential_expenses', 0)
                    )

                case InchulTools.OPTIMIZE_TAX_SEQUENCE.value:
                    result = service.optimize_tax_efficient_sequence(
                        arguments['annual_withdrawal_need'],
                        arguments['account_balances'],
                        arguments.get('guaranteed_income', 0),
                        arguments.get('tax_brackets', [])
                    )

                case InchulTools.MANAGE_BUCKETS.value:
                    result = service.manage_three_bucket_strategy(
                        arguments['total_portfolio'],
                        arguments['annual_withdrawal'],
                        arguments['market_condition']
                    )

                case InchulTools.CREATE_EXECUTION.value:
                    result = service.create_execution_plan(
                        arguments['withdrawal_strategy'],
                        arguments.get('account_details', {})
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
