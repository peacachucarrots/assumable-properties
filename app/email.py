# app/email.py
"""
Very small placeholder until you hook up a real mail provider.

Call send_invite_email("alice@example.com", "https://…/signup?token=123")
and check the console — you’ll see the invite link printed there.
"""

import asyncio

async def send_invite_email(to: str, link: str) -> None:
    # ‼️  In production replace this with fastapi-mail, aiosmtplib, etc.
    print(f"[DEV-MAIL] To: {to}\nClick to create your account: {link}\n")
    # make it awaitable so the admin route can 'await' it
    await asyncio.sleep(0)