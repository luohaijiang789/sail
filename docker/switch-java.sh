#!/usr/bin/env bash
# JDK 切换脚本。
# Build Worker 按 BuildPlan 的 jdk_version 调用此脚本切换 JAVA_HOME。
# 用法: switch-java 17  /  switch-java 21  /  switch-java 25

set -euo pipefail

JDK_VERSION="${1:?Usage: switch-java <17|21|25>}"

case "$JDK_VERSION" in
    17) JAVA_HOME_NEW="/usr/lib/jvm/java-17-openjdk-amd64" ;;
    21) JAVA_HOME_NEW="/usr/lib/jvm/java-21-openjdk-amd64" ;;
    25) JAVA_HOME_NEW="/usr/lib/jvm/java-25-openjdk-amd64" ;;
    *)  echo "Unsupported JDK version: $JDK_VERSION (supported: 17, 21, 25)"; exit 1 ;;
esac

if [ ! -d "$JAVA_HOME_NEW" ]; then
    echo "JDK $JDK_VERSION not installed at $JAVA_HOME_NEW"
    exit 1
fi

export JAVA_HOME="$JAVA_HOME_NEW"
export PATH="$JAVA_HOME/bin:$PATH"

# 输出供 Python 捕获
java -version 2>&1 | head -1
echo "JAVA_HOME=$JAVA_HOME"
