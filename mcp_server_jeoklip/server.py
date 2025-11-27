from datetime import datetime
from enum import Enum
import json
from typing import Sequence
import csv
import os
import sys
from pathlib import Path

# __pycache__ 폴더 생성 방지
sys.dont_write_bytecode = True

# 중앙 설정 모듈 import
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
from financial_constants_2025 import KOR_2025  # type: ignore

from mcp.server import Server  # type: ignore
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource


class JeoklipTools(str, Enum):
    COLLECT_USER_INFO = "collect_user_info"
    GENERATE_SCENARIOS = "generate_economic_scenarios"
    CALCULATE_RETIREMENT_CAPITAL = "calculate_retirement_capital"
    PROJECT_ASSETS = "project_retirement_assets"
    ANALYZE_GAP = "analyze_funding_gap"
    OPTIMIZE_SAVINGS = "optimize_savings_plan"
    CALCULATE_RECOMMENDED_EXPENSES = "calculate_recommended_expenses"
    ANALYZE_BRIDGE_PERIOD = "analyze_bridge_period"
    GENERATE_FINAL_SUMMARY = "generate_final_summary"


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
        # 계산 결과 저장소 (최종 요약용)
        self.calculation_results = {}
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

        # CSV 파일로 저장
        try:
            csv_filepath = self._save_to_csv(user_profile, income_structure,
                                            expense_categories, asset_portfolio)
            csv_saved = True
            csv_message = f'CSV 파일로 저장됨: {csv_filepath}'
        except Exception as e:
            csv_saved = False
            csv_message = f'CSV 저장 실패: {str(e)}'

        # 월 저축 가능액 계산
        monthly_income = income_structure.get('monthly_income', 0)
        monthly_expense = expense_categories.get('total_monthly_expense', 0)
        monthly_savings_capacity = monthly_income - monthly_expense

        # 비상금/여유금 계산 (월 지출의 3~6개월분 권장)
        emergency_fund_min = monthly_expense * 3  # 최소 3개월
        emergency_fund_max = monthly_expense * 6  # 권장 6개월

        # 현재 보유 비상금 판단 (현금성 자산 기준)
        current_cash = asset_portfolio.get('현금', 0) + asset_portfolio.get('예금', 0) + asset_portfolio.get('MMF', 0)
        emergency_fund_status = '충분' if current_cash >= emergency_fund_min else '부족'
        emergency_fund_gap = max(0, emergency_fund_min - current_cash)

        result = {
            'status': 'success',
            'message': '사용자 정보가 성공적으로 수집되었습니다.',
            'csv_saved': csv_saved,
            'csv_message': csv_message,
            'summary': {
                '현재나이': user_profile.get('current_age'),
                '목표은퇴나이': user_profile.get('target_retirement_age'),
                '월소득': monthly_income,
                '월지출': monthly_expense,
                '총자산': sum(asset_portfolio.values())
            },
            '월저축가능액': {
                '금액': round(monthly_savings_capacity, 0),
                '소득대비비율': f"{(monthly_savings_capacity/monthly_income*100):.1f}%" if monthly_income > 0 else "0%",
                '평가': self._evaluate_savings_rate(monthly_savings_capacity, monthly_income)
            },
            '비상금_여유금': {
                '권장_최소금액': round(emergency_fund_min, 0),
                '권장_최대금액': round(emergency_fund_max, 0),
                '현재_보유액': round(current_cash, 0),
                '상태': emergency_fund_status,
                '부족액': round(emergency_fund_gap, 0) if emergency_fund_gap > 0 else 0,
                '권장사항': f"월 지출의 {3}~{6}개월분 비상금을 현금성 자산으로 확보하세요."
            }
        }

        # 계산 결과 저장
        self.calculation_results['user_info'] = result
        self.calculation_results['monthly_savings_capacity'] = monthly_savings_capacity
        self.calculation_results['emergency_fund'] = result['비상금_여유금']

        return result

    def _evaluate_savings_rate(self, savings: float, income: float) -> str:
        """저축률 평가"""
        if income == 0:
            return "소득 정보 없음"
        rate = savings / income
        if rate >= 0.30:
            return "우수 (30% 이상)"
        elif rate >= 0.20:
            return "양호 (20% 이상)"
        elif rate >= 0.10:
            return "보통 (10% 이상)"
        else:
            return "개선 필요 (10% 미만)"

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

        result = {
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

        return result

    # Tool 3: 필요 은퇴자본 계산 (한국 특화)
    def calculate_retirement_capital(self, annual_expense: float,
                                     retirement_years: int,
                                     scenario: dict) -> dict:
        """한국형 필요 은퇴자본 계산 (기간별 SWR 조정)"""

        # 중앙설정모듈에서 은퇴 후 수익률 가져오기
        post_ret_rate = scenario.get('post_retirement_return', KOR_2025.ECON.baseline['post_ret'])

        # 한국형 SWR 범위 (기간 반영) - 중앙설정모듈 사용
        swr_band = self._swr_band_kor(retirement_years)

        # 방법 1: 안전인출률법 (기간별 조정)
        swr_low = annual_expense / swr_band['high']
        swr_high = annual_expense / swr_band['low']
        swr_avg = annual_expense / swr_band['mid']

        # 방법 2: 연금현가법 (PV of Annuity)
        pv_method = self.calculator.calculate_annuity_pv(
            annual_expense, post_ret_rate, retirement_years
        )

        # 한국형 의료비 버킷 (연령 가중) - 중앙설정모듈 사용
        medical_reserve = self._calculate_medical_reserve_kor(annual_expense, retirement_years)

        result = {
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
                'national_pension_available': '국민연금 수급 가능',
                'swr_base': f"{KOR_2025.SWR.base_moderate*100:.1f}%",
                'swr_min_floor': f"{KOR_2025.SWR.min_floor*100:.1f}%"
            },
            'note': f'기간 {retirement_years}년에 맞춘 SWR 조정과 한국 의료비 특성을 반영했습니다. (중앙설정모듈 적용)'
        }

        # 계산 결과 저장
        self.calculation_results['required_capital'] = result['recommended_total']
        self.calculation_results['retirement_capital_detail'] = result

        return result

    def _swr_band_kor(self, years: int) -> dict:
        """한국형 SWR 범위 (기간 중심 밴드) - 중앙설정모듈 사용"""
        # 중앙설정모듈의 SWR 규칙 사용
        mid = KOR_2025.SWR.adjust_by_duration(years)
        band_width = KOR_2025.SWR.by_years_delta  # 0.005

        return {
            'low': max(KOR_2025.SWR.min_floor, mid - band_width),
            'mid': mid,
            'high': min(0.04, mid + band_width)
        }

    def _calculate_medical_reserve_kor(self, annual_expense: float, retirement_years: int) -> float:
        """한국형 의료비 준비금 계산 - 중앙설정모듈 사용"""
        # 중앙설정모듈의 의료비 기준 비율 사용
        base_med = annual_expense * KOR_2025.BUCK.healthcare_base_ratio

        # 평균 연령 가중치 계산 (65-95세 가정)
        # healthcare_age_factor: {(65,70): 1.0, (70,75): 1.3, (75,80): 1.6, (80,85): 2.0, (85,200): 2.5}
        # 30년 기준 평균 가중치: (1.0*5 + 1.3*5 + 1.6*5 + 2.0*5 + 2.5*10) / 30 = 1.6
        avg_age_factor = 1.6

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

        result = {
            'total_projected_assets': round(total_projected, 0),
            'breakdown': projected_assets,
            'assumptions': {
                '수익률': f"{pre_ret_rate * 100:.1f}%",
                '기간': f"{years_to_retirement}년"
            }
        }

        # 계산 결과 저장
        self.calculation_results['projected_assets'] = result['total_projected_assets']
        self.calculation_results['projected_assets_detail'] = result

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

        return result

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

    # Tool 7: 권장 월 지출 계산 (은퇴 전/후)
    def calculate_recommended_expenses(self, monthly_income: float,
                                       current_monthly_expense: float,
                                       current_age: int,
                                       target_retirement_age: int) -> dict:
        """권장 월 지출 계산 (은퇴 전/후)"""

        # 은퇴 전 권장 월 지출 (소득 기반, 50/30/20 규칙 참고)
        # 필수지출(50%) + 선택지출(30%) + 저축(20%)
        pre_retirement_recommended = {
            '필수지출_권장': round(monthly_income * 0.50, 0),
            '선택지출_권장': round(monthly_income * 0.30, 0),
            '저축_권장': round(monthly_income * 0.20, 0),
            '총지출_권장': round(monthly_income * 0.80, 0),
            '현재지출': current_monthly_expense,
            '차이': round(monthly_income * 0.80 - current_monthly_expense, 0),
            '평가': self._evaluate_expense_level(current_monthly_expense, monthly_income)
        }

        # 은퇴 후 권장 월 지출 (은퇴 전 지출의 70-80% 권장)
        # 교통비, 의류비, 식비 감소를 반영
        retirement_expense_ratio_low = 0.70  # 보수적 (70%)
        retirement_expense_ratio_mid = 0.75  # 중도 (75%)
        retirement_expense_ratio_high = 0.80  # 여유 (80%)

        current_expense_base = current_monthly_expense

        post_retirement_recommended = {
            '보수형': {
                '월지출': round(current_expense_base * retirement_expense_ratio_low, 0),
                '비율': f"{retirement_expense_ratio_low*100:.0f}%",
                '설명': '최소 생활비 수준 (검소한 은퇴 생활)'
            },
            '중도형': {
                '월지출': round(current_expense_base * retirement_expense_ratio_mid, 0),
                '비율': f"{retirement_expense_ratio_mid*100:.0f}%",
                '설명': '적정 생활비 수준 (안정적 은퇴 생활)'
            },
            '여유형': {
                '월지출': round(current_expense_base * retirement_expense_ratio_high, 0),
                '비율': f"{retirement_expense_ratio_high*100:.0f}%",
                '설명': '넉넉한 생활비 수준 (여유로운 은퇴 생활)'
            },
            '권장': '중도형',
            '참고사항': [
                '은퇴 후 감소 항목: 교통비, 의류비, 식비 일부',
                '은퇴 후 증가 항목: 의료비, 여가비',
                '주택연금이나 국민연금으로 일부 충당 가능'
            ]
        }

        result = {
            '은퇴전_권장지출': pre_retirement_recommended,
            '은퇴후_권장지출': post_retirement_recommended,
            '현재상황': {
                '현재나이': current_age,
                '목표은퇴나이': target_retirement_age,
                '은퇴까지': f"{target_retirement_age - current_age}년"
            }
        }

        # 계산 결과 저장
        self.calculation_results['recommended_expenses'] = result

        return result

    def _evaluate_expense_level(self, expense: float, income: float) -> str:
        """지출 수준 평가"""
        if income == 0:
            return "소득 정보 없음"
        ratio = expense / income
        if ratio <= 0.70:
            return "우수 (70% 이하, 저축률 높음)"
        elif ratio <= 0.80:
            return "양호 (80% 이하, 적정 수준)"
        elif ratio <= 0.90:
            return "보통 (90% 이하)"
        else:
            return "개선 필요 (90% 초과, 지출 과다)"

    # Tool 8: 브릿지 구간 분석 (공적연금 전 부족분 충당 계획)
    def analyze_bridge_period(self, retirement_age: int,
                               national_pension_start_age: int,
                               monthly_expense_post_retirement: float,
                               expected_national_pension: float,
                               scenario: dict) -> dict:
        """브릿지 구간 분석 (은퇴 ~ 공적연금 수령 전까지)"""

        # 브릿지 구간 기간 계산
        bridge_years = national_pension_start_age - retirement_age

        if bridge_years <= 0:
            return {
                'status': 'no_bridge_period',
                'message': '브릿지 구간이 없습니다. 은퇴와 동시에 국민연금 수령이 가능합니다.',
                'bridge_years': 0
            }

        # 브릿지 구간 월별 부족분 계산
        monthly_shortfall = monthly_expense_post_retirement  # 전액 자기 자본으로 충당

        # 브릿지 구간 총 필요 자본
        total_bridge_capital_needed = monthly_shortfall * 12 * bridge_years

        # 인플레이션 반영 (중간값 적용)
        inflation_rate = scenario.get('inflation_rate', 0.02)
        avg_year = bridge_years / 2
        inflation_adjusted_capital = total_bridge_capital_needed * ((1 + inflation_rate) ** avg_year)

        # 3버킷 전략 적용 (현금 2년 + 소득형 8년)
        cash_bucket_years = min(2, bridge_years)
        income_bucket_years = max(0, min(8, bridge_years - cash_bucket_years))
        growth_bucket_years = max(0, bridge_years - cash_bucket_years - income_bucket_years)

        cash_bucket_amount = monthly_shortfall * 12 * cash_bucket_years
        income_bucket_amount = monthly_shortfall * 12 * income_bucket_years
        growth_bucket_amount = monthly_shortfall * 12 * growth_bucket_years

        # 충당 방안
        funding_strategies = [
            {
                '전략': '3버킷 전략 (현금 + 소득형 + 성장형)',
                '현금버킷': f"{cash_bucket_years}년치 ({round(cash_bucket_amount, 0):,}원)",
                '소득버킷': f"{income_bucket_years}년치 ({round(income_bucket_amount, 0):,}원)",
                '성장버킷': f"{growth_bucket_years}년치 ({round(growth_bucket_amount, 0):,}원)" if growth_bucket_years > 0 else "불필요",
                '설명': '안정성과 수익성을 균형있게 확보'
            },
            {
                '전략': '연금저축 인출',
                '금액': f"월 {round(monthly_shortfall, 0):,}원 x {bridge_years}년",
                '세금': f"연금소득세 {KOR_2025.TAX.pension_separated_brackets[0][1]*100:.1f}% 적용",
                '설명': '세제혜택을 받은 연금계좌에서 인출'
            },
            {
                '전략': '주택연금 조기 가입',
                '조건': f"만 {KOR_2025.HOUSING.min_age}세 이상, 주택가격 {KOR_2025.HOUSING.property_value_limit/100000000:.0f}억 이하",
                '예상수령': '주택가격에 따라 월 80만~210만원',
                '설명': '주택을 담보로 평생 연금 수령 (브릿지 구간 해결)'
            }
        ]

        # 국민연금 수령 시작 후 (브릿지 이후)
        post_bridge_monthly_shortfall = monthly_expense_post_retirement - expected_national_pension
        post_bridge_status = '충분' if post_bridge_monthly_shortfall <= 0 else '부족'

        result = {
            '브릿지구간_기본정보': {
                '시작나이': retirement_age,
                '종료나이': national_pension_start_age,
                '기간': f"{bridge_years}년",
                '설명': f"{retirement_age}세 은퇴 ~ {national_pension_start_age}세 국민연금 수령 전까지"
            },
            '브릿지구간_자금소요': {
                '월소요액': round(monthly_shortfall, 0),
                '연소요액': round(monthly_shortfall * 12, 0),
                '총소요액': round(total_bridge_capital_needed, 0),
                '인플레이션반영': round(inflation_adjusted_capital, 0),
                '인플레이션율': f"{inflation_rate*100:.1f}%"
            },
            '3버킷_전략_배분': {
                '현금버킷': {
                    '기간': f"{cash_bucket_years}년",
                    '금액': round(cash_bucket_amount, 0),
                    '설명': '즉시 인출 가능 (예금, MMF)'
                },
                '소득버킷': {
                    '기간': f"{income_bucket_years}년",
                    '금액': round(income_bucket_amount, 0),
                    '설명': '안정적 수익 (채권, 배당주)'
                },
                '성장버킷': {
                    '기간': f"{growth_bucket_years}년" if growth_bucket_years > 0 else "불필요",
                    '금액': round(growth_bucket_amount, 0) if growth_bucket_years > 0 else 0,
                    '설명': '장기 성장 (주식형 펀드)' if growth_bucket_years > 0 else "브릿지 기간이 짧아 불필요"
                }
            },
            '충당방안': funding_strategies,
            '브릿지이후_상황': {
                '국민연금_수령액': round(expected_national_pension, 0),
                '월지출': round(monthly_expense_post_retirement, 0),
                '월부족분': round(post_bridge_monthly_shortfall, 0) if post_bridge_monthly_shortfall > 0 else 0,
                '상태': post_bridge_status,
                '설명': f"국민연금 수령 후에도 월 {round(abs(post_bridge_monthly_shortfall), 0):,}원 {'추가 필요' if post_bridge_monthly_shortfall > 0 else '여유'}"
            },
            '권장사항': [
                f"브릿지 구간 {bridge_years}년 동안 총 {round(inflation_adjusted_capital/100000000, 1):.1f}억원 필요",
                "3버킷 전략으로 현금 유동성과 수익성을 동시에 확보하세요",
                "연금저축, IRP 등 세제혜택 계좌를 우선 활용하세요",
                "주택연금 가입 조건에 해당하면 적극 검토하세요",
                f"국민연금 수령 시기를 조정({national_pension_start_age-1}세 조기 or {national_pension_start_age+1}세 연기)하여 브릿지 구간을 조절할 수 있습니다"
            ]
        }

        # 계산 결과 저장
        self.calculation_results['bridge_period'] = result

        return result

    # Tool 9: 최종 요약 생성 (신규 추가)
    def generate_final_summary(self) -> dict:
        """적립메이트 분석 최종 요약 카드 생성"""

        # 저장된 계산 결과가 없거나 부족한 경우
        if not self.calculation_results:
            return {
                'status': 'incomplete',
                'message': '⚠️ 분석 데이터가 부족합니다. 먼저 사용자 정보 수집 및 분석을 진행해주세요.',
                '필요한_단계': [
                    '1. collect_user_info (사용자 정보 수집)',
                    '2. calculate_retirement_capital (필요 은퇴자본 계산)',
                    '3. project_retirement_assets (은퇴시점 자산 추정)',
                    '4. calculate_recommended_expenses (권장 지출 계산)',
                    '5. analyze_bridge_period (브릿지 구간 분석)'
                ]
            }

        # 1. 필요자산
        required_capital = self.calculation_results.get('required_capital', 0)

        # 2. 은퇴 시 기대보유자산
        projected_assets = self.calculation_results.get('projected_assets', 0)

        # 3. 권장 월 지출 (은퇴 전, 후)
        recommended_expenses = self.calculation_results.get('recommended_expenses', {})
        pre_retirement_expense = recommended_expenses.get('은퇴전_권장지출', {})
        post_retirement_expense = recommended_expenses.get('은퇴후_권장지출', {})

        # 4. 월 저축 가능액
        monthly_savings_capacity = self.calculation_results.get('monthly_savings_capacity', 0)

        # 5. 비상금/여유금
        emergency_fund = self.calculation_results.get('emergency_fund', {})

        # 6. 브릿지 구간 카드
        bridge_period = self.calculation_results.get('bridge_period', {})

        # 자금 격차 계산
        funding_gap = required_capital - projected_assets
        gap_status = '충분' if funding_gap <= 0 else '부족'

        # 간단한 요약 카드 생성
        # 은퇴 전 권장 지출 (총지출 권장)
        pre_retirement_recommended = round(pre_retirement_expense.get('총지출_권장', 0))

        # 은퇴 후 권장 지출 (중도형 권장)
        post_retirement_recommended = round(post_retirement_expense.get('중도형', {}).get('월지출', 0))

        # 비상금 현재 보유액
        current_emergency_fund = round(emergency_fund.get('현재_보유액', 0))

        # 브릿지 구간 정보
        bridge_info = bridge_period.get('브릿지구간_기본정보', {})
        bridge_years = bridge_info.get('기간', '0년')
        bridge_total = round(bridge_period.get('브릿지구간_자금소요', {}).get('인플레이션반영', 0))

        # 명확한 텍스트 형식의 요약 생성
        summary_lines = []
        summary_lines.append("📌 최종 요약")
        summary_lines.append("━━━━━━━━━━━━━━━━━━━━")

        # 1. 필요 은퇴자산
        if required_capital > 0:
            summary_lines.append(f"- 필요 은퇴자산: {round(required_capital/100000000, 1):.1f}억원")
        else:
            summary_lines.append("- 필요 은퇴자산: 계산 필요")

        # 2. 60세(또는 목표 은퇴나이) 예상 자산
        user_info = self.calculation_results.get('user_info', {})
        retirement_age = user_info.get('summary', {}).get('목표은퇴나이', 60)
        if projected_assets > 0:
            summary_lines.append(f"- {retirement_age}세 예상 자산: {round(projected_assets/100000000, 1):.1f}억원")
        else:
            summary_lines.append(f"- {retirement_age}세 예상 자산: 계산 필요")

        # 3. 자금 격차
        if required_capital > 0 and projected_assets > 0:
            gap_amount = round(abs(funding_gap)/100000000, 1)
            summary_lines.append(f"- 자금 격차: {gap_amount:.1f}억원 {gap_status}")
        else:
            summary_lines.append("- 자금 격차: 계산 필요")

        # 4. 현재 월 저축
        if monthly_savings_capacity != 0:
            summary_lines.append(f"- 현재 월 저축: {round(monthly_savings_capacity/10000)}만원")
        else:
            summary_lines.append("- 현재 월 저축: 계산 필요")

        # 5. 권장 월 지출 (은퇴 전/후)
        if pre_retirement_recommended > 0:
            summary_lines.append(f"- 권장 월 지출 (은퇴 전): {round(pre_retirement_recommended/10000)}만원")
        else:
            summary_lines.append("- 권장 월 지출 (은퇴 전): 계산 필요")

        if post_retirement_recommended > 0:
            summary_lines.append(f"- 권장 월 지출 (은퇴 후): {round(post_retirement_recommended/10000)}만원")
        else:
            summary_lines.append("- 권장 월 지출 (은퇴 후): 계산 필요")

        # 6. 비상금
        if emergency_fund:
            emergency_min = round(emergency_fund.get('권장_최소금액', 0)/10000)
            emergency_max = round(emergency_fund.get('권장_최대금액', 0)/10000)
            summary_lines.append(f"- 비상금/여유금: {round(current_emergency_fund/10000)}만원 (권장: {emergency_min}~{emergency_max}만원)")
        else:
            summary_lines.append("- 비상금/여유금: 계산 필요")

        # 7. 브릿지 기간
        if bridge_total > 0:
            summary_lines.append(f"- 브릿지 기간: {bridge_years} 동안 {round(bridge_total/100000000, 1):.1f}억원 필요")
        elif bridge_period:
            summary_lines.append("- 브릿지 기간: 없음 (은퇴와 동시에 국민연금 수령)")
        else:
            summary_lines.append("- 브릿지 기간: 계산 필요")


        # 텍스트를 하나의 문자열로 결합
        summary_text = "\n".join(summary_lines)

        return {
            'status': 'success',
            'summary_text': summary_text,
            'display_instruction': '위의 summary_text를 그대로 사용자에게 표시하세요. 추가 설명 없이 텍스트만 출력하면 됩니다.'
        }

    def _evaluate_retirement_readiness(self, gap: float, required: float) -> str:
        """은퇴 준비도 평가"""
        if required == 0:
            return "평가 불가"

        gap_ratio = abs(gap / required)

        if gap <= 0:
            return "✅ 우수 - 목표 달성"
        elif gap_ratio < 0.20:
            return "🟢 양호 - 목표에 근접"
        elif gap_ratio < 0.40:
            return "🟡 보통 - 추가 노력 필요"
        elif gap_ratio < 0.60:
            return "🟠 주의 - 상당한 격차 존재"
        else:
            return "🔴 위험 - 전면 재검토 필요"

    def _generate_key_message(self, gap: float, required: float, savings: float) -> str:
        """핵심 메시지 생성"""
        if gap <= 0:
            return "축하합니다! 현재 계획대로라면 은퇴 목표를 달성할 수 있습니다. 정기적인 재점검을 통해 계획을 유지하세요."

        gap_in_uk = round(abs(gap) / 100000000, 1)

        # 필요한 추가 저축 계산 (간단 버전)
        years_to_retirement = self.calculation_results.get('user_info', {}).get('summary', {}).get('목표은퇴나이', 65) - \
                              self.calculation_results.get('user_info', {}).get('summary', {}).get('현재나이', 30)

        if years_to_retirement > 0:
            additional_monthly_needed = gap / (years_to_retirement * 12)
            return f"현재 {gap_in_uk}억원의 자금 격차가 있습니다. " \
                   f"월 약 {round(additional_monthly_needed):,}원을 추가로 저축하거나, " \
                   f"은퇴 계획을 조정하는 것을 권장합니다."
        else:
            return f"현재 {gap_in_uk}억원의 자금 격차가 있습니다. 은퇴 계획의 전면 재검토가 필요합니다."

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
            ),
            Tool(
                name=JeoklipTools.CALCULATE_RECOMMENDED_EXPENSES.value,
                description="권장 월 지출을 계산합니다 (은퇴 전/후)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "monthly_income": {
                            "type": "number",
                            "description": "월 소득"
                        },
                        "current_monthly_expense": {
                            "type": "number",
                            "description": "현재 월 지출"
                        },
                        "current_age": {
                            "type": "integer",
                            "description": "현재 나이"
                        },
                        "target_retirement_age": {
                            "type": "integer",
                            "description": "목표 은퇴 나이"
                        }
                    },
                    "required": ["monthly_income", "current_monthly_expense", "current_age", "target_retirement_age"]
                }
            ),
            Tool(
                name=JeoklipTools.ANALYZE_BRIDGE_PERIOD.value,
                description="브릿지 구간(은퇴 ~ 공적연금 수령 전)을 분석하고 충당 계획을 제시합니다",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "retirement_age": {
                            "type": "integer",
                            "description": "은퇴 나이"
                        },
                        "national_pension_start_age": {
                            "type": "integer",
                            "description": "국민연금 수령 시작 나이 (보통 65세)"
                        },
                        "monthly_expense_post_retirement": {
                            "type": "number",
                            "description": "은퇴 후 월 지출액"
                        },
                        "expected_national_pension": {
                            "type": "number",
                            "description": "예상 국민연금 수령액 (월)"
                        },
                        "scenario": {
                            "type": "object",
                            "description": "경제 시나리오"
                        }
                    },
                    "required": ["retirement_age", "national_pension_start_age", "monthly_expense_post_retirement", "expected_national_pension", "scenario"]
                }
            ),
            Tool(
                name=JeoklipTools.GENERATE_FINAL_SUMMARY.value,
                description="⭐ [필수] 적립메이트 분석의 최종 요약을 생성합니다. 모든 분석이 완료된 후 반드시 이 도구를 호출하여 '📌 최종 요약' 섹션을 사용자에게 표시하세요. 이 도구는 summary_text 필드에 포맷된 요약문을 반환하므로, 해당 텍스트를 그대로 사용자에게 출력하면 됩니다. 매개변수 없이 호출 가능하며, 이전에 계산된 모든 결과를 자동으로 요약합니다.",
                inputSchema={
                    "type": "object",
                    "properties": {}
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

                case JeoklipTools.CALCULATE_RECOMMENDED_EXPENSES.value:
                    result = service.calculate_recommended_expenses(
                        arguments['monthly_income'],
                        arguments['current_monthly_expense'],
                        arguments['current_age'],
                        arguments['target_retirement_age']
                    )

                case JeoklipTools.ANALYZE_BRIDGE_PERIOD.value:
                    result = service.analyze_bridge_period(
                        arguments['retirement_age'],
                        arguments['national_pension_start_age'],
                        arguments['monthly_expense_post_retirement'],
                        arguments['expected_national_pension'],
                        arguments['scenario']
                    )

                case JeoklipTools.GENERATE_FINAL_SUMMARY.value:
                    result = service.generate_final_summary()

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