<<<<<<< HEAD
# Dockerfile
=======
# 1. Python 3.11 베이스 이미지
>>>>>>> c0c1d9d183f6ff0072c48033e74b9d1ff2ba4d27
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사
COPY requirements.txt .

# Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 파일 복사
COPY . .

# 환경변수 설정
ENV PYTHONUNBUFFERED=1

# 기본 명령어 (서버별로 변경 가능)
CMD ["python", "-m", "mcp_server_jeoklip"]