"""
yfinance를 사용한 주식 데이터 수집기
"""
import yfinance as yf
import requests
import asyncio
import logging
from datetime import datetime
from typing import List, Tuple, Optional
from config import (
    YFINANCE_PERIOD,
    YFINANCE_INTERVAL,
    SYMBOL_MARKET,
    TARGET_SYMBOLS,
)
from market_utils import get_active_symbols, format_timestamp, get_current_timezone_time
from database import db_manager

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StockDataCollector:
    """주식 데이터 수집 클래스"""
    
    def __init__(self):
        self.is_running = False
        # yfinance 내부 세션에 사용자 에이전트 주입으로 차단/빈응답 완화
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            )
        })
        # 명시적으로 각 호출에 session 전달 (공유 세션 주입 제거)
    
    async def collect_stock_data(
        self, force_all_symbols: bool = False
    ) -> List[Tuple[str, float, str]]:
        """
        활성 종목들의 주식 데이터 수집
        
        Returns:
            List[Tuple[str, float, str]]: (symbol, price, timestamp) 튜플 리스트
        """
        # 기본: 시장 상태에 따라 활성 종목, 필요 시 강제 전체
        symbols_pool = get_active_symbols()
        if force_all_symbols or not symbols_pool:
            symbols_pool = list(SYMBOL_MARKET.keys())

        # 최종 대상: 미리 정한 종목만 필터링
        active_symbols = [s for s in symbols_pool if s in TARGET_SYMBOLS]
        if not active_symbols:
            logger.info("대상 심볼이 비어 있습니다(TARGET_SYMBOLS 확인)")
            return []
        
        logger.info(f"활성 종목 {len(active_symbols)}개 데이터 수집 시작")
        
        try:
            # 심볼별 개별 요청으로 신뢰도 향상 및 폴백 적용
            collected_data = []
            current_time = datetime.now()

            for symbol in active_symbols:
                try:
                    latest_price = None

                    # 1차: 기본 설정으로 1분봉 시도 (세션 주입된 Ticker 사용)
                    try:
                        df = yf.Ticker(symbol, session=self.session).history(
                            period=YFINANCE_PERIOD,
                            interval=YFINANCE_INTERVAL,
                            auto_adjust=False,
                            prepost=True
                        )
                        if df is not None and len(df) > 0 and 'Close' in df:
                            latest = df['Close'].dropna()
                            if len(latest) > 0:
                                latest_price = float(latest.iloc[-1])
                    except Exception as e1:
                        logger.debug(
                            f"{symbol} 기본 수집 실패(1m): {e1}"
                        )

                    # 2차: 2분봉 폴백
                    if latest_price is None:
                        try:
                            df2 = yf.Ticker(symbol, session=self.session).history(
                                period=YFINANCE_PERIOD,
                                interval="2m",
                                auto_adjust=False,
                                prepost=True
                            )
                            if df2 is not None and len(df2) > 0 and 'Close' in df2:
                                latest2 = df2['Close'].dropna()
                                if len(latest2) > 0:
                                    latest_price = float(latest2.iloc[-1])
                                    logger.info(f"{symbol}: 1m 미가용, 2m 데이터 사용")
                        except Exception as e2:
                            logger.debug(
                                f"{symbol} 2m 폴백 실패: {e2}"
                            )

                    # 3차: 5분봉 폴백
                    if latest_price is None:
                        try:
                            df5 = yf.Ticker(symbol, session=self.session).history(
                                period=YFINANCE_PERIOD,
                                interval="5m",
                                auto_adjust=False,
                                prepost=True
                            )
                            if df5 is not None and len(df5) > 0 and 'Close' in df5:
                                latest5 = df5['Close'].dropna()
                                if len(latest5) > 0:
                                    latest_price = float(latest5.iloc[-1])
                                    logger.info(
                                        f"{symbol}: 1m/2m 미가용, 5m 데이터 사용"
                                    )
                        except Exception as e25:
                            logger.debug(
                                f"{symbol} 5m 폴백 실패: {e25}"
                            )

                    # 4차: 15분봉 폴백
                    if latest_price is None:
                        try:
                            df15 = yf.Ticker(symbol, session=self.session).history(
                                period=YFINANCE_PERIOD,
                                interval="15m",
                                auto_adjust=False,
                                prepost=True
                            )
                            if df15 is not None and len(df15) > 0 and 'Close' in df15:
                                latest15 = df15['Close'].dropna()
                                if len(latest15) > 0:
                                    latest_price = float(latest15.iloc[-1])
                                    logger.info(
                                        f"{symbol}: 15m 데이터 사용"
                                    )
                        except Exception as e15:
                            logger.debug(
                                f"{symbol} 15m 폴백 실패: {e15}"
                            )

                    # 5차: 일봉 폴백(최근 5일 중 마지막 종가)
                    if latest_price is None:
                        try:
                            dfd = yf.Ticker(symbol, session=self.session).history(
                                period="5d",
                                interval="1d",
                                auto_adjust=False,
                                prepost=True
                            )
                            if dfd is not None and len(dfd) > 0 and 'Close' in dfd:
                                latestd = dfd['Close'].dropna()
                                if len(latestd) > 0:
                                    latest_price = float(latestd.iloc[-1])
                                    logger.info(
                                        f"{symbol}: intraday 미가용, 1d 마지막 종가 사용"
                                    )
                        except Exception as e3:
                            logger.debug(
                                f"{symbol} 1d 폴백 실패: {e3}"
                            )

                    # 6차: fast_info/ info 기반 초간단 시세 폴백 (dict/속성 모두 대응)
                    if latest_price is None:
                        try:
                            tkr = yf.Ticker(symbol, session=self.session)
                            value = None
                            fi = getattr(tkr, 'fast_info', None)
                            # fast_info 접근 (속성/딕셔너리 모두 시도)
                            if fi is not None:
                                candidate_keys = [
                                    'last_price', 'lastPrice',
                                    'regularMarketPrice',
                                    'previous_close', 'previousClose'
                                ]
                                for key in candidate_keys:
                                    v = None
                                    try:
                                        # 딕셔너리 형태
                                        if isinstance(fi, dict) and key in fi:
                                            v = fi[key]
                                        else:
                                            v = getattr(fi, key)
                                    except Exception:
                                        v = None
                                    if v is not None:
                                        value = v
                                        break
                            # info/get_info 백업 경로
                            if value is None:
                                try:
                                    info = {}
                                    # get_info가 있으면 우선 사용
                                    if hasattr(tkr, 'get_info'):
                                        info = tkr.get_info() or {}
                                    elif hasattr(tkr, 'info'):
                                        info = tkr.info or {}
                                    for key in (
                                        'regularMarketPrice', 'previousClose',
                                        'currentPrice'
                                    ):
                                        if key in info and info[key] is not None:
                                            value = info[key]
                                            break
                                except Exception:
                                    pass

                            if value is not None:
                                latest_price = float(value)
                                logger.info(f"{symbol}: fast_info/info 폴백 사용")
                        except Exception as e4:
                            logger.debug(
                                f"{symbol} fast_info 폴백 실패: {e4}"
                            )

                    # 7차: 월간 기간(1mo) + 일봉 범위 확대 폴백
                    if latest_price is None:
                        try:
                            dfd2 = yf.Ticker(symbol, session=self.session).history(
                                period="1mo",
                                interval="1d",
                                auto_adjust=False,
                                prepost=True
                            )
                            if dfd2 is not None and len(dfd2) > 0 and 'Close' in dfd2:
                                latestd2 = dfd2['Close'].dropna()
                                if len(latestd2) > 0:
                                    latest_price = float(latestd2.iloc[-1])
                                    logger.info(
                                        f"{symbol}: 1mo/1d 폴백 사용"
                                    )
                        except Exception as e5:
                            logger.debug(
                                f"{symbol} 1mo/1d 폴백 실패: {e5}"
                            )

                    # 8차: 연간 기간(1y) + 일봉 폴백
                    if latest_price is None:
                        try:
                            dfd3 = yf.Ticker(symbol, session=self.session).history(
                                period="1y",
                                interval="1d",
                                auto_adjust=False,
                                prepost=True
                            )
                            if dfd3 is not None and len(dfd3) > 0 and 'Close' in dfd3:
                                latestd3 = dfd3['Close'].dropna()
                                if len(latestd3) > 0:
                                    latest_price = float(latestd3.iloc[-1])
                                    logger.info(
                                        f"{symbol}: 1y/1d 폴백 사용"
                                    )
                        except Exception as e6:
                            logger.debug(
                                f"{symbol} 1y/1d 폴백 실패: {e6}"
                            )

                    # 9차: yf.download 기반 일봉 폴백 (5d/1d)
                    if latest_price is None:
                        try:
                            dld = yf.download(
                                tickers=symbol,
                                period="5d",
                                interval="1d",
                                progress=False
                            )
                            if dld is not None and len(dld) > 0:
                                # download는 단일 종목 시 'Close' 컬럼 바로 존재
                                close_series = dld['Close'] if 'Close' in dld else None
                                if close_series is not None:
                                    latest_close = close_series.dropna()
                                    if len(latest_close) > 0:
                                        latest_price = float(latest_close.iloc[-1])
                                        logger.info(f"{symbol}: download 5d/1d 폴백 사용")
                        except Exception as e7:
                            logger.debug(f"{symbol} download 5d/1d 폴백 실패: {e7}")

                    # 10차: yf.download 기반 일봉 폴백 (1mo/1d)
                    if latest_price is None:
                        try:
                            dld2 = yf.download(
                                tickers=symbol,
                                period="1mo",
                                interval="1d",
                                progress=False
                            )
                            if dld2 is not None and len(dld2) > 0:
                                close_series2 = dld2['Close'] if 'Close' in dld2 else None
                                if close_series2 is not None:
                                    latest_close2 = close_series2.dropna()
                                    if len(latest_close2) > 0:
                                        latest_price = float(latest_close2.iloc[-1])
                                        logger.info(f"{symbol}: download 1mo/1d 폴백 사용")
                        except Exception as e8:
                            logger.debug(f"{symbol} download 1mo/1d 폴백 실패: {e8}")

                    if latest_price is not None:
                        timestamp = format_timestamp(current_time)
                        collected_data.append(
                            (symbol, float(latest_price), timestamp)
                        )
                    else:
                        logger.warning(f"{symbol}: 사용할 수 있는 가격 데이터 없음")

                except Exception as e:
                    logger.error(f"{symbol} 데이터 처리 중 오류: {e}")
                    continue

            logger.info(
                f"성공적으로 {len(collected_data)}개 종목 데이터 수집 완료"
            )
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
    
    async def collect_and_save(self, force_all_symbols: bool = False) -> bool:
        """
        데이터 수집 및 저장을 한 번에 수행
        
        Returns:
            bool: 성공 여부
        """
        try:
            # 데이터 수집
            stock_data = await self.collect_stock_data(
                force_all_symbols=force_all_symbols
            )
            
            if stock_data:
                # 데이터베이스에 저장
                success = await self.save_to_database(stock_data)
                return success
            else:
                logger.info("저장할 데이터가 없습니다.")
                return False
                
        except Exception as e:
            logger.error(f"데이터 수집 및 저장 중 오류: {e}")
            return False


# 전역 데이터 수집기 인스턴스
stock_collector = StockDataCollector() 