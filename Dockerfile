# Dockerfile
# 은퇴 플래닝 MCP 서버 (Jeoklip, Tooja, Inchul 통합)
# 멀티 아키텍처 지원 (AMD64 + ARM64)

FROM python:3.11-slim

# 메타데이터
LABEL maintainer="silverbell"
LABEL description="Retirement Planning MCP Server (적립메이트, 투자메이트, 인출메이트)"
LABEL version="1.0.0"

# 빌드 시 서버 지정 (기본값: jeoklip)
ARG SERVER=jeoklip

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 빌드 도구 설치
# pykrx, numpy 빌드에 필요한 패키지 포함
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Python 의존성 파일 복사
COPY requirements.txt .

# pip 업그레이드 및 Python 패키지 설치
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# 프로젝트 파일 복사 (불필요한 파일 제외는 .dockerignore에서 처리)
COPY mcp_server_jeoklip/ ./mcp_server_jeoklip/
COPY mcp_server_tooja/ ./mcp_server_tooja/
COPY mcp_server_inchul/ ./mcp_server_inchul/
COPY config/ ./config/

# 환경변수 설정
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV MCP_SERVER=${SERVER}

# 헬스체크 (선택사항)
# HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
#     CMD python -c "import mcp_server_${MCP_SERVER}" || exit 1

# 실행할 서버 모듈 지정
CMD ["sh", "-c", "python -m mcp_server_${MCP_SERVER}"]