from enum import Enum
import json
from typing import Sequence
import numpy as np
import sys
import os

# 중앙 설정 모듈 import
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
from financial_constants_2025 import KOR_2025 # type: ignore

# KRX 데이터 서비스 import
from mcp_server_tooja.krx_data_service import KRXDataService, PYKRX_AVAILABLE

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

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
    # KRX 데이터 도구
    GET_MARKET_OVERVIEW = "get_market_overview"
    GET_MARKET_VOLATILITY = "get_market_volatility"
    GET_ETF_RECOMMENDATIONS = "get_etf_recommendations"
    GET_STOCK_PRICE = "get_stock_price"
    GET_INVESTOR_TRADING = "get_investor_trading"
    # 신규: 실시간 시장 스크리닝 도구
    GET_TOP_STOCKS_BY_MARKET_CAP = "get_top_stocks_by_market_cap"
    GET_TOP_ETFS_BY_PERFORMANCE = "get_top_etfs_by_performance"


# ========== 시각화 헬퍼 함수 ==========

class VisualFormatter:
    """응답을 시각적으로 표현하기 위한 포맷터"""

    @staticmethod
    def format_progress_bar(value: float, max_value: float, width: int = 30, label: str = "") -> str:
        """진행 바 생성"""
        percentage = min(100, (value / max_value * 100))
        filled = int(width * value / max_value)
        bar = '█' * filled + '░' * (width - filled)
        return f"{label} [{bar}] {percentage:.1f}%"

    @staticmethod
    def format_allocation_chart(allocation: dict) -> str:
        """자산 배분 차트 생성"""
        chart = "\n📊 자산 배분 비율\n" + "=" * 50 + "\n"
        total = sum(allocation.values())

        for asset, value in sorted(allocation.items(), key=lambda x: x[1], reverse=True):
            percentage = (value / total * 100) if total > 0 else 0
            bar_length = int(percentage / 2.5)  # 40칸 기준
            bar = '█' * bar_length + '░' * (40 - bar_length)
            chart += f"{asset:8s} [{bar}] {percentage:5.1f}%\n"

        return chart

    @staticmethod
    def format_comparison_table(data: dict, title: str = "") -> str:
        """비교 테이블 생성"""
        if title:
            table = f"\n📋 {title}\n" + "=" * 80 + "\n"
        else:
            table = "\n" + "=" * 80 + "\n"

        table += f"{'항목':<20s} | {'값':>20s}\n"
        table += "-" * 80 + "\n"

        for key, value in data.items():
            if isinstance(value, (int, float)):
                if value > 1000:
                    value_str = f"{value:,.0f}원"
                else:
                    value_str = f"{value:.2f}"
            else:
                value_str = str(value)
            table += f"{key:<20s} | {value_str:>20s}\n"

        return table

    @staticmethod
    def format_account_priority_visual(irp_amount: float, isa_amount: float,
                                       general_amount: float, total: float) -> str:
        """계좌 우선순위 시각화"""
        visual = "\n💰 월 투자금 배분 흐름\n" + "=" * 60 + "\n\n"

        # 총 투자금
        visual += f"총 투자금: {total:,.0f}원\n"
        visual += "       │\n"
        visual += "       ▼\n"

        # 1순위: IRP
        irp_pct = (irp_amount / total * 100) if total > 0 else 0
        visual += f"┌──────────────────────────────────────┐\n"
        visual += f"│  1순위: IRP/연금저축                  │\n"
        visual += f"│  {irp_amount:,.0f}원 ({irp_pct:.1f}%){'':>15s}│\n"
        visual += f"│  ✓ 세액공제 13.2~16.5%               │\n"
        visual += f"└──────────────────────────────────────┘\n"

        if isa_amount > 0 or general_amount > 0:
            visual += "       │ 잔액: " + f"{total - irp_amount:,.0f}원\n"
            visual += "       ▼\n"

        # 2순위: ISA
        if isa_amount > 0:
            isa_pct = (isa_amount / total * 100) if total > 0 else 0
            visual += f"┌──────────────────────────────────────┐\n"
            visual += f"│  2순위: ISA                          │\n"
            visual += f"│  {isa_amount:,.0f}원 ({isa_pct:.1f}%){'':>15s}│\n"
            visual += f"│  ✓ 비과세 + 9.9% 저율과세            │\n"
            visual += f"└──────────────────────────────────────┘\n"

            if general_amount > 0:
                visual += "       │ 잔액: " + f"{general_amount:,.0f}원\n"
                visual += "       ▼\n"

        # 3순위: 일반계좌
        if general_amount > 0:
            general_pct = (general_amount / total * 100) if total > 0 else 0
            visual += f"┌──────────────────────────────────────┐\n"
            visual += f"│  3순위: 일반계좌                     │\n"
            visual += f"│  {general_amount:,.0f}원 ({general_pct:.1f}%){'':>10s}│\n"
            visual += f"│  한도 초과분 투자                    │\n"
            visual += f"└──────────────────────────────────────┘\n"

        return visual

    @staticmethod
    def format_scenario_comparison(scenarios: dict) -> str:
        """시나리오 비교 테이블 생성"""
        visual = "\n📈 위험성향별 시나리오 비교\n" + "=" * 100 + "\n\n"

        # 헤더
        visual += f"{'구분':<15s} | {'안정형':>25s} | {'중립형':>25s} | {'공격형':>25s}\n"
        visual += "-" * 100 + "\n"

        # 연간 수익률
        visual += f"{'명목수익률':<15s} | "
        visual += f"{scenarios['conservative']['nominal_annual_return']:>24.1f}% | "
        visual += f"{scenarios['moderate']['nominal_annual_return']:>24.1f}% | "
        visual += f"{scenarios['aggressive']['nominal_annual_return']:>24.1f}%\n"

        # 실질 수익률
        visual += f"{'실질수익률':<15s} | "
        visual += f"{scenarios['conservative']['real_annual_return']:>24.1f}% | "
        visual += f"{scenarios['moderate']['real_annual_return']:>24.1f}% | "
        visual += f"{scenarios['aggressive']['real_annual_return']:>24.1f}%\n"

        visual += "-" * 100 + "\n"

        # 미래 자산 (명목)
        visual += f"{'미래자산(명목)':<15s} | "
        for risk_type in ['conservative', 'moderate', 'aggressive']:
            val = scenarios[risk_type]['total_expected_assets_nominal']
            visual += f"{val:>22,.0f}원 | "
        visual += "\n"

        # 미래 자산 (실질)
        visual += f"{'미래자산(실질)':<15s} | "
        for risk_type in ['conservative', 'moderate', 'aggressive']:
            val = scenarios[risk_type]['total_expected_assets_real']
            visual += f"{val:>22,.0f}원 | "
        visual += "\n"

        visual += "-" * 100 + "\n"

        # 목표 달성률
        visual += f"{'목표달성률':<15s} | "
        for risk_type in ['conservative', 'moderate', 'aggressive']:
            achievement = scenarios[risk_type]['achievement_rate_nominal']
            visual += f"{achievement:>24.1f}% | "
        visual += "\n"

        # 달성 여부 표시
        visual += f"{'목표달성여부':<15s} | "
        for risk_type in ['conservative', 'moderate', 'aggressive']:
            achieves = scenarios[risk_type]['achieves_110_target']
            status = "✓ 달성" if achieves else "✗ 미달성"
            visual += f"{status:>25s} | "
        visual += "\n"

        return visual

    @staticmethod
    def format_tax_comparison(general: dict, isa: dict, irp: dict) -> str:
        """세금 비교 차트"""
        visual = "\n💸 계좌별 세금 비교 (투자 기간 종료 시점)\n" + "=" * 80 + "\n\n"

        accounts = [
            ("일반계좌", general),
            ("ISA", isa),
            ("IRP/연금저축", irp)
        ]

        max_tax = max(general['total_tax'], isa['total_tax'], irp['total_tax'])

        for account_name, account_data in accounts:
            tax = account_data['total_tax']
            after_tax = account_data['total_value_after_tax']

            # 세금 막대 그래프
            bar_length = int((tax / max_tax * 40)) if max_tax > 0 else 0
            bar = '█' * bar_length + '░' * (40 - bar_length)

            visual += f"\n{account_name:<12s}\n"
            visual += f"  세금: [{bar}] {tax:>15,.0f}원\n"
            visual += f"  세후: {after_tax:>15,.0f}원\n"

        # 절세 효과
        isa_savings = general['total_tax'] - isa['total_tax']
        irp_savings = general['total_tax'] - irp['total_tax']

        visual += "\n" + "-" * 80 + "\n"
        visual += f"💰 ISA 절세액:  {isa_savings:>15,.0f}원\n"
        visual += f"💰 IRP 절세액:  {irp_savings:>15,.0f}원\n"

        if 'tax_deduction_benefit' in irp:
            visual += f"💰 IRP 세액공제: {irp['tax_deduction_benefit']:>15,.0f}원 (추가)\n"

        return visual

    @staticmethod
    def format_portfolio_visual(portfolio: dict) -> str:
        """포트폴리오 시각화"""
        visual = f"\n🎯 {portfolio.get('portfolio_name', '포트폴리오')}\n" + "=" * 60 + "\n\n"

        # 자산 배분
        allocation = portfolio.get('asset_allocation', {})
        visual += VisualFormatter.format_allocation_chart(allocation)

        # 예상 수익률과 변동성
        visual += "\n" + "-" * 60 + "\n"
        visual += f"📊 기대 수익률: {portfolio.get('expected_annual_return', 0):.1f}%\n"
        visual += f"📉 예상 변동성: {portfolio.get('expected_volatility', 0):.1f}%\n"

        return visual


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
        self.krx_service = KRXDataService()  # KRX 데이터 서비스 초기화

    def assess_risk_profile(self, demographic_info: dict, _financial_capacity: dict,
                            _liquidity_requirements: dict, behavioral_preferences: dict) -> dict:
        """투자성향 분석 (간소화)"""
        # _financial_capacity, _liquidity_requirements: 향후 확장용 파라미터
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
        """포트폴리오 3가지 생성 (KRX 실시간 데이터 통합)"""

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

        # 시각화 추가
        visual_output = "\n" + "="*80 + "\n"
        visual_output += "🎯 포트폴리오 3가지 제안\n"
        visual_output += "="*80 + "\n"

        for portfolio_type, portfolio in portfolios.items():
            visual_output += VisualFormatter.format_portfolio_visual(portfolio)
            visual_output += "\n"

        # ========== KRX 실시간 데이터 자동 통합 ==========
        market_overview = self.get_market_overview()
        investor_trading = self.get_investor_trading()

        # 계좌별 ETF 추천
        irp_etfs = self.get_etf_recommendations('IRP')
        isa_etfs = self.get_etf_recommendations('ISA')
        general_stocks = self.get_etf_recommendations('GENERAL')

        return {
            'portfolios': portfolios,
            'recommendation': 'moderate',
            'visual_summary': visual_output,
            # KRX 실시간 데이터
            'market_data': {
                'market_overview': market_overview,
                'investor_trading': investor_trading,
            },
            'etf_recommendations': {
                'IRP': irp_etfs,
                'ISA': isa_etfs,
                'GENERAL': general_stocks,
            }
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

        # 시각화 추가
        visual_output = VisualFormatter.format_account_priority_visual(
            irp_monthly, isa_monthly, general_monthly, monthly_investment
        )

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
            'warnings': self._generate_account_warnings(monthly_investment, irp_monthly, isa_monthly, isa_limit_reached),
            'visual_summary': visual_output
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

        # ========== KRX 실시간 데이터 자동 통합 ==========
        market_overview = self.get_market_overview()
        investor_trading = self.get_investor_trading()

        # 계좌별 구체적인 ETF 추천 (실시간 시세 포함)
        irp_etfs = self.get_etf_recommendations('IRP')
        isa_etfs = self.get_etf_recommendations('ISA')
        general_stocks = self.get_etf_recommendations('GENERAL')

        return {
            'account_allocation': account_allocation,
            'asset_placement_strategy': asset_placement_strategy,
            'execution_steps': execution_steps,
            'warnings': warnings,
            'rebalancing_rules': {
                'frequency': '연 1회',
                'timing': '매년 12월 또는 시장 급변동 시',
                'threshold': '목표 비중 대비 ±5% 이상 이탈 시'
            },
            # KRX 실시간 데이터
            'market_data': {
                'market_overview': market_overview,
                'investor_trading': investor_trading,
            },
            'etf_recommendations': {
                'IRP': irp_etfs,
                'ISA': isa_etfs,
                'GENERAL': general_stocks,
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
                                        monthly_investment: float = 0,
                                        scenario_type: str = 'baseline') -> dict:
        """은퇴 목표 달성 여부 및 투자 전략 계산 (인플레이션 반영)

        Args:
            current_age: 현재 나이
            retirement_age: 목표 은퇴 나이
            current_assets: 현재 투자 가능 자산
            required_retirement_assets: 필요한 은퇴 자산
            monthly_investment: 월 투자 가능 금액 (기본값: 0)
            scenario_type: 경제 시나리오 ('pessimistic', 'baseline', 'optimistic') (기본값: 'baseline')
        """

        years_to_retirement = retirement_age - current_age

        if years_to_retirement <= 0:
            return {
                'error': '현재 나이가 목표 은퇴 나이보다 크거나 같습니다.'
            }

        # 목표: 필요 은퇴자산의 110%
        target_assets = required_retirement_assets * 1.1

        # 인플레이션율 가져오기 (중앙설정모듈 사용)
        inflation_rate = KOR_2025.ECON.__dict__[scenario_type]['inflation_rate']

        # 위험성향에 따른 명목 수익률 (연간) - 중앙설정모듈 사용
        nominal_returns = {
            'conservative': KOR_2025.RISK_ALLOC.allocations['conservative']['expected_return'],
            'moderate': KOR_2025.RISK_ALLOC.allocations['moderate']['expected_return'],
            'aggressive': KOR_2025.RISK_ALLOC.allocations['aggressive']['expected_return']
        }

        # 실질 수익률 계산 (명목 수익률 - 인플레이션)
        real_returns = {
            risk_level: nominal_return - inflation_rate
            for risk_level, nominal_return in nominal_returns.items()
        }

        # 각 시나리오별로 미래 자산 계산
        scenarios = {}
        for risk_level, real_return in real_returns.items():
            nominal_return = nominal_returns[risk_level]

            # 현재 자산의 미래 가치 계산 (명목 수익률 사용)
            future_value_current = current_assets * ((1 + nominal_return) ** years_to_retirement)

            # 월 투자금의 미래 가치 계산 (연금의 미래가치 공식, 명목 수익률 사용)
            if monthly_investment > 0:
                monthly_rate = nominal_return / 12
                months = years_to_retirement * 12
                future_value_monthly = monthly_investment * (((1 + monthly_rate) ** months - 1) / monthly_rate)
            else:
                future_value_monthly = 0

            total_future_value = future_value_current + future_value_monthly

            # 인플레이션을 고려한 실질 구매력 계산
            real_purchasing_power = total_future_value / ((1 + inflation_rate) ** years_to_retirement)

            # 목표 달성률 계산 (명목 가치 기준)
            achievement_rate = (total_future_value / target_assets) * 100

            # 실질 구매력 기준 목표 달성률
            real_achievement_rate = (real_purchasing_power / required_retirement_assets) * 100

            scenarios[risk_level] = {
                'nominal_annual_return': round(nominal_return * 100, 1),
                'real_annual_return': round(real_return * 100, 1),
                'inflation_rate': round(inflation_rate * 100, 1),
                'future_value_current_assets': round(future_value_current),
                'future_value_monthly_investment': round(future_value_monthly),
                'total_expected_assets_nominal': round(total_future_value),
                'total_expected_assets_real': round(real_purchasing_power),
                'target_assets': round(target_assets),
                'achievement_rate_nominal': round(achievement_rate, 1),
                'achievement_rate_real': round(real_achievement_rate, 1),
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
            moderate_return = nominal_returns['moderate']
            monthly_rate = moderate_return / 12
            months = years_to_retirement * 12
            future_value_current = current_assets * ((1 + moderate_return) ** years_to_retirement)

            # 필요한 추가 자산
            needed_from_monthly = target_assets - future_value_current

            if needed_from_monthly > 0:
                # 연금의 미래가치 공식을 역으로 계산
                required_additional_monthly = needed_from_monthly * monthly_rate / (((1 + monthly_rate) ** months - 1))

        # 시각화 추가
        visual_output = VisualFormatter.format_scenario_comparison(scenarios)

        # ========== KRX 실시간 데이터 자동 통합 ==========
        market_overview = self.get_market_overview()
        investor_trading = self.get_investor_trading()

        # 추천 전략에 맞는 ETF 추천
        irp_etfs = self.get_etf_recommendations('IRP')
        isa_etfs = self.get_etf_recommendations('ISA')
        general_stocks = self.get_etf_recommendations('GENERAL')

        return {
            'financial_status': {
                'current_age': current_age,
                'retirement_age': retirement_age,
                'years_to_retirement': years_to_retirement,
                'current_assets': current_assets,
                'monthly_investment': monthly_investment,
                'required_retirement_assets': required_retirement_assets,
                'target_assets_110': round(target_assets),
                'economic_scenario': scenario_type,
                'inflation_rate': round(inflation_rate * 100, 1)
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
                    required_additional_monthly,
                    inflation_rate
                )
            },
            'visual_summary': visual_output,
            # KRX 실시간 데이터
            'market_data': {
                'market_overview': market_overview,
                'investor_trading': investor_trading,
            },
            'etf_recommendations': {
                'IRP': irp_etfs,
                'ISA': isa_etfs,
                'GENERAL': general_stocks,
            }
        }

    def _generate_achievement_message(self, scenarios: dict, recommended_strategy: str,
                                     current_age: int, retirement_age: int,
                                     current_assets: float, target_assets: float,
                                     required_additional_monthly: float,
                                     inflation_rate: float) -> str:
        """목표 달성 메시지 생성 (인플레이션 반영)"""

        if recommended_strategy:
            scenario = scenarios[recommended_strategy]
            return f"""
재무 현황

현재 나이: {current_age}세 → 목표 은퇴 나이: {retirement_age}세 ({retirement_age - current_age}년 남음)

현재 투자자산: {current_assets:,.0f}원

{retirement_age}세 예상 자산 (명목): {scenario['total_expected_assets_nominal']:,.0f}원
{retirement_age}세 예상 자산 (실질): {scenario['total_expected_assets_real']:,.0f}원

필요 은퇴자산: {target_assets:,.0f}원 (목표 대비 110%)

결론: 목표 대비 110% 달성 예정!

권장 전략: {recommended_strategy.title()}형 포트폴리오
- 명목 수익률: {scenario['nominal_annual_return']}% (인플레이션 {scenario['inflation_rate']}% 반영)
- 실질 수익률: {scenario['real_annual_return']}%
- 명목 달성률: {scenario['achievement_rate_nominal']}%
- 실질 달성률: {scenario['achievement_rate_real']}%
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

{retirement_age}세 예상 자산 (Aggressive, 명목): {aggressive['total_expected_assets_nominal']:,.0f}원
{retirement_age}세 예상 자산 (Aggressive, 실질): {aggressive['total_expected_assets_real']:,.0f}원

필요 은퇴자산: {target_assets:,.0f}원 (목표 대비 110%)

결론: 현재 계획으로는 목표 달성 어려움

권장 조치:
1. Aggressive형 포트폴리오 채택
   - 명목 수익률: {aggressive['nominal_annual_return']}% (인플레이션 {aggressive['inflation_rate']}% 반영)
   - 실질 수익률: {aggressive['real_annual_return']}%
   - 명목 달성률: {aggressive['achievement_rate_nominal']}%
   - 실질 달성률: {aggressive['achievement_rate_real']}%
   - 부족 금액 (명목): {target_assets - aggressive['total_expected_assets_nominal']:,.0f}원{additional_msg}

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

        # 시각화 추가
        visual_output = VisualFormatter.format_tax_comparison(
            general_account_result,
            isa_account_result,
            irp_account_result
        )

        # ========== KRX 실시간 데이터 자동 통합 ==========
        market_overview = self.get_market_overview()
        investor_trading = self.get_investor_trading()

        # 계좌별 구체적인 ETF 추천 (실시간 시세 포함)
        irp_etfs = self.get_etf_recommendations('IRP')
        isa_etfs = self.get_etf_recommendations('ISA')
        general_stocks = self.get_etf_recommendations('GENERAL')

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
            ),
            'visual_summary': visual_output,
            # KRX 실시간 데이터
            'market_data': {
                'market_overview': market_overview,
                'investor_trading': investor_trading,
            },
            'etf_recommendations': {
                'IRP': irp_etfs,
                'ISA': isa_etfs,
                'GENERAL': general_stocks,
            }
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
            'total_tax': round(total_tax, 0),
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

    # ========== KRX 데이터 서비스 메서드 ==========

    def get_market_overview(self) -> dict:
        """
        시장 전체 현황 조회 (KOSPI + KOSDAQ + 변동성)
        실시간 KRX 데이터를 기반으로 시장 상태 및 포트폴리오 조정 권장사항 제공
        """
        overview = self.krx_service.get_market_overview()

        # 시각화 추가
        visual = "\n📊 시장 현황 요약\n" + "=" * 60 + "\n"
        visual += f"KOSPI: {overview['kospi'].get('current_value', 'N/A'):,.0f} "
        visual += f"({overview['kospi'].get('change_rate_30d', 0):+.1f}% / 30일)\n"
        visual += f"KOSDAQ: {overview['kosdaq'].get('current_value', 'N/A'):,.0f} "
        visual += f"({overview['kosdaq'].get('change_rate_30d', 0):+.1f}% / 30일)\n"
        visual += "-" * 60 + "\n"
        visual += f"시장 변동성: {overview['volatility'].get('volatility_annual', 'N/A'):.1f}% (연환산)\n"
        visual += f"변동성 상태: {overview['volatility'].get('regime', 'N/A')}\n"
        visual += f"시장 판단: {overview['market_status']} - {overview['market_comment']}\n"
        visual += "-" * 60 + "\n"
        adj = overview['portfolio_recommendation']
        visual += f"포트폴리오 조정 권장:\n"
        visual += f"  주식: {adj['stocks_adjustment']:+d}%p\n"
        visual += f"  채권: {adj['bonds_adjustment']:+d}%p\n"
        visual += f"  현금: {adj['cash_adjustment']:+d}%p\n"
        visual += f"  사유: {adj['reason']}\n"

        overview['visual_summary'] = visual
        return overview

    def get_market_volatility(self, days: int = 60) -> dict:
        """
        시장 변동성 조회 (KOSPI 기준)

        Args:
            days: 계산 기간 (기본 60일)

        Returns:
            변동성 데이터 및 포트폴리오 조정 권장사항
        """
        volatility = self.krx_service.get_market_volatility(days)

        # 시각화 추가
        visual = "\n📉 시장 변동성 분석\n" + "=" * 60 + "\n"
        visual += f"연환산 변동성: {volatility.get('volatility_annual', 'N/A'):.2f}%\n"
        visual += f"일간 변동성: {volatility.get('volatility_daily', 'N/A'):.4f}%\n"
        visual += f"최근 20일 변동성: {volatility.get('recent_20d_volatility', 'N/A'):.2f}%\n"
        visual += f"변동성 추세: {volatility.get('volatility_trend', 'N/A')}\n"
        visual += "-" * 60 + "\n"
        visual += f"변동성 상태: {volatility.get('regime', 'N/A')}\n"
        visual += f"권장사항: {volatility.get('recommendation', 'N/A')}\n"

        volatility['visual_summary'] = visual
        return volatility

    def get_etf_recommendations(self, account_type: str, asset_class: str = None,
                                 sort_by: str = 'score', min_return: float = None,
                                 top_n: int = None) -> dict:
        """
        계좌 유형별 ETF 추천 (기본 추천 + 실시간 스크리닝 통합)

        Args:
            account_type: 'IRP', 'ISA', 'GENERAL'
            asset_class: 자산군 (선택) - '해외주식', '채권', '리츠', '금', '고배당', '대형주'
            sort_by: 정렬 기준 - 'score'(추천점수), 'return_1y'(1년수익률), 'volatility'(변동성), 'sharpe_ratio'(샤프비율)
            min_return: 최소 1년 수익률 필터 (%) - 예: 5.0 이면 5% 이상만 추천
            top_n: 상위 N개만 추천 (기본: 전체)

        Returns:
            기본 추천 + 실시간 스크리닝 통합 ETF 리스트
        """
        recommendations = self.krx_service.get_etf_recommendations_by_account(
            account_type, asset_class, sort_by, min_return, top_n
        )

        # 시각화 추가
        account_names = {'IRP': 'IRP/연금저축', 'ISA': 'ISA', 'GENERAL': '일반계좌'}
        visual = f"\n🎯 {account_names.get(account_type, account_type)} 추천 ETF/종목\n"
        visual += "=" * 70 + "\n"

        # 추천 기준 설명
        sort_labels = {
            'score': '종합 추천점수',
            'return_1y': '1년 수익률',
            'volatility': '변동성(낮은순)',
            'sharpe_ratio': '샤프비율(위험조정수익)'
        }
        visual += f"📊 정렬 기준: {sort_labels.get(sort_by, sort_by)}\n"
        visual += "💡 기본 추천(세금최적화) + 실시간 스크리닝 통합\n"
        if min_return is not None:
            visual += f"📉 최소 수익률 필터: {min_return}% 이상\n"
        visual += "-" * 70 + "\n"

        if asset_class:
            visual += f"자산군: {asset_class}\n"
            visual += "-" * 70 + "\n"

        if not recommendations:
            visual += "⚠️ 조건에 맞는 추천 종목이 없습니다.\n"
        else:
            # 소스별 카운트
            curated_count = sum(1 for e in recommendations if e.get('source') == 'curated')
            screening_count = sum(1 for e in recommendations if e.get('source') == 'screening')
            visual += f"📋 기본추천: {curated_count}개 | 🔍 스크리닝: {screening_count}개\n"
            visual += "-" * 70 + "\n"

            for i, etf in enumerate(recommendations, 1):
                # 순위 표시 (상위 3개는 메달)
                rank_emoji = {1: '🥇', 2: '🥈', 3: '🥉'}.get(i, f'{i}.')
                # 소스 표시
                source_tag = '📋' if etf.get('source') == 'curated' else '🔍'
                visual += f"{rank_emoji} {source_tag} {etf['name']} ({etf['ticker']})\n"
                visual += f"   유형: {etf.get('type', 'ETF')}\n"

                # 실시간 시세 정보
                if etf.get('current_price'):
                    visual += f"   💰 현재가: {etf['current_price']:,.0f}원\n"

                # 수익률 정보
                if etf.get('return_1y') is not None:
                    return_emoji = '📈' if etf['return_1y'] > 0 else '📉'
                    visual += f"   {return_emoji} 1년 수익률: {etf['return_1y']:+.1f}%\n"

                if etf.get('return_1m') is not None:
                    momentum_emoji = '🔥' if etf['return_1m'] > 3 else ('📊' if etf['return_1m'] > 0 else '❄️')
                    visual += f"   {momentum_emoji} 최근 1개월: {etf['return_1m']:+.1f}%\n"

                # 위험 지표
                if etf.get('volatility'):
                    vol_level = '낮음' if etf['volatility'] < 15 else ('보통' if etf['volatility'] < 25 else '높음')
                    visual += f"   📊 변동성: {etf['volatility']:.1f}% ({vol_level})\n"

                if etf.get('sharpe_ratio') is not None:
                    sr_quality = '우수' if etf['sharpe_ratio'] > 0.5 else ('양호' if etf['sharpe_ratio'] > 0 else '부진')
                    visual += f"   ⚖️ 샤프비율: {etf['sharpe_ratio']:.2f} ({sr_quality})\n"

                # 추천 점수 및 이유
                if etf.get('recommendation_score', 0) > 0:
                    score_bar_len = int(etf['recommendation_score'] / 5)
                    score_bar = '█' * score_bar_len + '░' * (20 - score_bar_len)
                    visual += f"   ⭐ 추천점수: [{score_bar}] {etf['recommendation_score']:.0f}/100\n"

                if etf.get('recommendation_reason'):
                    visual += f"   💡 {etf['recommendation_reason']}\n"

                visual += "\n"

            # 요약 통계
            valid_returns = [e['return_1y'] for e in recommendations if e.get('return_1y') is not None]
            if valid_returns:
                visual += "-" * 70 + "\n"
                visual += f"📈 평균 1년 수익률: {sum(valid_returns)/len(valid_returns):+.1f}%\n"
                visual += f"📊 최고 수익률: {max(valid_returns):+.1f}% | 최저: {min(valid_returns):+.1f}%\n"

        # 데이터 출처 표시
        visual += "\n" + "-" * 70 + "\n"
        visual += "📋 = 세금최적화 기본추천 | 🔍 = 실시간 스크리닝 발굴\n"
        if PYKRX_AVAILABLE:
            visual += "📡 데이터 출처: KRX (pykrx 실시간)\n"
        else:
            visual += "⚠️ pykrx 미설치 - 실시간 데이터 없음 (pip install pykrx)\n"

        return {
            'account_type': account_type,
            'asset_class': asset_class,
            'sort_by': sort_by,
            'min_return_filter': min_return,
            'top_n': top_n,
            'total_recommendations': len(recommendations),
            'recommendations': recommendations,
            'pykrx_available': PYKRX_AVAILABLE,
            'visual_summary': visual
        }

    def get_stock_price(self, ticker: str, days: int = 30) -> dict:
        """
        개별 종목/ETF 시세 조회

        Args:
            ticker: 종목코드 (예: '005930' 삼성전자)
            days: 조회 기간 (기본 30일)

        Returns:
            종목 시세 정보
        """
        result = self.krx_service.get_stock_price(ticker, days)

        if 'error' in result:
            return result

        # 시각화 추가
        visual = f"\n📈 {result['name']} ({result['ticker']}) 시세 정보\n"
        visual += "=" * 60 + "\n"
        visual += f"현재가: {result['current_price']:,}원\n"
        visual += f"등락률({days}일): {result['change_rate']:+.2f}%\n"
        visual += f"최고가({days}일): {result['high']:,}원\n"
        visual += f"최저가({days}일): {result['low']:,}원\n"
        visual += f"평균 거래량: {result['avg_volume']:,}주\n"
        visual += f"기준일: {result['data_date']}\n"

        result['visual_summary'] = visual
        return result

    def get_investor_trading(self, days: int = 5) -> dict:
        """
        투자자별 매매 동향 조회

        Args:
            days: 조회 기간 (기본 5일)

        Returns:
            외국인/기관/개인 순매수 현황
        """
        result = self.krx_service.get_investor_trading(days)

        if 'error' in result:
            return result

        # 시각화 추가
        visual = "\n👥 투자자별 매매 동향\n" + "=" * 60 + "\n"
        visual += f"조회 기간: 최근 {result['period_days']}일\n"
        visual += "-" * 60 + "\n"
        visual += f"외국인 순매수: {result['foreign_net_buy']:+,}원\n"
        visual += f"기관 순매수:   {result['institution_net_buy']:+,}원\n"
        visual += f"개인 순매수:   {result['retail_net_buy']:+,}원\n"
        visual += "-" * 60 + "\n"
        visual += f"시장 센티먼트: {result['sentiment']}\n"
        visual += f"분석: {result['comment']}\n"

        result['visual_summary'] = visual
        return result

    def get_top_stocks_by_market_cap(self, market: str = 'ALL', top_n: int = 20,
                                      include_performance: bool = True) -> dict:
        """
        시가총액 상위 종목 자동 추천 (실시간 KRX 데이터 기반)

        Args:
            market: 'KOSPI', 'KOSDAQ', 'ALL'
            top_n: 상위 N개 종목
            include_performance: 수익률/변동성 정보 포함

        Returns:
            시가총액 상위 종목 리스트
        """
        recommendations = self.krx_service.get_top_stocks_by_market_cap(
            market, top_n, include_performance
        )

        # 에러 체크
        if recommendations and 'error' in recommendations[0]:
            return {'error': recommendations[0]['error']}

        # 시각화 추가
        market_labels = {'KOSPI': 'KOSPI', 'KOSDAQ': 'KOSDAQ', 'ALL': 'KOSPI+KOSDAQ'}
        visual = f"\n🏆 {market_labels.get(market, market)} 시가총액 상위 {top_n}개 종목\n"
        visual += "=" * 80 + "\n"
        visual += "📊 실시간 KRX 데이터 기반 (하드코딩 아님)\n"
        visual += "-" * 80 + "\n"

        for i, stock in enumerate(recommendations, 1):
            rank_emoji = {1: '🥇', 2: '🥈', 3: '🥉'}.get(i, f'{i}.')
            visual += f"{rank_emoji} {stock['name']} ({stock['ticker']}) - {stock['market']}\n"
            visual += f"   💰 현재가: {stock['current_price']:,}원\n"
            visual += f"   📊 시가총액: {stock['market_cap_billion']:.1f}조원\n"

            if stock.get('return_1y') is not None:
                return_emoji = '📈' if stock['return_1y'] > 0 else '📉'
                visual += f"   {return_emoji} 1년 수익률: {stock['return_1y']:+.1f}%\n"

            if stock.get('return_1m') is not None:
                momentum_emoji = '🔥' if stock['return_1m'] > 3 else ('📊' if stock['return_1m'] > 0 else '❄️')
                visual += f"   {momentum_emoji} 최근 1개월: {stock['return_1m']:+.1f}%\n"

            if stock.get('volatility'):
                vol_level = '낮음' if stock['volatility'] < 25 else ('보통' if stock['volatility'] < 35 else '높음')
                visual += f"   📉 변동성: {stock['volatility']:.1f}% ({vol_level})\n"

            if stock.get('recommendation_score', 0) > 0:
                score_bar_len = int(stock['recommendation_score'] / 5)
                score_bar = '█' * score_bar_len + '░' * (20 - score_bar_len)
                visual += f"   ⭐ 추천점수: [{score_bar}] {stock['recommendation_score']:.0f}/100\n"

            if stock.get('recommendation_reason'):
                visual += f"   💡 {stock['recommendation_reason']}\n"

            visual += "\n"

        # 요약 통계
        valid_returns = [s['return_1y'] for s in recommendations if s.get('return_1y') is not None]
        if valid_returns:
            visual += "-" * 80 + "\n"
            visual += f"📈 평균 1년 수익률: {sum(valid_returns)/len(valid_returns):+.1f}%\n"
            total_market_cap = sum(s['market_cap_billion'] for s in recommendations)
            visual += f"📊 총 시가총액: {total_market_cap:.1f}조원\n"

        visual += "\n" + "-" * 80 + "\n"
        visual += "📡 데이터 출처: KRX (pykrx 실시간)\n"

        return {
            'market': market,
            'top_n': top_n,
            'total_recommendations': len(recommendations),
            'recommendations': recommendations,
            'pykrx_available': PYKRX_AVAILABLE,
            'visual_summary': visual
        }

    def get_top_etfs_by_performance(self, top_n: int = 20, min_volume: int = 10000,
                                     sort_by: str = 'return_1y') -> dict:
        """
        전체 ETF 중 수익률 상위 종목 자동 스크리닝 (하드코딩 아님)

        Args:
            top_n: 상위 N개 ETF
            min_volume: 최소 일평균 거래량 (유동성 필터)
            sort_by: 정렬 기준 ('return_1y', 'return_1m', 'sharpe_ratio')

        Returns:
            수익률 상위 ETF 리스트
        """
        recommendations = self.krx_service.get_top_etfs_by_performance(
            top_n, min_volume, sort_by
        )

        # 에러 체크
        if recommendations and 'error' in recommendations[0]:
            return {'error': recommendations[0]['error']}

        # 시각화 추가
        sort_labels = {
            'return_1y': '1년 수익률',
            'return_1m': '1개월 수익률',
            'sharpe_ratio': '샤프비율(위험조정수익)'
        }
        visual = f"\n🎯 전체 ETF 수익률 상위 {top_n}개 (자동 스크리닝)\n"
        visual += "=" * 80 + "\n"
        visual += f"📊 정렬 기준: {sort_labels.get(sort_by, sort_by)}\n"
        visual += f"📉 최소 거래량: {min_volume:,}주 이상\n"
        visual += "💡 하드코딩 아님 - KRX 전체 ETF 실시간 스캔\n"
        visual += "-" * 80 + "\n"

        for i, etf in enumerate(recommendations, 1):
            rank_emoji = {1: '🥇', 2: '🥈', 3: '🥉'}.get(i, f'{i}.')
            visual += f"{rank_emoji} {etf['name']} ({etf['ticker']})\n"

            if etf.get('current_price'):
                visual += f"   💰 현재가: {etf['current_price']:,.0f}원\n"

            if etf.get('return_1y') is not None:
                return_emoji = '📈' if etf['return_1y'] > 0 else '📉'
                visual += f"   {return_emoji} 1년 수익률: {etf['return_1y']:+.1f}%\n"

            if etf.get('return_1m') is not None:
                momentum_emoji = '🔥' if etf['return_1m'] > 3 else ('📊' if etf['return_1m'] > 0 else '❄️')
                visual += f"   {momentum_emoji} 최근 1개월: {etf['return_1m']:+.1f}%\n"

            if etf.get('volatility'):
                vol_level = '낮음' if etf['volatility'] < 15 else ('보통' if etf['volatility'] < 25 else '높음')
                visual += f"   📊 변동성: {etf['volatility']:.1f}% ({vol_level})\n"

            if etf.get('sharpe_ratio') is not None:
                sr_quality = '우수' if etf['sharpe_ratio'] > 0.5 else ('양호' if etf['sharpe_ratio'] > 0 else '부진')
                visual += f"   ⚖️ 샤프비율: {etf['sharpe_ratio']:.2f} ({sr_quality})\n"

            if etf.get('avg_volume'):
                visual += f"   📊 일평균거래량: {etf['avg_volume']:,}주\n"

            if etf.get('recommendation_score', 0) > 0:
                score_bar_len = int(etf['recommendation_score'] / 5)
                score_bar = '█' * score_bar_len + '░' * (20 - score_bar_len)
                visual += f"   ⭐ 추천점수: [{score_bar}] {etf['recommendation_score']:.0f}/100\n"

            if etf.get('recommendation_reason'):
                visual += f"   💡 {etf['recommendation_reason']}\n"

            visual += "\n"

        # 요약 통계
        valid_returns = [e['return_1y'] for e in recommendations if e.get('return_1y') is not None]
        if valid_returns:
            visual += "-" * 80 + "\n"
            visual += f"📈 평균 1년 수익률: {sum(valid_returns)/len(valid_returns):+.1f}%\n"
            visual += f"📊 최고 수익률: {max(valid_returns):+.1f}% | 최저: {min(valid_returns):+.1f}%\n"

        visual += "\n" + "-" * 80 + "\n"
        visual += "📡 데이터 출처: KRX 전체 ETF 실시간 스캔 (pykrx)\n"

        return {
            'sort_by': sort_by,
            'min_volume': min_volume,
            'top_n': top_n,
            'total_recommendations': len(recommendations),
            'recommendations': recommendations,
            'pykrx_available': PYKRX_AVAILABLE,
            'visual_summary': visual
        }

    def adjust_portfolio_with_realtime_volatility(self, base_portfolio: dict) -> dict:
        """
        실시간 변동성 기반 포트폴리오 조정 (KRX 데이터 활용)

        Args:
            base_portfolio: 기본 포트폴리오 (asset_allocation 포함)

        Returns:
            변동성 조정된 포트폴리오
        """
        # 실시간 변동성 조회
        volatility_data = self.krx_service.get_market_volatility()

        # 기존 변동성 조정 로직 호출
        market_volatility_data = {
            'current_volatility': volatility_data.get('volatility_annual', 22.0),
            'historical_average': 22.0  # 하드코딩된 평균값
        }

        return self.adjust_portfolio_volatility(base_portfolio, market_volatility_data)


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
                description="은퇴 목표 달성 여부 계산 및 110% 목표 달성 투자 방법 제시 (인플레이션 반영)",
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
                        },
                        "scenario_type": {
                            "type": "string",
                            "description": "경제 시나리오 ('pessimistic', 'baseline', 'optimistic', 옵션, 기본값: 'baseline')",
                            "enum": ["pessimistic", "baseline", "optimistic"],
                            "default": "baseline"
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
            ),
            # ========== KRX 데이터 도구 ==========
            Tool(
                name=ToojaTools.GET_MARKET_OVERVIEW.value,
                description="📊 시장 전체 현황 조회 - KOSPI/KOSDAQ 지수, 변동성, 시장 상태 및 포트폴리오 조정 권장사항 (pykrx 사용)",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name=ToojaTools.GET_MARKET_VOLATILITY.value,
                description="📉 시장 변동성 조회 - KOSPI 기준 연환산 변동성 계산, 변동성 상태(HIGH/NORMAL/LOW) 판단 및 포트폴리오 조정 권장 (pykrx 사용)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "number",
                            "description": "변동성 계산 기간 (일, 기본값: 60)",
                            "default": 60
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name=ToojaTools.GET_ETF_RECOMMENDATIONS.value,
                description="🎯 계좌 유형별 ETF/종목 추천 - 세금최적화 기본추천 + 실시간 스크리닝 통합. IRP(해외ETF, 채권), ISA(고배당), 일반계좌(국내주식) 최적 상품을 수익률/변동성/샤프비율 기준으로 정렬. 📋기본추천 + 🔍실시간발굴 통합 (pykrx)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "account_type": {
                            "type": "string",
                            "description": "계좌 유형: 'IRP', 'ISA', 'GENERAL'",
                            "enum": ["IRP", "ISA", "GENERAL"]
                        },
                        "asset_class": {
                            "type": "string",
                            "description": "자산군 (선택): IRP-'해외주식','채권','리츠','금' / ISA-'고배당' / GENERAL-'대형주'"
                        },
                        "sort_by": {
                            "type": "string",
                            "description": "정렬 기준: 'score'(종합추천점수), 'return_1y'(1년수익률순), 'volatility'(낮은변동성순), 'sharpe_ratio'(샤프비율순)",
                            "enum": ["score", "return_1y", "volatility", "sharpe_ratio"],
                            "default": "score"
                        },
                        "min_return": {
                            "type": "number",
                            "description": "최소 1년 수익률 필터 (%) - 예: 5.0 입력 시 5% 이상 수익률 종목만 추천"
                        },
                        "top_n": {
                            "type": "number",
                            "description": "상위 N개 종목만 추천 (기본: 전체)"
                        }
                    },
                    "required": ["account_type"]
                }
            ),
            Tool(
                name=ToojaTools.GET_STOCK_PRICE.value,
                description="📈 개별 종목/ETF 시세 조회 - 종목코드로 현재가, 등락률, 거래량 등 조회 (pykrx 사용)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "종목코드 (예: '005930' 삼성전자, '379800' KODEX 미국S&P500TR)"
                        },
                        "days": {
                            "type": "number",
                            "description": "조회 기간 (일, 기본값: 30)",
                            "default": 30
                        }
                    },
                    "required": ["ticker"]
                }
            ),
            Tool(
                name=ToojaTools.GET_INVESTOR_TRADING.value,
                description="👥 투자자별 매매 동향 - 외국인/기관/개인 순매수 현황 및 시장 센티먼트 분석 (pykrx 사용)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "number",
                            "description": "조회 기간 (일, 기본값: 5)",
                            "default": 5
                        }
                    },
                    "required": []
                }
            ),
            # ========== 신규: 실시간 시장 스크리닝 도구 ==========
            Tool(
                name=ToojaTools.GET_TOP_STOCKS_BY_MARKET_CAP.value,
                description="🏆 시가총액 상위 종목 자동 추천 - KRX 전체 종목 실시간 스캔. 하드코딩 아님! KOSPI/KOSDAQ 시총 상위 종목을 1년 수익률/변동성과 함께 자동 추천 (pykrx 실시간)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "market": {
                            "type": "string",
                            "description": "시장: 'KOSPI', 'KOSDAQ', 'ALL'(전체)",
                            "enum": ["KOSPI", "KOSDAQ", "ALL"],
                            "default": "ALL"
                        },
                        "top_n": {
                            "type": "number",
                            "description": "상위 N개 종목 (기본: 20)",
                            "default": 20
                        },
                        "include_performance": {
                            "type": "boolean",
                            "description": "수익률/변동성 정보 포함 여부 (기본: true)",
                            "default": True
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name=ToojaTools.GET_TOP_ETFS_BY_PERFORMANCE.value,
                description="🎯 전체 ETF 수익률 상위 자동 스크리닝 - KRX 전체 ETF 실시간 스캔! 하드코딩 아님! 1년/1개월 수익률, 샤프비율 기준 상위 ETF 자동 발굴 (pykrx 실시간)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "top_n": {
                            "type": "number",
                            "description": "상위 N개 ETF (기본: 20)",
                            "default": 20
                        },
                        "min_volume": {
                            "type": "number",
                            "description": "최소 일평균 거래량 - 유동성 필터 (기본: 10000)",
                            "default": 10000
                        },
                        "sort_by": {
                            "type": "string",
                            "description": "정렬 기준: 'return_1y'(1년수익률), 'return_1m'(1개월수익률), 'sharpe_ratio'(샤프비율)",
                            "enum": ["return_1y", "return_1m", "sharpe_ratio"],
                            "default": "return_1y"
                        }
                    },
                    "required": []
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
                        arguments.get('monthly_investment', 0),
                        arguments.get('scenario_type', 'baseline')
                    )

                case ToojaTools.COMPARE_TAX_EFFICIENCY.value:
                    result = service.compare_tax_efficiency_across_accounts(
                        arguments['investment_period_years'],
                        arguments['monthly_investment'],
                        arguments['asset_allocation'],
                        arguments.get('expected_returns', None)
                    )

                # ========== KRX 데이터 도구 핸들러 ==========
                case ToojaTools.GET_MARKET_OVERVIEW.value:
                    result = service.get_market_overview()

                case ToojaTools.GET_MARKET_VOLATILITY.value:
                    result = service.get_market_volatility(
                        arguments.get('days', 60)
                    )

                case ToojaTools.GET_ETF_RECOMMENDATIONS.value:
                    result = service.get_etf_recommendations(
                        arguments['account_type'],
                        arguments.get('asset_class', None),
                        arguments.get('sort_by', 'score'),
                        arguments.get('min_return', None),
                        arguments.get('top_n', None)
                    )

                case ToojaTools.GET_STOCK_PRICE.value:
                    result = service.get_stock_price(
                        arguments['ticker'],
                        arguments.get('days', 30)
                    )

                case ToojaTools.GET_INVESTOR_TRADING.value:
                    result = service.get_investor_trading(
                        arguments.get('days', 5)
                    )

                # ========== 신규: 실시간 시장 스크리닝 도구 핸들러 ==========
                case ToojaTools.GET_TOP_STOCKS_BY_MARKET_CAP.value:
                    result = service.get_top_stocks_by_market_cap(
                        arguments.get('market', 'ALL'),
                        arguments.get('top_n', 20),
                        arguments.get('include_performance', True)
                    )

                case ToojaTools.GET_TOP_ETFS_BY_PERFORMANCE.value:
                    result = service.get_top_etfs_by_performance(
                        arguments.get('top_n', 20),
                        arguments.get('min_volume', 10000),
                        arguments.get('sort_by', 'return_1y')
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
