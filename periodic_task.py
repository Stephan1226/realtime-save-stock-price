"""
주기적 주식 데이터 수집 작업 관리
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional
from config import DATA_COLLECTION_INTERVAL
from stock_data_collector import stock_collector
from market_utils import get_market_status

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PeriodicTaskManager:
    """주기적 작업 관리 클래스"""
    
    def __init__(self):
        self.task: Optional[asyncio.Task] = None
        self.is_running = False
        self.cycle_count = 0
        self.start_time: Optional[datetime] = None
    
    async def periodic_data_collection(self):
        """
        60초 간격으로 주식 데이터를 수집하는 주기적 작업
        설정된 간격(DATA_COLLECTION_INTERVAL=60초)을 유지하며 사이클 소요 시간을 측정
        """
        self.is_running = True
        self.start_time = datetime.now()
        logger.info("주기적 데이터 수집 작업 시작")
        
        while self.is_running:
            cycle_start = datetime.now()
            self.cycle_count += 1
            
            try:
                # 시장 상태 확인
                market_status = get_market_status()
                logger.info(f"사이클 {self.cycle_count} 시작 - 시장 상태: {market_status}")
                
                # 데이터 수집 및 저장
                # 장 여부와 무관하게 미리 정한 종목만 강제 수집
                success = await stock_collector.collect_and_save(
                    force_all_symbols=True
                )
                
                if success:
                    logger.info(f"사이클 {self.cycle_count} 완료")
                else:
                    logger.warning(f"사이클 {self.cycle_count} 실패")
                
            except Exception as e:
                logger.error(f"사이클 {self.cycle_count} 중 오류 발생: {e}")
            
            # 사이클 소요 시간 계산
            cycle_end = datetime.now()
            cycle_duration = (cycle_end - cycle_start).total_seconds()
            logger.info(f"사이클 {self.cycle_count} 소요 시간: {cycle_duration:.2f}초")
            
            # 정확히 10초 주기 유지를 위한 대기 시간 계산
            if cycle_duration < DATA_COLLECTION_INTERVAL:
                sleep_time = DATA_COLLECTION_INTERVAL - cycle_duration
                logger.info(f"다음 사이클까지 {sleep_time:.2f}초 대기")
                await asyncio.sleep(sleep_time)
            else:
                logger.warning(f"사이클 {self.cycle_count}이 {DATA_COLLECTION_INTERVAL}초를 초과했습니다")
    
    def start(self):
        """주기적 작업 시작"""
        if not self.is_running:
            self.task = asyncio.create_task(self.periodic_data_collection())
            logger.info("주기적 작업이 시작되었습니다")
    
    def stop(self):
        """주기적 작업 중지"""
        if self.is_running:
            self.is_running = False
            if self.task:
                self.task.cancel()
            logger.info("주기적 작업이 중지되었습니다")
    
    def get_status(self) -> dict:
        """
        작업 상태 정보 반환
        
        Returns:
            dict: 작업 상태 정보
        """
        total_runtime = None
        if self.start_time:
            total_runtime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "is_running": self.is_running,
            "cycle_count": self.cycle_count,
            "total_runtime_seconds": total_runtime,
            "interval_seconds": DATA_COLLECTION_INTERVAL
        }


# 전역 주기적 작업 매니저 인스턴스
task_manager = PeriodicTaskManager() 