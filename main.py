

from telethon import TelegramClient, events
from telethon.tl.functions.contacts import BlockRequest
import asyncio
from datetime import datetime
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import time

# ===============  Render ===============
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        # نمایش وضعیت ربات
        status = "✅ فعال" if 'client' in globals() else "🔄 در حال راه‌اندازی"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>ربات تلگرام</title>
            <meta http-equiv="refresh" content="30">
            <style>
                body {{ font-family: Arial, text-align: center; padding: 50px; background: #1a1a1a; color: white; }}
                .status {{ color: #00ff00; font-size: 24px; }}
                .info {{ color: #888; margin-top: 20px; }}
                .stats {{ margin-top: 30px; text-align: left; display: inline-block; background: #333; padding: 20px; border-radius: 10px; }}
            </style>
        </head>
        <body>
            <h1>🤖 ربات مسدودکننده پیام‌های خصوصی</h1>
            <div class="status">{status}</div>
            <div class="info">زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
            <div class="stats">
                <h3>آمار:</h3>
                <p>🚫 کاربران بن شده: {len(banned)}</p>
                <p>⚠️ کاربران دارای اخطار: {len(violations)}</p>
                <p>👋 خوش‌آمدگویی: {len(welcomed)}</p>
                <p>⏰ آخرین فعالیت: {last_activity}</p>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html.encode('utf-8'))
    
    def log_message(self, format, *args):
        pass

def run_health_server():
    """اجرای وب سرور روی پورت ۱۰۰۰۰"""
    port = int(os.environ.get('PORT', 10000))
    try:
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        print(f"🌐 Web server running on port {port}")
        server.serve_forever()
    except Exception as e:
        print(f"❌ Web server error: {e}")

# =============== تابع Keep Alive ===============
def keep_alive():
    """هر ۵ دقیقه به خودش پینگ می‌زنه تا نخوابه"""
    url = f"https://{os.environ.get('RENDER_SERVICE_NAME', 'localhost')}.onrender.com"
    if url == "https://.onrender.com":
        url = "https://user-11.onrender.com"  # آدرس خودت رو بذار
    
    while True:
        try:
            response = requests.get(url, timeout=10)
            print(f"💓 Keep-alive ping sent at {datetime.now().strftime('%H:%M:%S')} - Status: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Keep-alive error: {e}")
        time.sleep(300)  # ۵ دقیقه

# =============== دریافت اطلاعات ===============
API_ID = int(os.environ.get('API_ID', 0))
API_HASH = os.environ.get('API_HASH', '')
PHONE = os.environ.get('PHONE', '')
SUPPORT_BOT_TOKEN = os.environ.get('SUPPORT_BOT_TOKEN', '')
SUPPORT_BOT_USERNAME = os.environ.get('SUPPORT_BOT_USERNAME', '@chatbot11011_bot')
WHITELIST_IDS = os.environ.get('WHITELIST_IDS', '')

# =============== پردازش لیست سفید ===============
SUPPORT_BOT_ID = int(SUPPORT_BOT_TOKEN.split(':')[0]) if ':' in SUPPORT_BOT_TOKEN else 0

# لیست سفید اصلی + آیدی جدید 1718269955
WHITELIST = [777000, SUPPORT_BOT_ID, 1718269955]

if WHITELIST_IDS:
    for wid in WHITELIST_IDS.split(','):
        try:
            WHITELIST.append(int(wid.strip()))
        except:
            pass

# حذف مقادیر تکراری
WHITELIST = list(set(WHITELIST))

print(f"🟢 لیست سفید: {WHITELIST}")

# =============== تنظیمات ===============
MAX_VIOLATIONS = 15
WELCOME_DELETE = 35
WARNING_DELETE = 25
BAN_DELETE = 20

# =============== دیتابیس ===============
violations = {}
banned = set()
welcomed = set()
last_activity = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# =============== پیام‌ها ===============
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
🌟 **ربات پشتیبانی:** {support_bot}
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
👉 **{support_bot}** 👈

📊 **تخلفات شما:**

🔸 تعداد اخطار: **{count} از {max_count}**
🔸 اخطار باقی‌مانده: **{remaining}**
🔸 ریسک مسدودیت: **{risk}%**

{message}

⏳ **این هشدار {delete_time} ثانیه دیگر محو می‌شود...**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔗 [ربات پشتیبانی](https://t.me/{support_bot_raw})
"""

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

async def main():
    """تابع اصلی - همه چی داخل async"""
    global last_activity
    
    print("🚀 ربات در حال راه‌اندازی...")
    
    # ساخت کلاینت داخل تابع async
    client = TelegramClient('pm_blocker_session', API_ID, API_HASH)
    
    @client.on(events.NewMessage)
    async def handler(event):
        """هندلر اصلی پیام‌ها"""
        global last_activity
        last_activity = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if not event.is_private:
            return
        
        try:
            sender = await event.get_sender()
            user_id = sender.id
            
            # چک کردن لیست سفید
            if user_id in WHITELIST:
                print(f"🟢 کاربر لیست سفید: {user_id}")
                return
            
            if user_id in banned:
                await event.delete()
                return
            
            if sender.bot:
                if user_id == SUPPORT_BOT_ID:
                    return
                if sender.username and SUPPORT_BOT_USERNAME[1:].lower() in sender.username.lower():
                    return
            
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
            
            await event.delete()
            
            if not sender.bot:
                violations[user_id] = violations.get(user_id, 0) + 1
                count = violations[user_id]
                remaining = MAX_VIOLATIONS - count
                risk = min(100, int((count / MAX_VIOLATIONS) * 100))
                
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
                
                if count >= MAX_VIOLATIONS:
                    try:
                        await client(BlockRequest(id=user_id))
                        banned.add(user_id)
                        
                        ban_msg = await client.send_message(
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
            pass
    
    # شروع کلاینت
    await client.start(phone=PHONE)
    print("✅ ربات با موفقیت روشن شد! منتظر پیام‌ها...")
    print(f"🟢 لیست سفید نهایی: {WHITELIST}")
    
    # اجرای تا بی‌نهایت
    await client.run_until_disconnected()

if __name__ == "__main__":
    # اجرای وب سرور در یک نخ جداگانه
    web_thread = threading.Thread(target=run_health_server, daemon=True)
    web_thread.start()
    
    # اجرای Keep Alive در یک نخ جداگانه
    keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
    keep_alive_thread.start()
    
    try:
        # اجرای تابع اصلی با asyncio.run
        asyncio.run(main())
    except KeyboardInterrupt:
        print("👋 ربات خاموش شد")
    except Exception as e:
        print(f"❌ خطا: {e}")
