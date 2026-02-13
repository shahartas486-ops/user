"""
ربات مسدودکننده پیام‌های خصوصی
سازگار با پایتون ۳.۱۴ و بالاتر
استاندارد جدید asyncio
"""

from telethon import TelegramClient, events
from telethon.tl.functions.contacts import BlockRequest
import asyncio
from datetime import datetime
import os

# =============== دریافت اطلاعات ===============
API_ID = int(os.environ.get('API_ID', 0))
API_HASH = os.environ.get('API_HASH', '')
PHONE = os.environ.get('PHONE', '')
SUPPORT_BOT_TOKEN = os.environ.get('SUPPORT_BOT_TOKEN', '')
SUPPORT_BOT_USERNAME = os.environ.get('SUPPORT_BOT_USERNAME', '@chatbot11011_bot')
WHITELIST_IDS = os.environ.get('WHITELIST_IDS', '')

# =============== پردازش لیست سفید ===============
SUPPORT_BOT_ID = int(SUPPORT_BOT_TOKEN.split(':')[0]) if ':' in SUPPORT_BOT_TOKEN else 0
WHITELIST = [777000, SUPPORT_BOT_ID]

if WHITELIST_IDS:
    for wid in WHITELIST_IDS.split(','):
        try:
            WHITELIST.append(int(wid.strip()))
        except:
            pass

# =============== تنظیمات ===============
MAX_VIOLATIONS = 5
WELCOME_DELETE = 35
WARNING_DELETE = 25
BAN_DELETE = 20

# =============== دیتابیس در حافظه ===============
violations = {}
banned = set()
welcomed = set()

# =============== پیام خوش‌آمدگویی ===============
WELCOME_EPIC = """
🚫 **دسترسی غیرمجاز | Unauthorized Access** 🚫

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👋 **سلام {name} جان!**
🆔 **شناسه دیجیتال:** `{user_id}`
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔒 **شما وارد یک منطقه امنیتی شدید!**

⚠️ **ارسال پیام مستقیم به این حساب ممنوع می‌باشد!**

🤖 **راه ارتباطی رسمی:**
➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖
🌟 **ربات پشتیبانی:** `{support_bot}`
➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖

📋 **راهنمای ارتباط:**

【۱】 روی آیدی ربات کلیک کنید
【۲】 دکمه START را بزنید
【۳】 پیام خود را ارسال کنید

⚠️ **هشدار امنیتی:**
❌ پس از {max_viol} بار تخلف، **مسدود** خواهید شد

⏳ **این پیام {delete_time} ثانیه دیگر منقضی می‌شود...**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔗 [ربات پشتیبانی](https://t.me/{support_bot_raw})
"""

# =============== پیام هشدار ===============
WARNING_EPIC = """
⛔ **اخطار امنیتی | Security Warning** ⛔

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 **اطلاعات کاربر:**

┌──────────────────────────────
├ 👤 نام: {name}
├ 🆔 آیدی: `{user_id}`
├ 📊 وضعیت: **اخطار {count}/{max_count}**
└ 📆 تاریخ: {date}
──────────────────────────────

❌ **پیام شما حذف گردید!**

🤖 **مسیر صحیح:**
👉 **`{support_bot}`** 👈

📊 **تخلفات شما:**

🔸 تعداد اخطار: **{count} از {max_count}**
🔸 اخطار باقی‌مانده: **{remaining}**
🔸 ریسک مسدودیت: **{risk}%**

{message}

⏳ **این هشدار {delete_time} ثانیه دیگر محو می‌شود...**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔗 [ربات پشتیبانی](https://t.me/{support_bot_raw})
"""

# =============== پیام مسدودیت ===============
BAN_EPIC = """
🔴 **مسدودیت دائمی | Permanent Ban** 🔴

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 **اطلاعات کاربر مسدود شده:**

┌──────────────────────────────
├ 👤 نام: {name}
├ 🆔 آیدی: `{user_id}`
├ 📆 تاریخ: {date}
└ ⚖️ دلیل: {max_count} اخطار متوالی
──────────────────────────────

❌ **دسترسی شما قطع شد!**

🤖 **تنها راه ارتباطی:**
👉 **`{support_bot}`** 👈

⚠️ این تصمیم **قطعی و غیرقابل بازگشت** است

⏳ **این پیام {delete_time} ثانیه دیگر محو می‌شود...**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔗 [ربات پشتیبانی](https://t.me/{support_bot_raw})
"""

async def handler(event):
    """هندلر اصلی پیام‌ها"""
    if not event.is_private:
        return
    
    try:
        sender = await event.get_sender()
        user_id = sender.id
        
        # چک لیست سفید
        if user_id in WHITELIST:
            return
        
        # چک بن بودن
        if user_id in banned:
            await event.delete()
            return
        
        # چک ربات پشتیبانی
        if sender.bot:
            if user_id == SUPPORT_BOT_ID:
                return
            if sender.username and SUPPORT_BOT_USERNAME[1:].lower() in sender.username.lower():
                return
        
        # ارسال پیام خوش‌آمدگویی برای اولین پیام
        if user_id not in welcomed and not sender.bot:
            welcomed.add(user_id)
            
            welcome_msg = await event.reply(
                WELCOME_EPIC.format(
                    name=sender.first_name or 'کاربر',
                    user_id=user_id,
                    support_bot=SUPPORT_BOT_USERNAME,
                    support_bot_raw=SUPPORT_BOT_USERNAME[1:],
                    max_viol=MAX_VIOLATIONS,
                    delete_time=WELCOME_DELETE
                ),
                parse_mode='md',
                link_preview=False
            )
            
            await asyncio.sleep(WELCOME_DELETE)
            try:
                await welcome_msg.delete()
            except:
                pass
        
        # حذف پیام کاربر
        await event.delete()
        
        # مدیریت اخطارها برای کاربران عادی
        if not sender.bot:
            violations[user_id] = violations.get(user_id, 0) + 1
            count = violations[user_id]
            remaining = MAX_VIOLATIONS - count
            risk = min(100, int((count / MAX_VIOLATIONS) * 100))
            
            # پیام متناسب با تعداد اخطار
            if count == 1:
                message_advice = "این اولین فرصت شماست!"
            elif count == 2:
                message_advice = "دومین اخطار!"
            elif count == 3:
                message_advice = "اخطار سوم! فقط ۲ فرصت دیگر دارید."
            elif count == 4:
                message_advice = "اخطار چهارم! آخرین فرصت..."
            else:
                message_advice = "اخطار نهایی! این آخرین شانس شماست."
            
            # ارسال پیام هشدار
            warn_msg = await event.reply(
                WARNING_EPIC.format(
                    count=count,
                    max_count=MAX_VIOLATIONS,
                    remaining=remaining,
                    name=sender.first_name or 'کاربر',
                    user_id=user_id,
                    date=datetime.now().strftime('%Y-%m-%d'),
                    support_bot=SUPPORT_BOT_USERNAME,
                    support_bot_raw=SUPPORT_BOT_USERNAME[1:],
                    risk=risk,
                    message=message_advice,
                    delete_time=WARNING_DELETE
                ),
                parse_mode='md',
                link_preview=False
            )
            
            await asyncio.sleep(WARNING_DELETE)
            try:
                await warn_msg.delete()
            except:
                pass
            
            # بن کردن کاربر بعد از ۵ اخطار
            if count >= MAX_VIOLATIONS:
                try:
                    await event.client(BlockRequest(id=user_id))
                    banned.add(user_id)
                    
                    ban_msg = await event.client.send_message(
                        user_id,
                        BAN_EPIC.format(
                            name=sender.first_name or 'کاربر',
                            user_id=user_id,
                            date=datetime.now().strftime('%Y-%m-%d'),
                            max_count=MAX_VIOLATIONS,
                            support_bot=SUPPORT_BOT_USERNAME,
                            support_bot_raw=SUPPORT_BOT_USERNAME[1:],
                            delete_time=BAN_DELETE
                        ),
                        parse_mode='md',
                        link_preview=False
                    )
                    
                    await asyncio.sleep(BAN_DELETE)
                    try:
                        await ban_msg.delete()
                    except:
                        pass
                    
                except:
                    pass
    
    except Exception:
        # خطاها رو نادیده بگیر
        pass

async def main():
    """تابع اصلی با مدیریت درست event loop"""
    print("🚀 ربات در حال راه‌اندازی...")
    
    # استفاده از async with برای مدیریت خودکار client
    async with TelegramClient('pm_blocker_session', API_ID, API_HASH) as client:
        # ثبت هندلر
        client.add_event_handler(handler, events.NewMessage)
        
        # شروع با شماره تلفن
        await client.start(phone=PHONE)
        print("✅ ربات با موفقیت روشن شد! منتظر پیام‌ها...")
        
        # اجرای تا بی‌نهایت
        await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        # asyncio.run خودش event loop رو مدیریت می‌کنه
        asyncio.run(main())
    except KeyboardInterrupt:
        print("👋 ربات خاموش شد")
    except Exception as e:
        print(f"❌ خطا: {e}")
