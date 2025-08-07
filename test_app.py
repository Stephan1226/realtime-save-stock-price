#!/usr/bin/env python3
"""
애플리케이션 기능 테스트 스크립트
"""
import asyncio
import sys
from datetime import datetime

# 프로젝트 모듈 임포트
try:
    from config import SYMBOL_MARKET, MARKET_HOURS
    from market_utils import get_market_status, get_active_symbols, is_market_open
    from database import db_manager
    from stock_data_collector import stock_collector
    print("✅ 모든 모듈 임포트 성공")
except ImportError as e:
    print(f"❌ 모듈 임포트 실패: {e}")
    sys.exit(1)


async def test_market_utils():
    """시장 유틸리티 기능 테스트"""
    print("\n🔍 시장 유틸리티 테스트")
    print("-" * 40)
    
    # 시장 상태 확인
    market_status = get_market_status()
    print(f"시장 상태: {market_status}")
    
    # 활성 종목 확인
    active_symbols = get_active_symbols()
    print(f"활성 종목 수: {len(active_symbols)}")
    if active_symbols:
        print(f"활성 종목: {active_symbols}")
    
    # 개별 시장 확인
    for market in ['US', 'KR']:
        is_open = is_market_open(market)
        print(f"{market} 시장 개장 여부: {is_open}")


async def test_database_connection():
    """데이터베이스 연결 테스트"""
    print("\n🗄️ 데이터베이스 연결 테스트")
    print("-" * 40)
    
    try:
        connected = db_manager.connect()
        if connected:
            print("✅ 데이터베이스 연결 성공")
            
            # 테이블 생성 테스트
            tables_created = db_manager.create_tables()
            if tables_created:
                print("✅ 테이블 생성 성공")
            else:
                print("⚠️ 테이블 생성 실패")
        else:
            print("❌ 데이터베이스 연결 실패")
            print("   MySQL 서버가 실행 중인지 확인하세요")
    except Exception as e:
        print(f"❌ 데이터베이스 테스트 중 오류: {e}")
    finally:
        db_manager.disconnect()


async def test_stock_data_collection():
    """주식 데이터 수집 테스트"""
    print("\n📊 주식 데이터 수집 테스트")
    print("-" * 40)
    
    try:
        # 데이터 수집 테스트
        print("주식 데이터 수집 중...")
        stock_data = await stock_collector.collect_stock_data()
        
        if stock_data:
            print(f"✅ {len(stock_data)}개 종목 데이터 수집 성공")
            for symbol, price, timestamp in stock_data[:3]:  # 처음 3개만 출력
                print(f"   {symbol}: ${price:.2f} ({timestamp})")
        else:
            print("⚠️ 수집된 데이터가 없습니다 (장이 닫혀있을 수 있음)")
            
    except Exception as e:
        print(f"❌ 데이터 수집 테스트 중 오류: {e}")


def test_config():
    """설정 테스트"""
    print("\n⚙️ 설정 테스트")
    print("-" * 40)
    
    print(f"등록된 종목 수: {len(SYMBOL_MARKET)}")
    print(f"지원 시장: {list(MARKET_HOURS.keys())}")
    
    print("\n등록된 종목:")
    for symbol, market in SYMBOL_MARKET.items():
        print(f"  {symbol} ({market})")


async def main():
    """메인 테스트 함수"""
    print("🚀 실시간 주식 데이터 수집 애플리케이션 테스트")
    print("=" * 50)
    print(f"테스트 시작 시간: {datetime.now()}")
    
    # 설정 테스트
    test_config()
    
    # 시장 유틸리티 테스트
    await test_market_utils()
    
    # 데이터베이스 연결 테스트
    await test_database_connection()
    
    # 주식 데이터 수집 테스트
    await test_stock_data_collection()
    
    print("\n" + "=" * 50)
    print("✅ 모든 테스트 완료!")
    print("\n애플리케이션을 실행하려면:")
    print("  python main.py")
    print("  또는")
    print("  ./run.sh")


if __name__ == "__main__":
    asyncio.run(main()) 