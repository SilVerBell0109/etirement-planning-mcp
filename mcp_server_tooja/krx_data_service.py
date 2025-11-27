# ============================================================
# 📊 KRX 데이터 모듈 (투자메이트 통합용)
# 파일: mcp_server_tooja/krx_data_service.py
#
# 사용 라이브러리: pykrx (pip install pykrx)
# 참고: https://github.com/sharebook-kr/pykrx
# ============================================================

from datetime import datetime, timedelta
from typing import Dict, List
import numpy as np

# pykrx 라이브러리 import (설치 필요: pip install pykrx)
try:
    from pykrx import stock
    PYKRX_AVAILABLE = True
except ImportError:
    PYKRX_AVAILABLE = False
    print("⚠️ pykrx 라이브러리가 없습니다. pip install pykrx 로 설치하세요.")


class KRXDataService:
    """
    한국거래소(KRX) 데이터 조회 서비스

    기능:
    1. 시장 지수 조회 (KOSPI, KOSDAQ)
    2. 변동성 계산 (실시간)
    3. ETF 정보 조회 및 추천
    4. 개별 종목 시세 조회
    5. 투자자별 매매 동향

    성능 최적화:
    - ETF/종목 정보 캐싱 (세션 내 중복 조회 방지)
    - 캐시 TTL: 10분
    """

    # 캐시 설정
    CACHE_TTL_SECONDS = 600  # 10분

    # ========== 추천 ETF 목록 (계좌별 최적화) ==========
    # IRP/연금계좌용 ETF (해외 ETF, 채권 ETF)
    IRP_RECOMMENDED_ETFS = {
        '해외주식': [
            {'ticker': '379800', 'name': 'KODEX 미국S&P500TR', 'type': '미국대형주'},
            {'ticker': '379810', 'name': 'KODEX 미국나스닥100TR', 'type': '미국기술주'},
            {'ticker': '371460', 'name': 'TIGER 차이나전기차SOLACTIVE', 'type': '중국'},
            {'ticker': '195930', 'name': 'TIGER 유로스탁스50', 'type': '유럽'},
            {'ticker': '238720', 'name': 'KINDEX 일본Nikkei225', 'type': '일본'},
        ],
        '채권': [
            {'ticker': '148070', 'name': 'KOSEF 국고채10년', 'type': '국채장기'},
            {'ticker': '114820', 'name': 'TIGER 국채3년', 'type': '국채단기'},
            {'ticker': '182490', 'name': 'TIGER 단기선진하이일드', 'type': '회사채'},
            {'ticker': '453850', 'name': 'TIGER 미국채10년선물', 'type': '미국채'},
        ],
        '리츠': [
            {'ticker': '329200', 'name': 'TIGER 부동산인프라고배당', 'type': '국내리츠'},
            {'ticker': '352560', 'name': 'TIGER 미국MSCI리츠', 'type': '미국리츠'},
        ],
        '금': [
            {'ticker': '132030', 'name': 'KODEX 골드선물(H)', 'type': '금'},
            {'ticker': '411060', 'name': 'ACE KRX금현물', 'type': 'KRX금'},
        ],
    }

    # ISA용 ETF (배당 중심)
    ISA_RECOMMENDED_ETFS = {
        '고배당': [
            {'ticker': '161510', 'name': 'ARIRANG 고배당주', 'type': '국내고배당'},
            {'ticker': '211900', 'name': 'KODEX 배당성장', 'type': '배당성장'},
            {'ticker': '279530', 'name': 'KODEX 고배당', 'type': '고배당'},
            {'ticker': '458730', 'name': 'TIGER 미국배당다우존스', 'type': '미국배당'},
        ],
    }

    # 일반계좌용 (국내 주식 - 매매차익 비과세)
    GENERAL_RECOMMENDED_STOCKS = {
        '대형주': [
            {'ticker': '005930', 'name': '삼성전자', 'type': '반도체'},
            {'ticker': '000660', 'name': 'SK하이닉스', 'type': '반도체'},
            {'ticker': '373220', 'name': 'LG에너지솔루션', 'type': '2차전지'},
            {'ticker': '005380', 'name': '현대차', 'type': '자동차'},
            {'ticker': '035420', 'name': 'NAVER', 'type': 'IT'},
        ],
    }

    def __init__(self):
        """초기화"""
        # 캐시 저장소
        self._etf_cache: Dict[str, Dict] = {}  # ticker -> {data, timestamp}
        self._stock_cache: Dict[str, Dict] = {}  # ticker -> {data, timestamp}
        self._market_cache: Dict[str, Dict] = {}  # key -> {data, timestamp}

    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """캐시 유효성 검사"""
        if not cache_entry:
            return False
        cached_time = cache_entry.get('timestamp', 0)
        return (datetime.now().timestamp() - cached_time) < self.CACHE_TTL_SECONDS

    def _get_cached_etf(self, ticker: str) -> Dict:
        """캐시된 ETF 정보 조회"""
        cache_entry = self._etf_cache.get(ticker)
        if self._is_cache_valid(cache_entry):
            return cache_entry['data']
        return None

    def _set_cached_etf(self, ticker: str, data: Dict):
        """ETF 정보 캐싱"""
        self._etf_cache[ticker] = {
            'data': data,
            'timestamp': datetime.now().timestamp()
        }

    def clear_cache(self):
        """캐시 초기화"""
        self._etf_cache.clear()
        self._stock_cache.clear()
        self._market_cache.clear()

    # ========== 1. 시장 지수 조회 ==========

    def get_market_index(self, market: str = 'KOSPI', days: int = 30) -> Dict:
        """
        시장 지수 조회

        Args:
            market: 'KOSPI' 또는 'KOSDAQ'
            days: 조회 기간 (일)

        Returns:
            지수 데이터 딕셔너리
        """
        if not PYKRX_AVAILABLE:
            return self._get_fallback_index(market)

        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')

            # 지수 조회
            if market == 'KOSPI':
                ticker = '1001'  # KOSPI 지수
            else:
                ticker = '2001'  # KOSDAQ 지수

            df = stock.get_index_ohlcv(start_date, end_date, ticker)

            if df.empty:
                return self._get_fallback_index(market)

            current_price = float(df['종가'].iloc[-1])
            prev_price = float(df['종가'].iloc[0])
            change_rate = (current_price - prev_price) / prev_price * 100

            # 일별 수익률 계산
            daily_returns = df['종가'].pct_change().dropna()
            volatility = float(daily_returns.std() * np.sqrt(252) * 100)  # 연환산

            return {
                'market': market,
                'current_value': current_price,
                'change_rate_30d': round(change_rate, 2),
                'volatility_annual': round(volatility, 2),
                'high_30d': float(df['고가'].max()),
                'low_30d': float(df['저가'].min()),
                'avg_volume': int(df['거래량'].mean()),
                'data_date': end_date,
                'source': 'KRX (pykrx)'
            }

        except Exception as e:
            print(f"⚠️ KRX 데이터 조회 실패: {e}")
            return self._get_fallback_index(market)

    def _get_fallback_index(self, market: str) -> Dict:
        """API 실패 시 기본값 반환"""
        return {
            'market': market,
            'current_value': 2500 if market == 'KOSPI' else 800,
            'change_rate_30d': 0.0,
            'volatility_annual': 22.0,  # 기존 하드코딩 값
            'high_30d': None,
            'low_30d': None,
            'avg_volume': None,
            'data_date': datetime.now().strftime('%Y%m%d'),
            'source': 'Fallback (하드코딩)'
        }

    # ========== 2. 변동성 계산 ==========

    def get_market_volatility(self, days: int = 60) -> Dict:
        """
        시장 변동성 계산 (KOSPI 기준)

        Args:
            days: 계산 기간 (일)

        Returns:
            변동성 데이터
        """
        if not PYKRX_AVAILABLE:
            return self._get_fallback_volatility()

        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')

            df = stock.get_index_ohlcv(start_date, end_date, '1001')  # KOSPI

            if df.empty or len(df) < 20:
                return self._get_fallback_volatility()

            # 일별 수익률
            daily_returns = df['종가'].pct_change().dropna()

            # 변동성 계산
            volatility_daily = float(daily_returns.std())
            volatility_annual = volatility_daily * np.sqrt(252) * 100

            # 최근 20일 vs 60일 비교 (변동성 추세)
            recent_vol = float(daily_returns[-20:].std()) * np.sqrt(252) * 100

            # 시장 상태 판단
            if volatility_annual > 30:
                regime = 'HIGH'
                recommendation = '주식 비중 -10%p, 채권/현금 +10%p 권장'
            elif volatility_annual > 20:
                regime = 'NORMAL'
                recommendation = '기존 포트폴리오 유지'
            else:
                regime = 'LOW'
                recommendation = '주식 비중 +5%p 고려 가능'

            return {
                'volatility_annual': round(volatility_annual, 2),
                'volatility_daily': round(volatility_daily * 100, 4),
                'recent_20d_volatility': round(recent_vol, 2),
                'volatility_trend': 'UP' if recent_vol > volatility_annual else 'DOWN',
                'regime': regime,
                'recommendation': recommendation,
                'calculation_period': days,
                'data_date': end_date,
                'source': 'KRX (pykrx)'
            }

        except Exception as e:
            print(f"⚠️ 변동성 계산 실패: {e}")
            return self._get_fallback_volatility()

    def _get_fallback_volatility(self) -> Dict:
        """API 실패 시 기본 변동성"""
        return {
            'volatility_annual': 22.0,
            'volatility_daily': 1.39,
            'recent_20d_volatility': 22.0,
            'volatility_trend': 'NORMAL',
            'regime': 'NORMAL',
            'recommendation': '기존 포트폴리오 유지',
            'calculation_period': 60,
            'data_date': datetime.now().strftime('%Y%m%d'),
            'source': 'Fallback (하드코딩 22%)'
        }

    # ========== 3. ETF 정보 조회 ==========

    def get_etf_info(self, ticker: str) -> Dict:
        """
        ETF 상세 정보 조회 (캐싱 적용)

        Args:
            ticker: ETF 종목코드

        Returns:
            ETF 정보 딕셔너리
        """
        # 캐시 확인
        cached = self._get_cached_etf(ticker)
        if cached:
            return cached

        if not PYKRX_AVAILABLE:
            return {'error': 'pykrx 라이브러리 필요'}

        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')

            # 시세 조회
            df = stock.get_etf_ohlcv_by_date(start_date, end_date, ticker)

            if df.empty:
                return {'error': f'ETF {ticker} 데이터 없음'}

            # 수익률 계산
            current_price = float(df['종가'].iloc[-1])

            # 1년 수익률
            if len(df) >= 252:
                year_ago_price = float(df['종가'].iloc[-252])
                return_1y = (current_price - year_ago_price) / year_ago_price * 100
            else:
                return_1y = None

            # 최근 1개월 수익률
            if len(df) >= 20:
                month_ago_price = float(df['종가'].iloc[-20])
                return_1m = (current_price - month_ago_price) / month_ago_price * 100
            else:
                return_1m = None

            # 변동성
            daily_returns = df['종가'].pct_change().dropna()
            volatility = float(daily_returns.std() * np.sqrt(252) * 100)

            # ETF 기본정보
            name = stock.get_etf_ticker_name(ticker)

            result = {
                'ticker': ticker,
                'name': name,
                'current_price': current_price,
                'return_1m': round(return_1m, 2) if return_1m else None,
                'return_1y': round(return_1y, 2) if return_1y else None,
                'volatility_annual': round(volatility, 2),
                'avg_volume': int(df['거래량'].mean()),
                'data_date': end_date,
                'source': 'KRX (pykrx)'
            }

            # 캐시에 저장
            self._set_cached_etf(ticker, result)
            return result

        except Exception as e:
            return {'error': str(e)}

    def get_etf_recommendations_by_account(self, account_type: str,
                                           asset_class: str = None,
                                           sort_by: str = 'return_1y',
                                           min_return: float = None,
                                           top_n: int = None,
                                           include_screening: bool = False) -> List[Dict]:
        """
        계좌 유형별 ETF 추천 (하드코딩 기본목록 + 실시간 스크리닝 통합)

        Args:
            account_type: 'IRP', 'ISA', 'GENERAL'
            asset_class: 자산군 (선택)
            sort_by: 정렬 기준 ('return_1y', 'volatility', 'sharpe_ratio')
            min_return: 최소 수익률 필터 (%)
            top_n: 상위 N개만 반환
            include_screening: 실시간 스크리닝 결과 포함 여부

        Returns:
            기본 추천 + 실시간 스크리닝 통합 ETF 리스트
        """
        recommendations = []
        seen_tickers = set()

        # ========== 1단계: 기본 추천 목록 (세금 최적화 검증 ETF) ==========
        if account_type == 'IRP':
            etf_dict = self.IRP_RECOMMENDED_ETFS
        elif account_type == 'ISA':
            etf_dict = self.ISA_RECOMMENDED_ETFS
        else:  # GENERAL
            etf_dict = self.GENERAL_RECOMMENDED_STOCKS

        # 특정 자산군만 필터링
        if asset_class and asset_class in etf_dict:
            etf_list = etf_dict[asset_class]
        else:
            etf_list = []
            for etfs in etf_dict.values():
                etf_list.extend(etfs)

        # 기본 목록에 실시간 정보 추가
        for etf in etf_list:
            etf_info = self._build_etf_info(etf['ticker'], etf['name'], etf['type'], account_type, is_curated=True)
            recommendations.append(etf_info)
            seen_tickers.add(etf['ticker'])

        # ========== 2단계: 실시간 스크리닝 결과 추가 ==========
        if include_screening and PYKRX_AVAILABLE:
            screening_results = self.get_top_etfs_by_performance(
                top_n=30, min_volume=10000, sort_by=sort_by
            )

            for etf in screening_results:
                if 'error' in etf:
                    continue
                if etf['ticker'] in seen_tickers:
                    continue  # 중복 제외

                # 계좌 유형에 적합한지 간단 필터링
                etf_name = etf.get('name', '').upper()

                # IRP: 해외/채권/금/리츠 ETF 선호
                if account_type == 'IRP':
                    keywords = ['미국', 'S&P', '나스닥', '채권', '국채', '금', '골드', '리츠', '배당', '선진국', '글로벌']
                    if not any(kw in etf_name for kw in keywords):
                        continue
                # ISA: 배당 ETF 선호
                elif account_type == 'ISA':
                    keywords = ['배당', '고배당', '인컴', '리츠']
                    if not any(kw in etf_name for kw in keywords):
                        continue
                # GENERAL: 국내주식 ETF (레버리지/인버스 제외)
                else:
                    if '레버리지' in etf_name or '인버스' in etf_name or '2X' in etf_name:
                        continue

                etf['account'] = account_type
                etf['source'] = 'screening'
                etf['recommendation_reason'] = f"실시간 스크리닝 발굴, {etf.get('recommendation_reason', '')}"
                recommendations.append(etf)
                seen_tickers.add(etf['ticker'])

        # ========== 3단계: 필터링 및 정렬 ==========
        # 최소 수익률 필터링
        if min_return is not None:
            recommendations = [
                r for r in recommendations
                if r.get('return_1y') is not None and r['return_1y'] >= min_return
            ]

        # 정렬
        if recommendations:
            if sort_by == 'return_1y':
                recommendations.sort(
                    key=lambda x: (x.get('return_1y') is not None, x.get('return_1y') or -999),
                    reverse=True
                )
            elif sort_by == 'volatility':
                recommendations.sort(
                    key=lambda x: (x.get('volatility') is not None, -(x.get('volatility') or 999))
                )
            elif sort_by == 'sharpe_ratio':
                recommendations.sort(
                    key=lambda x: (x.get('sharpe_ratio') is not None, x.get('sharpe_ratio') or -999),
                    reverse=True
                )
            else:
                recommendations.sort(
                    key=lambda x: x.get('recommendation_score', 0),
                    reverse=True
                )

        # 상위 N개만 반환
        if top_n is not None and top_n > 0:
            recommendations = recommendations[:top_n]

        return recommendations

    def _build_etf_info(self, ticker: str, name: str, etf_type: str,
                        account_type: str, is_curated: bool = False) -> Dict:
        """ETF 정보 구조체 생성 및 실시간 데이터 조회"""
        etf_info = {
            'ticker': ticker,
            'name': name,
            'type': etf_type,
            'account': account_type,
            'source': 'curated' if is_curated else 'screening',
            'current_price': None,
            'return_1y': None,
            'return_1m': None,
            'volatility': None,
            'sharpe_ratio': None,
            'recommendation_score': 0,
            'recommendation_reason': '세금 최적화 기본 추천' if is_curated else '',
        }

        if not PYKRX_AVAILABLE:
            return etf_info

        try:
            real_info = self.get_etf_info(ticker)
            if 'error' in real_info:
                return etf_info

            etf_info['current_price'] = real_info.get('current_price')
            etf_info['return_1y'] = real_info.get('return_1y')
            etf_info['return_1m'] = real_info.get('return_1m')
            etf_info['volatility'] = real_info.get('volatility_annual')

            # 샤프 비율 계산
            risk_free_rate = 3.5
            if etf_info['return_1y'] is not None and etf_info['volatility'] and etf_info['volatility'] > 0:
                etf_info['sharpe_ratio'] = round(
                    (etf_info['return_1y'] - risk_free_rate) / etf_info['volatility'], 2
                )

            # 추천 점수 계산
            score = 0
            reasons = []

            # 기본 추천 가산점
            if is_curated:
                score += 10
                reasons.append('세금최적화')

            # 1년 수익률 (50%)
            if etf_info['return_1y'] is not None:
                return_score = min(50, max(0, etf_info['return_1y'] * 2.5))
                score += return_score
                if etf_info['return_1y'] > 10:
                    reasons.append(f"고수익({etf_info['return_1y']:+.1f}%)")
                elif etf_info['return_1y'] > 0:
                    reasons.append(f"양호({etf_info['return_1y']:+.1f}%)")

            # 샤프 비율 (30%)
            if etf_info['sharpe_ratio'] is not None:
                sharpe_score = min(30, max(0, (etf_info['sharpe_ratio'] + 1) * 10))
                score += sharpe_score
                if etf_info['sharpe_ratio'] > 0.5:
                    reasons.append(f"SR:{etf_info['sharpe_ratio']:.2f}")

            # 모멘텀 (20%)
            if etf_info['return_1m'] is not None:
                momentum_score = min(20, max(0, (etf_info['return_1m'] + 5) * 2))
                score += momentum_score
                if etf_info['return_1m'] > 3:
                    reasons.append(f"모멘텀({etf_info['return_1m']:+.1f}%)")

            etf_info['recommendation_score'] = round(score, 1)
            etf_info['recommendation_reason'] = ', '.join(reasons) if reasons else '기본 추천'

        except Exception:
            etf_info['recommendation_reason'] = '데이터 조회 실패'

        return etf_info

    # ========== 4. 시가총액 상위 종목 자동 추천 ==========

    def get_top_stocks_by_market_cap(self, market: str = 'ALL', top_n: int = 20,
                                      include_performance: bool = True) -> List[Dict]:
        """
        시가총액 상위 종목 자동 조회 (하드코딩 아님, 실시간 KRX 데이터)

        Args:
            market: 'KOSPI', 'KOSDAQ', 'ALL'
            top_n: 상위 N개 종목
            include_performance: 수익률/변동성 정보 포함 여부

        Returns:
            시가총액 상위 종목 리스트 (실시간 데이터 기반)
        """
        if not PYKRX_AVAILABLE:
            return [{'error': 'pykrx 라이브러리 필요'}]

        try:
            today = datetime.now().strftime('%Y%m%d')
            year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')

            # 시장별 조회
            markets_to_query = []
            if market == 'ALL':
                markets_to_query = ['KOSPI', 'KOSDAQ']
            else:
                markets_to_query = [market]

            all_stocks = []

            for mkt in markets_to_query:
                # 시가총액 데이터 조회
                try:
                    cap_df = stock.get_market_cap_by_ticker(today, market=mkt)
                    if cap_df.empty:
                        # 오늘 데이터가 없으면 최근 영업일 조회
                        for i in range(1, 10):
                            prev_date = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
                            cap_df = stock.get_market_cap_by_ticker(prev_date, market=mkt)
                            if not cap_df.empty:
                                today = prev_date
                                break

                    if cap_df.empty:
                        continue

                    # 시가총액 순 정렬
                    cap_df = cap_df.sort_values('시가총액', ascending=False)

                    for ticker in cap_df.head(top_n * 2).index:  # 여유있게 조회
                        try:
                            name = stock.get_market_ticker_name(ticker)
                            market_cap = int(cap_df.loc[ticker, '시가총액'])
                            current_price = int(cap_df.loc[ticker, '종가'])

                            stock_info = {
                                'ticker': ticker,
                                'name': name,
                                'market': mkt,
                                'current_price': current_price,
                                'market_cap': market_cap,
                                'market_cap_billion': round(market_cap / 1_000_000_000_000, 2),  # 조 단위
                                'return_1y': None,
                                'return_1m': None,
                                'volatility': None,
                                'recommendation_score': 0,
                                'recommendation_reason': '',
                            }

                            # 수익률 정보 추가
                            if include_performance:
                                try:
                                    perf = self._get_stock_performance(ticker, year_ago, today)
                                    stock_info.update(perf)
                                except:
                                    pass

                            all_stocks.append(stock_info)

                        except Exception:
                            continue

                except Exception as e:
                    print(f"⚠️ {mkt} 시가총액 조회 실패: {e}")
                    continue

            # 전체 시가총액 순 정렬
            all_stocks.sort(key=lambda x: x['market_cap'], reverse=True)

            # 추천 점수 계산
            for i, s in enumerate(all_stocks[:top_n]):
                score = 0
                reasons = []

                # 시가총액 순위 점수 (30%)
                rank_score = max(0, 30 - i * 1.5)
                score += rank_score
                if i < 5:
                    reasons.append(f"시총 {i+1}위")

                # 1년 수익률 점수 (40%)
                if s.get('return_1y') is not None:
                    return_score = min(40, max(0, s['return_1y'] * 2))
                    score += return_score
                    if s['return_1y'] > 20:
                        reasons.append(f"고수익({s['return_1y']:+.1f}%)")
                    elif s['return_1y'] > 0:
                        reasons.append(f"양호({s['return_1y']:+.1f}%)")

                # 변동성 점수 (30%) - 낮을수록 좋음
                if s.get('volatility') is not None:
                    vol_score = max(0, 30 - s['volatility'] * 0.5)
                    score += vol_score
                    if s['volatility'] < 25:
                        reasons.append("안정적")

                s['recommendation_score'] = round(score, 1)
                s['recommendation_reason'] = ', '.join(reasons) if reasons else '대형 우량주'

            return all_stocks[:top_n]

        except Exception as e:
            return [{'error': str(e)}]

    def get_top_etfs_by_performance(self, top_n: int = 20, min_volume: int = 10000,
                                     sort_by: str = 'return_1y') -> List[Dict]:
        """
        전체 ETF 중 수익률 상위 종목 자동 스크리닝 (하드코딩 아님)

        Args:
            top_n: 상위 N개 ETF
            min_volume: 최소 일평균 거래량 (유동성 필터)
            sort_by: 정렬 기준 ('return_1y', 'return_1m', 'sharpe_ratio')

        Returns:
            수익률 상위 ETF 리스트
        """
        if not PYKRX_AVAILABLE:
            return [{'error': 'pykrx 라이브러리 필요'}]

        try:
            today = datetime.now().strftime('%Y%m%d')

            # 전체 ETF 목록 조회
            etf_tickers = stock.get_etf_ticker_list(today)
            if not etf_tickers:
                # 오늘 데이터가 없으면 최근 영업일 조회
                for i in range(1, 10):
                    prev_date = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
                    etf_tickers = stock.get_etf_ticker_list(prev_date)
                    if etf_tickers:
                        today = prev_date
                        break

            all_etfs = []

            # 각 ETF 정보 조회 (최대 50개까지만 - 성능 최적화)
            for ticker in etf_tickers[:50]:
                try:
                    etf_info = self.get_etf_info(ticker)
                    if 'error' in etf_info:
                        continue

                    # 거래량 필터
                    if etf_info.get('avg_volume', 0) < min_volume:
                        continue

                    # 샤프 비율 계산
                    risk_free_rate = 3.5
                    sharpe_ratio = None
                    if etf_info.get('return_1y') is not None and etf_info.get('volatility_annual') and etf_info['volatility_annual'] > 0:
                        sharpe_ratio = round(
                            (etf_info['return_1y'] - risk_free_rate) / etf_info['volatility_annual'], 2
                        )

                    etf_data = {
                        'ticker': ticker,
                        'name': etf_info.get('name', ''),
                        'type': 'ETF',
                        'current_price': etf_info.get('current_price'),
                        'return_1y': etf_info.get('return_1y'),
                        'return_1m': etf_info.get('return_1m'),
                        'volatility': etf_info.get('volatility_annual'),
                        'sharpe_ratio': sharpe_ratio,
                        'avg_volume': etf_info.get('avg_volume'),
                        'recommendation_score': 0,
                        'recommendation_reason': '',
                    }

                    # 추천 점수 계산
                    score = 0
                    reasons = []

                    if etf_data['return_1y'] is not None:
                        return_score = min(50, max(0, etf_data['return_1y'] * 2.5))
                        score += return_score
                        if etf_data['return_1y'] > 15:
                            reasons.append(f"고수익({etf_data['return_1y']:+.1f}%)")

                    if sharpe_ratio is not None:
                        sharpe_score = min(30, max(0, (sharpe_ratio + 1) * 10))
                        score += sharpe_score
                        if sharpe_ratio > 0.5:
                            reasons.append(f"우수한 SR({sharpe_ratio:.2f})")

                    if etf_data['return_1m'] is not None and etf_data['return_1m'] > 3:
                        score += 20
                        reasons.append(f"모멘텀({etf_data['return_1m']:+.1f}%)")

                    etf_data['recommendation_score'] = round(score, 1)
                    etf_data['recommendation_reason'] = ', '.join(reasons) if reasons else 'ETF'

                    all_etfs.append(etf_data)

                except Exception:
                    continue

            # 정렬
            if sort_by == 'return_1y':
                all_etfs.sort(key=lambda x: (x['return_1y'] is not None, x['return_1y'] or -999), reverse=True)
            elif sort_by == 'return_1m':
                all_etfs.sort(key=lambda x: (x['return_1m'] is not None, x['return_1m'] or -999), reverse=True)
            elif sort_by == 'sharpe_ratio':
                all_etfs.sort(key=lambda x: (x['sharpe_ratio'] is not None, x['sharpe_ratio'] or -999), reverse=True)
            else:
                all_etfs.sort(key=lambda x: x['recommendation_score'], reverse=True)

            return all_etfs[:top_n]

        except Exception as e:
            return [{'error': str(e)}]

    def _get_stock_performance(self, ticker: str, start_date: str, end_date: str) -> Dict:
        """개별 종목 수익률/변동성 계산"""
        try:
            df = stock.get_market_ohlcv_by_date(start_date, end_date, ticker)

            if df.empty or len(df) < 20:
                return {}

            current_price = float(df['종가'].iloc[-1])

            # 1년 수익률
            return_1y = None
            if len(df) >= 200:
                year_ago_price = float(df['종가'].iloc[0])
                return_1y = round((current_price - year_ago_price) / year_ago_price * 100, 2)

            # 1개월 수익률
            return_1m = None
            if len(df) >= 20:
                month_ago_price = float(df['종가'].iloc[-20])
                return_1m = round((current_price - month_ago_price) / month_ago_price * 100, 2)

            # 변동성
            daily_returns = df['종가'].pct_change().dropna()
            volatility = round(float(daily_returns.std() * np.sqrt(252) * 100), 2)

            return {
                'return_1y': return_1y,
                'return_1m': return_1m,
                'volatility': volatility,
            }

        except Exception:
            return {}

    # ========== 5. 개별 종목 시세 조회 ==========

    def get_stock_price(self, ticker: str, days: int = 30) -> Dict:
        """
        개별 종목 시세 조회

        Args:
            ticker: 종목코드
            days: 조회 기간

        Returns:
            종목 정보
        """
        if not PYKRX_AVAILABLE:
            return {'error': 'pykrx 라이브러리 필요'}

        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')

            df = stock.get_market_ohlcv_by_date(start_date, end_date, ticker)

            if df.empty:
                return {'error': f'종목 {ticker} 데이터 없음'}

            current_price = int(df['종가'].iloc[-1])
            prev_price = int(df['종가'].iloc[0])
            change_rate = (current_price - prev_price) / prev_price * 100

            # 종목명 조회
            name = stock.get_market_ticker_name(ticker)

            return {
                'ticker': ticker,
                'name': name,
                'current_price': current_price,
                'change_rate': round(change_rate, 2),
                'high': int(df['고가'].max()),
                'low': int(df['저가'].min()),
                'avg_volume': int(df['거래량'].mean()),
                'data_date': end_date,
                'source': 'KRX (pykrx)'
            }

        except Exception as e:
            return {'error': str(e)}

    # ========== 6. 시장 전체 현황 ==========

    def get_market_overview(self) -> Dict:
        """
        시장 전체 현황 조회 (KOSPI + KOSDAQ + 변동성) - 캐싱 적용

        Returns:
            시장 현황 종합
        """
        # 캐시 확인
        cache_key = 'market_overview'
        cache_entry = self._market_cache.get(cache_key)
        if self._is_cache_valid(cache_entry):
            return cache_entry['data']

        kospi = self.get_market_index('KOSPI')
        kosdaq = self.get_market_index('KOSDAQ')
        volatility = self.get_market_volatility()

        # 시장 상태 종합 판단
        kospi_change = kospi.get('change_rate_30d', 0)
        vol_regime = volatility.get('regime', 'NORMAL')

        if kospi_change > 5 and vol_regime == 'LOW':
            market_status = 'BULLISH'
            market_comment = '상승장. 주식 비중 유지/확대 고려'
        elif kospi_change < -5 or vol_regime == 'HIGH':
            market_status = 'BEARISH'
            market_comment = '하락/변동장. 방어적 포지션 권장'
        else:
            market_status = 'NEUTRAL'
            market_comment = '보합장. 분할 매수 전략 유지'

        result = {
            'kospi': kospi,
            'kosdaq': kosdaq,
            'volatility': volatility,
            'market_status': market_status,
            'market_comment': market_comment,
            'portfolio_recommendation': self._get_portfolio_adjustment(vol_regime),
            'updated_at': datetime.now().isoformat()
        }

        # 캐시에 저장
        self._market_cache[cache_key] = {
            'data': result,
            'timestamp': datetime.now().timestamp()
        }

        return result

    def _get_portfolio_adjustment(self, vol_regime: str) -> Dict:
        """변동성 기반 포트폴리오 조정 권장"""
        if vol_regime == 'HIGH':
            return {
                'stocks_adjustment': -10,  # -10%p
                'bonds_adjustment': +5,
                'cash_adjustment': +5,
                'reason': '고변동성 환경 - 방어적 배분 권장'
            }
        elif vol_regime == 'LOW':
            return {
                'stocks_adjustment': +5,
                'bonds_adjustment': -3,
                'cash_adjustment': -2,
                'reason': '저변동성 환경 - 공격적 배분 고려'
            }
        else:
            return {
                'stocks_adjustment': 0,
                'bonds_adjustment': 0,
                'cash_adjustment': 0,
                'reason': '정상 변동성 - 기존 배분 유지'
            }

    # ========== 7. 투자자별 매매 동향 ==========

    def get_investor_trading(self, days: int = 5) -> Dict:
        """
        투자자별 매매 동향 (외국인, 기관, 개인) - 캐싱 적용

        Args:
            days: 조회 기간

        Returns:
            투자자별 순매수 현황
        """
        # 캐시 확인
        cache_key = f'investor_trading_{days}'
        cache_entry = self._market_cache.get(cache_key)
        if self._is_cache_valid(cache_entry):
            return cache_entry['data']

        if not PYKRX_AVAILABLE:
            return {'error': 'pykrx 라이브러리 필요'}

        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')

            df = stock.get_market_trading_value_by_investor(
                start_date, end_date, "KOSPI"
            )

            if df.empty:
                return {'error': '투자자 데이터 조회 실패'}

            # 주요 투자자 순매수
            foreign_net = int(df.loc['외국인', '순매수']) if '외국인' in df.index else 0
            inst_net = int(df.loc['기관합계', '순매수']) if '기관합계' in df.index else 0
            retail_net = int(df.loc['개인', '순매수']) if '개인' in df.index else 0

            # 시장 센티먼트 판단
            if foreign_net > 0 and inst_net > 0:
                sentiment = 'POSITIVE'
                comment = '외국인/기관 동반 순매수 - 긍정적 신호'
            elif foreign_net < 0 and inst_net < 0:
                sentiment = 'NEGATIVE'
                comment = '외국인/기관 동반 순매도 - 주의 필요'
            else:
                sentiment = 'MIXED'
                comment = '혼조세 - 관망 권장'

            result = {
                'period_days': days,
                'foreign_net_buy': foreign_net,
                'institution_net_buy': inst_net,
                'retail_net_buy': retail_net,
                'sentiment': sentiment,
                'comment': comment,
                'data_date': end_date,
                'source': 'KRX (pykrx)'
            }

            # 캐시에 저장
            self._market_cache[cache_key] = {
                'data': result,
                'timestamp': datetime.now().timestamp()
            }

            return result

        except Exception as e:
            return {'error': str(e)}


# ============================================================
# 🧪 테스트 코드
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("📊 KRX 데이터 서비스 테스트")
    print("=" * 60)

    service = KRXDataService()

    # 1. 시장 현황
    print("\n1️⃣ 시장 현황 조회")
    overview = service.get_market_overview()
    print(f"  KOSPI: {overview['kospi'].get('current_value')}")
    print(f"  변동성: {overview['volatility'].get('volatility_annual')}%")
    print(f"  시장 상태: {overview['market_status']}")

    # 2. 시가총액 상위 종목 (신규)
    print("\n2️⃣ 시가총액 상위 5개 종목")
    top_stocks = service.get_top_stocks_by_market_cap('KOSPI', top_n=5)
    for s in top_stocks[:5]:
        if 'error' not in s:
            print(f"  - {s['name']} ({s['ticker']}): {s['market_cap_billion']:.1f}조원")

    # 3. ETF 수익률 상위 (신규)
    print("\n3️⃣ ETF 1년 수익률 상위 5개")
    top_etfs = service.get_top_etfs_by_performance(top_n=5)
    for e in top_etfs[:5]:
        if 'error' not in e:
            ret = e.get('return_1y')
            print(f"  - {e['name']}: {ret:+.1f}%" if ret else f"  - {e['name']}")

    # 4. 계좌별 ETF 추천
    print("\n4️⃣ IRP 계좌용 ETF 추천 (1년 수익률순)")
    irp_etfs = service.get_etf_recommendations_by_account('IRP', sort_by='return_1y', top_n=3)
    for etf in irp_etfs:
        ret = etf.get('return_1y')
        print(f"  - {etf['name']}: {ret:+.1f}%" if ret else f"  - {etf['name']}")

    print("\n" + "=" * 60)
    print("✅ 테스트 완료")
