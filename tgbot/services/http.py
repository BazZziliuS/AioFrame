import aiohttp


class HttpClient:
    """Shared aiohttp session for calls to external APIs from handlers.

    Created once at startup and injected into handlers as `http_client`:

        async def handler(message: Message, http_client: HttpClient):
            session = await http_client.session()
            async with session.get("https://api.example.com") as response:
                data = await response.json()
    """

    def __init__(self) -> None:
        self._session: aiohttp.ClientSession | None = None

    async def session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self._session

    async def close(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()
