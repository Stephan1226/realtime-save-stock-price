"""
FastAPI 기반 주식 데이터 수집 애플리케이션
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import logging
from typing import List, Dict, Optional
from datetime import datetime

from config import API_HOST, API_PORT
from database import db_manager
from market_utils import get_market_status, get_active_symbols
from periodic_task import task_manager

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="실시간 주식 데이터 수집 API",
    description="yfinance를 사용한 실시간 주식 데이터 수집 및 MySQL 저장 API",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 실행되는 이벤트"""
    logger.info("FastAPI 서버 시작 중...")
    
    # 데이터베이스 연결 시도
    db_connected = db_manager.connect()
    if db_connected:
        # 테이블 생성
        if not db_manager.create_tables():
            logger.warning("테이블 생성 실패 - 데이터 저장 기능이 제한됩니다")
    else:
        logger.warning("데이터베이스 연결 실패 - 데이터 저장 기능이 제한됩니다")
    
    # 주기적 데이터 수집 작업 시작 (데이터베이스 없어도 실행 가능)
    task_manager.start()
    logger.info("주기적 데이터 수집 작업이 시작되었습니다")


@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 실행되는 이벤트"""
    logger.info("FastAPI 서버 종료 중...")
    
    # 주기적 작업 중지
    task_manager.stop()
    
    # 데이터베이스 연결 해제
    db_manager.disconnect()
    
    logger.info("서버가 안전하게 종료되었습니다")


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "실시간 주식 데이터 수집 API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/status")
async def get_status():
    """작업 상태 확인 엔드포인트"""
    try:
        task_status = task_manager.get_status()
        market_status = get_market_status()
        active_symbols = get_active_symbols()
        
        return {
            "task_status": task_status,
            "market_status": market_status,
            "active_symbols": active_symbols,
            "active_symbols_count": len(active_symbols),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"상태 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/prices")
async def get_latest_prices(symbols: Optional[str] = None):
    """
    최신 주식 가격 조회 엔드포인트
    
    Args:
        symbols: 쉼표로 구분된 심볼 리스트 (예: "AAPL,GOOGL,MSFT")
    """
    try:
        symbol_list = None
        if symbols:
            symbol_list = [s.strip() for s in symbols.split(",")]
        
        prices = db_manager.get_latest_prices(symbol_list)
        
        return {
            "prices": prices,
            "count": len(prices),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"가격 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/symbols")
async def get_symbols():
    """등록된 모든 심볼 조회 엔드포인트"""
    try:
        from config import SYMBOL_MARKET
        
        return {
            "symbols": list(SYMBOL_MARKET.keys()),
            "markets": list(set(SYMBOL_MARKET.values())),
            "total_count": len(SYMBOL_MARKET)
        }
    except Exception as e:
        logger.error(f"심볼 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/task/start")
async def start_task():
    """주기적 작업 수동 시작"""
    try:
        if task_manager.is_running:
            return {"message": "작업이 이미 실행 중입니다", "status": "running"}
        
        task_manager.start()
        return {"message": "주기적 작업이 시작되었습니다", "status": "started"}
    except Exception as e:
        logger.error(f"작업 시작 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/task/stop")
async def stop_task():
    """주기적 작업 수동 중지"""
    try:
        if not task_manager.is_running:
            return {"message": "작업이 실행 중이 아닙니다", "status": "stopped"}
        
        task_manager.stop()
        return {"message": "주기적 작업이 중지되었습니다", "status": "stopped"}
    except Exception as e:
        logger.error(f"작업 중지 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    try:
        # 데이터베이스 연결 상태 확인
        db_connected = db_manager.connection is not None and db_manager.connection.open
        
        return {
            "status": "healthy" if db_connected else "unhealthy",
            "database_connected": db_connected,
            "task_running": task_manager.is_running,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"헬스 체크 중 오류: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"서버를 {API_HOST}:{API_PORT}에서 시작합니다...")
    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=API_PORT,
        reload=False,
        log_level="info"
    ) 