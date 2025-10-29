# tests/test_korean_financial_constants.py
# 한국 금융 상수 핵심 테스트 (Claude MCP 환경용)
import unittest
import sys
import os

# 상위 디렉토리에서 config 모듈 import
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
from financial_constants_2025 import KOR_2025, marginal_rate_from_brackets, get_healthcare_factor

class TestKoreanFinancialConstants(unittest.TestCase):
    """한국 금융 상수 핵심 테스트"""

    def test_swr_core(self):
        """SWR 핵심 로직 테스트"""
        # 30년: 3.5% (기본값)
        swr_30 = KOR_2025.SWR.adjust_by_duration(30)
        self.assertAlmostEqual(swr_30, 0.035, places=3)

    def test_tax_core(self):
        """세율 핵심 로직 테스트"""
        # 분리과세 한도 (수정됨: 1,200만원)
        self.assertEqual(KOR_2025.TAX.pension_separated_cap, 12_000_000)
        
        # 이자/배당 세율
        self.assertEqual(KOR_2025.TAX.interest_dividend, 0.154)

    def test_market_core(self):
        """시장 특성 핵심 테스트"""
        # 국내/해외 주식 비중 (수정됨: 40%/60%)
        self.assertEqual(KOR_2025.MKT.domestic_equity_ratio, 0.40)
        self.assertEqual(KOR_2025.MKT.foreign_equity_ratio, 0.60)

    def test_healthcare_core(self):
        """의료비 핵심 로직 테스트"""
        # 65-70세: 1.0
        factor = get_healthcare_factor(67)
        self.assertEqual(factor, 1.0)

if __name__ == '__main__':
    unittest.main()
