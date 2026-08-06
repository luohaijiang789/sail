FROM python:3.11-slim

# CodeQL CLI
ARG CODEQL_VERSION=2.17.0
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl unzip openjdk-17-jdk-headless maven \
    && rm -rf /var/lib/apt/lists/*
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

RUN curl -L "https://github.com/github/codeql-cli-binaries/releases/download/v${CODEQL_VERSION}/codeql-linux64.zip" -o /tmp/codeql.zip \
    && unzip /tmp/codeql.zip -d /opt \
    && rm /tmp/codeql.zip \
    && ln -s /opt/codeql/codeql /usr/local/bin/codeql

WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

COPY . .

# 非 root 用户运行 Worker（安全隔离）
RUN useradd -m sail
USER sail

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
