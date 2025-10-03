from .server import serve


def main():
    """MCP 적립메이트 - 은퇴 자산 적립 계획 수립 서비스"""
    import asyncio
    asyncio.run(serve())


if __name__ == "__main__":
    main()
