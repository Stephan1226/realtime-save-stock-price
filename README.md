# 실시간 주식 데이터 수집 애플리케이션

yfinance를 사용한 실시간 주식 데이터 수집 및 MySQL 저장 FastAPI 애플리케이션입니다.

## 주요 기능

- **실시간 데이터 수집**: yfinance API를 사용해 주요 종목의 주식 데이터를 60초(1분) 간격으로 수집
- **거래소별 개장 시간 확인**: 미국(NYSE/NASDAQ)과 한국(KOSPI) 거래소의 개장 시간을 확인하여 장이 열려 있을 때만 데이터 수집
- **비동기 처리**: asyncio를 사용한 비동기 데이터 수집 및 저장
- **MySQL 저장**: 수집된 데이터를 MySQL 데이터베이스에 벌크 삽입
- **REST API**: FastAPI를 통한 데이터 조회 및 상태 확인 API 제공

## 지원 종목

### 미국 종목
- AAPL (Apple)
- GOOGL (Alphabet)
- MSFT (Microsoft)
- AMZN (Amazon)
- TSLA (Tesla)
- META (Meta Platforms)
- NVDA (NVIDIA)
- JPM (JPMorgan Chase)
- WMT (Walmart)
- DIS (Disney)

### 한국 종목
- 005930.KS (삼성전자)
- 000660.KS (SK하이닉스)

## 설치 및 설정

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. MySQL 데이터베이스 설정

MySQL 서버를 실행하고 데이터베이스를 생성합니다:

```sql
CREATE DATABASE stocks CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. 환경 변수 설정

`.env` 파일을 생성하거나 환경 변수를 설정합니다:

```bash
export DB_HOST=localhost
export DB_USER=your_user
export DB_PASSWORD=your_password
export DB_NAME=stocks
```

## 실행 방법

### 개발 서버 실행

```bash
python main.py
```

또는 uvicorn 직접 실행:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 프로덕션 실행

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
```

## API 엔드포인트

### 기본 정보
- `GET /`: 애플리케이션 정보
- `GET /health`: 헬스 체크
- `GET /status`: 작업 상태 및 시장 정보

### 데이터 조회
- `GET /prices`: 최신 주식 가격 조회
- `GET /prices?symbols=AAPL,GOOGL,MSFT`: 특정 종목 가격 조회
- `GET /symbols`: 등록된 모든 심볼 조회

### 작업 제어
- `POST /task/start`: 주기적 작업 수동 시작
- `POST /task/stop`: 주기적 작업 수동 중지

## 데이터베이스 스키마

### stock_prices 테이블

```sql
CREATE TABLE stock_prices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    price DECIMAL(10, 4) NOT NULL,
    timestamp DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_symbol_timestamp (symbol, timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

## 거래소 개장 시간

### 미국 (NYSE/NASDAQ)
- 시간대: US/Eastern (ET)
- 개장: 09:30 ET
- 폐장: 16:00 ET
- 주말 휴장

### 한국 (KOSPI)
- 시간대: Asia/Seoul (KST)
- 개장: 09:00 KST
- 폐장: 15:30 KST
- 주말 휴장

## 주요 특징

### 성능 최적화
- **정확한 60초 주기**: asyncio.sleep을 사용해 정확히 60초 간격 유지
- **사이클 시간 측정**: 각 데이터 수집 사이클의 소요 시간을 측정하고 로그 출력
- **배치 처리**: yfinance의 배치 다운로드 기능을 사용해 효율적인 데이터 요청
- **벌크 삽입**: MySQL의 executemany를 사용해 데이터베이스 성능 최적화

### 에러 처리
- **Rate Limit 대응**: yfinance API 호출 시 발생할 수 있는 rate limit 예외 처리
- **장 폐장 시 처리**: 거래소가 닫혀 있을 때는 데이터 수집을 건너뛰고 로그 출력
- **데이터 유효성 검사**: NaN 값이나 빈 데이터에 대한 검증 및 처리

### 모니터링
- **상세한 로깅**: 각 단계별 상세한 로그 출력
- **상태 확인 API**: 작업 상태, 시장 상태, 활성 종목 수 등 실시간 모니터링
- **헬스 체크**: 데이터베이스 연결 상태 및 작업 실행 상태 확인

## 주의사항

1. **yfinance 데이터 갱신 주기**: 60초 간격으로 요청하며 yfinance의 1분 주기와 일치합니다.
2. **API 제한**: yfinance API의 rate limit을 고려하여 적절한 간격으로 요청합니다.
3. **데이터베이스 연결**: MySQL 서버가 실행 중이어야 하며, 적절한 권한이 설정되어야 합니다.
4. **시간대 설정**: 정확한 거래소 시간 확인을 위해 pytz를 사용한 시간대 처리가 필요합니다.

## 개발 환경

- Python 3.8+
- FastAPI 0.104.1
- yfinance 0.2.18
- PyMySQL 1.1.0
- pytz 2023.3

## 라이선스

MIT License 