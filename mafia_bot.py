# mafia_discord_bot.py
# Python 3.10+
# pip install -U discord.py

import os
import asyncio
import json
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import discord
from discord.ext import commands

# ---------- تنظیمات پایه ----------
TOKEN = os.getenv("DISCORD_TOKEN")
COMMAND_PREFIX = "!"
INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.members = True
BOT = commands.Bot(command_prefix=COMMAND_PREFIX, intents=INTENTS)

# ---------- سناریوهای داخلی (می‌تونی بعداً سناریو سفارشی JSON لود کنی) ----------
BUILTIN_SCENARIOS = {
    "classic": {
        "name": "classic",
        "roles": [
            {"role": "Godfather", "count": 1},
            {"role": "Mafia", "count": 1},
            {"role": "Doctor", "count": 1},
            {"role": "Detective", "count": 1},
            {"role": "Villager", "count": "fill"}
        ],
        "rules": {
            "revealOnLynch": False,
            "timers": {"night": 90, "day": 180, "vote": 60}
        }
    },
    "iranian": {
        "name": "iranian",
        "roles": [
            {"role": "Godfather", "count": 1},
            {"role": "Mafia", "count": 1},
            {"role": "MafiaSupport", "count": 1},
            {"role": "Doctor", "count": 1},
            {"role": "Detective", "count": 1},
            {"role": "Psychologist", "count": 1},
            {"role": "Villager", "count": "fill"}
        ],
        "rules": {
            "revealOnLynch": True,
            "timers": {"night": 80, "day": 160, "vote": 60}
        }
    },
    "speed": {
        "name": "speed",
        "roles": [
            {"role": "Godfather", "count": 1},
            {"role": "Mafia", "count": 1},
            {"role": "Doctor", "count": 1},
            {"role": "Detective", "count": 1},
            {"role": "Villager", "count": "fill"}
        ],
        "rules": {
            "revealOnLynch": False,
            "timers": {"night": 60, "day": 120, "vote": 45}
        }
    }
}

TEAM_OF_ROLE = {
    "Godfather": "Mafia",
    "Mafia": "Mafia",
    "MafiaSupport": "Mafia",
    "Doctor": "Town",
    "Detective": "Town",
    "Psychologist": "Town",
    "Sniper": "Town",
    "Villager": "Town",
}

# ---------- مدل داده ----------
@dataclass
class PlayerState:
    user_id: int
    display_name: str
    role: Optional[str] = None
    alive: bool = True
    last_night_action: Optional[Tuple[str, Optional[int]]] = None  # (action_type, target_id)

@dataclass
class GameState:
    channel_id: int
    host_id: int  # کسی که بازی را ساخته (گاد اولیه)
    god_id: Optional[int] = None
    state: str = "Lobby"  # Lobby, AssignRoles, Night, DawnReport, DayDiscussion, Voting, LynchResult, WinCheck, EndGame
    scenario: Dict = field(default_factory=lambda: BUILTIN_SCENARIOS["classic"])
    timers: Dict[str, int] = field(default_factory=lambda: {"night": 90, "day": 180, "vote": 60})
    reveal_on_lynch: bool = False
    players: Dict[int, PlayerState] = field(default_factory=dict)  # user_id -> PlayerState
    votes: Dict[int, int] = field(default_factory=dict)  # voter_id -> target_id
    log: List[str] = field(default_factory=list)
    night_actions_queue: List[Tuple[int, str, Optional[int]]] = field(default_factory=list)  # (actor_id, action, target_id)
    last_report: str = ""

    def alive_players(self) -> List[PlayerState]:
        return [p for p in self.players.values() if p.alive]

    def mafia_count(self) -> int:
        return sum(1 for p in self.alive_players() if TEAM_OF_ROLE.get(p.role, "") == "Mafia")

    def town_count(self) -> int:
        return sum(1 for p in self.alive_players() if TEAM_OF_ROLE.get(p.role, "") == "Town")


GAMES: Dict[int, GameState] = {}  # channel_id -> GameState

# ---------- ابزارها ----------
def format_tally(game: GameState) -> str:
    counts: Dict[int, int] = {}
    for target_id in game.votes.values():
        counts[target_id] = counts.get(target_id, 0) + 1
    if not counts:
        return "بدون رأی"
    lines = []
    for tid, c in sorted(counts.items(), key=lambda x: -x[1]):
        lines.append(f"<@{tid}>: {c}")
    return "\n".join(lines)

def assign_roles(game: GameState):
    count = len(game.players)
    roles_spec = game.scenario["roles"]

    base_roles: List[str] = []
    fixed_total = 0
    for spec in roles_spec:
        c = spec["count"]
        if isinstance(c, int):
            base_roles.extend([spec["role"]] * c)
            fixed_total += c
    # fill rest
    for spec in roles_spec:
        if spec["count"] == "fill":
            fill_role = spec["role"]
            to_fill = max(0, count - fixed_total)
            base_roles.extend([fill_role] * to_fill)
            break

    random.shuffle(base_roles)
    if len(base_roles) != count:
        # اگر mismatch شد، با Villager پر می‌کنیم
        while len(base_roles) < count:
            base_roles.append("Villager")
        base_roles = base_roles[:count]

    i = 0
    for p in game.players.values():
        p.role = base_roles[i]
        i += 1

def resolve_night(game: GameState) -> List[str]:
    # ترتیب حل: Block (MafiaSupport/Psychologist) > Protect (Doctor) > Kill (Godfather/Mafia) > Investigate (Detective)
    actions = list(game.night_actions_queue)
    game.night_actions_queue.clear()

    blocks: set[int] = set()
    protects: set[int] = set()
    kills: List[int] = []
    investigations: List[Tuple[int, int]] = []  # (detective_id, target_id)

    id_to_player = game.players

    def role_of(uid: int) -> Optional[str]:
        return id_to_player.get(uid).role if uid in id_to_player else None

    # دسته‌بندی
    for actor_id, action, target_id in actions:
        r = role_of(actor_id)
        if not r or not id_to_player[actor_id].alive:
            continue
        if action == "block" and r in {"MafiaSupport", "Psychologist"} and target_id:
            blocks.add(target_id)
        elif action == "protect" and r == "Doctor" and target_id:
            protects.add(target_id)
        elif action == "kill" and r in {"Godfather", "Mafia"} and target_id:
            kills.append(target_id)
        elif action == "investigate" and r == "Detective" and target_id:
            investigations.append((actor_id, target_id))

    # اعمال بلاک: هر کسی در blocks نتونه اکشن بده (اکشن‌ها قبلاً ثبت شده‌اند؛ اثر بلاک در آینده می‌تونه گسترده‌تر بشه)
    # محافظت: اگر در لیست کشتار باشد و protect شاملش شود، kill بی‌اثر
    # kill: اگر protect نشود، حذف
    night_log: List[str] = []

    # Kill‌ها
    killed_final: List[int] = []
    for t in kills:
        if t in protects:
            night_log.append(f"ترور روی <@{t}> بی‌اثر شد.")
        else:
            # اگر هدف زنده است
            if t in id_to_player and id_to_player[t].alive:
                id_to_player[t].alive = False
                killed_final.append(t)
                night_log.append(f"دیشب <@{t}> کشته شد.")

    # Investigate
    for det_id, tgt_id in investigations:
        if det_id in blocks:
            night_log.append(f"اکشن کارآگاه <@{det_id}> بلاک شد.")
            continue
        tgt_role = id_to_player.get(tgt_id).role if tgt_id in id_to_player else None
        # گادفادر ضدآشکارسازی: به‌عنوان Villager نمایش داده شود
        if tgt_role == "Godfather":
            shown = "Villager"
        else:
            shown = tgt_role or "Unknown"
        night_log.append(f"نتیجه استعلام <@{det_id}>: نقش <@{tgt_id}> -> {shown}")

    return night_log

def win_check(game: GameState) -> Optional[str]:
    mafia = game.mafia_count()
    town = game.town_count()
    if mafia == 0:
        return "برد شهروندان! همه مافیا حذف شدند."
    if mafia >= town:  # برابری یا بیشتر: مافیا کنترل شهر را گرفت
        return "برد مافیا! تعداد مافیا با شهر برابر/بیشتر شد."
    return None

def game_report(game: GameState) -> str:
    roles_lines = []
    for p in game.players.values():
        roles_lines.append(f"• {p.display_name}: {p.role} ({'زنده' if p.alive else 'حذف'})")
    log_lines = "\n".join([f"• {l}" for l in game.log]) if game.log else "—"
    return (
        f"گزارش نهایی بازی\n"
        f"نقش‌ها و وضعیت:\n" + "\n".join(roles_lines) + "\n"
        f"رخدادها:\n" + log_lines
    )

# ---------- دستورات بازیکنان ----------
@BOT.command(name="newgame")
async def newgame(ctx: commands.Context, scenario_name: str = "classic"):
    if ctx.channel.id in GAMES:
        await ctx.send("در این کانال یک بازی فعال است.")
        return
    scenario = BUILTIN_SCENARIOS.get(scenario_name)
    if not scenario:
        await ctx.send("سناریو یافت نشد. سناریوهای موجود: " + ", ".join(BUILTIN_SCENARIOS.keys()))
        return
    g = GameState(
        channel_id=ctx.channel.id,
        host_id=ctx.author.id,
        god_id=ctx.author.id,
        scenario=scenario,
        timers=scenario["rules"]["timers"],
        reveal_on_lynch=scenario["rules"]["revealOnLynch"]
    )
    GAMES[ctx.channel.id] = g
    await ctx.send(f"اتاق مافیا ساخته شد با سناریو: {scenario_name}\nبا !join وارد شوید. گاد: <@{g.god_id}>")

@BOT.command(name="join")
async def join(ctx: commands.Context):
    game = GAMES.get(ctx.channel.id)
    if not game or game.state != "Lobby":
        await ctx.send("لابی فعال نیست.")
        return
    if ctx.author.id in game.players:
        await ctx.send("قبلاً وارد شدی.")
        return
    member = ctx.author
    game.players[member.id] = PlayerState(user_id=member.id, display_name=member.display_name if hasattr(member, 'display_name') else member.name)
    await ctx.send(f"<@{member.id}> وارد لابی شد. تعداد: {len(game.players)}")

@BOT.command(name="lock")
async def lock(ctx: commands.Context):
    game = GAMES.get(ctx.channel.id)
    if not game or game.state != "Lobby":
        await ctx.send("لابی فعال نیست.")
        return
    if ctx.author.id != game.host_id and ctx.author.id != game.god_id:
        await ctx.send("فقط میزبان/گاد می‌تواند لابی را قفل کند.")
        return
    if len(game.players) < 6:
        await ctx.send("حداقل 6 نفر لازم است.")
        return
    game.state = "AssignRoles"
    assign_roles(game)
    await ctx.send("لابی قفل شد. نقش‌ها در حال ارسال هستند…")
    # ارسال نقش‌ها به DM
    for p in game.players.values():
        user = await BOT.fetch_user(p.user_id)
        try:
            await user.send(f"نقش شما: {p.role}\n"
                            f"اکشن شب را با پاسخ همین پیام اعلام کنید (اگر دارید). مثال: kill @User یا protect @User یا investigate @User یا block @User")
        except Exception:
            await ctx.send(f"<@{p.user_id}> لطفاً DM خود را فعال کنید تا نقش برای شما ارسال شود.")
    game.state = "Night"
    game.log.append("شب اول آغاز شد.")
    await ctx.send("شب است. نقش‌ها اکشن‌های خود را تا زمان تعیین‌شده ثبت کنند.")
    # شروع تایمر شب
    asyncio.create_task(night_timer(ctx.channel.id))

async def night_timer(channel_id: int):
    await asyncio.sleep(GAMES[channel_id].timers["night"])
    game = GAMES.get(channel_id)
    if not game or game.state != "Night":
        return
    night_log = resolve_night(game)
    report = "گزارش سحرگاه:\n" + ("\n".join([f"• {l}" for l in night_log]) if night_log else "• دیشب اتفاق خاصی نیفتاد.")
    game.log.append("سحرگاه اعلام شد.")
    game.state = "DawnReport"
    game.last_report = report
    channel = BOT.get_channel(channel_id)
    if channel:
        await channel.send(report)
        game.state = "DayDiscussion"
        await channel.send("روز است. زمان بحث شروع شد.")
        asyncio.create_task(day_timer(channel_id))

async def day_timer(channel_id: int):
    await asyncio.sleep(GAMES[channel_id].timers["day"])
    game = GAMES.get(channel_id)
    if not game or game.state != "DayDiscussion":
        return
    game.state = "Voting"
    channel = BOT.get_channel(channel_id)
    if channel:
        await channel.send("فاز رأی‌گیری شروع شد. با !vote @user رأی دهید. می‌توانید با !unvote رأی خود را حذف کنید.")
        asyncio.create_task(vote_timer(channel_id))

async def vote_timer(channel_id: int):
    await asyncio.sleep(GAMES[channel_id].timers["vote"])
    game = GAMES.get(channel_id)
    if not game or game.state != "Voting":
        return
    # محاسبه اعدام
    tally: Dict[int, int] = {}
    for t in game.votes.values():
        tally[t] = tally.get(t, 0) + 1
    if not tally:
        result_text = "هیچ رأیی ثبت نشد. امروز کسی اعدام نمی‌شود."
        lynched_id = None
    else:
        # بیشترین رأی، اگر مساوی است عدم اعدام
        sorted_tally = sorted(tally.items(), key=lambda x: (-x[1], x[0]))
        top = sorted_tally[0]
        # بررسی مساوی
        if len(sorted_tally) > 1 and sorted_tally[0][1] == sorted_tally[1][1]:
            result_text = "رأی‌ها مساوی شد. امروز اعدام صورت نمی‌گیرد."
            lynched_id = None
        else:
            lynched_id = top[0]
            result_text = f"با {top[1]} رأی، <@{lynched_id}> اعدام شد."
            if lynched_id in game.players and game.players[lynched_id].alive:
                game.players[lynched_id].alive = False
                if game.reveal_on_lynch:
                    result_text += f" نقش او: {game.players[lynched_id].role}"

    game.state = "LynchResult"
    channel = BOT.get_channel(channel_id)
    if channel:
        await channel.send(result_text)
        game.log.append(result_text)
        game.state = "WinCheck"
        winner = win_check(game)
        if winner:
            await channel.send(winner)
            rep = game_report(game)
            await channel.send(rep)
            game.state = "EndGame"
            del GAMES[channel_id]
        else:
            # روز بعد: Night
            game.votes.clear()
            await channel.send("بازی ادامه دارد. شب بعد آغاز می‌شود…")
            game.state = "Night"
            asyncio.create_task(night_timer(channel_id))

@BOT.command(name="vote")
async def vote(ctx: commands.Context, member: Optional[discord.Member]):
    game = GAMES.get(ctx.channel.id)
    if not game or game.state != "Voting":
        await ctx.send("الان فاز رأی‌گیری نیست.")
        return
    if not member:
        await ctx.send("هدف معتبر نیست. مثال: !vote @username")
        return
    if ctx.author.id not in game.players or not game.players[ctx.author.id].alive:
        await ctx.send("شما در بازی نیستید یا حذف شده‌اید.")
        return
    if member.id not in game.players or not game.players[member.id].alive:
        await ctx.send("هدف معتبر نیست یا حذف شده است.")
        return
    game.votes[ctx.author.id] = member.id
    await ctx.send("رأی ثبت شد.\n" + format_tally(game))

@BOT.command(name="unvote")
async def unvote(ctx: commands.Context):
    game = GAMES.get(ctx.channel.id)
    if not game or game.state != "Voting":
        await ctx.send("الان فاز رأی‌گیری نیست.")
        return
    game.votes.pop(ctx.author.id, None)
    await ctx.send("رأی شما حذف شد.\n" + format_tally(game))

@BOT.command(name="status")
async def status(ctx: commands.Context):
    game = GAMES.get(ctx.channel.id)
    if not game:
        await ctx.send("بازی‌ای فعال نیست.")
        return
    alive = ", ".join([p.display_name for p in game.alive_players()]) or "—"
    await ctx.send(f"فاز: {game.state}\nزنده‌ها: {alive}")

@BOT.command(name="end")
async def end(ctx: commands.Context):
    game = GAMES.get(ctx.channel.id)
    if not game:
        await ctx.send("بازی‌ای فعال نیست.")
        return
    if ctx.author.id not in {game.host_id, game.god_id}:
        await ctx.send("فقط میزبان/گاد می‌تواند پایان دهد.")
        return
    rep = game_report(game)
    await ctx.send("بازی پایان یافت.\n" + rep)
    del GAMES[ctx.channel.id]

# ---------- دستورات گاد ----------
def is_god(ctx: commands.Context, game: GameState) -> bool:
    return ctx.author.id in {game.god_id, game.host_id}

@BOT.command(name="god_take")
async def god_take(ctx: commands.Context):
    game = GAMES.get(ctx.channel.id)
    if not game:
        await ctx.send("بازی‌ای فعال نیست.")
        return
    game.god_id = ctx.author.id
    await ctx.send(f"گاد تنظیم شد: <@{ctx.author.id}>")

@BOT.command(name="god_assign")
async def god_assign(ctx: commands.Context, member: discord.Member, role: str):
    game = GAMES.get(ctx.channel.id)
    if not game:
        await ctx.send("بازی‌ای فعال نیست.")
        return
    if not is_god(ctx, game):
        await ctx.send("دسترسی گاد لازم است.")
        return
    p = game.players.get(member.id)
    if not p:
        await ctx.send("بازیکن در بازی نیست.")
        return
    p.role = role
    await ctx.send(f"نقش <@{member.id}> به {role} تغییر کرد.")

@BOT.command(name="god_kill")
async def god_kill(ctx: commands.Context, member: discord.Member):
    game = GAMES.get(ctx.channel.id)
    if not game:
        await ctx.send("بازی‌ای فعال نیست.")
        return
    if not is_god(ctx, game):
        await ctx.send("دسترسی گاد لازم است.")
        return
    p = game.players.get(member.id)
    if not p or not p.alive:
        await ctx.send("هدف معتبر نیست یا قبلاً حذف شده.")
        return
    p.alive = False
    await ctx.send(f"<@{member.id}> توسط گاد حذف شد.")
    w = win_check(game)
    if w:
        await ctx.send(w)
        rep = game_report(game)
        await ctx.send(rep)
        del GAMES[ctx.channel.id]

@BOT.command(name="god_revive")
async def god_revive(ctx: commands.Context, member: discord.Member):
    game = GAMES.get(ctx.channel.id)
    if not game:
        await ctx.send("بازی‌ای فعال نیست.")
        return
    if not is_god(ctx, game):
        await ctx.send("دسترسی گاد لازم است.")
        return
    p = game.players.get(member.id)
    if not p:
        await ctx.send("بازیکن در بازی نیست.")
        return
    p.alive = True
    await ctx.send(f"<@{member.id}> توسط گاد برگردانده شد.")

@BOT.command(name="god_state")
async def god_state(ctx: commands.Context, new_state: str):
    game = GAMES.get(ctx.channel.id)
    if not game:
        await ctx.send("بازی‌ای فعال نیست.")
        return
    if not is_god(ctx, game):
        await ctx.send("دسترسی گاد لازم است.")
        return
    game.state = new_state
    await ctx.send(f"حالت بازی به {new_state} تغییر کرد.")

@BOT.command(name="god_scenario")
async def god_scenario(ctx: commands.Context, action: str, *, payload: str = ""):
    """
    !god_scenario load classic
    !god_scenario load iranian
    !god_scenario json {"name":"custom","roles":[...],"rules":{"revealOnLynch":true,"timers":{"night":70,"day":150,"vote":60}}}
    """
    game = GAMES.get(ctx.channel.id)
    if not game:
        await ctx.send("بازی‌ای فعال نیست.")
        return
    if not is_god(ctx, game):
        await ctx.send("دسترسی گاد لازم است.")
        return
    if action == "load":
        name = payload.strip()
        sc = BUILTIN_SCENARIOS.get(name)
        if not sc:
            await ctx.send("سناریو یافت نشد.")
            return
        game.scenario = sc
        game.timers = sc["rules"]["timers"]
        game.reveal_on_lynch = sc["rules"]["revealOnLynch"]
        await ctx.send(f"سناریو لود شد: {name}")
    elif action == "json":
        try:
            sc = json.loads(payload)
            game.scenario = sc
            game.timers = sc["rules"]["timers"]
            game.reveal_on_lynch = sc["rules"]["revealOnLynch"]
            await ctx.send(f"سناریوی سفارشی لود شد: {sc.get('name','custom')}")
        except Exception as e:
            await ctx.send(f"JSON نامعتبر: {e}")
    else:
        await ctx.send("استفاده: !god_scenario load <name> یا !god_scenario json <json>")

# ---------- اکشن‌های شب از طریق DM ----------
@BOT.event
async def on_message(message: discord.Message):
    # اجازه به commands برای پردازش
    await BOT.process_commands(message)

    # فقط DMها برای اکشن شب
    if message.guild is not None:
        return  # فقط DM
    if message.author.bot:
        return

    # هر بازی در کانال‌های مختلف است؛ کاربر ممکن است در چند بازی باشد.
    # برای سادگی، اولین بازی‌ای که کاربر داخلش هست و فاز Night باشد را پیدا می‌کنیم.
    target_game: Optional[GameState] = None
    for g in GAMES.values():
        if g.state == "Night" and message.author.id in g.players and g.players[message.author.id].alive:
            target_game = g
            break
    if not target_game:
        return

    content = message.content.strip()
    # الگوهای ساده: kill @id | protect @id | investigate @id | block @id
    def parse_target_id(text: str) -> Optional[int]:
        # انتظار داریم mention به صورت <@12345> یا @نام؛ برای سادگی فقط mention عددی را می‌گیریم
        if "<@" in text and ">" in text:
            try:
                num = text[text.find("<@")+2:text.find(">")].replace("!", "")
                return int(num)
            except:
                return None
        return None

    actor_id = message.author.id
    lower = content.lower()
    action, target_id = None, None
    if lower.startswith("kill"):
        action = "kill"
        target_id = parse_target_id(content)
    elif lower.startswith("protect"):
        action = "protect"
        target_id = parse_target_id(content)
    elif lower.startswith("investigate"):
        action = "investigate"
        target_id = parse_target_id(content)
    elif lower.startswith("block"):
        action = "block"
        target_id = parse_target_id(content)

    if not action:
        await message.channel.send("اکشن نامعتبر. از kill/protect/investigate/block استفاده کن و هدف را mention کن.")
        return

    # اعتبار نقش
    role = target_game.players[actor_id].role
    valid_by_role = {
        "Godfather": {"kill"},
        "Mafia": {"kill"},
        "MafiaSupport": {"block"},
        "Doctor": {"protect"},
        "Detective": {"investigate"},
        "Psychologist": {"block"},
        "Sniper": set(),  # روز
        "Villager": set()
    }
    if action not in valid_by_role.get(role, set()):
        await message.channel.send("این اکشن برای نقش شما معتبر نیست.")
        return

    # ثبت اکشن (آخرین اکشن تا پایان تایمر ملاک است)
    # اگر target_id خالی بود، تلاش برای match با نام‌ها را می‌توان افزود؛ فعلاً لازم است mention شود.
    target_game.night_actions_queue = [a for a in target_game.night_actions_queue if a[0] != actor_id]
    target_game.night_actions_queue.append((actor_id, action, target_id))
    target_game.players[actor_id].last_night_action = (action, target_id)
    await message.channel.send("اکشن شما ثبت شد.")

# ---------- راه‌اندازی ----------
@BOT.event
async def on_ready():
    print(f"Logged in as {BOT.user} (id: {BOT.user.id})")
    print("Bot is ready. Commands: !newgame, !join, !lock, !vote, !unvote, !status, !end, !god_take, !god_assign, !god_kill, !god_revive, !god_state, !god_scenario")

if __name__ == "__main__":
    if not TOKEN:
        print("DISCORD_TOKEN را به‌عنوان متغیر محیطی تنظیم کنید.")
    else:
        BOT.run(TOKEN)
