"""
애플리케이션 설정 및 데이터베이스 연결 정보
"""
import os
from typing import Dict, List

# 데이터베이스 설정
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'your_user'),
    'password': os.getenv('DB_PASSWORD', 'your_password'),
    'db': os.getenv('DB_NAME', 'stocks'),
    'charset': 'utf8mb4',
    'autocommit': True
}

# 주식 심볼 및 거래소 정보
SYMBOL_MARKET: Dict[str, str] = {
    # 한국 종목 전환
    '005930.KS': 'KR',  # 삼성전자
    '000660.KS': 'KR',  # SK하이닉스
    '035420.KS': 'KR',  # NAVER
    '035720.KS': 'KR',  # 카카오
    '005380.KS': 'KR',  # 현대차
    '051910.KS': 'KR',  # LG화학
    '068270.KS': 'KR',  # 셀트리온
    '207940.KS': 'KR',  # 삼성바이오로직스
}

# 수집 대상 심볼(미리 정한 종목만 수집)
TARGET_SYMBOLS: List[str] = [
    '005930.KS',  # 삼성전자
    '000660.KS',  # SK하이닉스
    '035420.KS',  # NAVER
    '035720.KS',  # 카카오
]

# 거래소별 개장 시간 (ET/KST)
MARKET_HOURS = {
    'US': {
        'timezone': 'US/Eastern',
        'open_time': '09:30',
        'close_time': '16:00'
    },
    'KR': {
        'timezone': 'Asia/Seoul', 
        'open_time': '09:00',
        'close_time': '15:30'
    }
}

# 데이터 수집 설정
DATA_COLLECTION_INTERVAL = 60  # 초 (1분)
YFINANCE_PERIOD = "1d"
YFINANCE_INTERVAL = "1m"

# FastAPI 설정
API_HOST = "0.0.0.0"
API_PORT = 8000 