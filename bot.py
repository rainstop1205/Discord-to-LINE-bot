import os
import discord
from discord import app_commands
import requests
from discord.ext import commands

# 環境變數
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_TARGET_GROUP_ID = os.environ.get("LINE_TARGET_GROUP_ID")  # LINE 群組 ID

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

@tree.command(name="send-to-line", description="傳送訊息到 LINE 群組")
@app_commands.describe(message="你要傳送的訊息")
async def send_to_line(interaction: discord.Interaction, message: str):
    await interaction.response.defer(thinking=False)
    
    sender = interaction.user.display_name
    text = f"💬 {sender}：{message}"
    success = push_to_line_group(text)
    
    if success:
        await interaction.followup.send("✅ 已成功發送訊息到 LINE 群組！")
    else:
        await interaction.followup.send("⚠️ 發送失敗，請稍後再試～")

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
    bot.run(DISCORD_BOT_TOKEN)