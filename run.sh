#!/bin/bash

# 실시간 주식 데이터 수집 애플리케이션 실행 스크립트

echo "실시간 주식 데이터 수집 애플리케이션을 시작합니다..."

# 가상환경 활성화
if [ -d "venv" ]; then
    echo "가상환경을 활성화합니다..."
    source venv/bin/activate
else
    echo "가상환경이 없습니다. 생성합니다..."
    python3 -m venv venv
    source venv/bin/activate
    echo "의존성을 설치합니다..."
    pip install -r requirements.txt
fi

# 환경 변수 설정 (필요시 수정)
export DB_HOST=${DB_HOST:-localhost}
export DB_USER=${DB_USER:-your_user}
export DB_PASSWORD=${DB_PASSWORD:-your_password}
export DB_NAME=${DB_NAME:-stocks}

echo "환경 변수 설정:"
echo "  DB_HOST: $DB_HOST"
echo "  DB_USER: $DB_USER"
echo "  DB_NAME: $DB_NAME"

# 애플리케이션 실행
echo "FastAPI 서버를 시작합니다..."
echo "API 문서: http://localhost:8000/docs"
echo "상태 확인: http://localhost:8000/status"
echo "종료하려면 Ctrl+C를 누르세요."

python main.py 