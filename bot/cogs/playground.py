import json
import logging

import aiohttp
import discord
from discord.ext import commands

log = logging.getLogger(__name__)


class CodeBlock:
    missing_error = "Missing code block. Please use the following markdown\n\\`\\`\\`rust\ncode here\n\\`\\`\\`"

    def __init__(self, argument):
        try:
            block, code = argument.split("\n", 1)
        except ValueError:
            raise commands.BadArgument(self.missing_error)

        if not block.startswith("```") and not code.endswith("```"):
            raise commands.BadArgument(self.missing_error)

        self.source = code.rstrip("`")


class CodeSection:
    missing_error = "Missing code section. Please use the following markdown\n\\`code here\\`\nor\n\\`\\`\\`rust\ncode here\n\\`\\`\\`"

    def __init__(self, code):
        codeblock = code.startswith("```") and code.endswith("```")
        codesection = code.startswith("`") and code.endswith("`")
        if not codesection and not codeblock:
            raise commands.BadArgument(self.missing_error)

        if codeblock:
            self.source = "\n".join(code.split("\n")[1:]).rstrip("`")
        else:
            self.source = code.strip("`")


class Playground:
    """Evaluates Rust code.

    Usage:

    ?play ```rs
    <your Rust code here>
    ```

    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = aiohttp.ClientSession(loop=self.bot.loop)

    def __unload(self):
        self.session.close()

    @commands.command()
    async def play(self, ctx: commands.Context, *, code: CodeBlock):
        """Evaluates Rust code. Exactly equal to https://play.integer32.com/"""

        await self.query_playground(ctx, code.source)

    @commands.command()
    async def eval(self, ctx: commands.Context, *, code: CodeSection):
        """Evaluates Rust code and debug prints the results. Exactly equal to https://play.integer32.com/"""

        await self.query_playground(
            ctx, 'fn main(){println!("{:?}",{' + code.source + "});}"
        )

    async def query_playground(self, ctx: commands.Context, source):
        async with ctx.typing():
            payload = json.dumps(
                {
                    "channel": "nightly",
                    "code": source,
                    "crateType": "bin",
                    "mode": "debug",
                    "tests": False,
                }
            )

            async with self.session.post(
                "https://play.integer32.com/execute", data=payload
            ) as r:
                if r.status != 200:
                    raise commands.CommandError(
                        "Rust i32 Playground didn't respond in time."
                    )

                response = await r.json()
                if "error" in response:
                    raise commands.CommandError(response["error"])

                stderr = response["stderr"]
                stdout = response["stdout"]

                full_response = (
                    stdout
                    if len(stderr.split("\n")) <= 4
                    else "\n".join(stderr.split("\n")[1:-7])
                )
                len_response = len(full_response)
                if len_response < 1990:
                    msg = f"```rs\n{full_response}```"
                elif 1990 <= len_response <= 5000:
                    msg = await self.get_gist(full_response)
                else:
                    raise commands.CommandError("Output too big!")

                await ctx.send(msg)

    async def get_gist(self, msg):
        data = json.dumps({"public": True, "files": {"main.rs": {"content": msg}}})

        headers = {"Accept": "application/vnd.github.v3+json"}

        async with self.session.post(
            "https://api.github.com/gists", data=data, headers=headers
        ) as r:
            response = await r.json()

        return "https://gist.github.com/anonymous/" + response["id"]

    async def __error(self, ctx: commands.Context, error):
        log.error("Playground error: %s", error)
        if isinstance(error, (discord.HTTPException, discord.Forbidden)):
            await ctx.send("Error while sending the output.")
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(CodeBlock.missing_error)
        if isinstance(error, commands.CommandError):
            await ctx.send(str(error))


def setup(bot):
    bot.add_cog(Playground(bot))
