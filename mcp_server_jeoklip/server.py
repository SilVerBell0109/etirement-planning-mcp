from datetime import datetime
from enum import Enum
import json
from typing import Sequence
import numpy as np  # type: ignore
import csv
import os
import sys
from pathlib import Path

# 중앙 설정 모듈 import
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
from financial_constants_2025 import KOR_2025

from mcp.server import Server  # type: ignore
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.shared.exceptions import McpError

from pydantic import BaseModel


class JeoklipTools(str, Enum):
    COLLECT_USER_INFO = "collect_user_info"
    GENERATE_SCENARIOS = "generate_economic_scenarios"
    CALCULATE_RETIREMENT_CAPITAL = "calculate_retirement_capital"
    PROJECT_ASSETS = "project_retirement_assets"
    ANALYZE_GAP = "analyze_funding_gap"
    OPTIMIZE_SAVINGS = "optimize_savings_plan"


# ========== 데이터 모델 ==========

class UserProfile(BaseModel):
    current_age: int
    target_retirement_age: int
    life_expectancy: int
    monthly_income: float
    monthly_expense: float


class AssetPortfolio(BaseModel):
    cash_savings: float
    funds_etf: float
    pension_account: float
    real_estate: float


class EconomicScenario(BaseModel):
    scenario_type: str  # conservative, moderate, aggressive
    inflation_rate: float
    pre_retirement_return: float
    post_retirement_return: float
    wage_growth_rate: float


class RetirementCapital(BaseModel):
    safe_withdrawal_method: float
    present_value_method: float
    recommended_range: dict


class AssetProjection(BaseModel):
    total_projected_assets: float
    breakdown: dict


class FundingGap(BaseModel):
    required_capital: float
    projected_assets: float
    gap_amount: float
    gap_percentage: float


class SavingsPlan(BaseModel):
    monthly_savings_needed: float
    annual_savings_needed: float
    feasibility_score: float
    recommendations: list


# ========== 금융 계산 엔진 ==========

class FinancialCalculator:

    @staticmethod
    def calculate_present_value(future_value: float, rate: float, periods: int) -> float:
        """미래가치의 현재가치 계산"""
        return future_value / ((1 + rate) ** periods)

    @staticmethod
    def calculate_future_value(present_value: float, rate: float, periods: int) -> float:
        """현재가치의 미래가치 계산"""
        return present_value * ((1 + rate) ** periods)

    @staticmethod
    def calculate_annuity_pv(payment: float, rate: float, periods: int) -> float:
        """연금의 현재가치 계산"""
        if rate == 0:
            return payment * periods
        return payment * (1 - (1 + rate) ** -periods) / rate

    @staticmethod
    def calculate_pmt(present_value: float, rate: float, periods: int) -> float:
        """정기 지급액 계산 (PMT)"""
        if rate == 0:
            return present_value / periods
        return present_value * rate / (1 - (1 + rate) ** -periods)

    @staticmethod
    def adjust_for_inflation(amount: float, inflation_rate: float, years: int) -> float:
        """인플레이션 조정"""
        return amount / ((1 + inflation_rate) ** years)


# ========== 적립메이트 서비스 로직 ==========

class JeoklipService:

    def __init__(self):
        self.calculator = FinancialCalculator()
        self.user_data = {}
        # CSV 저장 경로 설정
        self.csv_dir = Path(__file__).parent
        self.csv_dir.mkdir(parents=True, exist_ok=True)

    # ========== CSV 저장 기능 (신규 추가) ==========
    
    def _save_to_csv(self, user_profile: dict, income_structure: dict,
                     expense_categories: dict, asset_portfolio: dict) -> str:
        """사용자 정보를 CSV 파일로 저장"""
        
        # 타임스탬프로 파일명 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'user_info_{timestamp}.csv'
        filepath = self.csv_dir / filename
        
        # CSV 데이터 준비
        csv_data = []
        
        # 헤더 및 사용자 프로필 데이터
        csv_data.append(['수집 시각', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        csv_data.append([''])  # 빈 줄
        
        # 사용자 프로필
        csv_data.append(['=== 사용자 프로필 ===', ''])
        for key, value in user_profile.items():
            csv_data.append([key, value])
        csv_data.append([''])  # 빈 줄
        
        # 소득 구조
        csv_data.append(['=== 소득 구조 ===', ''])
        for key, value in income_structure.items():
            csv_data.append([key, value])
        csv_data.append([''])  # 빈 줄
        
        # 지출 항목
        csv_data.append(['=== 지출 항목 ===', ''])
        for key, value in expense_categories.items():
            csv_data.append([key, value])
        csv_data.append([''])  # 빈 줄
        
        # 자산 포트폴리오
        csv_data.append(['=== 자산 포트폴리오 ===', ''])
        total_assets = 0
        for key, value in asset_portfolio.items():
            csv_data.append([key, value])
            if isinstance(value, (int, float)):
                total_assets += value
        csv_data.append(['총 자산', total_assets])
        
        # CSV 파일 작성
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(csv_data)
        
        return str(filepath)
    
    # Tool 1: 정보 수집
    def collect_user_info(self, user_profile: dict, income_structure: dict,
                          expense_categories: dict, asset_portfolio: dict) -> dict:
        """사용자 정보 수집 및 저장"""

        self.user_data = {
            'profile': user_profile,
            'income': income_structure,
            'expense': expense_categories,
            'assets': asset_portfolio,
            'collected_at': datetime.now().isoformat()
        }
        
        # CSV 파일로 저장 (신규 추가)
        try:
            csv_filepath = self._save_to_csv(user_profile, income_structure, 
                                            expense_categories, asset_portfolio)
            csv_saved = True
            csv_message = f'CSV 파일로 저장됨: {csv_filepath}'
        except Exception as e:
            csv_saved = False
            csv_message = f'CSV 저장 실패: {str(e)}'

        return {
            'status': 'success',
            'message': '사용자 정보가 성공적으로 수집되었습니다.',
            'csv_saved': csv_saved,
            'csv_message': csv_message,
            'summary': {
                '현재나이': user_profile.get('current_age'),
                '목표은퇴나이': user_profile.get('target_retirement_age'),
                '월소득': income_structure.get('monthly_income'),
                '월지출': expense_categories.get('total_monthly_expense'),
                '총자산': sum(asset_portfolio.values())
            }
        }

    # Tool 2: 경제 시나리오 생성 (한국 특화)
    def generate_economic_scenarios(self) -> dict:
        """한국 경제 시나리오 생성 (중앙 설정 기반)"""

        # 한국 시장 변동성 반영
        scenarios = {
            'pessimistic': {
                'scenario_name': '보수 시나리오',
                'inflation_rate': KOR_2025.ECON.pessimistic['inflation_rate'],
                'pre_retirement_return': KOR_2025.ECON.pessimistic['pre_ret'],
                'post_retirement_return': KOR_2025.ECON.pessimistic['post_ret'],
                'wage_growth_rate': KOR_2025.ECON.pessimistic['wage'],
                'real_return': KOR_2025.ECON.pessimistic['real_ret'],
                'probability': KOR_2025.ECON.pessimistic['p'],
                'description': '안정적이지만 보수적인 가정 (한국 시장 특성 반영)'
            },
            'baseline': {
                'scenario_name': '기준 시나리오',
                'inflation_rate': KOR_2025.ECON.baseline['inflation_rate'],
                'pre_retirement_return': KOR_2025.ECON.baseline['pre_ret'],
                'post_retirement_return': KOR_2025.ECON.baseline['post_ret'],
                'wage_growth_rate': KOR_2025.ECON.baseline['wage'],
                'real_return': KOR_2025.ECON.baseline['real_ret'],
                'probability': KOR_2025.ECON.baseline['p'],
                'description': '균형잡힌 중도적 가정 (한국 시장 특성 반영)'
            },
            'optimistic': {
                'scenario_name': '공격 시나리오',
                'inflation_rate': KOR_2025.ECON.optimistic['inflation_rate'],
                'pre_retirement_return': KOR_2025.ECON.optimistic['pre_ret'],
                'post_retirement_return': KOR_2025.ECON.optimistic['post_ret'],
                'wage_growth_rate': KOR_2025.ECON.optimistic['wage'],
                'real_return': KOR_2025.ECON.optimistic['real_ret'],
                'probability': KOR_2025.ECON.optimistic['p'],
                'description': '낙관적이고 적극적인 가정 (한국 시장 특성 반영)'
            }
        }

        return {
            'scenarios': scenarios,
            'market_characteristics': {
                'kospi_volatility': KOR_2025.MKT.kospi_volatility,
                'bond_volatility': KOR_2025.MKT.bond_volatility,
                'domestic_equity_ratio': KOR_2025.MKT.domestic_equity_ratio,
                'foreign_equity_ratio': KOR_2025.MKT.foreign_equity_ratio
            },
            'recommendation': 'baseline',
            'note': '한국 시장 특성을 반영한 시나리오입니다. 본인의 위험 성향과 시장 전망에 따라 선택하세요.'
        }

    # Tool 3: 필요 은퇴자본 계산 (한국 특화)
    def calculate_retirement_capital(self, annual_expense: float,
                                     retirement_years: int,
                                     scenario: dict) -> dict:
        """한국형 필요 은퇴자본 계산 (기간별 SWR 조정)"""

        post_ret_rate = scenario.get('post_retirement_return', 0.025)

        # 한국형 SWR 범위 (기간 반영)
        swr_band = self._swr_band_kor(retirement_years)
        
        # 방법 1: 안전인출률법 (기간별 조정)
        swr_low = annual_expense / swr_band['high']
        swr_high = annual_expense / swr_band['low']
        swr_avg = annual_expense / swr_band['mid']

        # 방법 2: 연금현가법 (PV of Annuity)
        pv_method = self.calculator.calculate_annuity_pv(
            annual_expense, post_ret_rate, retirement_years
        )

        # 한국형 의료비 버킷 (연령 가중)
        medical_reserve = self._calculate_medical_reserve_kor(annual_expense, retirement_years)

        return {
            'safe_withdrawal_method': {
                '최소필요자본': round(swr_low, 0),
                '최대필요자본': round(swr_high, 0),
                '평균': round(swr_avg, 0),
                'swr_rates': {
                    'low': f"{swr_band['low']*100:.2f}%",
                    'mid': f"{swr_band['mid']*100:.2f}%", 
                    'high': f"{swr_band['high']*100:.2f}%"
                }
            },
            'present_value_method': round(pv_method, 0),
            'medical_reserve': round(medical_reserve, 0),
            'recommended_total': round((swr_avg + pv_method) / 2 + medical_reserve, 0),
            'korean_characteristics': {
                'healthcare_ratio': f"{KOR_2025.BUCK.healthcare_base_ratio*100:.1f}%",
                'medical_cost_ratio': f"{KOR_2025.KR.medical_cost_ratio*100:.1f}%",
                'national_pension_available': '국민연금 수급 가능'
            },
            'note': f'기간 {retirement_years}년에 맞춘 SWR 조정과 한국 의료비 특성을 반영했습니다.'
        }

    def _swr_band_kor(self, years: int) -> dict:
        """한국형 SWR 범위 (기간 중심 밴드)"""
        mid = KOR_2025.SWR.adjust_by_duration(years)
        return {
            'low': max(KOR_2025.SWR.min_floor, mid - 0.005),
            'mid': mid,
            'high': min(0.04, mid + 0.005)
        }

    def _calculate_medical_reserve_kor(self, annual_expense: float, retirement_years: int) -> float:
        """한국형 의료비 준비금 계산"""
        base_med = annual_expense * KOR_2025.BUCK.healthcare_base_ratio
        # 평균 연령 가중치 적용 (65-95세)
        avg_age_factor = 1.6  # 평균 가중치
        return base_med * min(30, retirement_years) * avg_age_factor

    # Tool 4: 은퇴시점 자산 프로젝션
    def project_retirement_assets(self, current_assets: dict,
                                  monthly_savings: float,
                                  years_to_retirement: int,
                                  scenario: dict) -> dict:
        """은퇴시점의 예상 자산 계산"""

        pre_ret_rate = scenario.get('pre_retirement_return', 0.040)

        projected_assets = {}

        # 현재 자산의 미래가치
        for asset_type, amount in current_assets.items():
            if asset_type != 'pension_db':  # DB형 연금은 제외
                future_value = self.calculator.calculate_future_value(
                    amount, pre_ret_rate, years_to_retirement
                )
                projected_assets[asset_type] = round(future_value, 0)

        # 월 저축의 미래가치 (연금 복리)
        if monthly_savings > 0:
            annual_savings = monthly_savings * 12
            # FV of Annuity 계산
            fv_savings = annual_savings * \
                (((1 + pre_ret_rate) ** years_to_retirement - 1) / pre_ret_rate)
            projected_assets['정기저축_누적'] = round(fv_savings, 0)

        total_projected = sum(projected_assets.values())

        return {
            'total_projected_assets': round(total_projected, 0),
            'breakdown': projected_assets,
            'assumptions': {
                '수익률': f"{pre_ret_rate * 100:.1f}%",
                '기간': f"{years_to_retirement}년"
            }
        }

    # Tool 5: 자금격차 분석
    def analyze_funding_gap(self, required_capital: float,
                            projected_assets: float) -> dict:
        """필요자본과 예상자산 비교"""

        gap = required_capital - projected_assets
        gap_pct = (gap / required_capital * 100) if required_capital > 0 else 0

        status = '충분' if gap <= 0 else '부족'

        return {
            'required_capital': round(required_capital, 0),
            'projected_assets': round(projected_assets, 0),
            'gap_amount': round(gap, 0),
            'gap_percentage': round(gap_pct, 1),
            'status': status,
            'message': f"은퇴자금이 {abs(round(gap/10000, 0))}만원 {status}합니다."
        }

    # Tool 6: 저축계획 최적화 (한국 특화)
    def optimize_savings_plan(self, funding_gap: float,
                              years_to_retirement: int,
                              current_monthly_savings: float,
                              scenario: dict) -> dict:
        """한국형 저축계획 최적화 (시나리오 가중 평가)"""

        if funding_gap <= 0:
            return {
                'status': 'sufficient',
                'message': '현재 계획으로 충분합니다.',
                'monthly_savings_needed': 0,
                'annual_savings_needed': 0
            }

        pre_ret_rate = scenario.get('pre_retirement_return', 0.040)

        # PMT 계산 (필요한 정기 저축액)
        annual_pmt = self.calculator.calculate_pmt(
            funding_gap, pre_ret_rate, years_to_retirement
        )
        monthly_pmt = annual_pmt / 12

        # 한국형 실행 가능성 점수 (시나리오 가중)
        feasibility = self._feasibility_score_kor(current_monthly_savings, monthly_pmt, scenario)

        # 한국 특화 권장사항
        recommendations = []
        if feasibility < 80:
            recommendations.append("은퇴 나이를 1-2년 늦추는 것을 고려하세요.")
            recommendations.append("목표 생활비를 10% 줄이는 것을 검토하세요.")
            recommendations.append("세제혜택 계좌(IRP, 연금저축)를 우선 활용하세요.")
            recommendations.append("주택연금 도입을 검토하세요 (한도 3억원).")
            recommendations.append("국민연금 수급 시점을 늦추는 것을 고려하세요.")

        return {
            'monthly_savings_needed': round(monthly_pmt, 0),
            'annual_savings_needed': round(annual_pmt, 0),
            'current_monthly_savings': current_monthly_savings,
            'additional_needed': round(monthly_pmt - current_monthly_savings, 0),
            'feasibility_score': round(feasibility, 1),
            'korean_alternatives': {
                '주택연금_도입시': f"월 {round(monthly_pmt * 0.3, 0):,}원 절약 가능",
                'IRP_최대활용시': f"연 {KOR_2025.KR.irp_limit:,}원까지 세제혜택",
                '연금저축_최대활용시': f"연 {KOR_2025.KR.pension_savings_limit:,}원까지 세제혜택",
                '국민연금_1년_늦춤시': f"월 {round(monthly_pmt * 0.2, 0):,}원 절약 가능"
            },
            'recommendations': recommendations,
            'alternatives': {
                '은퇴_1년_연장시': round(monthly_pmt * years_to_retirement / (years_to_retirement + 1), 0),
                '은퇴_2년_연장시': round(monthly_pmt * years_to_retirement / (years_to_retirement + 2), 0),
                '목표지출_10%감소시': round(monthly_pmt * 0.9, 0)
            }
        }

    def _feasibility_score_kor(self, current_savings: float, needed_savings: float, scenario: dict) -> float:
        """한국형 실행 가능성 점수 (시나리오 가중)"""
        if current_savings > 0:
            base_feasibility = min(100, (current_savings / needed_savings) * 100)
        else:
            base_feasibility = 0
        
        # 시나리오별 가중치 적용 (간단 버전)
        scenario_weight = scenario.get('probability', 0.5)
        adjusted_feasibility = base_feasibility * (0.5 + scenario_weight * 0.5)
        
        return min(100, adjusted_feasibility)


# ========== MCP Server 설정 ==========

async def serve() -> None:
    server = Server("mcp-jeoklip")
    service = JeoklipService()

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """적립메이트 도구 목록"""
        return [
            Tool(
                name=JeoklipTools.COLLECT_USER_INFO.value,
                description="사용자의 기본 정보를 수집합니다 (나이, 소득, 지출, 자산 등)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_profile": {
                            "type": "object",
                            "description": "나이, 은퇴목표 등 기본 정보"
                        },
                        "income_structure": {
                            "type": "object",
                            "description": "소득 구조"
                        },
                        "expense_categories": {
                            "type": "object",
                            "description": "지출 항목"
                        },
                        "asset_portfolio": {
                            "type": "object",
                            "description": "현재 보유 자산"
                        }
                    },
                    "required": ["user_profile"]
                }
            ),
            Tool(
                name=JeoklipTools.GENERATE_SCENARIOS.value,
                description="보수/기준/공격 3가지 경제 시나리오를 생성합니다",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name=JeoklipTools.CALCULATE_RETIREMENT_CAPITAL.value,
                description="필요한 은퇴자본을 계산합니다 (안전인출률법, 연금현가법)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "annual_expense": {
                            "type": "number",
                            "description": "연간 목표 지출액"
                        },
                        "retirement_years": {
                            "type": "integer",
                            "description": "은퇴 기간 (년)"
                        },
                        "scenario": {
                            "type": "object",
                            "description": "경제 시나리오"
                        }
                    },
                    "required": ["annual_expense", "retirement_years", "scenario"]
                }
            ),
            Tool(
                name=JeoklipTools.PROJECT_ASSETS.value,
                description="은퇴시점의 예상 자산을 계산합니다",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "current_assets": {
                            "type": "object",
                            "description": "현재 보유 자산"
                        },
                        "monthly_savings": {
                            "type": "number",
                            "description": "월 저축액"
                        },
                        "years_to_retirement": {
                            "type": "integer",
                            "description": "은퇴까지 남은 기간"
                        },
                        "scenario": {
                            "type": "object",
                            "description": "경제 시나리오"
                        }
                    },
                    "required": ["current_assets", "years_to_retirement", "scenario"]
                }
            ),
            Tool(
                name=JeoklipTools.ANALYZE_GAP.value,
                description="필요자본과 예상자산의 격차를 분석합니다",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "required_capital": {
                            "type": "number",
                            "description": "필요 은퇴자본"
                        },
                        "projected_assets": {
                            "type": "number",
                            "description": "예상 자산"
                        }
                    },
                    "required": ["required_capital", "projected_assets"]
                }
            ),
            Tool(
                name=JeoklipTools.OPTIMIZE_SAVINGS.value,
                description="최적의 저축 계획을 수립합니다",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "funding_gap": {
                            "type": "number",
                            "description": "자금 격차"
                        },
                        "years_to_retirement": {
                            "type": "integer",
                            "description": "은퇴까지 남은 기간"
                        },
                        "current_monthly_savings": {
                            "type": "number",
                            "description": "현재 월 저축액"
                        },
                        "scenario": {
                            "type": "object",
                            "description": "경제 시나리오"
                        }
                    },
                    "required": ["funding_gap", "years_to_retirement", "scenario"]
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
                case JeoklipTools.COLLECT_USER_INFO.value:
                    result = service.collect_user_info(
                        arguments.get('user_profile', {}),
                        arguments.get('income_structure', {}),
                        arguments.get('expense_categories', {}),
                        arguments.get('asset_portfolio', {})
                    )

                case JeoklipTools.GENERATE_SCENARIOS.value:
                    result = service.generate_economic_scenarios()

                case JeoklipTools.CALCULATE_RETIREMENT_CAPITAL.value:
                    result = service.calculate_retirement_capital(
                        arguments['annual_expense'],
                        arguments['retirement_years'],
                        arguments['scenario']
                    )

                case JeoklipTools.PROJECT_ASSETS.value:
                    result = service.project_retirement_assets(
                        arguments['current_assets'],
                        arguments.get('monthly_savings', 0),
                        arguments['years_to_retirement'],
                        arguments['scenario']
                    )

                case JeoklipTools.ANALYZE_GAP.value:
                    result = service.analyze_funding_gap(
                        arguments['required_capital'],
                        arguments['projected_assets']
                    )

                case JeoklipTools.OPTIMIZE_SAVINGS.value:
                    result = service.optimize_savings_plan(
                        arguments['funding_gap'],
                        arguments['years_to_retirement'],
                        arguments.get('current_monthly_savings', 0),
                        arguments['scenario']
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
