#!/bin/sh
set -e

# 디버그 메시지는 stderr로 출력 (MCP 프로토콜과 충돌 방지)
echo "MCP_SERVER=${MCP_SERVER}" >&2

case "$MCP_SERVER" in
  jeoklip)
    echo "Starting jeoklip server..." >&2
    exec python -m mcp_server_jeoklip
    ;;
  tooja)
    echo "Starting tooja server..." >&2
    exec python -m mcp_server_tooja
    ;;
  inchul)
    echo "Starting inchul server..." >&2
    exec python -m mcp_server_inchul
    ;;
  *)
    echo "ERROR: Unknown or empty MCP_SERVER: '$MCP_SERVER'" >&2
    echo "Please set MCP_SERVER to one of: jeoklip, tooja, inchul" >&2
    exit 1
    ;;
esac

