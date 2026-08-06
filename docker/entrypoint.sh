#!/usr/bin/env bash
# SAIL Worker 启动脚本。
# 根据角色启动 Celery Worker，监听对应队列。
# 用法: entrypoint.sh <role>
# role: fetch / build / codeql / extract / ai / postprocess / api

set -euo pipefail

ROLE="${1:?Usage: entrypoint.sh <fetch|build|codeql|extract|ai|postprocess|api>}"

case "$ROLE" in
    fetch)
        exec celery -A workers.celery_app worker \
            -Q source_fetch -c 4 \
            -n fetch@%h --loglevel=info
        ;;
    build)
        exec celery -A workers.celery_app worker \
            -Q java_build_jdk17 -c 2 \
            -n build@%h --loglevel=info
        ;;
    codeql)
        exec celery -A workers.celery_app worker \
            -Q codeql_query -c 2 \
            -n codeql@%h --loglevel=info
        ;;
    extract)
        exec celery -A workers.celery_app worker \
            -Q source_extract -c 4 \
            -n extract@%h --loglevel=info
        ;;
    ai)
        exec celery -A workers.celery_app worker \
            -Q ai_analysis -c 4 \
            -n ai@%h --loglevel=info
        ;;
    postprocess)
        exec celery -A workers.celery_app worker \
            -Q result_process -c 4 \
            -n post@%h --loglevel=info
        ;;
    api)
        exec uvicorn app.main:app \
            --host 0.0.0.0 --port 8000
        ;;
    *)
        echo "Unknown role: $ROLE"
        echo "Supported: fetch build codeql extract ai postprocess api"
        exit 1
        ;;
esac
