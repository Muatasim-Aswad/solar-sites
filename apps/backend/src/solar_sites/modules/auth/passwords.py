import asyncio
import secrets
from concurrent.futures import ThreadPoolExecutor

from pwdlib import PasswordHash


class Passwords:
    def __init__(self) -> None:
        self.hasher = PasswordHash.recommended()
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="passwords")
        self.dummy_hash = ""

    async def start(self) -> None:
        self.dummy_hash = await self.hash(password=secrets.token_urlsafe(32))

    async def hash(self, *, password: str) -> str:
        return await asyncio.get_running_loop().run_in_executor(
            self.executor, self.hasher.hash, password
        )

    async def verify(self, *, password: str, hashed: str) -> bool:
        return await asyncio.get_running_loop().run_in_executor(
            self.executor, self.hasher.verify, password, hashed
        )

    async def close(self) -> None:
        await asyncio.to_thread(self.executor.shutdown, wait=True, cancel_futures=True)
