export const TOP_INDICES = [
    { name: 'KOSPI', value: '2,512.40', change: '-15.20', changePercent: '-0.60%', up: false },
    { name: 'KOSDAQ', value: '884.20', change: '+5.30', changePercent: '+0.60%', up: true },
    { name: 'KOSPI 200', value: '335.50', change: '-1.20', changePercent: '-0.36%', up: false },
]

export const INVESTOR_TRENDS = [
    { type: '개인', value: '+3,420억', up: true },
    { type: '외국인', value: '-1,230억', up: false },
    { type: '기관', value: '-2,150억', up: false },
]

export const POPULAR_SEARCHES = [
    { rank: 1, name: '삼성전자', price: '72,100', up: true },
    { rank: 2, name: 'SK하이닉스', price: '136,500', up: false },
    { rank: 3, name: '에코프로', price: '654,000', up: true },
    { rank: 4, name: 'POSCO홀딩스', price: '450,000', up: false },
    { rank: 5, name: '한미반도체', price: '58,200', up: true },
    { rank: 6, name: 'LG에너지솔루션', price: '410,000', up: false },
    { rank: 7, name: '현대차', price: '198,000', up: true },
    { rank: 8, name: 'NAVER', price: '210,000', up: false },
    { rank: 9, name: '카카오', price: '54,300', up: true },
    { rank: 10, name: '두산로보틱스', price: '85,400', up: true },
]

export const THEME_RANKINGS = [
    { name: 'HBM (고대역폭메모리)', change: '+4.25%', avg3d: '+1.20%', up: 12, flat: 2, down: 4, lead: 'SK하이닉스' },
    { name: '온디바이스 AI', change: '+3.80%', avg3d: '+0.90%', up: 8, flat: 1, down: 2, lead: '제주반도체' },
    { name: '초전도체', change: '+2.15%', avg3d: '-1.50%', up: 5, flat: 0, down: 8, lead: '신성델타테크' },
    { name: '2차전지(소재)', change: '-1.20%', avg3d: '-0.50%', up: 4, flat: 1, down: 15, lead: '에코프로비엠' },
    { name: '자동차부품', change: '-0.80%', avg3d: '+0.20%', up: 10, flat: 5, down: 20, lead: '현대모비스' },
]

export const INDUSTRY_RANKINGS = [
    { name: '반도체와반도체장비', change: '+2.10%', total: 145, up: 98, flat: 12, down: 35 },
    { name: '양방향미디어와서비스', change: '+1.50%', total: 24, up: 15, flat: 3, down: 6 },
    { name: '자동차', change: '+1.20%', total: 15, up: 10, flat: 2, down: 3 },
    { name: '제약', change: '-0.50%', total: 112, up: 45, flat: 10, down: 57 },
    { name: '화학', change: '-1.10%', total: 85, up: 20, flat: 5, down: 60 },
]

export const RECOMENDATIONS = [
    { rank: 1, ticker: '005930', name: '삼성전자', weight: '15.5%', target: 'BUY', score: 92 },
    { rank: 2, ticker: '000660', name: 'SK하이닉스', weight: '12.0%', target: 'BUY', score: 89 },
    { rank: 3, ticker: '035420', name: 'NAVER', weight: '8.5%', target: 'BUY', score: 85 },
    { rank: 4, ticker: '005380', name: '현대차', weight: '7.2%', target: 'WAIT', score: 78 },
    { rank: 5, ticker: '051910', name: 'LG화학', weight: '6.0%', target: 'SELL', score: 65 },
]

export const SIGNALS = [
    { ticker: '005930', name: '삼성전자', date: '2023-10-24', type: 'BUY', horizon: '1D', price: '72,100', reason: 'RSI 과매도 구간 진입 및 외국인 수급 유입 확인' },
    { ticker: '000660', name: 'SK하이닉스', date: '2023-10-24', type: 'WAIT', horizon: '1D', price: '136,500', reason: '20일 이평선 저항 테스트 중' },
    { ticker: '035420', name: 'NAVER', date: '2023-10-23', type: 'BUY', horizon: '1D', price: '210,000', reason: '실적 발표 호조 예상 및 기관 매수세' },
    { ticker: '051910', name: 'LG화학', date: '2023-10-23', type: 'SELL', horizon: '1W', price: '510,000', reason: '2차전지 섹터 전반적 조정세 심화' },
]
