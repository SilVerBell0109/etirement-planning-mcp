# tests/test_tooja_korean.py
# 투자메이트 핵심 비즈니스 로직 테스트 (Claude MCP 환경용)
import unittest
import sys
import os

# 상위 디렉토리에서 모듈 import
tooja_path = os.path.join(os.path.dirname(__file__), '..', 'mcp_server_tooja')
sys.path.insert(0, tooja_path)
from server import ToojaService

class TestToojaCoreLogic(unittest.TestCase):
    """투자메이트 핵심 비즈니스 로직 테스트"""

    def setUp(self):
        self.service = ToojaService()

    def test_equity_cap_core(self):
        """위험점수 → 주식 상한 핵심 로직 테스트"""
        # 위험점수 50: 30% + (50/100)*50% = 55%
        cap = self.service._equity_cap_from_risk_kor(50)
        self.assertAlmostEqual(cap, 0.55, places=2)

    def test_life_phase_core(self):
        """생애주기 단계 핵심 로직 테스트"""
        # 40세, 25년 남음: accumulation
        phase = self.service._determine_life_phase(40, 25)
        self.assertEqual(phase, 'accumulation')

    def test_allocation_core(self):
        """자산 배분 핵심 로직 테스트"""
        allocation = self.service._lifecycle_allocation_kor(
            age=40, risk_level='moderate', phase='accumulation', risk_score=50
        )
        
        # 기본 구조 확인
        self.assertIn('국내주식', allocation)
        self.assertIn('해외주식', allocation)
        self.assertIn('채권', allocation)
        
        # 비중 합계 100% 확인
        total = sum(allocation.values())
        self.assertEqual(total, 100)

if __name__ == '__main__':
    unittest.main()
