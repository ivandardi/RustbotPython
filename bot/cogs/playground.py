import json
import logging
import re

import aiohttp
import discord
from discord.ext import commands

log = logging.getLogger(__name__)
err_regex = re.compile(r"^error(\[.*\])*:", re.MULTILINE)


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
    """Evaluates Rust code with an optional compilation mode.
    Defaults to debug.

    Usage:

    ?play (--release|--debug) ```rs
    <your Rust code here>
    ```

    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = aiohttp.ClientSession(loop=self.bot.loop)

    def __unload(self):
        self.session.close()

    @commands.command()
    async def play(self, ctx: commands.Context, *, arg):
        """Evaluates Rust code. Exactly equal to https://play.integer32.com/"""
        (mode, code) = self.parse_args(arg)
        await self.query_playground(ctx, mode, code.source)

    @commands.command()
    async def playwarn(self, ctx: commands.Context, *, arg):
        """Evaluates Rust code and outputs generated warnings. Exactly equal to https://play.integer32.com/"""
        (mode, code) = self.parse_args(arg)
        await self.query_playground(ctx, mode, code.source, warnings=True)

    @commands.command()
    async def eval(self, ctx: commands.Context, *, arg):
        """Evaluates Rust code and debug prints the results. Exactly equal to https://play.integer32.com/"""
        (mode, code) = self.parse_args(arg)
        comment_index = code.source.find("//")
        end_idx = comment_index if comment_index != -1 else len(code.source)
        await self.query_playground(
            ctx, mode, 'fn main(){println!("{:?}",{' + code.source[:end_idx] + "});}"
        )

    def parse_args(self, args):
        args = args.replace("\n`", " `").split(" ")
        if args[0].startswith("--"):
            mode = args[0][2:]
            mode.strip()
            print("aaaaaa", mode)
            code = " ".join(args[1:])
            if mode != "release" and mode != "debug":
                raise commands.BadArgument(
                    "Bad compile mode. Valid options are `--release` and `--debug`"
                )

            return (mode, CodeSection(code))
        else:
            code = " ".join(args[0:])
            return (None, CodeSection(code))

    async def query_playground(
        self, ctx: commands.Context, mode, source, warnings=None
    ):
        async with ctx.typing():
            payload = json.dumps(
                {
                    "channel": "nightly",
                    "code": source,
                    "crateType": "bin",
                    "mode": mode if mode is not None else "debug",
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
                    if err_regex.search(stderr) is None
                    and not (warnings is not None and len(stderr) >= 4)
                    and not "panicked" in stderr
                    else "\n".join(stderr.split("\n")[1:]) + "\n\n" + stdout
                )
                len_response = len(full_response)
                if len_response == 0:
                    msg = "``` ```"
                elif len_response < 1990:
                    full_response = full_response.replace("```", "  ̀  ̀  ̀")
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
