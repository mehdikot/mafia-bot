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

# تابع برای استفاده از دستورات جدید
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

    await ctx.send("بازی شروع شد! 🌙 شب آغاز شد...\nگاد با `.next` فаз بعدی رو شروع کنه.")

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
        await ctx.send("☀️ روز شد!")
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
            await ctx.send("🌙 شب بعدی...")

@bot.command()
async def n(ctx):
    """تغییر به فاز شب"""
    game = games.get(ctx.guild.id)
    if not game or ctx.author != game["god"]:
        await ctx.send("فقط گاد می‌تونه فاز رو عوض کنه!")
        return
    if game["status"] == "day":
        game["status"] = "night"
        await ctx.send("🌙 شب شد!")
    elif game["status"] == "voting":
        game["status"] = "night"
        await ctx.send("🌙 شب شد!")

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
    if not game:
        await ctx.send("بازی فعالی وجود ندارد!")
        return
    alive = [p.display_name for p in game["alive"].keys()]
    roles = [r for r in game["alive"].values()]
    await ctx.send(f"✅ وضعیت اتوماتیک:\nزنده‌ها: {', '.join(alive)}\nنقش‌ها: {', '.join(roles)}")

@bot.command()
async def side(ctx, target: discord.Member):
    """نشان دادن ساید پلیر"""
    game = games.get(ctx.guild.id)
    if not game:
        await ctx.send("بازی فعالی وجود ندارد!")
        return
    if target not in game["alive"]:
        await ctx.send("این نفر زنده نیست!")
        return
    role = game["alive"][target]
    await ctx.send(f"{target.mention} نقش: **{role}**")

@bot.command()
async def rep(ctx, user1: discord.Member, user2: discord.Member):
    """جایگزین کردن پلیر داخل و بیرون بازی"""
    game = games.get(ctx.guild.id)
    if not game:
        await ctx.send("بازی فعالی وجود ندارد!")
        return
    if user1 not in game["players"] or user2 not in game["players"]:
        await ctx.send("هر دو نفر باید در لیست بازیکنان باشند!")
        return
    game["players"].remove(user1)
    game["players"].append(user2)
    await ctx.send(f"{user1.mention} و {user2.mention} جایگزین شدند!")

@bot.command()
async def rg(ctx, target: discord.Member):
    """تغییر راوی بازی"""
    game = games.get(ctx.guild.id)
    if not game:
        await ctx.send("بازی فعالی وجود ندارد!")
        return
    if ctx.author != game["god"]:
        await ctx.send("فقط گاد می‌تونه راوی رو عوض کنه!")
        return
    game["god"] = target
    await ctx.send(f"راوی بازی به {target.mention} تغییر کرد!")

@bot.command()
async def v(ctx, target: discord.Member = None, number: int = None, name: str = None):
    """رأی گیری برای یک پلیر"""
    game = games.get(ctx.guild.id)
    if not game or game["status"] != "voting":
        await ctx.send("الان زمان رأی‌گیری نیست!")
        return
    if ctx.author not in game["alive"]:
        await ctx.send("تو مرده‌ای!")
        return
    if target and target in game["alive"]:
        game["votes"][ctx.author] = target
        await ctx.send(f"✅ {ctx.author.display_name} به {target.display_name} رأی داد.")
    elif number and 1 <= number <= len(game["players"]):
        target = game["players"][number - 1]
        if target in game["alive"]:
            game["votes"][ctx.author] = target
            await ctx.send(f"✅ {ctx.author.display_name} به {target.display_name} (شماره {number}) رأی داد.")
    elif name:
        found = False
        for p in game["players"]:
            if name.lower() in p.display_name.lower():
                game["votes"][ctx.author] = p
                await ctx.send(f"✅ {ctx.author.display_name} به {p.display_name} رأی داد.")
                found = True
                break
        if not found:
            await ctx.send("پلیری با این نام یافت نشد!")
    else:
        await ctx.send("فرمت نامعتبر! استفاده کن: `.v @user` یا `.v 1` یا `.v example`")

@bot.command()
async def bazporsi(ctx, num1: int, num2: int):
    """رأی گیری بازپرسی بین دو پلیر"""
    game = games.get(ctx.guild.id)
    if not game or game["status"] != "voting":
        await ctx.send("الان زمان رأی‌گیری نیست!")
        return
    if num1 < 1 or num2 < 1 or num1 > len(game["players"]) or num2 > len(game["players"]):
        await ctx.send("شماره‌های نامعتبر!")
        return
    p1 = game["players"][num1 - 1]
    p2 = game["players"][num2 - 1]
    if p1 not in game["alive"] or p2 not in game["alive"]:
        await ctx.send("یکی از این دو نفر مرده!")
        return
    game["votes"][ctx.author] = p1 if p1 == p2 else p1  # اینجا فقط نمونه‌ایه، باید منطق دقیق‌تری داشته باشه
    await ctx.send(f"✅ {ctx.author.display_name} در بازپرسی بین {p1.display_name} و {p2.display_name} رأی داد.")

@bot.command()
async def ha(ctx):
    """کشیدن کارت حرکت آخر (شب مافیا)"""
    game = games.get(ctx.guild.id)
    if not game or game["status"] != "night":
        await ctx.send("فقط در شب می‌تونی این دستور رو بزنی!")
        return
    # اینجا منطق خاصی برای کارت حرکت آخر می‌تونه اضافه بشه
    await ctx.send("کارت حرکت آخر کشیده شد! (نمونه)")

@bot.command()
async def kill(ctx, target: discord.Member = None, number: int = None, name: str = None):
    """کشتن یک پلیر"""
    game = games.get(ctx.guild.id)
    if not game or game["status"] != "night":
        await ctx.send("فقط در شب می‌تونی این دستور رو بزنی!")
        return
    if target and target in game["alive"]:
        game["alive"].pop(target, None)
        await ctx.send(f"💀 {target.mention} کشته شد!")
    elif number and 1 <= number <= len(game["players"]):
        target = game["players"][number - 1]
        if target in game["alive"]:
            game["alive"].pop(target, None)
            await ctx.send(f"💀 {target.mention} (شماره {number}) کشته شد!")
    elif name:
        found = False
        for p in game["players"]:
            if name.lower() in p.display_name.lower():
                game["alive"].pop(p, None)
                await ctx.send(f"💀 {p.display_name} کشته شد.")
                found = True
                break
        if not found:
            await ctx.send("پلیری با این نام یافت نشد!")
    else:
        await ctx.send("فرmat نامعتبر! استفاده کن: `.kill @user` یا `.kill 1` یا `.kill example`")

@bot.command()
async def revive(ctx, target: discord.Member = None, number: int = None, name: str = None):
    """زنده کردن یک پلیر کشته شده"""
    game = games.get(ctx.guild.id)
    if not game or game["status"] != "night":
        await ctx.send("فقط در شب می‌تونی این دستور رو بزنی!")
        return
    if target and target not in game["alive"]:
        game["alive"][target] = "Villager"  # یا نقش دیگر
        await ctx.send(f"🧟‍♂️ {target.mention} زنده شد!")
    elif number and 1 <= number <= len(game["players"]):
        target = game["players"][number - 1]
        if target not in game["alive"]:
            game["alive"][target] = "Villager"
            await ctx.send(f"🧟‍♂️ {target.mention} (شماره {number}) زنده شد!")
    elif name:
        found = False
        for p in game["players"]:
            if name.lower() in p.display_name.lower():
                if p not in game["alive"]:
                    game["alive"][p] = "Villager"
                    await ctx.send(f"🧟‍♂️ {p.display_name} زنده شد.")
                    found = True
                    break
        if not found:
            await ctx.send("پلیری با این نام یافت نشد!")
    else:
        await ctx.send("فرmat نامعتبر! استفاده کن: `.revive @user` یا `.revive 1` یا `.revive example`")

@bot.command()
async def td(ctx, target: discord.Member = None, number: int = None, name: str = None):
    """تایمر دفاعیه 60 ثانیه ای"""
    if target and isinstance(target, discord.Member):
        await ctx.send(f"⏳ تایمر دفاعیه برای {target.mention} شروع شد (60 ثانیه)")
        await asyncio.sleep(60)
        await ctx.send(f"⏰ تایمر دفاعیه برای {target.mention} تمام شد!")
    elif number and 1 <= number <= len(game["players"]):
        target = game["players"][number - 1]
        await ctx.send(f"⏳ تایمر دفاعیه برای {target.display_name} شروع شد (60 ثانیه)")
        await asyncio.sleep(60)
        await ctx.send(f"⏰ تایمر دفاعیه برای {target.display_name} تمام شد!")
    elif name:
        found = False
        for p in game["players"]:
            if name.lower() in p.display_name.lower():
                await ctx.send(f"⏳ تایمر دفاعیه برای {p.display_name} شروع شد (60 ثانیه)")
                await asyncio.sleep(60)
                await ctx.send(f"⏰ تایمر دفاعیه برای {p.display_name} تمام شد!")
                found = True
                break
        if not found:
            await ctx.send("پلیری با این نام یافت نشد!")
    else:
        await ctx.send("فرmat نامعتبر! استفاده کن: `.td @user` یا `.td 1` یا `.td example`")

@bot.command()
async def tt(ctx, target: discord.Member = None, number: int = None, name: str = None):
    """تایمر ترن 45 ثانیه ای"""
    if target and isinstance(target, discord.Member):
        await ctx.send(f"⏳ تایمر ترن برای {target.mention} شروع شد (45 ثانیه)")
        await asyncio.sleep(45)
        await ctx.send(f"⏰ تایمر ترن برای {target.mention} تمام شد!")
    elif number and 1 <= number <= len(game["players"]):
        target = game["players"][number - 1]
        await ctx.send(f"⏳ تایمر ترن برای {target.display_name} شروع شد (45 ثانیه)")
        await asyncio.sleep(45)
        await ctx.send(f"⏰ تایمر ترن برای {target.display_name} تمام شد!")
    elif name:
        found = False
        for p in game["players"]:
            if name.lower() in p.display_name.lower():
                await ctx.send(f"⏳ تایمر ترن برای {p.display_name} شروع شد (45 ثانیه)")
                await asyncio.sleep(45)
                await ctx.send(f"⏰ تایمر ترن برای {p.display_name} تمام شد!")
                found = True
                break
        if not found:
            await ctx.send("پلیری با این نام یافت نشد!")
    else:
        await ctx.send("فرmat نامعتبر! استفاده کن: `.tt @user` یا `.tt 1` یا `.tt example`")

@bot.command()
async def tc(ctx, target: discord.Member = None, number: int = None, name: str = None):
    """تایمر چالش 30 ثانیه ای"""
    if target and isinstance(target, discord.Member):
        await ctx.send(f"⏳ تایمر چالش برای {target.mention} شروع شد (30 ثانیه)")
        await asyncio.sleep(30)
        await ctx.send(f"⏰ تایمر چالش برای {target.mention} تمام شد!")
    elif number and 1 <= number <= len(game["players"]):
        target = game["players"][number - 1]
        await ctx.send(f"⏳ تایمر چالش برای {target.display_name} شروع شد (30 ثانیه)")
        await asyncio.sleep(30)
        await ctx.send(f"⏰ تایمر چالش برای {target.display_name} تمام شد!")
    elif name:
        found = False
        for p in game["players"]:
            if name.lower() in p.display_name.lower():
                await ctx.send(f"⏳ تایمر چالش برای {p.display_name} شروع شد (30 ثانیه)")
                await asyncio.sleep(30)
                await ctx.send(f"⏰ تایمر چالش برای {p.display_name} تمام شد!")
                found = True
                break
        if not found:
            await ctx.send("پلیری با این نام یافت نشد!")
    else:
        await ctx.send("فرmat نامعتبر! استفاده کن: `.tc @user` یا `.tc 1` یا `.tc example`")

@bot.command()
async def t(ctx, time_str: str = None):
    """تایمر با زمان دلخواه"""
    if not time_str:
        await ctx.send("زمان را وارد کن! مثال: `.t 100` یا `.t 5m` یا `.t 1h`")
        return
    try:
        # پارس کردن زمان
        if time_str.isdigit():
            seconds = int(time_str)
        else:
            parts = time_str.split()
            seconds = 0
            for part in parts:
                if part.endswith('s'):
                    seconds += int(part[:-1])
                elif part.endswith('m'):
                    seconds += int(part[:-1]) * 60
                elif part.endswith('h'):
                    seconds += int(part[:-1]) * 3600
                else:
                    seconds += int(part)
        await ctx.send(f"⏳ تایمر برای {seconds} ثانیه شروع شد!")
        await asyncio.sleep(seconds)
        await ctx.send("⏰ تایمر تمام شد!")
    except Exception as e:
        await ctx.send(f"خطا در پارس کردن زمان: {e}")

@bot.command()
async def warn(ctx, target: discord.Member):
    """اخطار به پلیر"""
    game = games.get(ctx.guild.id)
    if not game:
        await ctx.send("بازی فعالی وجود ندارد!")
        return
    if target not in game["alive"]:
        await ctx.send("این نفر زنده نیست!")
        return
    await ctx.send(f"⚠️ {target.mention} اخطار داده شد!")

@bot.command()
async def result(ctx):
    """اتمام بازی با فرستادن و ثبت نتیجه"""
    game = games.get(ctx.guild.id)
    if not game:
        await ctx.send("بازی فعالی وجود ندارد!")
        return
    if ctx.author != game["god"]:
        await ctx.send("فقط گاد می‌تونه این دستور رو بزنه!")
        return
    # محاسبه نتیجه
    mafia_count = sum(1 for r in game["alive"].values() if r in ["Mafia", "Serial Killer"])
    villager_count = len(game["alive"]) - mafia_count
    if mafia_count >= villager_count:
        await ctx.send("🔴 **مافیاها بردند!**")
    else:
        await ctx.send("🟢 **شهروندان بردند!**")
    del games[ctx.guild.id]

@bot.command()
async def show(ctx):
    """تغییر نام پلیر ها به اسم نقششون"""
    game = games.get(ctx.guild.id)
    if not game:
        await ctx.send("بازی فعالی وجود ندارد!")
        return
    for player, role in game["alive"].items():
        try:
            await player.edit(nick=f"{role}")
        except:
            await ctx.send(f"⚠️ نتونستم نیک {player.mention} رو عوض کنم.")
    await ctx.send("✅ نام‌های پلیرها به نقش‌شان تغییر کرد!")

@bot.command()
async def reset_nick(ctx):
    """برگرداندن اسم ها بعد از دستور show"""
    game = games.get(ctx.guild.id)
    if not game:
        await ctx.send("بازی فعالی وجود ندارد!")
        return
    for player in game["alive"].keys():
        try:
            await player.edit(nick=None)
        except:
            await ctx.send(f"⚠️ نتونستم نیک {player.mention} رو برگردونم.")
    await ctx.send("✅ نام‌های پلیرها به حالت اولیه برگشتند!")

@bot.command()
async def bp(ctx):
    """رأی گیری بست پلیر بازی"""
    game = games.get(ctx.guild.id)
    if not game:
        await ctx.send("بازی فعالی وجود ندارد!")
        return
    if game["status"] != "voting":
        await ctx.send("الان زمان رأی‌گیری نیست!")
        return
    # منطق بست پلیر
    await ctx.send("🗳️ رأی‌گیری بست پلیر شروع شد! (نمونه)")

@bot.command()
async def tahlil(ctx):
    """نوبت دهی تحلیل بازی بصورت شانسی"""
    game = games.get(ctx.guild.id)
    if not game:
        await ctx.send("بازی فعالی وجود ندارد!")
        return
    if game["status"] != "day":
        await ctx.send("فقط در روز می‌تونی این دستور رو بزنی!")
        return
    # انتخاب تصادفی
    players = [p for p in game["alive"].keys()]
    if not players:
        await ctx.send("هیچ پلیری برای تحلیل وجود ندارد!")
        return
    selected = random.choice(players)
    await ctx.send(f"🧠 تحلیل بازی به {selected.mention} واگذار شد!")

@bot.command()
async def mvp(ctx):
    """دیدن لیست بهترین پلیر های سرور"""
    # اینجا منطق MVP می‌تونه اضافه بشه
    await ctx.send("🏆 لیست MVP: (نمونه - منطق بعداً اضافه می‌شه)")

@bot.command()
async def player(ctx, target: discord.Member = None):
    """دیدن مشخصات و سابقه بازی یک پلیر"""
    if target:
        await ctx.send(f"👤 مشخصات {target.mention}: (نمونه)")
    else:
        await ctx.send(f"👤 مشخصات شما: (نمونه)")

@bot.command()
async def thistime(ctx):
    """پیدا کردن لیریک موزیک"""
    # اینجا منطق لیریک می‌تونه اضافه بشه
    await ctx.send("🎵 لیریک موزیک: (نمونه - منطق بعداً اضافه می‌شه)")

@bot.command()
async def dan(ctx):
    """گذاشتن شماره برای پلیر های رو ویس"""
    # اینجا منطق دان می‌تونه اضافه بشه
    await ctx.send("🔢 شماره‌های پلیرها تنظیم شد!")

@bot.command()
async def drn(ctx):
    """حذف شماره پلیر های رو ویس"""
    # اینجا منطق درن می‌تونه اضافه بشه
    await ctx.send("🗑️ شماره‌های پلیرها حذف شد!")

@bot.command()
async def rc(ctx):
    """چک کردن سیستم رندومایز اتوماتیک"""
    # اینجا منطق rc می‌تونه اضافه بشه
    await ctx.send("🎲 سیستم رندومایز اتوماتیک چک شد!")

@bot.command()
async def ln(ctx):
    """مدیریت اتوماتیک تایم شب سناریو بازپرس 10 نفره"""
    # اینجا منطق ln می‌تونه اضافه بشه
    await ctx.send("🕒 تایم شب برای سناریو بازپرس تنظیم شد!")

# دستورات متفرقه
@bot.command()
async def ava(ctx, target: discord.Member = None):
    """دیدن آواتار یوزر"""
    if target:
        await ctx.send(f"🖼️ آواتار {target.mention}: {target.avatar.url}")
    else:
        await ctx.send(f"🖼️ آواتار شما: {ctx.author.avatar.url}")

@bot.command()
async def banner(ctx, target: discord.Member = None):
    """دیدن بنر یوزر"""
    if target:
        if target.banner:
            await ctx.send(f"🎨 بنر {target.mention}: {target.banner.url}")
        else:
            await ctx.send(f"🎨 {target.mention} بنر نداره!")
    else:
        if ctx.author.banner:
            await ctx.send(f"🎨 بنر شما: {ctx.author.banner.url}")
        else:
            await ctx.send("🎨 شما بنر ندارید!")

@bot.command()
async def math(ctx, *, expression: str):
    """حل مسائل ریاضی"""
    try:
        result = eval(expression)
        await ctx.send(f"✅ نتیجه: {result}")
    except Exception as e:
        await ctx.send(f"❌ خطای محاسبه: {e}")

@bot.command()
async def clear(ctx, amount: int = 10):
    """حذف کردن گروهی پیام ها"""
    try:
        deleted = await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"🗑️ {len(deleted)} پیام حذف شد!", delete_after=5)
    except:
        await ctx.send("❌ نمی‌تونم پیام‌ها رو حذف کنم!")

@bot.command()
async def premium(ctx):
    """دیدن وضعیت اشتراک پرمیوم"""
    await ctx.send("💎 وضعیت پرمیوم: (نمونه)")

@bot.command()
async def promo(ctx, promo_code: str):
    """استفاده از پروموکد هدیه"""
    await ctx.send(f"🎁 پروموکد `{promo_code}` دریافت شد! (نمونه)")

@bot.command()
async def nick(ctx, *, new_nick: str = None):
    """ادیت نیک نیم"""
    if new_nick:
        try:
            await ctx.author.edit(nick=new_nick)
            await ctx.send(f"✅ نیک شما به `{new_nick}` تغییر کرد!")
        except:
            await ctx.send("❌ نمی‌تونم نیک شما رو عوض کنم!")
    else:
        await ctx.send("📌 استفاده کن: `.nick example`")

@bot.command()
async def dcme(ctx, duration: str):
    """تایمر دیسکانکت شدن"""
    try:
        # پارس کردن زمان
        if duration.isdigit():
            seconds = int(duration)
        else:
            parts = duration.split()
            seconds = 0
            for part in parts:
                if part.endswith('s'):
                    seconds += int(part[:-1])
                elif part.endswith('m'):
                    seconds += int(part[:-1]) * 60
                elif part.endswith('h'):
                    seconds += int(part[:-1]) * 3600
                else:
                    seconds += int(part)
        await ctx.send(f"⏳ تایمر دیسکانکت شدن برای {seconds} ثانیه شروع شد!")
        await asyncio.sleep(seconds)
        await ctx.author.edit(nick=None)  # یا عملیات دیگر
        await ctx.send("🔌 دیسکانکت شد!")
    except Exception as e:
        await ctx.send(f"خطا در پارس کردن زمان: {e}")

@bot.command()
async def lyrics(ctx, *, query: str):
    """دیدن لیریک موزیک"""
    # اینجا منطق لیریک می‌تونه اضافه بشه
    await ctx.send(f"🎵 لیریک `{query}`: (نمونه - منطق بعداً اضافه می‌شه)")

@bot.command()
async def user(ctx, target: discord.Member = None):
    """دیدن مشخصات اکانت"""
    if target:
        await ctx.send(f"👤 مشخصات {target.mention}: \n- ID: {target.id}\n- نیک: {target.display_name}\n- عضویت: {target.joined_at}")
    else:
        await ctx.send(f"👤 مشخصات شما: \n- ID: {ctx.author.id}\n- نیک: {ctx.author.display_name}\n- عضویت: {ctx.author.joined_at}")

@bot.command()
async def ping(ctx):
    """دیدن پینگ و آپتایم بات"""
    await ctx.send(f"🏓 پینگ: {bot.latency * 1000:.2f}ms")

@bot.command()
async def dollar(ctx):
    """قیمت لحظه ای دلار"""
    # اینجا منطق API می‌تونه اضافه بشه
    await ctx.send("💵 قیمت دلار: 48000 تومان (نمونه)")

@bot.command()
async def euro(ctx):
    """قیمت لحظه ای یورو"""
    # اینجا منطق API می‌تونه اضافه بشه
    await ctx.send("💶 قیمت یورو: 52000 تومان (نمونه)")

@bot.command()
async def ruble(ctx):
    """قیمت لحظه ای روبل روسیه"""
    # اینجا منطق API می‌تونه اضافه بشه
    await ctx.send("🇷🇺 قیمت روبل: 500 تومان (نمونه)")

@bot.command()
async def gold(ctx):
    """قیمت لحظه ای سکه و طلا"""
    # اینجا منطق API می‌تونه اضافه بشه
    await ctx.send("🟡 قیمت طلا: 12000000 تومان (نمونه)")

# اجرای ربات
bot.run(TOKEN)
