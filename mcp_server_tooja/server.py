from datetime import datetime
from enum import Enum
import json
from typing import Sequence
import numpy as np

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.shared.exceptions import McpError

from pydantic import BaseModel


class ToojaTools(str, Enum):
    ASSESS_RISK_PROFILE = "assess_risk_profile"
    GENERATE_PORTFOLIOS = "generate_three_tier_portfolios"
    ADJUST_VOLATILITY = "adjust_portfolio_volatility"
    BUILD_IMPLEMENTATION = "build_implementation_roadmap"
    MONITOR_PERFORMANCE = "monitor_portfolio_performance"


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


# ========== 투자메이트 서비스 로직 ==========

class ToojaService:

    def __init__(self):
        self.user_risk_profile = {}
        self.base_portfolios = {}

    def assess_risk_profile(self, demographic_info: dict, financial_capacity: dict,
                            liquidity_requirements: dict, behavioral_preferences: dict) -> dict:
        """사용자 투자성향 및 제약조건 분석"""

        age = demographic_info.get('age', 40)
        retirement_age = demographic_info.get('retirement_age', 65)
        years_to_retirement = retirement_age - age

        risk_score = behavioral_preferences.get('risk_tolerance_score', 50)

        if risk_score < 40:
            risk_level = 'conservative'
            max_equity = 0.30
            description = '보수적 - 안정성 우선'
        elif risk_score < 70:
            risk_level = 'moderate'
            max_equity = 0.50
            description = '중립적 - 균형 추구'
        else:
            risk_level = 'aggressive'
            max_equity = 0.70
            description = '공격적 - 성장 추구'

        age_based_equity = min((100 - age) / 100, max_equity)

        self.user_risk_profile = {
            'risk_level': risk_level,
            'max_equity_ratio': round(age_based_equity, 2),
            'years_to_retirement': years_to_retirement,
            'use_irp': behavioral_preferences.get('use_irp', True),
            'use_pension_savings': behavioral_preferences.get('use_pension_savings', True)
        }

        return {
            'risk_level': risk_level,
            'description': description,
            'max_equity_ratio': round(age_based_equity * 100, 1),
            'investment_constraints': {
                '주식_최대비중': f"{round(age_based_equity * 100, 1)}%",
                '채권_최소비중': f"{round((1 - age_based_equity) * 100, 1)}%",
                '세제혜택계좌_활용': 'IRP, 연금저축 우선' if self.user_risk_profile['use_irp'] else '일반계좌'
            },
            'recommendation': f'{years_to_retirement}년의 투자기간을 고려하여 {risk_level} 포트폴리오를 권장합니다.'
        }

    def generate_three_tier_portfolios(self, risk_constraints: dict) -> dict:
        """보수형/중립형/성장형 3가지 포트폴리오 생성"""

        max_equity = risk_constraints.get('max_equity_ratio', 0.50)

        portfolios = {
            'conservative': {
                'portfolio_name': '보수형 포트폴리오',
                'asset_allocation': {
                    '채권': 55,
                    '주식': min(20, int(max_equity * 100)),
                    '금': 10,
                    '현금': 10,
                    '대체투자': 5
                },
                'expected_annual_return': 4.5,
                'expected_volatility': 8.0,
                'characteristics': '안정적 수익, 낮은 변동성, 원금보존 중시'
            },
            'moderate': {
                'portfolio_name': '중립형 포트폴리오',
                'asset_allocation': {
                    '채권': 40,
                    '주식': min(35, int(max_equity * 100)),
                    '금': 10,
                    '현금': 10,
                    '대체투자': 5
                },
                'expected_annual_return': 6.0,
                'expected_volatility': 12.0,
                'characteristics': '균형잡힌 수익과 위험, 중도적 접근'
            },
            'aggressive': {
                'portfolio_name': '성장형 포트폴리오',
                'asset_allocation': {
                    '채권': 30,
                    '주식': min(50, int(max_equity * 100)),
                    '금': 10,
                    '현금': 5,
                    '대체투자': 5
                },
                'expected_annual_return': 7.5,
                'expected_volatility': 16.0,
                'characteristics': '높은 성장 잠재력, 변동성 감수'
            }
        }

        self.base_portfolios = portfolios

        return {
            'portfolios': portfolios,
            'recommended': 'moderate',
            'note': '본인의 위험성향과 투자목표에 따라 선택하거나 조합하세요.',
            'selection_guide': {
                'conservative': '안정성이 최우선, 변동성을 최소화하고 싶은 경우',
                'moderate': '적절한 수익과 안정성의 균형을 원하는 경우',
                'aggressive': '장기 성장을 추구하며 단기 변동성을 감내할 수 있는 경우'
            }
        }

    def adjust_portfolio_volatility(self, base_portfolio: dict,
                                    market_volatility_data: dict) -> dict:
        """시장 변동성에 따른 포트폴리오 동적 조정"""

        current_volatility = market_volatility_data.get(
            'current_volatility', 15.0)
        historical_avg = market_volatility_data.get('historical_average', 15.0)
        volatility_ratio = current_volatility / historical_avg

        allocation = base_portfolio.get('asset_allocation', {}).copy()

        if volatility_ratio > 1.2:
            regime = 'high_volatility'
            adjustment = '주식 비중 축소, 채권/금 확대'

            allocation['주식'] = max(10, allocation.get('주식', 0) - 10)
            allocation['채권'] = min(60, allocation.get('채권', 0) + 5)
            allocation['금'] = min(20, allocation.get('금', 0) + 5)

        elif volatility_ratio < 0.8:
            regime = 'low_volatility'
            adjustment = '주식 비중 확대, 성장 기회 포착'

            allocation['주식'] = min(60, allocation.get('주식', 0) + 5)
            allocation['채권'] = max(25, allocation.get('채권', 0) - 3)
            allocation['현금'] = max(5, allocation.get('현금', 0) - 2)

        else:
            regime = 'normal_volatility'
            adjustment = '기본 배분 유지'

        return {
            'volatility_regime': regime,
            'current_volatility': round(current_volatility, 2),
            'historical_average': round(historical_avg, 2),
            'volatility_ratio': round(volatility_ratio, 2),
            'original_allocation': base_portfolio.get('asset_allocation', {}),
            'adjusted_allocation': allocation,
            'adjustment_description': adjustment,
            'note': '시장 변동성에 따라 자동으로 포트폴리오를 조정하여 위험을 관리합니다.'
        }

    def build_implementation_roadmap(self, optimized_portfolio: dict,
                                     current_holdings: dict,
                                     account_info: dict) -> dict:
        """계좌별 실행 계획 및 리밸런싱 전략 수립"""

        target_allocation = optimized_portfolio.get('adjusted_allocation',
                                                    optimized_portfolio.get('asset_allocation', {}))

        account_strategy = {}

        if account_info.get('has_irp', False):
            account_strategy['IRP'] = {
                '우선배치자산': ['주식ETF', '채권'],
                '이유': '세액공제 및 이연과세 효과 극대화',
                '권장비중': '주식 50%, 채권 50%'
            }

        if account_info.get('has_pension_savings', False):
            account_strategy['연금저축'] = {
                '우선배치자산': ['글로벌주식ETF', '배당주ETF'],
                '이유': '장기 성장자산 위주 편입',
                '권장비중': '주식 70%, 채권 30%'
            }

        account_strategy['일반과세계좌'] = {
            '우선배치자산': ['금ETF', '리츠', '배당주'],
            '이유': '배당소득세 고려한 분산',
            '권장비중': '금 40%, 리츠 30%, 배당주 30%'
        }

        execution_steps = [
            {
                'step': 1,
                'action': '현금성 자산 확보',
                'detail': f"목표 현금비중 {target_allocation.get('현금', 10)}%를 CMA/MMF로 확보"
            },
            {
                'step': 2,
                'action': '세제혜택 계좌 우선 투자',
                'detail': 'IRP, 연금저축 한도 내 핵심 자산(주식/채권) 매수'
            },
            {
                'step': 3,
                'action': '일반 계좌 보완 투자',
                'detail': '금, 리츠 등 세제혜택 계좌에서 부족한 자산군 편입'
            },
            {
                'step': 4,
                'action': '초기 포트폴리오 완성',
                'detail': '목표 배분 달성 및 투자일지 작성'
            }
        ]

        rebalancing_rules = {
            '정기 리밸런싱': {
                '주기': '연 1회 (매년 12월)',
                '방법': '목표 배분 대비 ±5% 이상 차이시 조정'
            },
            '긴급 리밸런싱': {
                '조건': '목표 배분 대비 ±10% 이상 차이 발생',
                '방법': '즉시 재조정 실시'
            },
            '추가 투자시': {
                '원칙': '비중이 낮은 자산 위주로 매수',
                '방법': '자동 목표배분 유지'
            }
        }

        return {
            'account_strategy': account_strategy,
            'execution_steps': execution_steps,
            'rebalancing_rules': rebalancing_rules,
            'estimated_setup_time': '2-4주',
            'key_recommendations': [
                '세제혜택 계좌를 최대한 활용하세요',
                '일시 투자보다 3-6개월에 걸쳐 분할 매수를 고려하세요',
                '연 1회 리밸런싱으로 목표 배분을 유지하세요'
            ]
        }

    def monitor_portfolio_performance(self, portfolio_returns: dict,
                                      benchmark_returns: dict,
                                      time_period: str) -> dict:
        """포트폴리오 성과 분석 및 위험조정 지표 계산"""

        portfolio_return = portfolio_returns.get('total_return', 0.0)
        portfolio_volatility = portfolio_returns.get('volatility', 0.0)
        benchmark_return = benchmark_returns.get('total_return', 0.0)

        risk_free_rate = 0.02
        if portfolio_volatility > 0:
            sharpe_ratio = (portfolio_return - risk_free_rate) / \
                portfolio_volatility
        else:
            sharpe_ratio = 0

        excess_return = portfolio_return - benchmark_return

        returns_list = portfolio_returns.get('monthly_returns', [])
        if returns_list:
            cumulative = np.cumprod([1 + r for r in returns_list])
            running_max = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = np.min(drawdown) * 100
        else:
            max_drawdown = 0

        if excess_return > 0.02:
            performance_grade = 'A (우수)'
        elif excess_return > 0:
            performance_grade = 'B (양호)'
        elif excess_return > -0.02:
            performance_grade = 'C (보통)'
        else:
            performance_grade = 'D (부진)'

        return {
            'period': time_period,
            'portfolio_return': round(portfolio_return * 100, 2),
            'benchmark_return': round(benchmark_return * 100, 2),
            'excess_return': round(excess_return * 100, 2),
            'volatility': round(portfolio_volatility * 100, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'max_drawdown': round(max_drawdown, 2),
            'performance_grade': performance_grade,
            'risk_adjusted_metrics': {
                '샤프비율': round(sharpe_ratio, 2),
                '변동성': f"{round(portfolio_volatility * 100, 2)}%",
                '최대낙폭': f"{round(max_drawdown, 2)}%"
            },
            'recommendations': self._generate_performance_recommendations(
                excess_return, sharpe_ratio, max_drawdown
            )
        }

    def _generate_performance_recommendations(self, excess_return, sharpe_ratio, max_drawdown):
        """성과 기반 권장사항 생성"""
        recommendations = []

        if excess_return < 0:
            recommendations.append('벤치마크 대비 저조한 성과. 포트폴리오 점검이 필요합니다.')

        if sharpe_ratio < 0.5:
            recommendations.append('위험 대비 수익이 낮습니다. 자산배분 재검토를 권장합니다.')

        if abs(max_drawdown) > 20:
            recommendations.append('큰 낙폭이 발생했습니다. 변동성 관리가 필요합니다.')

        if not recommendations:
            recommendations.append('전반적으로 양호한 성과를 보이고 있습니다. 현재 전략을 유지하세요.')

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
                description="사용자의 투자 성향과 제약조건을 분석합니다",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "demographic_info": {
                            "type": "object",
                            "description": "나이, 은퇴목표 등"
                        },
                        "financial_capacity": {
                            "type": "object",
                            "description": "자산규모, 소득안정성"
                        },
                        "liquidity_requirements": {
                            "type": "object",
                            "description": "유동성 필요 시점"
                        },
                        "behavioral_preferences": {
                            "type": "object",
                            "description": "위험성향 설문 결과"
                        }
                    },
                    "required": ["demographic_info", "behavioral_preferences"]
                }
            ),
            Tool(
                name=ToojaTools.GENERATE_PORTFOLIOS.value,
                description="보수/중립/성장형 3가지 포트폴리오를 생성합니다",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "risk_constraints": {
                            "type": "object",
                            "description": "위험 제약조건"
                        }
                    },
                    "required": ["risk_constraints"]
                }
            ),
            Tool(
                name=ToojaTools.ADJUST_VOLATILITY.value,
                description="시장 변동성에 따라 포트폴리오를 조정합니다",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_portfolio": {
                            "type": "object",
                            "description": "기본 포트폴리오"
                        },
                        "market_volatility_data": {
                            "type": "object",
                            "description": "시장 변동성 데이터"
                        }
                    },
                    "required": ["base_portfolio", "market_volatility_data"]
                }
            ),
            Tool(
                name=ToojaTools.BUILD_IMPLEMENTATION.value,
                description="계좌별 실행 계획을 수립합니다",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "optimized_portfolio": {
                            "type": "object",
                            "description": "최적화된 포트폴리오"
                        },
                        "current_holdings": {
                            "type": "object",
                            "description": "현재 보유 자산"
                        },
                        "account_info": {
                            "type": "object",
                            "description": "계좌 정보"
                        }
                    },
                    "required": ["optimized_portfolio", "account_info"]
                }
            ),
            Tool(
                name=ToojaTools.MONITOR_PERFORMANCE.value,
                description="포트폴리오 성과를 모니터링하고 분석합니다",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "portfolio_returns": {
                            "type": "object",
                            "description": "포트폴리오 수익률"
                        },
                        "benchmark_returns": {
                            "type": "object",
                            "description": "벤치마크 수익률"
                        },
                        "time_period": {
                            "type": "string",
                            "description": "분석 기간"
                        }
                    },
                    "required": ["portfolio_returns", "benchmark_returns", "time_period"]
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

                case ToojaTools.MONITOR_PERFORMANCE.value:
                    result = service.monitor_portfolio_performance(
                        arguments['portfolio_returns'],
                        arguments['benchmark_returns'],
                        arguments['time_period']
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
