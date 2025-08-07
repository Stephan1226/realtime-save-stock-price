"""
yfinance를 사용한 주식 데이터 수집기
"""
import yfinance as yf
import asyncio
import logging
from datetime import datetime
from typing import List, Tuple, Optional
from config import YFINANCE_PERIOD, YFINANCE_INTERVAL
from market_utils import get_active_symbols, format_timestamp, get_current_timezone_time
from database import db_manager

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StockDataCollector:
    """주식 데이터 수집 클래스"""
    
    def __init__(self):
        self.is_running = False
    
    async def collect_stock_data(self) -> List[Tuple[str, float, str]]:
        """
        활성 종목들의 주식 데이터 수집
        
        Returns:
            List[Tuple[str, float, str]]: (symbol, price, timestamp) 튜플 리스트
        """
        active_symbols = get_active_symbols()
        
        if not active_symbols:
            logger.info("현재 개장 중인 거래소가 없습니다.")
            return []
        
        logger.info(f"활성 종목 {len(active_symbols)}개 데이터 수집 시작")
        
        try:
            # yfinance를 사용해 배치로 데이터 요청
            # period="1d", interval="1m"으로 최신 종가 데이터 수집
            # 10초 간격 요청이지만 yfinance는 1분 간격으로 데이터 갱신됨
            tickers = yf.download(
                tickers=active_symbols,
                period=YFINANCE_PERIOD,
                interval=YFINANCE_INTERVAL,
                group_by='ticker',
                progress=False
            )
            
            collected_data = []
            current_time = datetime.now()
            
            for symbol in active_symbols:
                try:
                    # 단일 종목인 경우와 다중 종목인 경우 처리
                    if len(active_symbols) == 1:
                        price_data = tickers['Close']
                    else:
                        price_data = tickers[symbol]['Close']
                    
                    if price_data is not None and len(price_data) > 0:
                        # 최신 종가 가져오기
                        latest_price = price_data.iloc[-1]
                        
                        if not (latest_price is None or latest_price != latest_price):  # NaN 체크
                            timestamp = format_timestamp(current_time)
                            collected_data.append((symbol, float(latest_price), timestamp))
                            logger.debug(f"{symbol}: ${latest_price:.2f}")
                        else:
                            logger.warning(f"{symbol}: 유효하지 않은 가격 데이터")
                    else:
                        logger.warning(f"{symbol}: 가격 데이터 없음")
                        
                except Exception as e:
                    logger.error(f"{symbol} 데이터 처리 중 오류: {e}")
                    continue
            
            logger.info(f"성공적으로 {len(collected_data)}개 종목 데이터 수집 완료")
            return collected_data
            
        except Exception as e:
            logger.error(f"주식 데이터 수집 중 오류 발생: {e}")
            return []
    
    async def save_to_database(self, data: List[Tuple[str, float, str]]) -> bool:
        """
        수집된 데이터를 데이터베이스에 저장
        
        Args:
            data: (symbol, price, timestamp) 튜플 리스트
        
        Returns:
            bool: 저장 성공 여부
        """
        if not data:
            return True
        
        # 데이터베이스 연결 상태 확인
        if db_manager.connection is None or not db_manager.connection.open:
            logger.warning("데이터베이스가 연결되지 않아 데이터 저장을 건너뜁니다")
            return False
        
        return db_manager.bulk_insert_prices(data)
    
    async def collect_and_save(self) -> bool:
        """
        데이터 수집 및 저장을 한 번에 수행
        
        Returns:
            bool: 성공 여부
        """
        try:
            # 데이터 수집
            stock_data = await self.collect_stock_data()
            
            if stock_data:
                # 데이터베이스에 저장
                success = await self.save_to_database(stock_data)
                return success
            else:
                logger.info("저장할 데이터가 없습니다.")
                return True
                
        except Exception as e:
            logger.error(f"데이터 수집 및 저장 중 오류: {e}")
            return False


# 전역 데이터 수집기 인스턴스
stock_collector = StockDataCollector() 