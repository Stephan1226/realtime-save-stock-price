"""
MySQL 데이터베이스 연결 및 테이블 관리
"""
import pymysql
import logging
from typing import List, Tuple, Optional
from config import DB_CONFIG

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """MySQL 데이터베이스 관리 클래스"""
    
    def __init__(self):
        self.connection = None
    
    def connect(self) -> bool:
        """데이터베이스 연결"""
        try:
            self.connection = pymysql.connect(**DB_CONFIG)
            logger.info("데이터베이스 연결 성공")
            return True
        except Exception as e:
            logger.error(f"데이터베이스 연결 실패: {e}")
            return False
    
    def disconnect(self):
        """데이터베이스 연결 해제"""
        if self.connection:
            self.connection.close()
            logger.info("데이터베이스 연결 해제")
    
    def create_tables(self) -> bool:
        """필요한 테이블 생성"""
        try:
            with self.connection.cursor() as cursor:
                # 주식 가격 테이블 생성
                create_table_sql = """
                CREATE TABLE IF NOT EXISTS stock_prices (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    price DECIMAL(10, 4) NOT NULL,
                    timestamp DATETIME NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_symbol_timestamp (symbol, timestamp)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """
                cursor.execute(create_table_sql)
                self.connection.commit()
                logger.info("테이블 생성 완료")
                return True
        except Exception as e:
            logger.error(f"테이블 생성 실패: {e}")
            return False
    
    def bulk_insert_prices(self, data: List[Tuple[str, float, str]]) -> bool:
        """
        주식 가격 데이터 벌크 삽입
        
        Args:
            data: (symbol, price, timestamp) 튜플 리스트
        """
        try:
            with self.connection.cursor() as cursor:
                insert_sql = """
                INSERT INTO stock_prices (symbol, price, timestamp)
                VALUES (%s, %s, %s)
                """
                cursor.executemany(insert_sql, data)
                self.connection.commit()
                logger.info(f"{len(data)}개 주식 가격 데이터 삽입 완료")
                return True
        except Exception as e:
            logger.error(f"데이터 삽입 실패: {e}")
            return False
    
    def get_latest_prices(self, symbols: Optional[List[str]] = None) -> List[dict]:
        """
        최신 주식 가격 조회
        
        Args:
            symbols: 조회할 심볼 리스트 (None이면 전체)
        """
        try:
            with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
                if symbols:
                    placeholders = ','.join(['%s'] * len(symbols))
                    sql = f"""
                    SELECT symbol, price, timestamp
                    FROM stock_prices 
                    WHERE symbol IN ({placeholders})
                    AND timestamp = (
                        SELECT MAX(timestamp) 
                        FROM stock_prices sp2 
                        WHERE sp2.symbol = stock_prices.symbol
                    )
                    ORDER BY symbol
                    """
                    cursor.execute(sql, symbols)
                else:
                    sql = """
                    SELECT symbol, price, timestamp
                    FROM stock_prices sp1
                    WHERE timestamp = (
                        SELECT MAX(timestamp) 
                        FROM stock_prices sp2 
                        WHERE sp2.symbol = sp1.symbol
                    )
                    ORDER BY symbol
                    """
                    cursor.execute(sql)
                
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"데이터 조회 실패: {e}")
            return []


# 전역 데이터베이스 매니저 인스턴스
db_manager = DatabaseManager() 