from .d2api import D2Database

async def setup(bot):
    await bot.add_cog(D2Database(bot))