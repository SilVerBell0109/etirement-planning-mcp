# tests/run_all_tests.py
# 핵심 비즈니스 로직 테스트 실행 (Claude MCP 환경용)
import unittest
import sys
import os

# 핵심 테스트 모듈들만
core_test_modules = [
    'test_korean_financial_constants',
    'test_inchul_korean',
    'test_jeoklip_korean', 
    'test_tooja_korean'
]

def run_core_tests():
    """핵심 비즈니스 로직 테스트만 실행"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 각 모듈의 핵심 테스트만 추가
    for module_name in core_test_modules:
        try:
            module = __import__(module_name)
            tests = loader.loadTestsFromModule(module)
            suite.addTests(tests)
            print(f"✓ {module_name} 핵심 테스트 로드 완료")
        except ImportError as e:
            print(f"✗ {module_name} 테스트 로드 실패: {e}")
        except Exception as e:
            print(f"✗ {module_name} 테스트 로드 중 오류: {e}")
    
    # 테스트 실행
    print(f"\n🚀 핵심 {suite.countTestCases()}개 테스트 실행...")
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    
    # 간단한 결과 요약
    print("\n" + "="*40)
    success_count = result.testsRun - len(result.failures) - len(result.errors)
    success_rate = success_count / result.testsRun * 100 if result.testsRun > 0 else 0
    
    print(f"핵심 테스트 결과: {success_count}/{result.testsRun} 통과 ({success_rate:.1f}%)")
    
    if success_rate == 100:
        print("🎉 핵심 로직 정상!")
    else:
        print("⚠️ 일부 핵심 로직 오류 - 수정 필요")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_core_tests()
    sys.exit(0 if success else 1)
