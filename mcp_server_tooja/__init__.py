from .server import serve


def main():
    """MCP 투자메이트 - 은퇴 자산 투자 전략 수립 서비스"""
    import asyncio
    asyncio.run(serve())


if __name__ == "__main__":
    main()
