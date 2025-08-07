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
    # 미국 종목
    'AAPL': 'US',
    'GOOGL': 'US', 
    'MSFT': 'US',
    'AMZN': 'US',
    'TSLA': 'US',
    'META': 'US',
    'NVDA': 'US',
    'JPM': 'US',
    'WMT': 'US',
    'DIS': 'US',
    # 한국 종목 (필요시 추가)
    '005930.KS': 'KR',  # 삼성전자
    '000660.KS': 'KR',  # SK하이닉스
}

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
DATA_COLLECTION_INTERVAL = 10  # 초
YFINANCE_PERIOD = "1d"
YFINANCE_INTERVAL = "1m"

# FastAPI 설정
API_HOST = "0.0.0.0"
API_PORT = 8000 