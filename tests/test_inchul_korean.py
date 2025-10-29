# tests/test_inchul_korean.py
# 인출메이트 핵심 비즈니스 로직 테스트 (Claude MCP 환경용)
import unittest
import sys
import os

# 상위 디렉토리에서 모듈 import
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'mcp_server_inchul'))
from server import WithdrawalCalculator, InchulService

class TestInchulCoreLogic(unittest.TestCase):
    """인출메이트 핵심 비즈니스 로직 테스트"""

    def setUp(self):
        self.calculator = WithdrawalCalculator()
        self.service = InchulService()

    def test_swr_calculation_core(self):
        """SWR 계산 핵심 로직 테스트"""
        # 기본값 3.5% 사용
        result = self.calculator.calculate_swr(100_000_000)
        self.assertAlmostEqual(result, 3_500_000, places=0)

    def test_tax_optimization_core(self):
        """세금 최적화 핵심 로직 테스트"""
        # 연금 분리과세 우선 (1,500만원까지)
        result = self.service._optimal_withdrawal_split_kor(
            taxable_balance=50_000_000,
            pension_balance=20_000_000,
            annual_need=10_000_000
        )
        
        # 연금 분리과세로 충분
        self.assertEqual(result['pension_separated'], 10_000_000)
        self.assertEqual(result['pension_comprehensive'], 0)
        self.assertEqual(result['taxable'], 0)

    def test_guardrail_core(self):
        """가드레일 핵심 로직 테스트"""
        # 정상 범위
        result = self.calculator.apply_guardrails(
            100_000_000, 100_000_000, 3_500_000
        )
        self.assertEqual(result['adjustment'], 'maintain')
        
        # 하락 25% (감액)
        result = self.calculator.apply_guardrails(
            100_000_000, 75_000_000, 3_500_000
        )
        self.assertEqual(result['adjustment'], 'decrease')

if __name__ == '__main__':
    unittest.main()
