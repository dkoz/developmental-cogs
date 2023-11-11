from .battlemetrics import BattleMetricsAPI

async def setup(bot):
    await bot.add_cog(BattleMetricsAPI(bot))