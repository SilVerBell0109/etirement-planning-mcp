from datetime import datetime
from enum import Enum
import json
from typing import Sequence
import numpy as np  # type: ignore
import csv
import os
from pathlib import Path

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
        
        # 결과 누적 저장소 (신규 추가)
        self.results = {
            'user_profile': None,
            'scenarios_result': None,
            'capital_result': None,
            'projection_result': None,
            'gap_result': None,
            'savings_result': None
        }

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
        
        # 결과 저장 (신규 추가)
        self.results['user_profile'] = user_profile
        
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

    # Tool 2: 경제 시나리오 생성
    def generate_economic_scenarios(self) -> dict:
        """보수/기준/공격 3가지 경제 시나리오 생성"""

        scenarios = {
            'conservative': {
                'scenario_name': '보수 시나리오',
                'inflation_rate': 0.020,
                'pre_retirement_return': 0.025,
                'post_retirement_return': 0.015,
                'wage_growth_rate': 0.030,
                'description': '안정적이지만 보수적인 가정'
            },
            'moderate': {
                'scenario_name': '기준 시나리오',
                'inflation_rate': 0.025,
                'pre_retirement_return': 0.040,
                'post_retirement_return': 0.025,
                'wage_growth_rate': 0.040,
                'description': '균형잡힌 중도적 가정'
            },
            'aggressive': {
                'scenario_name': '공격 시나리오',
                'inflation_rate': 0.030,
                'pre_retirement_return': 0.055,
                'post_retirement_return': 0.035,
                'wage_growth_rate': 0.050,
                'description': '낙관적이고 적극적인 가정'
            }
        }

        result = {
            'scenarios': scenarios,
            'recommendation': 'moderate',
            'note': '본인의 위험 성향과 시장 전망에 따라 시나리오를 선택하세요.'
        }
        
        # 결과 저장 (신규 추가)
        self.results['scenarios_result'] = result
        
        return result

    # Tool 3: 필요 은퇴자본 계산
    def calculate_retirement_capital(self, annual_expense: float,
                                     retirement_years: int,
                                     scenario: dict) -> dict:
        """안전인출률법과 연금현가법으로 필요 은퇴자본 계산"""

        post_ret_rate = scenario.get('post_retirement_return', 0.025)

        # 방법 1: 안전인출률법 (SWR: 3.0~3.5%)
        swr_low = annual_expense / 0.035
        swr_high = annual_expense / 0.030
        swr_avg = (swr_low + swr_high) / 2

        # 방법 2: 연금현가법 (PV of Annuity)
        pv_method = self.calculator.calculate_annuity_pv(
            annual_expense, post_ret_rate, retirement_years
        )

        # 의료비 버킷 (연간 지출의 20%)
        medical_reserve = annual_expense * 0.20 * retirement_years / 2

        result = {
            'safe_withdrawal_method': {
                '최소필요자본': round(swr_low, 0),
                '최대필요자본': round(swr_high, 0),
                '평균': round(swr_avg, 0)
            },
            'present_value_method': round(pv_method, 0),
            'medical_reserve': round(medical_reserve, 0),
            'recommended_total': round((swr_avg + pv_method) / 2 + medical_reserve, 0),
            'note': '두 방법의 평균에 의료비 버킷을 추가한 금액을 권장합니다.'
        }
        
        # 결과 저장 (신규 추가)
        self.results['capital_result'] = result
        
        return result

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

        result = {
            'total_projected_assets': round(total_projected, 0),
            'breakdown': projected_assets,
            'assumptions': {
                '수익률': f"{pre_ret_rate * 100:.1f}%",
                '기간': f"{years_to_retirement}년"
            }
        }
        
        # 결과 저장 (신규 추가)
        self.results['projection_result'] = result
        
        return result

    # Tool 5: 자금격차 분석
    def analyze_funding_gap(self, required_capital: float,
                            projected_assets: float) -> dict:
        """필요자본과 예상자산 비교"""

        gap = required_capital - projected_assets
        gap_pct = (gap / required_capital * 100) if required_capital > 0 else 0

        status = '충분' if gap <= 0 else '부족'

        result = {
            'required_capital': round(required_capital, 0),
            'projected_assets': round(projected_assets, 0),
            'gap_amount': round(gap, 0),
            'gap_percentage': round(gap_pct, 1),
            'status': status,
            'message': f"은퇴자금이 {abs(round(gap/10000, 0))}만원 {status}합니다."
        }
        
        # 결과 저장 (신규 추가)
        self.results['gap_result'] = result
        
        return result

    # Tool 6: 저축계획 최적화
    def optimize_savings_plan(self, funding_gap: float,
                              years_to_retirement: int,
                              current_monthly_savings: float,
                              scenario: dict) -> dict:
        """추가 저축 필요액 계산 및 실행 가능성 분석"""

        if funding_gap <= 0:
            result = {
                'status': 'sufficient',
                'message': '현재 계획으로 충분합니다.',
                'monthly_savings_needed': 0,
                'annual_savings_needed': 0
            }
        else:
            pre_ret_rate = scenario.get('pre_retirement_return', 0.040)

            # PMT 계산 (필요한 정기 저축액)
            annual_pmt = self.calculator.calculate_pmt(
                funding_gap, pre_ret_rate, years_to_retirement
            )
            monthly_pmt = annual_pmt / 12

            # 실행 가능성 점수
            if current_monthly_savings > 0:
                feasibility = min(
                    100, (current_monthly_savings / monthly_pmt) * 100)
            else:
                feasibility = 0

            # 권장사항
            recommendations = []
            if feasibility < 80:
                recommendations.append("은퇴 나이를 1-2년 늦추는 것을 고려하세요.")
                recommendations.append("목표 생활비를 10% 줄이는 것을 검토하세요.")
                recommendations.append("세제혜택 계좌(IRP, 연금저축)를 우선 활용하세요.")

            result = {
                'monthly_savings_needed': round(monthly_pmt, 0),
                'annual_savings_needed': round(annual_pmt, 0),
                'current_monthly_savings': current_monthly_savings,
                'additional_needed': round(monthly_pmt - current_monthly_savings, 0),
                'feasibility_score': round(feasibility, 1),
                'recommendations': recommendations,
                'alternatives': {
                    '은퇴_1년_연장시': round(monthly_pmt * years_to_retirement / (years_to_retirement + 1), 0),
                    '은퇴_2년_연장시': round(monthly_pmt * years_to_retirement / (years_to_retirement + 2), 0),
                    '목표지출_10%감소시': round(monthly_pmt * 0.9, 0)
                }
            }
        
        # 결과 저장 (신규 추가)
        self.results['savings_result'] = result
        
        # 자동 요약 출력 (신규 추가)
        if all(v is not None for v in self.results.values()):
            print("\n" + "="*50)
            print("📊 모든 계산 완료! 결과를 요약합니다...")
            print("="*50)
            
            try:
                summary = self.generate_savings_summary(
                    self.results['user_profile'],
                    self.results['scenarios_result'],
                    self.results['capital_result'],
                    self.results['projection_result'],
                    self.results['gap_result'],
                    self.results['savings_result']
                )
                # 요약을 결과에 포함
                result['auto_summary'] = summary
            except Exception as e:
                print(f"\n⚠️ 요약 생성 실패: {e}")
        
        return result


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