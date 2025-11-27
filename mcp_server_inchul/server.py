from enum import Enum
import json
from typing import Sequence
import sys
import os

# 중앙 설정 모듈 import
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
from financial_constants_2025 import KOR_2025, marginal_rate_from_brackets, get_healthcare_factor  # type: ignore

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

# __pycache__ 폴더 생성 방지
sys.dont_write_bytecode = True


class InchulTools(str, Enum):
    GENERATE_COMPREHENSIVE_PLAN = "generate_comprehensive_withdrawal_plan"
    COMPARE_TAX_EFFICIENCY = "compare_tax_efficiency_across_accounts"


# ========== 금융 계산 엔진 ==========

class WithdrawalCalculator:

    @staticmethod
    def calculate_swr(portfolio_value: float, swr_rate: float = None) -> float:
        """안전인출률(SWR) 기반 연간 인출액 계산"""
        if swr_rate is None:
            swr_rate = KOR_2025.SWR.base_moderate  # 3.5%
        return portfolio_value * swr_rate

    @staticmethod
    def calculate_swr_amount(portfolio_value: float, retirement_period: int, swr_rate: float) -> dict:
        """SWR 기반 인출액 계산"""
        annual = portfolio_value * swr_rate
        return {
            'annual': annual,
            'rate': swr_rate
        }

    @staticmethod
    def calculate_bridge_gap(annual_expense: float, guaranteed_income: float,
                             bridge_years: int, discount_rate: float) -> float:
        """브릿지 기간 부족분 현가 계산"""
        annual_gap = annual_expense - guaranteed_income

        pv = 0
        for year in range(1, bridge_years + 1):
            pv += annual_gap / ((1 + discount_rate) ** year)

        return pv



# ========== 인출메이트 서비스 로직 ==========

class InchulService:

    def __init__(self):
        self.calculator = WithdrawalCalculator()
        self.asset_structure = {}
        self.baseline = {}

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

    def optimize_tax_efficient_sequence(self, annual_withdrawal_need: float,
                                        account_balances: dict,
                                        guaranteed_income: float,
                                        tax_brackets: list = None,
                                        other_comprehensive_income: float = 0) -> dict:
        """한국 세제 최적화 인출 순서 및 금액 결정 (절세 핵심 원칙 적용)

        원칙: 세금이 없는 돈 → 세금이 낮은 돈 → 세금 이연 효과가 가장 큰 돈 순서
        1순위: 일반 금융계좌 (예/적금, 주식, 펀드)
        2순위: ISA 만기 인출금
        3순위: 연금계좌 (연금저축, IRP) - 가장 늦게 인출
        """

        remaining_need = annual_withdrawal_need - guaranteed_income

        if remaining_need <= 0:
            return {
                'total_need': round(annual_withdrawal_need, 0),
                'guaranteed_income': round(guaranteed_income, 0),
                'additional_withdrawal_needed': 0,
                'message': '보장소득만으로 충분합니다.'
            }

        # 계좌별 잔액 추출 (총액만 사용)
        general_balance = account_balances.get('일반금융계좌', account_balances.get('일반계좌', 0))
        isa_balance = account_balances.get('ISA', 0)

        # 연금계좌 내부 재원 구조 (법정 인출 순서)
        pension_details = account_balances.get('연금계좌_상세', {})
        pension_nontax = pension_details.get('비과세재원', 0)  # 세액공제 안받은 납입금, ISA이체금
        pension_retirement = pension_details.get('이연퇴직소득', 0)  # IRP 퇴직금
        pension_taxable = pension_details.get('과세재원', 0)  # 세액공제 받은 원금 + 수익

        # 한국 세제 최적화 로직 (올바른 순서 적용)
        result = self._optimal_withdrawal_split_kor(
            general_balance,
            isa_balance,
            pension_nontax,
            pension_retirement,
            pension_taxable,
            remaining_need,
            other_comprehensive_income
        )

        withdrawal_sequence = []
        order = 1

        # 1순위: 일반 금융계좌
        if result['general_account'] > 0:
            withdrawal_sequence.append({
                'order': order,
                'account': '일반금융계좌 (예/적금, 주식, 펀드)',
                'amount': round(result['general_account'], 0),
                'tax_amount': 0,  # 이미 원천징수 완료
                'tax_rate': '0% (원천징수 완료)',
                'reason': '인출 페널티 없음, 1순위 인출 대상'
            })
            order += 1

        # 2순위: ISA 만기 인출금
        if result['isa_account'] > 0:
            isa_tax = result['isa_tax']
            withdrawal_sequence.append({
                'order': order,
                'account': 'ISA (만기 인출)',
                'amount': round(result['isa_account'], 0),
                'tax_amount': round(isa_tax, 0),
                'tax_rate': '9.9% (200만원 초과분)',
                'reason': '세제혜택 확정, 연금계좌보다 우선'
            })
            order += 1

        # 3순위: 연금계좌 (법정 인출 순서 적용)
        if result['pension_nontax'] > 0:
            withdrawal_sequence.append({
                'order': order,
                'account': '연금계좌 - 비과세재원',
                'amount': round(result['pension_nontax'], 0),
                'tax_amount': 0,
                'tax_rate': '0%',
                'reason': '세액공제 미적용분/ISA이체금, 1,500만원 한도 미포함'
            })
            order += 1

        if result['pension_retirement'] > 0:
            ret_tax = result['pension_retirement_tax']
            withdrawal_sequence.append({
                'order': order,
                'account': '연금계좌 - 이연퇴직소득',
                'amount': round(result['pension_retirement'], 0),
                'tax_amount': round(ret_tax, 0),
                'tax_rate': '퇴직소득세의 70%',
                'reason': 'IRP 퇴직금, 1,500만원 한도 미포함'
            })
            order += 1

        if result['pension_taxable'] > 0:
            pension_tax = result['pension_taxable_tax']
            withdrawal_sequence.append({
                'order': order,
                'account': '연금계좌 - 과세재원',
                'amount': round(result['pension_taxable'], 0),
                'tax_amount': round(pension_tax, 0),
                'tax_rate': f"{result['pension_tax_rate']*100:.1f}%",
                'reason': f"연금소득세 적용, 1,500만원 한도 {'이내' if result['pension_taxable'] <= 15000000 else '초과'}"
            })
            order += 1

        total_withdrawal = sum([
            result['general_account'],
            result['isa_account'],
            result['pension_nontax'],
            result['pension_retirement'],
            result['pension_taxable']
        ])
        total_tax = result['total_tax']

        # 1,500만원 한도 경고
        warning_1500 = None
        if result['pension_taxable'] > 15000000:
            warning_1500 = {
                'status': 'warning',
                'message': f"연금 과세재원 인출액 {round(result['pension_taxable']/10000, 1)}만원이 1,500만원 한도를 초과합니다.",
                'recommendation': self._compare_tax_methods(
                    result['pension_taxable'],
                    other_comprehensive_income
                )
            }

        return {
            'annual_withdrawal_need': round(annual_withdrawal_need, 0),
            'guaranteed_income': round(guaranteed_income, 0),
            'additional_withdrawal_needed': round(remaining_need, 0),
            'withdrawal_sequence': withdrawal_sequence,
            'total_withdrawal_from_accounts': round(total_withdrawal, 0),
            'estimated_annual_tax': round(total_tax, 0),
            'after_tax_amount': round(total_withdrawal - total_tax, 0),
            'effective_tax_rate': f"{round(total_tax / total_withdrawal * 100, 2) if total_withdrawal > 0 else 0}%",
            'pension_1500_limit_check': warning_1500,
            'recommendations': [
                '✅ 1순위: 일반 금융계좌 먼저 인출 (페널티 없음)',
                '✅ 2순위: ISA 만기 자금 활용',
                '✅ 3순위: 연금계좌는 최대한 늦게 인출 (복리 효과)',
                '⚠️ 연금 과세재원은 연 1,500만원 이하 유지 권장',
                '⚠️ 1,500만원 초과 시 종합과세 vs 16.5% 분리과세 비교 필요'
            ]
        }

    def _compare_tax_methods(self, pension_amount: float, other_income: float) -> dict:
        """연금 1,500만원 초과 시 종합과세 vs 분리과세 비교"""
        T = KOR_2025.TAX

        # A. 종합과세 계산
        total_comprehensive_income = other_income + pension_amount
        comprehensive_tax = total_comprehensive_income * marginal_rate_from_brackets(
            total_comprehensive_income, T.comprehensive_income_brackets)
        # 기타 소득만의 세금
        other_income_tax = other_income * marginal_rate_from_brackets(
            other_income, T.comprehensive_income_brackets)
        # 연금 추가로 인한 증가분
        comprehensive_additional_tax = comprehensive_tax - other_income_tax

        # B. 분리과세 계산 (16.5%)
        separated_tax = pension_amount * 0.165

        # 비교
        if comprehensive_additional_tax < separated_tax:
            recommendation = 'comprehensive'
            message = f'종합과세 선택 권장 (세금 {round((separated_tax - comprehensive_additional_tax)/10000, 1)}만원 절약)'
            recommended_tax = comprehensive_additional_tax
        else:
            recommendation = 'separated'
            message = f'분리과세(16.5%) 선택 권장 (세금 {round((comprehensive_additional_tax - separated_tax)/10000, 1)}만원 절약)'
            recommended_tax = separated_tax

        return {
            'pension_amount': round(pension_amount, 0),
            'other_income': round(other_income, 0),
            'comprehensive_tax': {
                'total_tax': round(comprehensive_tax, 0),
                'additional_from_pension': round(comprehensive_additional_tax, 0),
                'marginal_rate': f"{marginal_rate_from_brackets(total_comprehensive_income, T.comprehensive_income_brackets)*100:.1f}%"
            },
            'separated_tax': {
                'tax': round(separated_tax, 0),
                'rate': '16.5%'
            },
            'recommendation': recommendation,
            'message': message,
            'recommended_tax': round(recommended_tax, 0),
            'savings': round(abs(comprehensive_additional_tax - separated_tax), 0)
        }

    def _optimal_withdrawal_split_kor(self,
                                      general_balance: float,
                                      isa_balance: float,
                                      pension_nontax: float,
                                      pension_retirement: float,
                                      pension_taxable: float,
                                      annual_need: float,
                                      other_income: float = 0) -> dict:
        """한국 세제 최적화 인출 분배 (절세 원칙: 일반계좌 → ISA → 연금계좌)"""
        T = KOR_2025.TAX
        remaining = annual_need

        # 1순위: 일반 금융계좌 (페널티 없음)
        general_take = min(general_balance, remaining)
        remaining -= general_take

        # 2순위: ISA 만기 자금
        isa_take = min(isa_balance, remaining)
        # ISA 세금: 200만원(서민형 400만원) 초과분 9.9%
        isa_taxable = max(0, isa_take - 2000000)
        isa_tax = isa_taxable * 0.099
        remaining -= isa_take

        # 3순위: 연금계좌 (법정 인출 순서 적용)
        # 3-1) 비과세 재원 (세금 0%, 1,500만원 한도 미포함)
        pension_nontax_take = min(pension_nontax, remaining)
        remaining -= pension_nontax_take

        # 3-2) 이연 퇴직소득 (퇴직소득세의 70%, 1,500만원 한도 미포함)
        pension_retirement_take = min(pension_retirement, remaining)
        # 간단한 퇴직소득세 계산 (실제로는 복잡함, 여기서는 예시로 3% 적용)
        pension_retirement_tax = pension_retirement_take * 0.03 * 0.7  # 퇴직소득세의 70%
        remaining -= pension_retirement_take

        # 3-3) 과세 재원 (연금소득세, 1,500만원 한도 적용)
        pension_taxable_take = min(pension_taxable, remaining)

        # 연금소득세율 결정 (나이별 차등, 여기서는 5.5% 가정)
        if pension_taxable_take <= T.pension_separated_cap:  # 1,500만원 이하
            # 분리과세 (3.3~5.5%, 여기서는 5.5% 적용)
            pension_tax_rate = 0.055
            pension_taxable_tax = pension_taxable_take * pension_tax_rate
        else:
            # 1,500만원 초과: 종합과세 vs 16.5% 분리과세 중 유리한 것 적용
            # 기본적으로 16.5% 분리과세 권장 (대부분의 경우 유리)
            pension_tax_rate = 0.165
            pension_taxable_tax = pension_taxable_take * pension_tax_rate

        remaining -= pension_taxable_take

        # 총 세금 계산
        total_tax = isa_tax + pension_retirement_tax + pension_taxable_tax

        return {
            'general_account': general_take,
            'isa_account': isa_take,
            'isa_tax': isa_tax,
            'pension_nontax': pension_nontax_take,
            'pension_retirement': pension_retirement_take,
            'pension_retirement_tax': pension_retirement_tax,
            'pension_taxable': pension_taxable_take,
            'pension_taxable_tax': pension_taxable_tax,
            'pension_tax_rate': pension_tax_rate,
            'total_tax': total_tax,
            'unfulfilled_amount': remaining  # 부족분
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

    def generate_comprehensive_withdrawal_plan(self,
                                               total_assets: float,
                                               asset_allocation: dict,
                                               monthly_expenses: float,
                                               monthly_pension: float,
                                               retirement_age: int,
                                               retirement_years: int,
                                               bridge_years: int = 0,
                                               inflation_rate: float = 0.02,
                                               other_comprehensive_income: float = 0) -> dict:
        """통합 인출 계획 생성 - 입력을 받아 모든 출력을 한번에 생성

        입력:
        - total_assets: 은퇴 시 기대보유자산
        - asset_allocation: 은퇴시점의 자산 분배 현황
        - monthly_expenses: 은퇴 후 월 지출
        - monthly_pension: 월 연금 기대 수령액
        - retirement_age: 은퇴 시작 나이
        - retirement_years: 은퇴 기간 (년)
        - bridge_years: 브릿지 기간 (공적연금 수령 전)
        - inflation_rate: 연 인플레이션율
        - other_comprehensive_income: 사적연금 외 종합소득

        출력:
        1. 연/월 인출 타깃표 (세후·실질)
        2. 계좌별 인출표 & 예상 세금 & 연말 잔액 & 여유금
        3. 버킷 현황 카드
        4. 대안 비교 시트
        """

        annual_expenses = monthly_expenses * 12
        annual_pension = monthly_pension * 12

        # ========== 1. 연/월 인출 타깃표 생성 ==========

        # SWR 기반 기본 인출액 계산
        baseline_result = self.optimize_withdrawal_baseline(
            annual_expenses,
            total_assets,
            bridge_years,
            retirement_years,
            "fixed_real"
        )

        recommended_annual = baseline_result['recommended']['연간인출액']
        recommended_monthly = baseline_result['recommended']['월인출액']

        # 브릿지 기간 동안 필요한 추가 자금
        bridge_annual_need = annual_expenses if bridge_years > 0 else 0

        # 공적연금 수령 후 필요 인출액
        post_bridge_annual_need = max(0, annual_expenses - annual_pension)
        post_bridge_monthly_need = post_bridge_annual_need / 12

        # 기간별 인출 타깃표
        withdrawal_target_table = {
            'summary': {
                '총_은퇴자산': round(total_assets, 0),
                '월_지출목표': round(monthly_expenses, 0),
                '연_지출목표': round(annual_expenses, 0),
                '월_연금수령액': round(monthly_pension, 0),
                '은퇴기간': f'{retirement_years}년',
                '브릿지기간': f'{bridge_years}년' if bridge_years > 0 else '없음'
            },
            'phase_targets': []
        }

        # Phase 1: 브릿지 기간 (공적연금 수령 전)
        if bridge_years > 0:
            withdrawal_target_table['phase_targets'].append({
                'phase': f'Phase 1: 브릿지 기간 (은퇴 후 {bridge_years}년)',
                'period': f'만 {retirement_age}세 ~ 만 {retirement_age + bridge_years - 1}세',
                'guaranteed_income': 0,
                'monthly_withdrawal_need': round(monthly_expenses, 0),
                'annual_withdrawal_need': round(bridge_annual_need, 0),
                'note': '공적연금 수령 전, 전액 자산에서 인출'
            })

        # Phase 2: 공적연금 수령 후
        withdrawal_target_table['phase_targets'].append({
            'phase': f'Phase 2: 공적연금 수령 기간 ({retirement_years - bridge_years}년)',
            'period': f'만 {retirement_age + bridge_years}세 ~ 만 {retirement_age + retirement_years - 1}세',
            'guaranteed_income': round(monthly_pension, 0),
            'monthly_withdrawal_need': round(post_bridge_monthly_need, 0),
            'annual_withdrawal_need': round(post_bridge_annual_need, 0),
            'note': f'공적연금으로 {round(monthly_pension / monthly_expenses * 100, 1) if monthly_expenses > 0 else 0}% 충당'
        })

        # 실질 인출액 (인플레이션 반영)
        withdrawal_target_table['inflation_adjusted_path'] = []
        for year in range(1, min(retirement_years + 1, 31)):  # 최대 30년
            if year <= bridge_years:
                nominal_withdrawal = bridge_annual_need * ((1 + inflation_rate) ** (year - 1))
                phase = 'Bridge'
            else:
                nominal_withdrawal = post_bridge_annual_need * ((1 + inflation_rate) ** (year - 1))
                phase = 'Post-Bridge'

            withdrawal_target_table['inflation_adjusted_path'].append({
                'year': year,
                'age': retirement_age + year - 1,
                'phase': phase,
                'nominal_annual_withdrawal': round(nominal_withdrawal, 0),
                'nominal_monthly_withdrawal': round(nominal_withdrawal / 12, 0),
                'real_annual_withdrawal': round(annual_expenses if year <= bridge_years else post_bridge_annual_need, 0)
            })

        # ========== 2. 계좌별 인출표 & 예상 세금 & 연말 잔액 & 여유금 ==========

        # 첫해 계좌별 인출 순서 및 세금 계산
        first_year_withdrawal = bridge_annual_need if bridge_years > 0 else post_bridge_annual_need

        tax_sequence_result = self.optimize_tax_efficient_sequence(
            first_year_withdrawal,
            asset_allocation,
            0 if bridge_years > 0 else annual_pension,
            None,
            other_comprehensive_income
        )

        # 계좌별 연간 인출 계획 (간단한 시뮬레이션)
        account_withdrawal_details = {
            'year_1_withdrawal_plan': tax_sequence_result['withdrawal_sequence'],
            'year_1_tax_summary': {
                'total_withdrawal': tax_sequence_result['total_withdrawal_from_accounts'],
                'total_tax': tax_sequence_result['estimated_annual_tax'],
                'after_tax_amount': tax_sequence_result['after_tax_amount'],
                'effective_tax_rate': tax_sequence_result['effective_tax_rate']
            },
            'year_end_balance_projection': {}
        }

        # 연말 잔액 예상 (단순화)
        remaining_assets = total_assets - first_year_withdrawal
        for account_name, initial_balance in asset_allocation.items():
            if account_name == '연금계좌_상세':
                continue
            # 간단한 인출 후 잔액 계산 (실제로는 더 복잡)
            withdrawn = 0
            for seq_item in tax_sequence_result['withdrawal_sequence']:
                if account_name in seq_item['account']:
                    withdrawn = seq_item['amount']
                    break

            year_end_balance = max(0, initial_balance - withdrawn)
            account_withdrawal_details['year_end_balance_projection'][account_name] = round(year_end_balance, 0)

        # 여유금 (비상금) 계산
        emergency_fund = remaining_assets * 0.05  # 자산의 5%를 비상금으로
        account_withdrawal_details['emergency_reserve'] = {
            'recommended_amount': round(emergency_fund, 0),
            'months_coverage': round(emergency_fund / monthly_expenses, 1) if monthly_expenses > 0 else 0,
            'status': 'sufficient' if emergency_fund >= monthly_expenses * 6 else 'insufficient',
            'note': '6개월치 생활비 비상금 권장'
        }

        # ========== 3. 버킷 현황 카드 ==========

        bucket_result = self.manage_three_bucket_strategy(
            total_assets,
            recommended_annual,
            'neutral',
            retirement_age
        )

        bucket1_amount = bucket_result['bucket_allocation']['bucket1_현금단기채']['금액']
        bucket1_depletion = bucket_result['bucket1_depletion_months']

        bucket_status_card = {
            'bucket_allocation': bucket_result['bucket_allocation'],
            'bucket1_status': {
                'current_amount': round(bucket1_amount, 0),
                'monthly_withdrawal': round(recommended_monthly, 0),
                'depletion_months': bucket1_depletion,
                'depletion_warning': 'WARNING' if bucket1_depletion < 12 else 'OK',
                'refill_alert': 'bucket1이 1년분 미만입니다. 즉시 재충전 필요!' if bucket1_depletion < 12 else 'bucket1 상태 양호'
            },
            'market_strategy': bucket_result['market_strategy'],
            'recommendations': bucket_result['recommendations']
        }

        # ========== 4. 대안 비교 시트 ==========

        alternative_scenarios = {
            'baseline': {
                'scenario': '기본 계획',
                'monthly_expenses': round(monthly_expenses, 0),
                'pension_start_age': retirement_age + bridge_years,
                'monthly_withdrawal': round(post_bridge_monthly_need, 0),
                'estimated_tax': round(tax_sequence_result['estimated_annual_tax'] / 12, 0),
                'after_tax_monthly': round(tax_sequence_result['after_tax_amount'] / 12, 0),
                'success_probability': '85%',  # 실제로는 시뮬레이션 필요
                'portfolio_longevity': f'{retirement_years}년'
            },
            'alternatives': []
        }

        # 대안 1: 지출 10% 감소
        reduced_expenses = monthly_expenses * 0.9
        reduced_annual = reduced_expenses * 12
        alternative_scenarios['alternatives'].append({
            'scenario': '월 지출 10% 감소',
            'monthly_expenses': round(reduced_expenses, 0),
            'change': f'-{round(monthly_expenses - reduced_expenses, 0)}원',
            'pension_start_age': retirement_age + bridge_years,
            'monthly_withdrawal': round(max(0, reduced_annual - annual_pension) / 12, 0),
            'estimated_annual_savings': round(annual_expenses * 0.1, 0),
            'portfolio_longevity': f'{retirement_years + 2}년 (+2년)',
            'success_probability': '92%',
            'note': '포트폴리오 수명 연장, 성공 가능성 증가'
        })

        # 대안 2: 공적연금 1년 늦춤
        if bridge_years >= 0:
            delayed_pension = monthly_pension * 1.06  # 6% 증액
            alternative_scenarios['alternatives'].append({
                'scenario': '공적연금 수령 1년 지연',
                'monthly_expenses': round(monthly_expenses, 0),
                'pension_start_age': retirement_age + bridge_years + 1,
                'increased_pension': round(delayed_pension, 0),
                'increase_rate': '+6%',
                'additional_bridge_cost': round(monthly_expenses * 12, 0),
                'lifetime_benefit': '장기적으로 유리 (기대수명 고려)',
                'monthly_withdrawal_after': round(max(0, annual_expenses - delayed_pension * 12) / 12, 0),
                'note': '1년 늦출 때마다 6% 증액, 장기적 유리'
            })

        # 대안 3: 주택연금 도입 (보유 부동산이 있는 경우)
        real_estate_value = asset_allocation.get('부동산자산', 0)
        if real_estate_value > 0:
            estimated_housing_pension = real_estate_value * 0.003  # 대략 연 0.3% (월)
            alternative_scenarios['alternatives'].append({
                'scenario': '주택연금 도입',
                'housing_value': round(real_estate_value, 0),
                'estimated_monthly_income': round(estimated_housing_pension, 0),
                'monthly_expenses': round(monthly_expenses, 0),
                'reduced_withdrawal': round(estimated_housing_pension, 0),
                'monthly_withdrawal_after': round(max(0, post_bridge_monthly_need - estimated_housing_pension), 0),
                'portfolio_longevity': f'{retirement_years + 5}년 이상 (+5년+)',
                'note': '상속 포기 대신 안정적 현금흐름 확보',
                'consideration': '상속 계획, 배우자 나이, 주택 소유권 확인 필요'
            })

        # 대안 4: 인출률 조정
        conservative_withdrawal = recommended_annual * 0.9
        alternative_scenarios['alternatives'].append({
            'scenario': '보수적 인출 (-10%)',
            'monthly_withdrawal': round(conservative_withdrawal / 12, 0),
            'reduction': f'-{round(recommended_monthly * 0.1, 0)}원',
            'portfolio_longevity': f'{retirement_years + 3}년 (+3년)',
            'success_probability': '95%',
            'note': '안정성 최우선, 지출 조정 필요'
        })

        # ========== 통합 결과 반환 ==========

        return {
            'input_summary': {
                '총_은퇴자산': round(total_assets, 0),
                '월_지출목표': round(monthly_expenses, 0),
                '월_연금수령액': round(monthly_pension, 0),
                '은퇴기간': f'{retirement_years}년',
                '브릿지기간': f'{bridge_years}년' if bridge_years > 0 else '없음'
            },
            '1_withdrawal_target_table': withdrawal_target_table,
            '2_account_withdrawal_details': account_withdrawal_details,
            '3_bucket_status_card': bucket_status_card,
            '4_alternative_scenarios': alternative_scenarios,
            'recommendations': [
                '✅ 1순위: 일반 금융계좌 → ISA → 연금계좌 순서로 인출',
                '✅ 연금계좌 과세재원은 연 1,500만원 이하 유지',
                '✅ bucket1이 1년분 미만으로 줄면 즉시 재충전',
                '⚠️ 하락장에서는 bucket3 매도 지연',
                f'⚠️ 비상금 {round(emergency_fund / 10000, 0)}만원 별도 확보 권장'
            ],
            'next_steps': [
                '1. 계좌별 자산 배분 확정',
                '2. bucket1 현금성 자산 준비 (2년분)',
                '3. 월별 자동이체 설정',
                '4. 분기별 포트폴리오 점검 일정 수립',
                '5. 세무사와 연말 절세 전략 상담'
            ]
        }

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

        # IRP 한도 상수 (투자메이트와 동일)
        IRP_MONTHLY_OPTIMAL = 1_500_000  # 월 150만원

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
        if monthly_investment >= IRP_MONTHLY_OPTIMAL:
            recommendations.append({
                'category': '최적 투자 전략',
                'details': [
                    f'1순위: IRP/연금저축 월 150만원 (연 1,800만원 한도)',
                    f'2순위: ISA 월 {monthly_investment - IRP_MONTHLY_OPTIMAL:,.0f}원 (총 1억원 한도)',
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
    server = Server("mcp-inchul")
    service = InchulService()

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """인출메이트 도구 목록"""
        return [
            Tool(
                name=InchulTools.GENERATE_COMPREHENSIVE_PLAN.value,
                description="통합 은퇴 인출 계획 생성 - 입력 4가지만 제공하면 모든 출력을 한번에 생성합니다 (인출 타깃표, 계좌별 인출표, 버킷 현황, 대안 비교)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "total_assets": {
                            "type": "number",
                            "description": "은퇴 시 기대보유자산 (총 금융자산)"
                        },
                        "asset_allocation": {
                            "type": "object",
                            "description": """은퇴시점의 자산 분배 현황 (총액 기준)

필수 형식:
{
  "일반금융계좌": 27000000,  // 또는 "일반계좌"
  "ISA": 82000000,
  "연금계좌_상세": {
    "비과세재원": 0,
    "이연퇴직소득": 0,
    "과세재원": 429000000
  }
}

주의사항:
- 일반금융계좌와 ISA는 총액(숫자)만 입력
- 연금계좌는 반드시 '연금계좌_상세' 키를 사용하여 비과세/과세 구분
- 세부 자산 배분(주식, 채권 등)은 지원하지 않음"""
                        },
                        "monthly_expenses": {
                            "type": "number",
                            "description": "은퇴 후 월 지출 (생활비)"
                        },
                        "monthly_pension": {
                            "type": "number",
                            "description": "월 연금 기대 수령액 (국민연금 등 공적연금)"
                        },
                        "retirement_age": {
                            "type": "integer",
                            "description": "은퇴 시작 나이"
                        },
                        "retirement_years": {
                            "type": "integer",
                            "description": "은퇴 기간 (예상 은퇴생활 년수)"
                        },
                        "bridge_years": {
                            "type": "integer",
                            "description": "브릿지 기간 (공적연금 수령 전 기간, 기본값 0)"
                        },
                        "inflation_rate": {
                            "type": "number",
                            "description": "연 인플레이션율 (기본값 0.02 = 2%)"
                        },
                        "other_comprehensive_income": {
                            "type": "number",
                            "description": "사적연금 외 종합소득 (임대소득 등, 기본값 0)"
                        }
                    },
                    "required": ["total_assets", "asset_allocation", "monthly_expenses", "monthly_pension", "retirement_age", "retirement_years"]
                }
            ),
            Tool(
                name=InchulTools.COMPARE_TAX_EFFICIENCY.value,
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
            match name:
                case InchulTools.GENERATE_COMPREHENSIVE_PLAN.value:
                    result = service.generate_comprehensive_withdrawal_plan(
                        arguments['total_assets'],
                        arguments['asset_allocation'],
                        arguments['monthly_expenses'],
                        arguments['monthly_pension'],
                        arguments['retirement_age'],
                        arguments['retirement_years'],
                        arguments.get('bridge_years', 0),
                        arguments.get('inflation_rate', 0.02),
                        arguments.get('other_comprehensive_income', 0)
                    )

                case InchulTools.COMPARE_TAX_EFFICIENCY.value:
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
