import os
import threading
import asyncio
from flask import Flask
import discord
from discord import app_commands
import requests
from discord.ext import commands

DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_TARGET_GROUP_ID = os.environ.get("LINE_TARGET_GROUP_ID")

# Flask App，回應 Cloud Run 的 HealthCheck
app = Flask(__name__)

@app.route("/")
def index():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# Discord Bot 設定
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print(f"🤖 Bot 上線：{bot.user}", flush=True)
    try:
        synced = await bot.tree.sync()
        print(f"✅ Slash commands 已同步：{[cmd.name for cmd in synced]}", flush=True)
    except Exception as e:
        print(f"⚠️ 指令同步失敗：{e}", flush=True)

@bot.tree.command(name="stl", description="傳送訊息到 LINE 群組") #stl = send to line
@app_commands.describe(message="你要傳送的訊息")
async def send_to_line(interaction: discord.Interaction, message: str):
    await interaction.response.defer(thinking=False)
    
    sender = interaction.user.display_name
    text = f"{sender}：{message}"
    
    try:
        success = await async_push_to_line_group(text)
        
        if success:
            await interaction.followup.send("✅ 已成功發送訊息到 LINE 群組！")
        else:
            await interaction.followup.send("⚠️ 發送失敗，請稍後再試～")
    except Exception as e:
        print(f"❌ 發送過程出錯：{e}", flush=True)
        await interaction.followup.send("🚨 發送過程中發生錯誤，請稍後再試！")

async def async_push_to_line_group(text):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, push_to_line_group, text)

def push_to_line_group(text):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": LINE_TARGET_GROUP_ID,
        "messages": [{"type": "text", "text": text}]
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print(f"✅ 已發送到 LINE 群組：{text}", flush=True)
        return True
    else:
        print(f"⚠️ LINE 發送失敗：{response.status_code} - {response.text}", flush=True)
        return False

if __name__ == "__main__":
    # 啟動 Flask HTTP Server (獨立 Thread)
    threading.Thread(target=run_flask).start()
    # 啟動 Discord Bot 主程式
    bot.run(DISCORD_BOT_TOKEN)