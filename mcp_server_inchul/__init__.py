from .server import serve


def main():
    """MCP 인출메이트 - 은퇴 후 절세 인출 전략 수립 서비스"""
    import asyncio
    asyncio.run(serve())


if __name__ == "__main__":
    main()
