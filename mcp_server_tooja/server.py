from datetime import datetime
from enum import Enum
import json
from typing import Sequence
import numpy as np
import sys
import os

# 중앙 설정 모듈 import
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
from financial_constants_2025 import KOR_2025

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
        """한국형 투자성향 및 제약조건 분석"""

        age = demographic_info.get('age', 40)
        retirement_age = demographic_info.get('retirement_age', 65)
        years_to_retirement = retirement_age - age

        risk_score = behavioral_preferences.get('risk_tolerance_score', 50)

        # 한국형 위험성향 분류
        if risk_score < 40:
            risk_level = 'conservative'
            description = '보수적 - 안정성 우선'
        elif risk_score < 70:
            risk_level = 'moderate'
            description = '중립적 - 균형 추구'
        else:
            risk_level = 'aggressive'
            description = '공격적 - 성장 추구'

        # 한국형 주식 상한 (위험점수 기반)
        max_equity = self._equity_cap_from_risk_kor(risk_score)
        
        # 생애주기 반영 (130-나이 규칙 변형)
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
            'description': description,
            'max_equity_ratio': round(age_based_equity * 100, 1),
            'life_phase': phase,
            'korean_investment_constraints': {
                '주식_최대비중': f"{round(age_based_equity * 100, 1)}%",
                '채권_최소비중': f"{round((1 - age_based_equity) * 100, 1)}%",
                '국내주식_비중': f"{KOR_2025.MKT.domestic_equity_ratio * 100:.0f}%",
                '해외주식_비중': f"{KOR_2025.MKT.foreign_equity_ratio * 100:.0f}%",
                '세제혜택계좌_활용': 'IRP, 연금저축 우선' if self.user_risk_profile['use_irp'] else '일반계좌',
                '리츠_권장비중': f"{KOR_2025.MKT.reit_ratio * 100:.0f}%"
            },
            'recommendation': f'{years_to_retirement}년의 투자기간과 {phase} 단계를 고려하여 {risk_level} 포트폴리오를 권장합니다.'
        }

    def _equity_cap_from_risk_kor(self, risk_score: int) -> float:
        """한국형 위험점수 → 주식 상한"""
        return max(0.30, min(0.80, 0.30 + (risk_score / 100) * 0.50))

    def _determine_life_phase(self, age: int, years_to_retirement: int) -> str:
        """생애주기 단계 결정"""
        if years_to_retirement > 15:
            return "accumulation"
        elif years_to_retirement > 5:
            return "transition"
        else:
            return "retirement"

    def _lifecycle_equity_allocation(self, age: int, phase: str, max_equity: float) -> float:
        """생애주기 반영 주식 배분"""
        if phase == "accumulation":
            base_eq = min(0.90, (130 - age) / 100)
        elif phase == "transition":
            base_eq = min(0.70, (120 - age) / 100)
        else:
            base_eq = min(0.60, (110 - age) / 100)
        
        return max(0.20, min(max_equity, base_eq))

    def generate_three_tier_portfolios(self, risk_constraints: dict) -> dict:
        """한국형 3가지 포트폴리오 생성 (국내/해외 분할 반영)"""

        max_equity = risk_constraints.get('max_equity_ratio', 0.50)
        risk_level = risk_constraints.get('risk_level', 'moderate')
        life_phase = risk_constraints.get('life_phase', 'accumulation')

        portfolios = {}
        
        for portfolio_type in ['conservative', 'moderate', 'aggressive']:
            # 한국형 자산 배분 계산
            allocation = self._lifecycle_allocation_kor(
                risk_constraints.get('age', 40), 
                portfolio_type, 
                life_phase, 
                risk_constraints.get('risk_score', 50)
            )
            
            portfolios[portfolio_type] = {
                'portfolio_name': f'{portfolio_type.title()}형 포트폴리오',
                'asset_allocation': allocation,
                'expected_annual_return': self._expected_return_kor(portfolio_type),
                'expected_volatility': self._expected_volatility_kor(portfolio_type),
                'characteristics': self._portfolio_characteristics_kor(portfolio_type),
                'korean_considerations': {
                    '국내주식_비중': f"{allocation.get('국내주식', 0)}%",
                    '해외주식_비중': f"{allocation.get('해외주식', 0)}%",
                    '리츠_비중': f"{allocation.get('리츠', 0)}%",
                    '세제혜택_활용': 'IRP/연금저축 우선 배치 권장'
                }
            }

        self.base_portfolios = portfolios

        return {
            'portfolios': portfolios,
            'recommendation': 'moderate',
            'korean_market_guidelines': {
                '국내주식_기준': f"{KOR_2025.MKT.domestic_equity_ratio * 100:.0f}%",
                '해외주식_기준': f"{KOR_2025.MKT.foreign_equity_ratio * 100:.0f}%",
                '리츠_권장': f"{KOR_2025.MKT.reit_ratio * 100:.0f}%",
                '변동성_특성': f"코스피 {KOR_2025.MKT.kospi_volatility * 100:.0f}%, 국채 {KOR_2025.MKT.bond_volatility * 100:.0f}%"
            },
            'note': '한국 시장 특성과 생애주기를 반영한 포트폴리오입니다. 본인의 위험성향과 투자목표에 따라 선택하세요.',
            'selection_guide': {
                'conservative': '안정성이 최우선, 변동성을 최소화하고 싶은 경우',
                'moderate': '적절한 수익과 안정성의 균형을 원하는 경우',
                'aggressive': '장기 성장을 추구하며 단기 변동성을 감내할 수 있는 경우'
            }
        }

    def _lifecycle_allocation_kor(self, age: int, risk_level: str, phase: str, risk_score: int) -> dict:
        """한국형 생애주기 자산 배분"""
        # 기본 주식 비중
        if phase == "accumulation":
            base_eq = min(0.90, (130 - age) / 100)
        elif phase == "transition":
            base_eq = min(0.70, (120 - age) / 100)
        else:
            base_eq = min(0.60, (110 - age) / 100)

        # 위험성향 조정
        risk_adj = {"conservative": -0.10, "moderate": 0.0, "aggressive": +0.10}[risk_level]
        cap = self._equity_cap_from_risk_kor(risk_score)
        eq = max(0.20, min(cap, base_eq + risk_adj))

        # 한국형 국내/해외 분할
        dom_ratio = KOR_2025.MKT.domestic_equity_ratio
        for_ratio = KOR_2025.MKT.foreign_equity_ratio
        reit_ratio = KOR_2025.MKT.reit_ratio

        # 자산 배분 계산
        bonds = int(round((1 - eq) * 0.65 * 100))
        stocks = int(round(eq * 100))
        domestic_stocks = int(round(stocks * dom_ratio))
        foreign_stocks = stocks - domestic_stocks
        reits = int(round(reit_ratio * 100))
        gold = 5
        alt = 8 if risk_level != "conservative" else 5
        cash = max(5, 100 - (bonds + stocks + gold + alt))

        return {
            "채권": bonds,
            "주식": stocks,
            "국내주식": domestic_stocks,
            "해외주식": foreign_stocks,
            "리츠": reits,
            "대체투자": alt,
            "금": gold,
            "현금": cash
        }

    def _expected_return_kor(self, portfolio_type: str) -> float:
        """한국형 기대수익률"""
        returns = {
            'conservative': 4.5,
            'moderate': 6.0,
            'aggressive': 7.5
        }
        return returns[portfolio_type]

    def _expected_volatility_kor(self, portfolio_type: str) -> float:
        """한국형 기대변동성 (한국 시장 특성 반영)"""
        volatilities = {
            'conservative': 8.0,
            'moderate': 12.0,
            'aggressive': 16.0
        }
        return volatilities[portfolio_type]

    def _portfolio_characteristics_kor(self, portfolio_type: str) -> str:
        """한국형 포트폴리오 특성"""
        characteristics = {
            'conservative': '안정적 수익, 낮은 변동성, 원금보존 중시 (한국 시장 특성 반영)',
            'moderate': '균형잡힌 수익과 위험, 중도적 접근 (국내/해외 분산)',
            'aggressive': '높은 성장 잠재력, 변동성 감수 (글로벌 분산)'
        }
        return characteristics[portfolio_type]

    def adjust_portfolio_volatility(self, base_portfolio: dict,
                                    market_volatility_data: dict) -> dict:
        """한국형 변동성 조정 (코스피 기준)"""

        current_volatility = market_volatility_data.get(
            'current_volatility', KOR_2025.MKT.kospi_volatility * 100)
        historical_avg = market_volatility_data.get('historical_average', KOR_2025.MKT.kospi_volatility * 100)
        volatility_ratio = current_volatility / historical_avg

        allocation = base_portfolio.get('asset_allocation', {}).copy()

        if volatility_ratio > 1.2:
            regime = 'high_volatility'
            adjustment = '주식 비중 축소, 채권/금 확대 (한국 시장 고변동성 대응)'

            allocation['주식'] = max(10, allocation.get('주식', 0) - 10)
            allocation['국내주식'] = max(5, allocation.get('국내주식', 0) - 5)
            allocation['해외주식'] = max(5, allocation.get('해외주식', 0) - 5)
            allocation['채권'] = min(60, allocation.get('채권', 0) + 5)
            allocation['금'] = min(20, allocation.get('금', 0) + 5)

        elif volatility_ratio < 0.8:
            regime = 'low_volatility'
            adjustment = '주식 비중 확대, 성장 기회 포착 (한국 시장 저변동성 활용)'

            allocation['주식'] = min(80, allocation.get('주식', 0) + 5)
            allocation['국내주식'] = min(50, allocation.get('국내주식', 0) + 3)
            allocation['해외주식'] = min(30, allocation.get('해외주식', 0) + 2)
            allocation['채권'] = max(20, allocation.get('채권', 0) - 3)
            allocation['현금'] = max(5, allocation.get('현금', 0) - 2)

        else:
            regime = 'normal_volatility'
            adjustment = '기본 배분 유지 (한국 시장 정상 변동성)'

        return {
            'volatility_regime': regime,
            'current_volatility': round(current_volatility, 2),
            'historical_average': round(historical_avg, 2),
            'volatility_ratio': round(volatility_ratio, 2),
            'korean_benchmark': {
                'kospi_volatility': KOR_2025.MKT.kospi_volatility * 100,
                'bond_volatility': KOR_2025.MKT.bond_volatility * 100
            },
            'original_allocation': base_portfolio.get('asset_allocation', {}),
            'adjusted_allocation': allocation,
            'adjustment_description': adjustment,
            'note': '한국 시장(코스피) 변동성에 따라 자동으로 포트폴리오를 조정하여 위험을 관리합니다.'
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

        # 한국형 리밸런싱 규칙
        rebalancing_rules = self._korean_rebalancing_rules()

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

        # 한국형 성과 평가 기준
        risk_free_rate = KOR_2025.PERF.risk_free_rate
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

        # 한국형 성과 등급
        performance_grade = self._korean_performance_grade(excess_return, sharpe_ratio, max_drawdown)

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

    def _korean_rebalancing_rules(self) -> dict:
        """한국형 리밸런싱 규칙"""
        return {
            '정기 리밸런싱': {
                '주기': '분기별 검토, 연 1회 실행 (매년 12월)',
                '방법': '목표 배분 대비 ±5% 이상 차이시 조정',
                '거래비용_고려': '0.1% 이상시 연기 검토'
            },
            '긴급 리밸런싱': {
                '조건': '목표 배분 대비 ±8% 이상 차이 발생',
                '방법': '즉시 재조정 실시',
                '집중도_제한': f"단일 자산 {KOR_2025.REG.max_concentration_ratio*100:.0f}% 이하 유지"
            },
            '추가 투자시': {
                '원칙': '비중이 낮은 자산 위주로 매수',
                '방법': '자동 목표배분 유지',
                '세제혜택_우선': 'IRP/연금저축 한도 내 우선 배치'
            },
            '한국_특화_규칙': {
                '국내해외_균형': '국내 60%, 해외 40% 기준 유지',
                '리츠_비중': f"{KOR_2025.MKT.reit_ratio*100:.0f}% 유지",
                '변동성_대응': '코스피 변동성 1.2배 이상시 주식 비중 축소'
            }
        }

    def _korean_performance_grade(self, excess_return: float, sharpe_ratio: float, max_drawdown: float) -> str:
        """한국형 성과 등급 평가"""
        bench = KOR_2025.PERF.sharpe_benchmark
        mdd_lim = KOR_2025.PERF.mdd_limits
        
        if excess_return > 0.02 and sharpe_ratio >= bench['excellent'] and abs(max_drawdown) <= mdd_lim['conservative']:
            return 'A+ (최우수)'
        elif excess_return > 0.02 and sharpe_ratio >= bench['good']:
            return 'A (우수)'
        elif excess_return > 0 and sharpe_ratio >= bench['ok']:
            return 'B (양호)'
        elif excess_return > -0.02 and sharpe_ratio >= bench['weak']:
            return 'C (보통)'
        else:
            return 'D (부진)'

    def _generate_performance_recommendations(self, excess_return, sharpe_ratio, max_drawdown):
        """한국형 성과 기반 권장사항 생성"""
        recommendations = []
        bench = KOR_2025.PERF.sharpe_benchmark
        mdd_lim = KOR_2025.PERF.mdd_limits

        if excess_return < 0:
            recommendations.append('벤치마크 대비 저조한 성과. 포트폴리오 점검이 필요합니다.')

        if sharpe_ratio < bench['ok']:
            recommendations.append('위험 대비 수익이 낮습니다. 자산배분 재검토를 권장합니다.')

        if abs(max_drawdown) > mdd_lim['moderate']:
            recommendations.append('큰 낙폭이 발생했습니다. 변동성 관리가 필요합니다.')

        if not recommendations:
            recommendations.append('전반적으로 양호한 성과를 보이고 있습니다. 현재 전략을 유지하세요.')

        # 한국 특화 권장사항
        recommendations.extend([
            '국내/해외 주식 비중을 60:40으로 유지하세요.',
            '리츠 비중을 5% 수준으로 유지하세요.',
            '세제혜택 계좌(IRP, 연금저축)를 최대한 활용하세요.'
        ])

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
