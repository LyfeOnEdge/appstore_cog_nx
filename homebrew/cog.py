import json
import discord
from discord.ext import commands
from discord.ext.commands import Cog
from .appstore_parser import parser as Parser
import config
from helpers.checks import check_if_bot_manager, check_if_staff

# # Add this to config.py
# # Homebrew Bot Config
# max_message_length = 2000
# fields_to_search = [
#     "name",
#     "title",
#     "category",
#     "author",
#     "description"
# ]
# embed_color = 0x800080
# repo_url = "https://www.switchbru.com/appstore/repo.json" 

def getPageURL(package):
    return "https://apps.fortheusers.org/switch/{}".format(package)

def getPackageIconURL(package):
    return "https://www.switchbru.com/appstore/packages/{}/icon.png".format(package)

class Homebrew(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Parser()

    @commands.guild_only()
    @commands.command(name="homebrew_list_games", aliases=["hb_list_games", "hblistgames", "hbgames"])
    async def list_games(self, ctx):
        """List available homebrew games"""
        embed = await self.embed_list(ctx, [hb["name"] for hb in self.db.games], "Switch Games:")
        await ctx.send(embed = embed)

    @commands.guild_only()
    @commands.command(name="homebrew_list_advanced", aliases=["hb_list_advanced", "hbadvanced"])
    async def list_advanced(self, ctx):
        """List advanced homebrew software"""
        embed = await self.embed_list(ctx, [hb["name"] for hb in self.db.advanced], "Advanced Switch Homebrew:")
        await ctx.send(embed = embed)

    @commands.guild_only()
    @commands.command(name="homebrew_list_tools", aliases=["hb_list_tools", "hblisttools", "hbtools"])
    async def list_tools(self, ctx):
        """List available homebrew tools"""
        embed = await self.embed_list(ctx, [hb["name"] for hb in self.db.tools], "Switch Tools:")
        await ctx.send(embed = embed)

    @commands.guild_only()
    @commands.command(name="homebrew_list_themes", aliases=["hb_list_themes", "hblistthemes", "hbthemes"])
    async def list_themes(self, ctx):
        """List available homebrew themes"""
        embed = await self.embed_list(ctx, [hb["name"] for hb in self.db.themes], "Switch Themes:")
        await ctx.send(embed = embed)

    @commands.guild_only()
    @commands.command(name="homebrew_list_emulators", aliases=["hb_list_emulators", "hblistemulators", "hbemulators", "hblistemus", "hbemus"])
    async def list_emus(self, ctx):
        """List available homebrew emulators"""
        embed = await self.embed_list(ctx, [hb["name"] for hb in self.db.emus], "Switch Emulators:")
        await ctx.send(embed = embed)

    @commands.guild_only()
    @commands.command(name="homebrew_search", aliases=["hb_search", "hbsearch", "search"])
    async def search_homebrew(self, ctx, search: str = ""):
        """Search package name/title/category/description"""
        packages = []
        if search:
            for package in self.db.all:
                try:
                    for field in config.fields_to_search:
                        if search.lower() in package[field].lower():
                            packages.append(package["name"])
                            break
                except:
                    pass
            resp = packages
        else:
            resp = "Invalid search term"
            await ctx.send(resp)
            return

        title = "Homebrew search results for '*{}*':".format(search, )
        if not len(resp):
            embed = await self.embed_list(ctx, ["No results"], title)
        elif len(resp) > 6:
            embed = await self.embed_list(ctx, packages, title + " ({} results)".format(len(resp)))
        else:
            embed = discord.Embed(title=title, description='Showing {} results.'.format(len(resp)), color=config.embed_color)
            for package in resp:
                pkg = await self.get_package(package)
                details = pkg["details"].replace("\\n\\n\\n", "\n").replace("\\n\\n", "\n").replace("\\n", """
    """).strip()
                body = "**Package:** {}\n**Author:** {}\n**About:** {}".format(package, pkg["author"], details)
                if len(body) > 200:
                    body = body[:200].strip() + "..."

                embed.add_field(name="**{}**".format(pkg["title"]), value=body)
        await ctx.send(embed = embed)

    @commands.guild_only()
    @commands.command(name="homebrew_info", aliases=["hb_info", "hbinfo"])
    async def get_homebrew_info(self, ctx, package: str = ""):
        """Get info and download link for given homebrew"""
        pkg = await self.get_package(package)

        if not pkg:
            resp = "Package not found"
            return await ctx.send(resp)

        details = pkg["details"].replace("\\n", """
""").strip()

        resp = ""
        resp += "**Author:** {}\n".format(pkg["author"])
        resp += "**Package name:** {}\n".format(pkg["name"])
        resp += "**Version:** {}\n".format(pkg["version"])
        resp += "**License:** {}\n".format(pkg["license"])
        resp += "**Website:** {}\n".format(getPageURL(pkg["name"]))
        resp += "\n{}".format(details)
        if len(resp) > config.max_message_length:
            resp = resp[:config.max_message_length]
            resp += "..."
        embed = discord.Embed(title=pkg["title"],
                              url=getPageURL(pkg["name"]),
                              description=resp)

        iconURL = getPackageIconURL(pkg["name"])
        embed.set_thumbnail(url=iconURL)

        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(name="homebrew_get_count", aliases=["hb_count", "hbcount"])
    async def get_homebrew_count(self, ctx, package: str = ""):
        """Get number of packages in appstore repo"""
        await ctx.send("There are {} packages in repo: {}".format(self.get_repo_size(), config.repo_url))

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.check(check_if_bot_manager)
    @commands.command(name="homebrew_reload_repo", aliases=["hb_reload", "hbreload"])
    async def reload_homebrew_repo(self, ctx):
        """Check repo etag, download if fresh, reload homebrew bot. Staff only."""
        result = await self.update_repo()
        if result: #Result on error
            return await ctx.send("Error reloading repo ~ {}".format(result))
        await ctx.send("Repo reloaded sucessfully!\nThere are {} packages in repo: {}".format(self.get_repo_size(), config.repo_url))

    async def embed_list(self, ctx, lis, title):
        resp = (''.join(s + ", " for s in sorted(lis))).strip(", ")

        if len(resp) > config.max_message_length:
            resp = resp[:config.max_message_length-3]+"..."

        embed = discord.Embed(title=title, description=resp, color=config.embed_color)
        return embed

    #Pass either a package name or title, must be an exact match
    async def get_package(self, package_name):
        for package in self.db.all:
            if package["name"] == package_name or package["title"] == package_name:
                return package

    #Reloads repo
    async def update_repo(self):
        log_channel = self.bot.get_channel(config.botlog_channel)
        await log_channel.send("Reloading homebrew database...")
        db_json = await self.get_json(config.repo_url)
        self.db.load_json(data)
        await log_channel.send("Found {} packages in repo: {}".format(self.get_repo_size(), config.repo_url))

    def get_repo_size(self):
        if self.db:
            return len(self.db.all)

    async def get_json(self, url):
        try:
            data = await self.bot.aiosession.get(url)
            if data.status == 200:
                text_data = await data.text()
                content_type = data.headers['Content-Type']
                return await data.json(content_type=content_type)
            else:
                self.bot.log.error(f"HTTP Error {data.status} "
                                   "while getting {url}")
        except:
            self.bot.log.error(f"Error while getting {url} "
                               f"on aiogetbytes: {traceback.format_exc()}")