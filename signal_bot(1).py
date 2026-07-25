"""
╔══════════════════════════════════════════════════════════════╗
║           🏆 OWNER EMRUL — WINGO VIP SIGNAL BOT 🏆          ║
║              Powered by IMRUL_AI_HACK Analysis              ║
║         Real Result Verification via dkwin9 API             ║
║                  @owner_Emrul1                              ║
╚══════════════════════════════════════════════════════════════╝

📦 ইনস্টল:
    pip install python-telegram-bot apscheduler pytz aiohttp

▶️ চালু:
    python signal_bot.py
"""

import asyncio
import logging
import pytz
import aiohttp
from typing import Optional
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot
from telegram.constants import ParseMode

# ══════════════════════════════════════════════════════
#  ⚙️  কনফিগারেশন — শুধু এই ৩টা বদলাও
# ══════════════════════════════════════════════════════
BOT_TOKEN     = "8833254810:AAFg0Qwi_W8tdDTkAXrBDRcHPuOkhumZljM"       # @BotFather থেকে নাও
CHANNEL_ID    = "@owner_Emrul1"    # যেমন: @emrul_signals
MAX_WIN       = 10                          # কত WIN হলে সেশন বন্ধ

# সেশন IST তে fixed ঘন্টায়: ০, ৩, ৬, ৯, ১২, ১৫, ১৮, ২১
SESSION_HOURS = [0, 3, 6, 9, 12, 15, 18, 21]

REGISTER_LINK = "https://dkwin9.com/#/register?invitationCode=186731981267"
STEF_LINK     = "https://owner-emrul-stef-maker.netlify.app/"
API_URL       = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
ADMIN_USER    = "@owner_Emrul1"

IST = pytz.timezone("Asia/Kolkata")


# ══════════════════════════════════════════════════════
#  📊 ANALYSIS ENGINE — IMRUL_AI_HACK
# ══════════════════════════════════════════════════════

def get_ist_now() -> datetime:
    return datetime.now(IST)


def get_wingo_period(dt: Optional[datetime] = None) -> str:
    """
    Wingo Live Period Calculator
    IST 05:30 AM থেকে প্রতি মিনিটে একটি নতুন period
    Source: IMRUL_AI_HACK decoded JS
    """
    if dt is None:
        dt = get_ist_now()

    current_minutes = dt.hour * 60 + dt.minute
    start_minutes   = 5 * 60 + 30  # 05:30 AM = 330 min

    if current_minutes >= start_minutes:
        elapsed     = current_minutes - start_minutes + 1
        date_prefix = dt.strftime("%Y%m%d")
    else:
        yesterday   = dt - timedelta(days=1)
        date_prefix = yesterday.strftime("%Y%m%d")
        elapsed     = 1110 + current_minutes + 1

    return f"{date_prefix}10001{str(elapsed).zfill(4)}"


def deterministic_prediction(period_str: str) -> dict:
    """
    Seed-based Deterministic Signal Generator
    Source: getDeterministicPrediction() — IMRUL_AI_HACK
    একই period সবসময় একই result দেবে
    """
    h = 0
    for ch in period_str:
        h = (h << 5) - h + ord(ch)
        h &= 0xFFFFFFFF
        if h >= 0x80000000:
            h -= 0x100000000

    is_big     = (abs(h) % 2 == 0)
    prediction = "BIG" if is_big else "SMALL"
    candidates = [5, 6, 7, 8, 9] if is_big else [0, 1, 2, 3, 4]
    num        = candidates[abs(h * 3) % len(candidates)]

    return {"prediction": prediction, "num": num, "period": period_str}


# ══════════════════════════════════════════════════════
#  🌐 REAL RESULT — dkwin9 API
# ══════════════════════════════════════════════════════

async def fetch_real_result(period: str) -> Optional[dict]:
    """
    API থেকে real result নিয়ে period number দিয়ে মেলাও।
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                API_URL,
                params  = {"pageNo": 1, "pageSize": 20},
                timeout = aiohttp.ClientTimeout(total=10),
                headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
            ) as resp:
                if resp.status != 200:
                    return None

                data = await resp.json(content_type=None)

                # বিভিন্ন API response format সামলাও
                records = (
                    data.get("data", {}).get("list", [])
                    or data.get("data", {}).get("data", [])
                    or data.get("list", [])
                    or data.get("result", [])
                    or []
                )

                for r in records:
                    # period/issue number মেলাও
                    issue = str(
                        r.get("issueNumber", "")
                        or r.get("issue", "")
                        or r.get("period", "")
                        or r.get("IssueName", "")
                    ).strip()

                    if issue != period:
                        continue

                    # real number বের করো
                    try:
                        real_num = int(r.get("number", r.get("num", r.get("Number", -1))))
                    except (ValueError, TypeError):
                        real_num = -1

                    # BIG/SMALL বের করো
                    bs_raw = str(
                        r.get("bigSmall", "")
                        or r.get("big_small", "")
                        or r.get("BigSmall", "")
                        or r.get("colour", "")
                        or r.get("color", "")
                    ).strip().upper()

                    if bs_raw in ("BIG", "RED", "B", "1"):
                        real_bs = "BIG"
                    elif bs_raw in ("SMALL", "GREEN", "S", "0"):
                        real_bs = "SMALL"
                    elif real_num >= 0:
                        # number থেকে নিজে বের করো
                        real_bs = "BIG" if real_num >= 5 else "SMALL"
                    else:
                        continue  # data incomplete

                    return {"period": period, "num": real_num, "big_small": real_bs}

        return None

    except Exception as e:
        print(f"[API ERROR] {e}")
        return None


async def wait_for_result(period: str, max_wait: int = 90) -> Optional[dict]:
    """
    Result না আসা পর্যন্ত retry করো — max ৯০ সেকেন্ড
    """
    waited = 0
    while waited < max_wait:
        result = await fetch_real_result(period)
        if result:
            return result
        await asyncio.sleep(5)
        waited += 5
    return None


# ══════════════════════════════════════════════════════
#  🗃️  Session State
# ══════════════════════════════════════════════════════

class SessionState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.active     = False
        self.win_count  = 0
        self.loss_count = 0
        self.streak     = 0
        self.history    = []

    def record_win(self, period, prediction, num):
        self.win_count += 1
        self.streak    += 1
        self.history.append((period, prediction, num, "WIN"))

    def record_loss(self, period, prediction, num):
        self.loss_count += 1
        self.streak      = 0
        self.history.append((period, prediction, num, "LOSS"))

SESSION = SessionState()


# ══════════════════════════════════════════════════════
#  ✉️  Message Templates (HTML parse mode — error নেই)
# ══════════════════════════════════════════════════════

def e(text) -> str:
    """HTML special char escape"""
    return str(text).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

FOOTER = f'\n\n━━━━━━━━━━━━━━━━━━━━━━━━━\n🏆 <b>OWNER EMRUL VIP CHANNEL</b>\n👤 Admin: <a href="https://t.me/owner_Emrul1">{ADMIN_USER}</a>'


def msg_30min_warning() -> str:
    t = get_ist_now()
    return (
        "┏━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        "┃  🏆 OWNER EMRUL VIP SIGNAL  ┃\n"
        "┗━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        "⏰ <b>আর মাত্র ৩০ মিনিট বাকি!</b>\n\n"
        "📢 যারা এখনো রেজিস্ট্রেশন করোনি:\n"
        "👇 নিচের লিঙ্ক দিয়ে একাউন্ট খোলো\n"
        "💰 ডিপোজিট দিয়ে রেডি থাকো!\n\n"
        f'🔗 <a href="{REGISTER_LINK}">📲 একাউন্ট খুলুন এখানে</a>\n\n'
        "✅ একাউন্ট আছে? ব্যালেন্স চেক করো\n"
        f"⏳ সেশন শুরু হবে <b>{e(t.strftime('%I:%M %p'))} IST</b> তে"
        + FOOTER
    )


def msg_1min_warning() -> str:
    return (
        "┏━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        "┃  🚨 সিগনাল শুরু হতে চলেছে!  ┃\n"
        "┗━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        "⚡ আমাদের সিগনাল এখনই শুরু হচ্ছে!\n\n"
        "📌 <b>এখনই STEF বানিয়ে নাও!</b>\n"
        "⛔ <b>STEF ছাড়া একদম খেলবে না!</b>\n\n"
        f'🔗 <a href="{STEF_LINK}">⚙️ STEF বানাও এখানে</a>\n\n'
        "⏳ <b>প্রথম সিগনাল আসছে ১ মিনিটের মধ্যে...</b>"
        + FOOTER
    )


def msg_signal(sig: dict, win: int, loss: int, is_first: bool = False) -> str:
    emoji  = "🔴" if sig["prediction"] == "BIG" else "🟢"
    header = "🟢 সেশন শুরু — প্রথম সিগনাল!" if is_first else "⚡ নতুন সিগনাল!"
    total  = win + loss
    return (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃      {header}\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"👑 <b>OWNER EMRUL PREDICTION</b>\n\n"
        f"📌 Period: <code>{e(sig['period'])}</code>\n"
        f"{emoji} Prediction: <b>{e(sig['prediction'])}</b>\n"
        f"🔢 Number: <b>{e(sig['num'])}</b>\n\n"
        f"📊 Win: <code>{win}</code> | Loss: <code>{loss}</code> | Total: <code>{total}</code>\n\n"
        f"⛔ STEF ছাড়া খেলবে না!\n"
        f'🔗 <a href="{STEF_LINK}">STEF বানাও</a>'
        + FOOTER
    )


def msg_result_win(sig: dict, streak: int, win: int, loss: int, real_num: int) -> str:
    if streak >= 3:
        fires    = "🔥" * min(streak, 8)
        headline = f"🏆 {streak} SUPER WIN!!! 🏆"
        sub      = f"{fires} টানা <b>{streak}</b>টা WIN!"
    else:
        headline = "✅ WIN!"
        sub      = "দারুণ! পরের সিগনালের জন্য অপেক্ষা করো।"

    return (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃      {headline}\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"📌 Period: <code>{e(sig['period'])}</code>\n"
        f"🎯 Prediction: <b>{e(sig['prediction'])}</b> ✅\n"
        f"🔢 আমাদের: <b>{e(sig['num'])}</b>  |  Real: <b>{e(real_num)}</b>\n\n"
        f"{sub}\n\n"
        f"📊 Win: <code>{win}</code> | Loss: <code>{loss}</code>"
        + FOOTER
    )


def msg_result_loss(sig: dict, win: int, loss: int, real_num: int) -> str:
    return (
        "┏━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        "┃          ❌ LOSS          ┃\n"
        "┗━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"📌 Period: <code>{e(sig['period'])}</code>\n"
        f"🎯 Prediction: <b>{e(sig['prediction'])}</b> ❌\n"
        f"🔢 আমাদের: <b>{e(sig['num'])}</b>  |  Real: <b>{e(real_num)}</b>\n\n"
        "💪 হতাশ হইও না, পরেরটায় ভালো হবে ইনশাআল্লাহ!\n\n"
        f"📊 Win: <code>{win}</code> | Loss: <code>{loss}</code>"
        + FOOTER
    )


def msg_jackpot(sig: dict, win: int, loss: int, real_num: int) -> str:
    return (
        "┏━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        "┃  💎🎰 JACKPOT WIN!!! 🎰💎  ┃\n"
        "┗━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"📌 Period: <code>{e(sig['period'])}</code>\n"
        f"🎯 Prediction: <b>{e(sig['prediction'])}</b> ✅\n"
        f"🔢 আমাদের: <b>{e(sig['num'])}</b>  =  Real: <b>{e(real_num)}</b> 💎\n\n"
        "<b>সংখ্যাটা একদম exact মিলে গেছে!</b>\n"
        "🎉 এটাই JACKPOT!\n\n"
        f"📊 Win: <code>{win}</code> | Loss: <code>{loss}</code>"
        + FOOTER
    )


def msg_api_failed(sig: dict, win: int, loss: int) -> str:
    return (
        "⚠️ <b>Result নেওয়া যায়নি</b>\n\n"
        f"📌 Period: <code>{e(sig['period'])}</code>\n"
        "🔄 API থেকে result পাওয়া যায়নি।\n"
        "পরের সিগনাল আসছে...\n\n"
        f"📊 Win: <code>{win}</code> | Loss: <code>{loss}</code>"
        + FOOTER
    )


def next_session_time() -> str:
    now = get_ist_now()
    for h in SESSION_HOURS:
        candidate = now.replace(hour=h, minute=0, second=0, microsecond=0)
        if candidate > now + timedelta(minutes=5):
            return candidate.strftime("%I:%M %p IST")
    tomorrow = (now + timedelta(days=1)).replace(
        hour=SESSION_HOURS[0], minute=0, second=0, microsecond=0
    )
    return tomorrow.strftime("%I:%M %p IST")


def msg_session_end(win: int, loss: int) -> str:
    total    = win + loss
    win_rate = round((win / total * 100) if total > 0 else 0, 1)
    stars    = "⭐" * min(win, 10)
    next_ses = next_session_time()
    return (
        "┏━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃  🏁 সেশন শেষ! {MAX_WIN} WIN হয়েছে!  ┃\n"
        "┗━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"👑 <b>OWNER EMRUL — SESSION REPORT</b>\n\n"
        f"{stars}\n\n"
        f"✅ Total Win:  <code>{win}</code>\n"
        f"❌ Total Loss: <code>{loss}</code>\n"
        f"📈 Win Rate:   <code>{win_rate}%</code>\n"
        f"🎮 Total Play: <code>{total}</code>\n\n"
        f"⏰ পরের সেশন: <b>{e(next_ses)}</b>\n\n"
        "🙏 সবাইকে ধন্যবাদ!\n"
        "📢 চ্যানেলে থাকো, নোটিফিকেশন অন রাখো!"
        + FOOTER
    )


# ══════════════════════════════════════════════════════
#  🤖  Bot Core
# ══════════════════════════════════════════════════════

bot = Bot(token=BOT_TOKEN)


async def send(text: str):
    try:
        await bot.send_message(
            chat_id              = CHANNEL_ID,
            text                 = text,
            parse_mode           = ParseMode.HTML,
            disable_web_page_preview = True
        )
    except Exception as ex:
        print(f"[SEND ERROR] {ex}")


# ══════════════════════════════════════════════════════
#  🔄  Period Watcher — Real API Result Check
# ══════════════════════════════════════════════════════

async def period_watcher():
    """
    প্রতি ৫ সেকেন্ডে Wingo period চেক করে।

    Flow প্রতি নতুন period এ:
      1. আগের period এর real result API থেকে আনো
      2. Period number দিয়ে exact match করো
      3. BIG/SMALL মেলাও → WIN / LOSS
      4. Exact number মেলাও → JACKPOT
      5. Result channel এ পাঠাও
      6. নতুন signal পাঠাও
      7. ১০ WIN হলে সেশন বন্ধ করো
    """
    last_sent_period = None
    pending_sig      = None
    is_first_signal  = True

    while SESSION.active and SESSION.win_count < MAX_WIN:
        current_period = get_wingo_period()

        if current_period != last_sent_period:

            # ── আগের signal এর REAL result চেক করো ──
            if pending_sig is not None:
                prev = pending_sig
                print(f"[API] Period {prev['period']} এর result আনা হচ্ছে...")

                real = await wait_for_result(prev["period"], max_wait=90)

                if real is None:
                    print(f"[API] Period {prev['period']} — result পাওয়া যায়নি")
                    await send(msg_api_failed(prev, SESSION.win_count, SESSION.loss_count))
                else:
                    real_num = real["num"]
                    real_bs  = real["big_small"]
                    print(f"[RESULT] {prev['period']} → Real: {real_bs} {real_num} | Pred: {prev['prediction']} {prev['num']}")

                    is_jackpot = (real_num == prev["num"])
                    is_win     = (real_bs  == prev["prediction"])

                    if is_jackpot:
                        # number exact মিলেছে — JACKPOT (WIN ও ধরা হয়)
                        SESSION.record_win(prev["period"], prev["prediction"], prev["num"])
                        await send(msg_jackpot(prev, SESSION.win_count, SESSION.loss_count, real_num))

                    elif is_win:
                        SESSION.record_win(prev["period"], prev["prediction"], prev["num"])
                        await send(msg_result_win(prev, SESSION.streak, SESSION.win_count, SESSION.loss_count, real_num))

                    else:
                        SESSION.record_loss(prev["period"], prev["prediction"], prev["num"])
                        await send(msg_result_loss(prev, SESSION.win_count, SESSION.loss_count, real_num))

                    # ১০ WIN হলে সেশন বন্ধ করো
                    if SESSION.win_count >= MAX_WIN:
                        SESSION.active = False
                        await asyncio.sleep(1)
                        await send(msg_session_end(SESSION.win_count, SESSION.loss_count))
                        return

                await asyncio.sleep(1)

            # ── নতুন period এর signal পাঠাও ──
            new_sig          = deterministic_prediction(current_period)
            pending_sig      = new_sig
            last_sent_period = current_period

            await send(msg_signal(new_sig, SESSION.win_count, SESSION.loss_count, is_first_signal))
            is_first_signal = False
            print(f"[SIGNAL] {current_period} → {new_sig['prediction']} {new_sig['num']}")

        await asyncio.sleep(5)


# ══════════════════════════════════════════════════════
#  ⏰  Session Triggers
# ══════════════════════════════════════════════════════

async def on_30min_warning():
    print("[BOT] ৩০ মিনিট warning পাঠানো হচ্ছে...")
    await send(msg_30min_warning())


async def on_1min_warning():
    print("[BOT] ১ মিনিট warning পাঠানো হচ্ছে...")
    await send(msg_1min_warning())


async def on_session_start():
    print("[BOT] সেশন শুরু হচ্ছে...")
    SESSION.reset()
    SESSION.active = True
    asyncio.create_task(period_watcher())


# ══════════════════════════════════════════════════════
#  📅  Scheduler — Fixed ঘন্টায় সেশন (IST)
# ══════════════════════════════════════════════════════

scheduler = AsyncIOScheduler(timezone=IST)


def setup_schedule():
    """
    SESSION_HOURS = [0, 3, 6, 9, 12, 15, 18, 21]

    প্রতিটি ঘন্টার জন্য ৩টি cron job:
      (H*60 - 30) min → ৩০ মিনিট আগে warning
      (H*60 - 1)  min → ১ মিনিট আগে warning
      H:00:00         → সেশন শুরু
    """
    for h in SESSION_HOURS:

        # ৩০ মিনিট আগে
        total_30 = h * 60 - 30
        if total_30 < 0:
            total_30 += 24 * 60          # midnight rollover
        w30_h, w30_m = divmod(total_30, 60)
        scheduler.add_job(
            on_30min_warning,
            trigger = "cron",
            hour    = w30_h % 24,
            minute  = w30_m,
            second  = 0,
            id      = f"warn30_h{h}"
        )

        # ১ মিনিট আগে
        total_1 = h * 60 - 1
        if total_1 < 0:
            total_1 += 24 * 60
        w1_h, w1_m = divmod(total_1, 60)
        scheduler.add_job(
            on_1min_warning,
            trigger = "cron",
            hour    = w1_h % 24,
            minute  = w1_m,
            second  = 0,
            id      = f"warn1_h{h}"
        )

        # সেশন শুরু
        scheduler.add_job(
            on_session_start,
            trigger = "cron",
            hour    = h,
            minute  = 0,
            second  = 0,
            id      = f"session_h{h}"
        )

        print(f"  ✅ {str(h).zfill(2)}:00 IST — সেশন scheduled")


# ══════════════════════════════════════════════════════
#  🚀  Main Entry Point
# ══════════════════════════════════════════════════════

async def main():
    print()
    print("╔══════════════════════════════════════════════╗")
    print("║   🏆  OWNER EMRUL — VIP SIGNAL BOT  🏆      ║")
    print("║            @owner_Emrul1                     ║")
    print("╠══════════════════════════════════════════════╣")
    print(f"║  Channel  : {CHANNEL_ID:<33}║")
    print(f"║  Sessions : {str(SESSION_HOURS):<33}║")
    print(f"║  Max Win  : {str(MAX_WIN):<33}║")
    print("╚══════════════════════════════════════════════╝")
    print()
    print("[SCHEDULE] সব সেশন:")

    setup_schedule()
    scheduler.start()

    now      = get_ist_now()
    next_ses = next_session_time()
    print()
    print(f"[BOT] ✅ চালু হয়েছে! বর্তমান সময়: {now.strftime('%I:%M %p IST')}")
    print(f"[BOT] ⏰ পরের সেশন: {next_ses}")
    print("[BOT] Ctrl+C দিয়ে বন্ধ করো।")
    print()

    try:
        while True:
            await asyncio.sleep(30)
    except (KeyboardInterrupt, SystemExit):
        print("\n[BOT] বন্ধ হচ্ছে...")
        scheduler.shutdown()


if __name__ == "__main__":
    logging.basicConfig(
        level  = logging.WARNING,
        format = "%(asctime)s [%(levelname)s] %(message)s"
    )
    asyncio.run(main())
