# tests/test_jeoklip_korean.py
# 적립메이트 핵심 비즈니스 로직 테스트 (Claude MCP 환경용)
import unittest
import sys
import os

# 상위 디렉토리에서 모듈 import
jeoklip_path = os.path.join(os.path.dirname(__file__), '..', 'mcp_server_jeoklip')
sys.path.insert(0, jeoklip_path)
from server import JeoklipService

class TestJeoklipCoreLogic(unittest.TestCase):
    """적립메이트 핵심 비즈니스 로직 테스트"""

    def setUp(self):
        self.service = JeoklipService()

    def test_retirement_capital_core(self):
        """필요 은퇴자본 계산 핵심 로직 테스트"""
        scenario = {
            'post_retirement_return': 0.035,
            'probability': 0.5
        }
        
        result = self.service.calculate_retirement_capital(
            annual_expense=60_000_000,
            retirement_years=30,
            scenario=scenario
        )
        
        # 기본 구조 확인
        self.assertIn('safe_withdrawal_method', result)
        self.assertIn('present_value_method', result)
        self.assertIn('recommended_total', result)

    def test_swr_band_core(self):
        """SWR 범위 핵심 로직 테스트"""
        # 30년: 기본 3.5%
        band = self.service._swr_band_kor(30)
        self.assertAlmostEqual(band['mid'], 0.035, places=3)

    def test_feasibility_core(self):
        """실행 가능성 핵심 로직 테스트"""
        # 충분한 저축
        score = self.service._feasibility_score_kor(3_000_000, 3_000_000, {'probability': 0.5})
        self.assertAlmostEqual(score, 100.0, places=1)

if __name__ == '__main__':
    unittest.main()
