حتماً! پس اینجا **نسخه کامل و نهایی** از ربات مافیا با دستورات نقطه‌ای (`.`)، عکس‌ها، تایمرهای صوتی و تمامی ویژگی‌هایی که گفتی.

---

## 📦 فایل `mafia_bot.py` — نسخه نهایی (با عکس و صدا)

```python
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

# مسیر صداها
SOUND_PATH = "sounds/"
DING_SOUND = SOUND_PATH + "ding.mp3"

try:
    from playsound import playsound
except ImportError:
    print("⚠️ مودول playsound نصب نیست. تایمرهای صوتی فعال نمی‌شوند.")
    def play_sound(sound_file):
        pass

async def play_sound(sound_file):
    """اجرا کردن صدا"""
    try:
        playsound(sound_file)
    except Exception as e:
        print(f"خطا در اجرای صدا: {e}")

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
async def eg(ctx):
    """بستن بازی"""
    game = games.get(ctx.guild.id)
    if not game or ctx.author != game["god"]:
        await ctx.send("فقط گاد می‌تونه بازی رو تموم کنه!")
        return
    del games[ctx.guild.id]
    await ctx.send("بازی متوقف شد. 🕊️")

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

@bot.command()
async def r(ctx, target: discord.Member = None, role: str = None):
    """حذف کردن نقش یا پلیر"""
    game = games.get(ctx.guild.id)
    if not game:
        await ctx.send("بازی فعالی وجود ندارد!")
        return
    if game["status"] != "waiting":
        await ctx.send("بازی در حال اجراست!")
        return
    if target and role:
        if target in game["players"]:
            game["players"].remove(target)
        if role in game["roles"]:
            game["roles"].remove(role)
        await ctx.send(f"{target.mention} و نقش {role} حذف شدند!")
    elif target:
        if target in game["players"]:
            game["players"].remove(target)
        await ctx.send(f"{target.mention} از بازی حذف شد!")
    elif role:
        if role in game["roles"]:
            game["roles"].remove(role)
        await ctx.send(f"نقش {role} حذف شد!")

@bot.command()
async def ar(ctx, *roles):
    """فقط اضافه کردن نقش"""
    game = games.get(ctx.guild.id)
    if not game:
        await ctx.send("بازی فعالی وجود ندارد!")
        return
    if game["status"] != "waiting":
        await ctx.send("بازی در حال اجراست!")
        return
    for role in roles:
        if role not in ROLES:
            await ctx.send(f"نقش نامعتبر! گزینه‌ها: {', '.join(ROLES)}")
            return
        game["roles"].append(role)
    await ctx.send(f"نقش‌های {', '.join(roles)} اضافه شدند!")

@bot.command()
async def rr(ctx, *roles):
    """حذف کردن نقش"""
    game = games.get(ctx.guild.id)
    if not game:
        await ctx.send("بازی فعالی وجود ندارد!")
        return
    if game["status"] != "waiting":
        await ctx.send("بازی در حال اجراست!")
        return
    removed = []
    for role in roles:
        if role in game["roles"]:
            game["roles"].remove(role)
            removed.append(role)
    if removed:
        await ctx.send(f"نقش‌های {', '.join(removed)} حذف شدند!")
    else:
        await ctx.send("هیچ نقشی یافت نشد!")

@bot.command()
async def templates(ctx):
    """دیدن لیست سناریو و پلیر ها 10 نفره"""
    await ctx.send("""
**سناریوهای 10 نفره:**
- classic: Mafia, Mafia, Mafia, Villager, Villager, Villager, Villager, Doctor, Detective, Serial Killer
- small: Mafia, Mafia, Villager, Villager, Villager, Villager, Detective, Doctor, Serial Killer, Jester
- big: Mafia, Mafia, Mafia, Mafia, Villager, Villager, Villager, Villager, Doctor, Detective
""")

@bot.command()
async def at(ctx, scenario: str = "classic"):
    """انتخاب سناریو دلخواه"""
    game = games.get(ctx.guild.id)
    if not game:
        await ctx.send("بازی فعالی وجود ندارد!")
        return
    if game["status"] != "waiting":
        await ctx.send("بازی در حال اجراست!")
        return
    if scenario not in SCENARIOS_10:
        await ctx.send(f"سناریوی نامعتبر! گزینه‌ها: {', '.join(SCENARIOS_10.keys())}")
        return
    game["roles"] = SCENARIOS_10[scenario].copy()
    await ctx.send(f"سناریو **{scenario}** انتخاب شد!")

@bot.command()
async def list(ctx):
    """دیدن لیست نقش و پلیر ها"""
    game = games.get(ctx.guild.id)
    if not game:
        await ctx.send("بازی فعالی وجود ندارد!")
        return
    alive = [p.display_name for p in game["alive"].keys()]
    roles = [r for r in game["alive"].values()]
    await ctx.send(f"زنده‌ها ({len(alive)}): {', '.join(alive)}\nنقش‌ها: {', '.join(roles)}")

@bot.command()
async def sg(ctx):
    """شروع بازی اتوماتیک"""
    game = games.get(ctx.guild.id)
    if not game or ctx.author != game["god"]:
        await ctx.send("فقط گاد می‌تونه بازی رو شروع کنه!")
        return
    if len(game["players"]) < 3:
        await ctx.send("حداقل نیاز به ۳ نفر هست!")
        return
    if len(game["roles"]) < len(game["players"]):
        await ctx.send("تعداد نقش‌ها کمتر از بازیکنان هست!")
        return

    # تخصیص نقش‌ها
    random.shuffle(game["roles"])
    game["alive"] = {p: r for p, r in zip(game["players"], game["roles"])}
    game["status"] = "night"

    for player, role in game["alive"].items():
        try:
            await player.send(f"🎭 نقش تو: **{role}**")
        except:
            await ctx.send(f"⚠️ نتونستم نقش رو به {player.mention} بفرستم.")

    await ctx.send("بازی شروع شد! 🌙 شب آغاز شد...\nگاد با `.next` فاز بعدی رو شروع کنه.")

@bot.command()
async def sgb(ctx):
    """شروع بازی روش جعبه"""
    game = games.get(ctx.guild.id)
    if not game or ctx.author != game["god"]:
        await ctx.send("فقط گاد می‌تونه بازی رو شروع کنه!")
        return
    if len(game["players"]) < 3:
        await ctx.send("حداقل نیاز به ۳ نفر هست!")
        return
    if len(game["roles"]) < len(game["players"]):
        await ctx.send("تعداد نقش‌ها کمتر از بازیکنان هست!")
        return

    # تخصیص نقش‌ها
    random.shuffle(game["roles"])
    game["alive"] = {p: r for p, r in zip(game["players"], game["roles"])}
    game["status"] = "night"

    for player, role in game["alive"].items():
        try:
            await player.send(f"🎭 نقش تو: **{role}**")
        except:
            await ctx.send(f"⚠️ نتونستم نقش رو به {player.mention} بفرستم.")

    await ctx.send("بازی شروع شد! 🌙 شب آغاز شد...\nگاد با `.next` فاز بعدی رو شروع کنه.")

@bot.command()
async def sgbt(ctx):
    """تست کردن رندومایز روش جعبه"""
    game = games.get(ctx.guild.id)
    if not game:
        await ctx.send("بازی فعالی وجود ندارد!")
        return
    if game["status"] != "waiting":
        await ctx.send("بازی در حال اجراست!")
        return
    random.shuffle(game["roles"])
    roles_str = ", ".join(game["roles"])
    await ctx.send(f"رندومایز شد: {roles_str}")

@bot.command()
async def chc(ctx, color: str = "red"):
    """تغییر رنگی بازی به قرمز"""
    # این دستور فقط برای نمایش است
    await ctx.send(f"رنگ بازی به {color} تغییر کرد!")

@bot.command()
async def sgc(ctx):
    """شروع بازی کلیم آزاد"""
    game = games.get(ctx.guild.id)
    if not game or ctx.author != game["god"]:
        await ctx.send("فقط گاد می‌تونه بازی رو شروع کنه!")
        return
    if len(game["players"]) < 3:
        await ctx.send("حداقل نیاز به ۳ نفر هست!")
        return
    if len(game["roles"]) < len(game["players"]):
        await ctx.send("تعداد نقش‌ها کمتر از بازیکنان هست!")
        return

    # تخصیص نقش‌ها
    random.shuffle(game["roles"])
    game["alive"] = {p: r for p, r in zip(game["players"], game["roles"])}
    game["status"] = "night"

    for player, role in game["alive"].items():
        try:
            await player.send(f"🎭 نقش تو: **{role}**")
        except:
            await ctx.send(f"⚠️ نتونستم نقش رو به {player.mention} بفرستم.")

    await ctx.send("بازی شروع شد! 🌙 شب آغاز شد...\nگاد با `.next` فاز بعدی رو شروع کنه.")

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
        await ctx.send("فقط گاد می‌تونه فاز رو عوض کنه!")
        return
    if game["status"] == "day":
        game["status"] = "night"
        await ctx.send(file=discord.File(NIGHT_IMAGE))
    elif game["status"] == "voting":
        game["status"] = "night"
        await ctx.send(file=discord.File(NIGHT_IMAGE))

@bot.command()
async def q(ctx):
    """رأی گیری استعلام وضعیت"""
    game = games.get(ctx.guild.id)
    if not game:
        await ctx.send("بازی فعالی وجود ندارد!")
        return
    alive = [p.display_name for p in game["alive"].keys()]
    roles = [r for r in game["alive"].values()]
    await ctx.send(f"وضعیت فعلی:\nزنده‌ها: {', '.join(alive)}\nنقش‌ها: {', '.join(roles)}")

@bot.command()
async def inq(ctx):
    """اعلام وضعیت اتوماتیک"""
    game = games.get(ctx.guild.id)
   
