"""
은퇴 계획 HTML 리포트 생성 모듈
PDF 변환에 최적화된 HTML 리포트를 생성합니다.
"""

from datetime import datetime


def generate_retirement_report_html(user_info: dict, years_to_retirement: int, 
                                    retirement_period: int, required_capital: float,
                                    projected_assets: float, funding_gap: float, 
                                    monthly_savings: float, portfolio: dict,
                                    annual_withdrawal: float, monthly_withdrawal: float,
                                    bucket1: float, bucket2: float, bucket3: float) -> str:
    """
    PDF 변환에 최적화된 HTML 콘텐츠 생성
    
    Args:
        user_info: 사용자 기본 정보
        years_to_retirement: 은퇴까지 남은 년수
        retirement_period: 은퇴 후 기간
        required_capital: 필요 은퇴 자본
        projected_assets: 예상 자산
        funding_gap: 자금 격차
        monthly_savings: 필요 월 저축액
        portfolio: 포트폴리오 배분
        annual_withdrawal: 연간 인출액
        monthly_withdrawal: 월 인출액
        bucket1, bucket2, bucket3: 3버킷 금액
        
    Returns:
        str: HTML 문서 전체
    """
    
    current_age = user_info.get('current_age', 40)
    retirement_age = user_info.get('retirement_age', 65)
    monthly_income = user_info.get('monthly_income', 5000000)
    monthly_expense = user_info.get('monthly_expense', 3500000)
    current_assets = user_info.get('current_assets', {})
    
    html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>나의 은퇴 설계 종합 리포트</title>
    <style>
        @page {{
            size: A4;
            margin: 2cm;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
            line-height: 1.6;
            color: #333;
            background: white;
        }}
        
        .container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        /* 표지 */
        .cover {{
            text-align: center;
            padding: 100px 20px;
            page-break-after: always;
        }}
        
        .cover h1 {{
            font-size: 36px;
            color: #2c3e50;
            margin-bottom: 20px;
        }}
        
        .cover .subtitle {{
            font-size: 18px;
            color: #7f8c8d;
            margin-bottom: 40px;
        }}
        
        .cover .date {{
            font-size: 14px;
            color: #95a5a6;
        }}
        
        /* 섹션 */
        .section {{
            margin-bottom: 40px;
            page-break-inside: avoid;
        }}
        
        .section-title {{
            font-size: 24px;
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        
        .subsection-title {{
            font-size: 18px;
            color: #34495e;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        
        /* 테이블 */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        
        th {{
            background-color: #3498db;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: bold;
        }}
        
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #ddd;
        }}
        
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        
        /* 하이라이트 박스 */
        .highlight-box {{
            background-color: #e8f4f8;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin: 20px 0;
        }}
        
        .highlight-box strong {{
            color: #2c3e50;
        }}
        
        /* 경고 박스 */
        .warning-box {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
        }}
        
        /* 성공 박스 */
        .success-box {{
            background-color: #d4edda;
            border-left: 4px solid #28a745;
            padding: 15px;
            margin: 20px 0;
        }}
        
        /* 리스트 */
        ul, ol {{
            margin-left: 20px;
            margin-bottom: 15px;
        }}
        
        li {{
            margin-bottom: 8px;
        }}
        
        /* 차트 바 */
        .chart-bar {{
            display: flex;
            align-items: center;
            margin: 10px 0;
        }}
        
        .chart-label {{
            width: 100px;
            font-weight: bold;
        }}
        
        .chart-bar-fill {{
            height: 30px;
            background: linear-gradient(90deg, #3498db, #2980b9);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
        }}
        
        /* 페이지 브레이크 */
        .page-break {{
            page-break-after: always;
        }}
        
        /* 프린트 설정 */
        @media print {{
            body {{
                background: white;
            }}
            
            .container {{
                max-width: 100%;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- 표지 -->
        <div class="cover">
            <h1>🎯 나의 은퇴 설계</h1>
            <div class="subtitle">종합 재무 계획 리포트</div>
            <div class="date">생성일: {datetime.now().strftime('%Y년 %m월 %d일')}</div>
        </div>
        
        <!-- 1. 사용자 정보 요약 -->
        <div class="section">
            <h2 class="section-title">📋 1. 기본 정보</h2>
            <table>
                <tr>
                    <th>항목</th>
                    <th>내용</th>
                </tr>
                <tr>
                    <td>현재 나이</td>
                    <td>{current_age}세</td>
                </tr>
                <tr>
                    <td>목표 은퇴 나이</td>
                    <td>{retirement_age}세 ({years_to_retirement}년 후)</td>
                </tr>
                <tr>
                    <td>예상 수명</td>
                    <td>{user_info.get('life_expectancy', 90)}세</td>
                </tr>
                <tr>
                    <td>은퇴 후 기간</td>
                    <td>{retirement_period}년</td>
                </tr>
                <tr>
                    <td>월 소득</td>
                    <td>{monthly_income:,.0f}원</td>
                </tr>
                <tr>
                    <td>월 지출</td>
                    <td>{monthly_expense:,.0f}원</td>
                </tr>
                <tr>
                    <td>월 저축 가능액</td>
                    <td>{(monthly_income - monthly_expense):,.0f}원</td>
                </tr>
            </table>
            
            <h3 class="subsection-title">현재 보유 자산</h3>
            <table>
                <tr>
                    <th>자산 종류</th>
                    <th>금액</th>
                </tr>
'''
    
    for asset_name, amount in current_assets.items():
        html += f'''                <tr>
                    <td>{asset_name}</td>
                    <td>{amount:,.0f}원</td>
                </tr>
'''
    
    total_assets = sum(current_assets.values())
    html += f'''                <tr>
                    <td><strong>총 자산</strong></td>
                    <td><strong>{total_assets:,.0f}원</strong></td>
                </tr>
            </table>
        </div>
        
        <div class="page-break"></div>
        
        <!-- 2. 적립 계획 -->
        <div class="section">
            <h2 class="section-title">💰 2. 적립 계획 (Accumulation)</h2>
            
            <div class="highlight-box">
                <strong>핵심 질문:</strong> 은퇴 시점까지 얼마를 모아야 하는가?
            </div>
            
            <h3 class="subsection-title">필요 은퇴 자본</h3>
            <table>
                <tr>
                    <th>항목</th>
                    <th>금액</th>
                </tr>
                <tr>
                    <td>연간 목표 지출</td>
                    <td>{monthly_expense * 12:,.0f}원</td>
                </tr>
                <tr>
                    <td>안전인출률 (SWR)</td>
                    <td>3.25%</td>
                </tr>
                <tr>
                    <td><strong>필요 은퇴 자본</strong></td>
                    <td><strong>{required_capital:,.0f}원</strong></td>
                </tr>
            </table>
            
            <h3 class="subsection-title">자산 프로젝션 ({years_to_retirement}년 후)</h3>
            <table>
                <tr>
                    <th>항목</th>
                    <th>금액</th>
                </tr>
                <tr>
                    <td>현재 자산</td>
                    <td>{total_assets:,.0f}원</td>
                </tr>
                <tr>
                    <td>예상 연평균 수익률</td>
                    <td>4.0%</td>
                </tr>
                <tr>
                    <td><strong>{years_to_retirement}년 후 예상 자산</strong></td>
                    <td><strong>{projected_assets:,.0f}원</strong></td>
                </tr>
            </table>
            
            <h3 class="subsection-title">자금 격차 분석</h3>
'''
    
    if funding_gap > 0:
        html += f'''            <div class="warning-box">
                <strong>⚠️ 부족:</strong> {funding_gap:,.0f}원이 부족합니다.<br>
                필요 자본의 {(funding_gap/required_capital*100):.1f}%를 추가로 준비해야 합니다.
            </div>
            
            <h3 class="subsection-title">추천 저축 계획</h3>
            <table>
                <tr>
                    <th>항목</th>
                    <th>금액</th>
                </tr>
                <tr>
                    <td>필요 월 저축액</td>
                    <td><strong>{monthly_savings:,.0f}원</strong></td>
                </tr>
                <tr>
                    <td>필요 연 저축액</td>
                    <td>{monthly_savings * 12:,.0f}원</td>
                </tr>
                <tr>
                    <td>현재 월 저축 가능액</td>
                    <td>{(monthly_income - monthly_expense):,.0f}원</td>
                </tr>
            </table>
            
            <div class="highlight-box">
                <strong>💡 실행 방안:</strong>
                <ul>
                    <li>IRP 및 연금저축 계좌를 우선 활용 (세액공제 혜택)</li>
                    <li>월급에서 자동이체 설정</li>
                    <li>목표 저축액 달성 어려울 시 은퇴 시기 1-2년 연장 검토</li>
                </ul>
            </div>
'''
    else:
        html += f'''            <div class="success-box">
                <strong>✅ 충분:</strong> 현재 계획대로라면 은퇴 자금이 충분합니다!<br>
                여유 자금: {abs(funding_gap):,.0f}원
            </div>
'''
    
    html += '''        </div>
        
        <div class="page-break"></div>
        
        <!-- 3. 투자 전략 -->
        <div class="section">
            <h2 class="section-title">📈 3. 투자 전략 (Investment)</h2>
            
            <div class="highlight-box">
                <strong>핵심 질문:</strong> 모은 돈을 어떻게 운용할 것인가?
            </div>
            
            <h3 class="subsection-title">추천 자산 배분</h3>
'''
    
    for asset, ratio in portfolio.items():
        html += f'''            <div class="chart-bar">
                <div class="chart-label">{asset}</div>
                <div class="chart-bar-fill" style="width: {ratio * 3}px;">{ratio}%</div>
            </div>
'''
    
    html += f'''            
            <h3 class="subsection-title">포트폴리오 특성</h3>
            <ul>
                <li><strong>위험 수준:</strong> 중립적 (나이 {current_age}세 기준)</li>
                <li><strong>예상 연수익률:</strong> 4-6%</li>
                <li><strong>예상 변동성:</strong> 10-15%</li>
            </ul>
            
            <h3 class="subsection-title">계좌별 실행 전략</h3>
            <table>
                <tr>
                    <th>계좌 유형</th>
                    <th>우선 배치 자산</th>
                    <th>이유</th>
                </tr>
                <tr>
                    <td>IRP</td>
                    <td>주식 50%, 채권 50%</td>
                    <td>세액공제 및 이연과세</td>
                </tr>
                <tr>
                    <td>연금저축</td>
                    <td>주식 70%, 채권 30%</td>
                    <td>장기 성장 자산 편입</td>
                </tr>
                <tr>
                    <td>일반 계좌</td>
                    <td>금 40%, 리츠 30%, 배당주 30%</td>
                    <td>분산 및 배당 수익</td>
                </tr>
            </table>
            
            <div class="highlight-box">
                <strong>💡 리밸런싱 규칙:</strong>
                <ul>
                    <li>연 1회 (매년 12월) 정기 리밸런싱</li>
                    <li>목표 배분 대비 ±5% 이상 차이 시 조정</li>
                    <li>급격한 시장 변동 시 긴급 리밸런싱 (±10% 이상)</li>
                </ul>
            </div>
        </div>
        
        <div class="page-break"></div>
        
        <!-- 4. 인출 전략 -->
        <div class="section">
            <h2 class="section-title">🏦 4. 인출 전략 (Withdrawal)</h2>
            
            <div class="highlight-box">
                <strong>핵심 질문:</strong> 은퇴 후 어떻게, 얼마나 인출할 것인가?
            </div>
            
            <h3 class="subsection-title">안전 인출 계획</h3>
            <table>
                <tr>
                    <th>항목</th>
                    <th>금액</th>
                </tr>
                <tr>
                    <td>안전인출률</td>
                    <td>3.25% (균형적)</td>
                </tr>
                <tr>
                    <td><strong>연간 인출액</strong></td>
                    <td><strong>{annual_withdrawal:,.0f}원</strong></td>
                </tr>
                <tr>
                    <td><strong>월 인출액</strong></td>
                    <td><strong>{monthly_withdrawal:,.0f}원</strong></td>
                </tr>
            </table>
            
            <h3 class="subsection-title">3버킷 전략</h3>
            <p>시장 하락기에도 안정적인 생활비 확보를 위한 전략</p>
            
            <table>
                <tr>
                    <th>버킷</th>
                    <th>자산 유형</th>
                    <th>금액</th>
                    <th>용도</th>
                </tr>
                <tr>
                    <td>Bucket 1</td>
                    <td>현금, MMF, 단기채</td>
                    <td>{bucket1:,.0f}원</td>
                    <td>2년분 생활비 (즉시 인출)</td>
                </tr>
                <tr>
                    <td>Bucket 2</td>
                    <td>중기채, 배당주, 리츠</td>
                    <td>{bucket2:,.0f}원</td>
                    <td>5년분 생활비 (완충)</td>
                </tr>
                <tr>
                    <td>Bucket 3</td>
                    <td>주식, 성장형 ETF</td>
                    <td>{bucket3:,.0f}원</td>
                    <td>장기 성장 (회복 대기)</td>
                </tr>
            </table>
            
            <div class="warning-box">
                <strong>⚠️ 시장 하락 시:</strong>
                <ul>
                    <li>Bucket 1, 2에서만 생활비 충당</li>
                    <li>Bucket 3 매도 중단 → 시장 회복 대기</li>
                    <li>필수 지출만 유지</li>
                </ul>
            </div>
            
            <h3 class="subsection-title">절세 인출 순서</h3>
            <ol>
                <li><strong>일반계좌 원금</strong> → 비과세</li>
                <li><strong>일반계좌 이익금</strong> → 15.4% 세율</li>
                <li><strong>연금계좌</strong> → 3.3-5.5% 세율 (최소한만)</li>
                <li><strong>부동산/주택연금</strong> → 필요시</li>
            </ol>
            
            <div class="highlight-box">
                <strong>💡 Guyton-Klinger 가드레일:</strong><br>
                포트폴리오 가치가 목표 대비 ±20% 이탈 시 인출액 자동 조정 (±10%)
            </div>
        </div>
        
        <div class="page-break"></div>
        
        <!-- 5. 실행 체크리스트 -->
        <div class="section">
            <h2 class="section-title">✅ 5. 실행 체크리스트</h2>
            
            <h3 class="subsection-title">지금 당장 (이번 주)</h3>
            <ol>
                <li>IRP 및 연금저축 계좌 개설 (미보유시)</li>
                <li>월 자동이체 설정 (저축액: {monthly_savings:,.0f}원)</li>
                <li>기존 자산 정리 및 목표 배분으로 조정</li>
            </ol>
            
            <h3 class="subsection-title">이번 달</h3>
            <ol>
                <li>세제혜택 계좌 우선 투자 시작</li>
                <li>투자 포트폴리오 구성 완료</li>
                <li>월별 저축 실행</li>
            </ol>
            
            <h3 class="subsection-title">분기별</h3>
            <ol>
                <li>Q1: 전년도 세금 정산, 저축 실적 점검</li>
                <li>Q2: 상반기 수익률 점검, 저축액 조정 필요 여부 확인</li>
                <li>Q3: 포트폴리오 밸런스 확인</li>
                <li>Q4: 연간 리밸런싱, 다음 연도 계획 수립</li>
            </ol>
            
            <h3 class="subsection-title">연간</h3>
            <ol>
                <li>리밸런싱 실시 (목표 배분 복원)</li>
                <li>은퇴 계획 전반 재검토</li>
                <li>세금 신고 및 공제 최대화</li>
            </ol>
        </div>
        
        <!-- 6. 주의사항 -->
        <div class="section">
            <h2 class="section-title">⚠️ 6. 주의사항</h2>
            
            <div class="warning-box">
                <strong>면책 조항</strong><br>
                이 리포트는 교육 및 정보 제공 목적으로만 제공됩니다.
                <ul>
                    <li>실제 투자 결정 전 반드시 전문가와 상담하세요</li>
                    <li>제공된 계산은 참고용이며 보장되지 않습니다</li>
                    <li>개인의 재무 상황에 따라 결과가 다를 수 있습니다</li>
                    <li>시장 상황 변화에 따라 계획 조정이 필요할 수 있습니다</li>
                </ul>
            </div>
        </div>
        
        <!-- 푸터 -->
        <div style="text-align: center; margin-top: 50px; padding: 20px; border-top: 2px solid #ddd;">
            <p style="color: #7f8c8d;">생성일: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}</p>
            <p style="color: #7f8c8d;">Powered by 적립메이트 · 투자메이트 · 인출메이트</p>
        </div>
    </div>
</body>
</html>'''
    
    return html
