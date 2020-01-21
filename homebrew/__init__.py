import asyncio
from .cog import Homebrew

async def background_task(bot, cog):
	await bot.wait_until_ready()
	while (bot.is_ready()):
		await cog.update_repo()
		await asyncio.sleep(1200)

def setup(bot):
	cog = Homebrew(bot)
	bot.loop.create_task(background_task(bot, cog))
	bot.add_cog(cog)