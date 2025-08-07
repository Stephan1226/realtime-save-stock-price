"""
거래소 개장 시간 확인 및 시장 상태 관리
"""
import pytz
from datetime import datetime, time
from typing import Dict, List
from config import MARKET_HOURS, SYMBOL_MARKET


def is_market_open(market: str) -> bool:
    """
    특정 거래소의 개장 여부 확인
    
    Args:
        market: 거래소 코드 ('US', 'KR')
    
    Returns:
        bool: 개장 여부
    """
    if market not in MARKET_HOURS:
        return False
    
    market_config = MARKET_HOURS[market]
    timezone = pytz.timezone(market_config['timezone'])
    
    # 현재 시간을 해당 시간대로 변환
    current_time = datetime.now(timezone)
    current_time_only = current_time.time()
    
    # 개장/폐장 시간 파싱
    open_time = datetime.strptime(market_config['open_time'], '%H:%M').time()
    close_time = datetime.strptime(market_config['close_time'], '%H:%M').time()
    
    # 주말 확인 (토요일=5, 일요일=6)
    if current_time.weekday() >= 5:
        return False
    
    # 개장 시간 내인지 확인
    return open_time <= current_time_only <= close_time


def get_active_symbols() -> List[str]:
    """
    현재 개장 중인 거래소의 활성 종목 리스트 반환
    
    Returns:
        List[str]: 활성 종목 심볼 리스트
    """
    active_symbols = []
    
    for symbol, market in SYMBOL_MARKET.items():
        if is_market_open(market):
            active_symbols.append(symbol)
    
    return active_symbols


def get_market_status() -> Dict[str, bool]:
    """
    모든 거래소의 개장 상태 반환
    
    Returns:
        Dict[str, bool]: 거래소별 개장 상태
    """
    status = {}
    for market in MARKET_HOURS.keys():
        status[market] = is_market_open(market)
    
    return status


def format_timestamp(dt: datetime) -> str:
    """
    datetime을 MySQL DATETIME 형식으로 변환
    
    Args:
        dt: datetime 객체
    
    Returns:
        str: MySQL DATETIME 형식 문자열
    """
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def get_current_timezone_time(market: str) -> datetime:
    """
    특정 거래소 시간대의 현재 시간 반환
    
    Args:
        market: 거래소 코드
    
    Returns:
        datetime: 해당 시간대의 현재 시간
    """
    if market not in MARKET_HOURS:
        return datetime.now()
    
    timezone = pytz.timezone(MARKET_HOURS[market]['timezone'])
    return datetime.now(timezone) 