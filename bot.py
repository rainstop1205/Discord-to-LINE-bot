import os
import asyncio
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from logger import logger

# 載入 .env 檔案
load_dotenv()

DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
ALLOWED_PARENT_CHANNEL_ID = int(os.environ.get("DISCORD_ALLOWED_PARENT_CHANNEL_ID"))
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_TARGET_GROUP_ID = os.environ.get("LINE_TARGET_GROUP_ID")

# Discord Bot 設定
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    logger.info(f"🤖 Bot 上線：{bot.user}")
    try:
        await bot.tree.sync()
        logger.info(f"✅ Slash commands 已同步：{[cmd.name for cmd in await bot.tree.fetch_commands()]}")

        for cmd in await bot.tree.fetch_commands():
            logger.info(f"📎 已註冊指令：/{cmd.name} - {cmd.description}")

    except Exception as e:
        logger.exception(f"⚠️ 指令同步失敗：{e}")

@bot.tree.command(name="stl", description="傳送訊息到 LINE 群組") #send_to_line
@app_commands.describe(message="你要傳送的訊息")
async def send_to_line(interaction: discord.Interaction, message: str):
    # getattr(obj, "attr", default)：如果 obj 有 attr 屬性就回傳它，沒有的話回傳 default
    parent_id = getattr(interaction.channel, "parent_id", interaction.channel.id)

    if parent_id != ALLOWED_PARENT_CHANNEL_ID:
        await interaction.response.send_message(
            "🚫 嘿嘿～別亂丟訊息到其他專案的 LINE 群組啦 📵", ephemeral=True)
        return
    
    await interaction.response.defer(thinking=True)
    
    sender = interaction.user.display_name
    text = f"{sender}：{message}"
    
    try:
        success = await asyncio.wait_for(async_push_to_line_group(text), timeout=10)
        
        if success:
            await interaction.followup.send(f"👤 {text}")
        else:
            await interaction.followup.send("⚠️ 發送失敗，請稍後再試～")
    except asyncio.TimeoutError:
        await interaction.followup.send("🚨 發送超時，請稍後再試！")
    except Exception as e:
        logger.exception(f"❌ 發送過程出錯：{e}")
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

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                text_resp = await resp.text()
                if 200 <= resp.status < 300:
                    logger.info("✅ 成功發送訊息至 LINE 群組。")
                    return True
                else:
                    logger.error(f"⚠️ LINE 發送失敗：{resp.status} - {text_resp}")
                    return False
    except Exception as e:
        logger.exception(f"💥 發送 LINE 訊息時發生例外：{e}")
        return False
    
if __name__ == "__main__":
    asyncio.run(bot.start(DISCORD_BOT_TOKEN))