from .ffxiv import FFXIVLodestone

async def setup(bot):
    await bot.add_cog(FFXIVLodestone(bot))