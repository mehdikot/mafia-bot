import os

# تست مستقیم متغیر محیطی
token = os.getenv("DISCORD_TOKEN")

if token is None:
    print("❌ خطا: DISCORD_TOKEN پیدا نشد!")
    print("لیست تمام متغیرهای محیطی:")
    for key in sorted(os.environ.keys()):
        if "TOKEN" in key or "DISCORD" in key:
            print(f"  - {key} = {os.environ[key]}")
        else:
            print(f"  - {key} = [hidden]")
    exit(1)
else:
    print("✅ DISCORD_TOKEN پیدا شد! طول توکن:", len(token))
    # اگر طول توکن کمتر از 50 بود، احتمالاً ناقصه
    if len(token) < 50:
        print("⚠️ هشدار: توکن خیلی کوتاهه! مطمئن شو کامل کپی شده.")

# اگر همه چیز اوکی بود، ربات واقعی رو اجرا کن
import discord
from discord.ext import commands
import random

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"🎉 ربات {bot.user} آنلاین شد!")

@bot.command()
async def test(ctx):
    await ctx.send("ربات کار می‌کنه!")

bot.run(token)
