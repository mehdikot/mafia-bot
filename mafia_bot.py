import discord
from discord.ext import commands
import random
import os
import asyncio
from datetime import datetime, timedelta

# بررسی وجود توکن
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("❌ متغیر DISCORD_TOKEN پیدا نشد!")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)

games = {}  # ذخیره بازی‌ها بر اساس guild_id

# سناریوها (10 نفره)
SCENARIOS_10 = {
    "classic": ["Mafia", "Mafia", "Mafia", "Villager", "Villager", "Villager", "Villager", "Doctor", "Detective", "Serial Killer"],
    "small": ["Mafia", "Mafia", "Villager", "Villager", "Villager", "Villager", "Detective", "Doctor", "Serial Killer", "Jester"],
    "big": ["Mafia", "Mafia", "Mafia", "Mafia", "Villager", "Villager", "Villager", "Villager", "Doctor", "Detective"]
}

# لیست نقش‌ها برای دستور ar/rr
ROLES = ["Mafia", "Villager", "Doctor", "Detective", "Serial Killer", "Jester", "Werewolf", "Seer", "Hunter", "Mayor"]

# مسیر عکس‌ها
IMAGE_PATH = "images/"
DAY_IMAGE = IMAGE_PATH + "day.png"
NIGHT_IMAGE = IMAGE_PATH + "night.png"
CG_IMAGE = IMAGE_PATH + "cg.png"

@bot.command()
async def d(ctx):
    """تغییر به فاز روز"""
    game = games.get(ctx.guild.id)
    if not game or ctx.author != game["god"]:
        await ctx.send("فقط گاد می‌تونه فاز رو عوض کنه!")
        return
    if game["status"] == "night":
        game["status"] = "day"
        await ctx.send(file=discord.File(DAY_IMAGE))
    elif game["status"] == "day":
        game["status"] = "voting"
        game["votes"] = {}
        await ctx.send("زمان رأی‌گیری! `.vote @user`")
    elif game["status"] == "voting":
        votes = game["votes"]
        if not votes:
            await ctx.send("هیچ‌کس رأی نداد!")
        else:
            target = max(votes, key=lambda x: (votes[x], -game["players"].index(x)))
            game["alive"].pop(target, None)
            await ctx.send(f"💀 {target.mention} اعدام شد!")

        mafia_count = sum(1 for r in game["alive"].values() if r in ["Mafia", "Serial Killer"])
        villager_count = len(game["alive"]) - mafia_count

        if mafia_count >= villager_count:
            await ctx.send("🔴 **مافیاها بردند!**")
            del games[ctx.guild.id]
        elif mafia_count == 0:
            await ctx.send("🟢 **شهروندان بردند!**")
            del games[ctx.guild.id]
        else:
            game["status"] = "night"
            await ctx.send(file=discord.File(NIGHT_IMAGE))

@bot.command()
async def n(ctx):
    """تغییر به فاز شب"""
    game = games.get(ctx.guild.id)
    if not game or ctx.author != game["god"]:
        await ctx.send("فقط گاد می‌تونه فаз رو عوض کنه!")
        return
    if game["status"] == "day":
        game["status"] = "night"
        await ctx.send(file=discord.File(NIGHT_IMAGE))
    elif game["status"] == "voting":
        game["status"] = "night"
        await ctx.send(file=discord.File(NIGHT_IMAGE))

@bot.command()
async def cg(ctx):
    """ساختن بازی جدید"""
    if ctx.guild.id in games:
        await ctx.send("بازی دیگه‌ای در حال اجراست!")
        return
    game = {
        "god": ctx.author,
        "players": [],
        "roles": [],
        "alive": {},
        "status": "waiting",
        "votes": {}
    }
    games[ctx.guild.id] = game
    await ctx.send(file=discord.File(CG_IMAGE))
    await ctx.send(f"بازی جدید ساخته شد! گاد: {ctx.author.mention}\nبرای پیوستن: `.join`")

@bot.command()
async def a(ctx, target: discord.Member = None, role: str = None):
    """اضافه کردن نقش یا پلیر"""
    game = games.get(ctx.guild.id)
    if not game:
        await ctx.send("بازی فعالی وجود ندارد!")
        return
    if game["status"] != "waiting":
        await ctx.send("بازی در حال اجراست!")
        return
    if target and role:
        if target not in game["players"]:
            game["players"].append(target)
        if role not in ROLES:
            await ctx.send(f"نقش نامعتبر! گزینه‌ها: {', '.join(ROLES)}")
            return
        game["roles"].append(role)
        await ctx.send(f"{target.mention} با نقش {role} اضافه شد!")
    elif target:
        if target not in game["players"]:
            game["players"].append(target)
        await ctx.send(f"{target.mention} به بازی اضافه شد!")
    elif role:
        if role not in ROLES:
            await ctx.send(f"نقش نامعتبر! گزینه‌ها: {', '.join(ROLES)}")
            return
        game["roles"].append(role)
        await ctx.send(f"نقش {role} اضافه شد!")

# ... (بقیه کد بدون تغییر)
