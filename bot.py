import os
import asyncio
import aiohttp
from quart import Quart
import discord
from discord import app_commands
from discord.ext import commands

DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_TARGET_GROUP_ID = os.environ.get("LINE_TARGET_GROUP_ID")

# 回應 Cloud Run 的 HealthCheck
app = Quart(__name__)

@app.route("/")
async def index():
    return "OK", 200

async def run_quart():
    port = int(os.environ.get("PORT", 8080))
    await app.run_task(host="0.0.0.0", port=port)

# Discord Bot 設定
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print(f"🤖 Bot 上線：{bot.user}", flush=True)
    try:
        # 清除舊的全域指令
        await bot.tree.sync()
        print(f"✅ Slash commands 已同步：{[cmd.name for cmd in await bot.tree.fetch_commands()]}", flush=True)

        # 可列出目前註冊的所有指令 (debug)
        for cmd in await bot.tree.fetch_commands():
            print(f"📎 已註冊指令：/{cmd.name} - {cmd.description}", flush=True)

    except Exception as e:
        print(f"⚠️ 指令同步失敗：{e}", flush=True)

@bot.tree.command(name="stl", description="傳送訊息到 LINE 群組") #stl = send to line
@app_commands.describe(message="你要傳送的訊息")
async def send_to_line(interaction: discord.Interaction, message: str):
    await interaction.response.defer(thinking=True)
    
    sender = interaction.user.display_name
    text = f"{sender}：{message}"
    
    try:
        success = await asyncio.wait_for(async_push_to_line_group(text), timeout=10)
        
        if success:
            await interaction.followup.send("✅ 已成功發送訊息到 LINE 群組！")
        else:
            await interaction.followup.send("⚠️ 發送失敗，請稍後再試～")
    except asyncio.TimeoutError:
        await interaction.followup.send("🚨 發送超時，請稍後再試！")
    except Exception as e:
        print(f"❌ 發送過程出錯：{e}", flush=True)
        await interaction.followup.send("🚨 發送過程中發生錯誤，請稍後再試！")

async def async_push_to_line_group(text):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": LINE_TARGET_GROUP_ID,
        "messages": [{"type": "text", "text": text}]
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status == 200:
                print(f"✅ 已發送到 LINE 群組：{text}", flush=True)
                return True
            else:
                text_resp = await resp.text()
                print(f"⚠️ LINE 發送失敗：{resp.status} - {text_resp}", flush=True)
                return False

async def main():
    # 啟動 Quart 伺服器（在背景 task）
    quart_task = asyncio.create_task(run_quart())
    # 啟動 Discord bot（await bot.start()）
    discord_task = asyncio.create_task(bot.start(DISCORD_BOT_TOKEN))

    # 等待任一任務結束（通常是 discord_task）
    done, pending = await asyncio.wait(
        [quart_task, discord_task],
        return_when=asyncio.FIRST_COMPLETED
    )

    # 如果有任務先結束，取消另一個
    for task in pending:
        task.cancel()

if __name__ == "__main__":
    asyncio.run(main())