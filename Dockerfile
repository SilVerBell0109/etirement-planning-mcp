# 1. Python 3.10 베이스 이미지
FROM python:3.10-slim

# 2. 작업 디렉토리
WORKDIR /app

# 3. requirements 먼저 복사 후 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 나머지 소스 코드 복사
COPY . .

# 5. entrypoint 스크립트 실행 권한 부여
RUN chmod +x ./entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]

