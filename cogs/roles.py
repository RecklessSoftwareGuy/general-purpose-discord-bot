import discord
from discord.ext import commands
from views import embeds


class roleCommands(commands.Cog):
    """🏷️ Role management commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # guild_id -> list of self-assignable role IDs
        self._self_roles: dict[int, list[int]] = {}
        print(f"Initialized: {self.__cog_name__}")
        super().__init__()

    # ── Helpers ────────────────────────────────────────────────────────────

    def _self_role_list(self, guild_id: int) -> list[int]:
        return self._self_roles.setdefault(guild_id, [])

    # ── Give / Take Role ──────────────────────────────────────────────────

    @commands.command(name="giverole", aliases=["addrole", "ar"])
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def giverole(self, ctx: commands.Context, member: discord.Member, *, role: discord.Role):
        """Give a role to a member. Usage: giverole <@member> <role>"""
        if role >= ctx.guild.me.top_role:  # type: ignore
            await ctx.send(embed=embeds.error_x0("I cannot assign a role that is higher than or equal to my highest role."))
            return
        if role in member.roles:
            await ctx.send(embed=embeds.error_x0(f"{member.mention} already has {role.mention}."))
            return
        await member.add_roles(role, reason=f"Role assigned by {ctx.author}")
        await ctx.send(embed=embeds.role_added_x0(member, role))

    @commands.command(name="takerole", aliases=["removerole", "rr"])
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def takerole(self, ctx: commands.Context, member: discord.Member, *, role: discord.Role):
        """Remove a role from a member. Usage: takerole <@member> <role>"""
        if role >= ctx.guild.me.top_role:  # type: ignore
            await ctx.send(embed=embeds.error_x0("I cannot remove a role that is higher than or equal to my highest role."))
            return
        if role not in member.roles:
            await ctx.send(embed=embeds.error_x0(f"{member.mention} doesn't have {role.mention}."))
            return
        await member.remove_roles(role, reason=f"Role removed by {ctx.author}")
        await ctx.send(embed=embeds.role_removed_x0(member, role))

    @commands.command(name="togglerole", aliases=["trole"])
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def togglerole(self, ctx: commands.Context, member: discord.Member, *, role: discord.Role):
        """Toggle a role on a member (adds if missing, removes if present)."""
        if role >= ctx.guild.me.top_role:  # type: ignore
            await ctx.send(embed=embeds.error_x0("I cannot manage a role that is higher than or equal to my highest role."))
            return
        if role in member.roles:
            await member.remove_roles(role, reason=f"Role toggled by {ctx.author}")
            await ctx.send(embed=embeds.role_removed_x0(member, role))
        else:
            await member.add_roles(role, reason=f"Role toggled by {ctx.author}")
            await ctx.send(embed=embeds.role_added_x0(member, role))

    # ── Create / Delete / Edit Roles ──────────────────────────────────────

    @commands.command(name="createrole", aliases=["newrole"])
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def createrole(
        self,
        ctx: commands.Context,
        color: str = "#000000",
        hoist: bool = False,
        mentionable: bool = False,
        *,
        name: str,
    ):
        """Create a new role. Usage: createrole [#hex color] [hoist true/false] [mentionable true/false] <name>
        Example: createrole #ff5733 True False Moderator"""
        if not ctx.guild:
            return
        try:
            colour = discord.Colour(int(color.lstrip("#"), 16))
        except ValueError:
            colour = discord.Colour.default()

        role = await ctx.guild.create_role(
            name=name,
            colour=colour,
            hoist=hoist,
            mentionable=mentionable,
            reason=f"Created by {ctx.author}",
        )
        await ctx.send(embed=embeds.role_created_x0(role))

    @commands.command(name="delrole", aliases=["deleterole"])
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def delrole(self, ctx: commands.Context, *, role: discord.Role):
        """Delete a role. Usage: delrole <role>"""
        if not ctx.guild:
            return
        if role >= ctx.guild.me.top_role:
            await ctx.send(embed=embeds.error_x0("I cannot delete a role that is higher than or equal to my highest role."))
            return
        name, role_id = role.name, role.id
        await role.delete(reason=f"Deleted by {ctx.author}")
        await ctx.send(embed=embeds.role_deleted_x0(name, role_id))

    @commands.command(name="editrole")
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def editrole(self, ctx: commands.Context, role: discord.Role, option: str, *, value: str):
        """Edit a role property. Usage: editrole <role> <name|color|hoist|mentionable> <value>
        Examples:
          editrole Mod name Moderator
          editrole Mod color #ff0000
          editrole Mod hoist true"""
        if not ctx.guild:
            return
        if role >= ctx.guild.me.top_role:
            await ctx.send(embed=embeds.error_x0("I cannot edit a role that is higher than or equal to my highest role."))
            return

        option = option.lower()
        try:
            if option == "name":
                await role.edit(name=value, reason=f"Edited by {ctx.author}")
                await ctx.send(embed=embeds.success_x0(f"Renamed role to **{value}**."))
            elif option in ("color", "colour"):
                colour = discord.Colour(int(value.lstrip("#"), 16))
                await role.edit(colour=colour, reason=f"Edited by {ctx.author}")
                await ctx.send(embed=embeds.success_x0(f"Set {role.mention} color to **{value}**."))
            elif option == "hoist":
                hoist = value.lower() in ("true", "yes", "1", "on")
                await role.edit(hoist=hoist, reason=f"Edited by {ctx.author}")
                state = "hoisted" if hoist else "not hoisted"
                await ctx.send(embed=embeds.success_x0(f"{role.mention} is now **{state}**."))
            elif option == "mentionable":
                mentionable = value.lower() in ("true", "yes", "1", "on")
                await role.edit(mentionable=mentionable, reason=f"Edited by {ctx.author}")
                state = "mentionable" if mentionable else "not mentionable"
                await ctx.send(embed=embeds.success_x0(f"{role.mention} is now **{state}**."))
            else:
                await ctx.send(embed=embeds.error_x0("Unknown option. Choose from: `name`, `color`, `hoist`, `mentionable`."))
        except ValueError:
            await ctx.send(embed=embeds.error_x0("Invalid color hex. Example: `#ff5733`."))

    # ── Role Information ──────────────────────────────────────────────────

    @commands.command(name="roleinfo", aliases=["ri"])
    async def roleinfo(self, ctx: commands.Context, *, role: discord.Role):
        """Display detailed info about a role. Usage: roleinfo <role>"""
        await ctx.send(embed=embeds.role_info_x0(role))

    @commands.command(name="rolemembers", aliases=["whohas", "inrole"])
    async def rolemembers(self, ctx: commands.Context, *, role: discord.Role):
        """List all members who have a specific role. Usage: rolemembers <role>"""
        await ctx.send(embed=embeds.role_members_x0(role))

    @commands.command(name="roles", aliases=["listroles", "allroles"])
    async def listroles(self, ctx: commands.Context):
        """List all roles in the server with member counts."""
        if not ctx.guild:
            return
        guild_roles = sorted(
            [r for r in ctx.guild.roles if r != ctx.guild.default_role],
            key=lambda r: r.position,
            reverse=True,
        )
        lines = [
            f"{r.mention} — **{len(r.members)}** member(s)"
            for r in guild_roles[:25]
        ]
        em = discord.Embed(
            title=f"🏷️ {ctx.guild.name} — Roles ({len(guild_roles)} total)",
            description="\n".join(lines) if lines else "No roles found.",
            colour=discord.Colour.blurple(),
        )
        if len(guild_roles) > 25:
            em.set_footer(text=f"Showing top 25 of {len(guild_roles)} roles.")
        await ctx.send(embed=em)

    # ── Mass Role Actions ─────────────────────────────────────────────────

    @commands.command(name="massrole")
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def massrole(self, ctx: commands.Context, action: str, *, role: discord.Role):
        """Add or remove a role for all members. Usage: massrole add/remove <role>
        ⚠️ This may take time for large servers."""
        if not ctx.guild:
            return
        if role >= ctx.guild.me.top_role:
            await ctx.send(embed=embeds.error_x0("I cannot manage a role that is higher than or equal to my highest role."))
            return

        action = action.lower()
        if action not in ("add", "remove"):
            await ctx.send(embed=embeds.error_x0("Action must be `add` or `remove`."))
            return

        msg = await ctx.send(embed=embeds.info_x0(f"Processing mass role **{action}** for {role.mention}… This may take a moment."))
        count = 0
        for member in ctx.guild.members:
            try:
                if action == "add" and role not in member.roles:
                    await member.add_roles(role, reason=f"Mass role by {ctx.author}")
                    count += 1
                elif action == "remove" and role in member.roles:
                    await member.remove_roles(role, reason=f"Mass role by {ctx.author}")
                    count += 1
            except discord.Forbidden:
                continue

        past = "added to" if action == "add" else "removed from"
        await msg.edit(embed=embeds.success_x0(f"{role.mention} {past} **{count}** member(s)."))

    @commands.command(name="masshumansrole", aliases=["humanrole"])
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def masshumansrole(self, ctx: commands.Context, action: str, *, role: discord.Role):
        """Add or remove a role from all human (non-bot) members. Usage: masshumansrole add/remove <role>"""
        if not ctx.guild:
            return
        if role >= ctx.guild.me.top_role:
            await ctx.send(embed=embeds.error_x0("I cannot manage a role that is higher than or equal to my highest role."))
            return

        action = action.lower()
        if action not in ("add", "remove"):
            await ctx.send(embed=embeds.error_x0("Action must be `add` or `remove`."))
            return

        msg = await ctx.send(embed=embeds.info_x0(f"Processing mass role **{action}** for humans with {role.mention}…"))
        count = 0
        for member in ctx.guild.members:
            if member.bot:
                continue
            try:
                if action == "add" and role not in member.roles:
                    await member.add_roles(role, reason=f"Mass humans role by {ctx.author}")
                    count += 1
                elif action == "remove" and role in member.roles:
                    await member.remove_roles(role, reason=f"Mass humans role by {ctx.author}")
                    count += 1
            except discord.Forbidden:
                continue

        past = "added to" if action == "add" else "removed from"
        await msg.edit(embed=embeds.success_x0(f"{role.mention} {past} **{count}** human member(s)."))

    @commands.command(name="massbotsrole", aliases=["botsrole"])
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def massbotsrole(self, ctx: commands.Context, action: str, *, role: discord.Role):
        """Add or remove a role from all bot accounts. Usage: massbotsrole add/remove <role>"""
        if not ctx.guild:
            return
        if role >= ctx.guild.me.top_role:
            await ctx.send(embed=embeds.error_x0("I cannot manage a role that is higher than or equal to my highest role."))
            return

        action = action.lower()
        if action not in ("add", "remove"):
            await ctx.send(embed=embeds.error_x0("Action must be `add` or `remove`."))
            return

        msg = await ctx.send(embed=embeds.info_x0(f"Processing mass role **{action}** for bots with {role.mention}…"))
        count = 0
        for member in ctx.guild.members:
            if not member.bot:
                continue
            try:
                if action == "add" and role not in member.roles:
                    await member.add_roles(role, reason=f"Mass bots role by {ctx.author}")
                    count += 1
                elif action == "remove" and role in member.roles:
                    await member.remove_roles(role, reason=f"Mass bots role by {ctx.author}")
                    count += 1
            except discord.Forbidden:
                continue

        past = "added to" if action == "add" else "removed from"
        await msg.edit(embed=embeds.success_x0(f"{role.mention} {past} **{count}** bot(s)."))

    # ── Self-Assignable Roles (SAR) ───────────────────────────────────────

    @commands.group(name="sar", invoke_without_command=True)
    async def sar(self, ctx: commands.Context):
        """Self-assignable roles menu. Subcommands: list, add (admin), remove (admin), get, drop"""
        if not ctx.guild:
            return
        role_ids = self._self_role_list(ctx.guild.id)
        roles = [ctx.guild.get_role(rid) for rid in role_ids]
        roles = [r for r in roles if r is not None]
        em = discord.Embed(
            title="🎭 Self-Assignable Roles",
            colour=discord.Colour.blurple(),
        )
        if roles:
            em.description = "\n".join(f"• {r.mention}" for r in roles)
            em.set_footer(text="Use -sar get <role> to assign a role to yourself.")
        else:
            em.description = "No self-assignable roles are configured yet.\nAdmins can add them with `-sar add <role>`."
        await ctx.send(embed=em)

    @sar.command(name="add")
    @commands.has_permissions(manage_roles=True)
    async def sar_add(self, ctx: commands.Context, *, role: discord.Role):
        """Mark a role as self-assignable. Usage: sar add <role>"""
        if not ctx.guild:
            return
        role_ids = self._self_role_list(ctx.guild.id)
        if role.id in role_ids:
            await ctx.send(embed=embeds.error_x0(f"{role.mention} is already self-assignable."))
            return
        role_ids.append(role.id)
        await ctx.send(embed=embeds.success_x0(f"{role.mention} is now self-assignable."))

    @sar.command(name="remove")
    @commands.has_permissions(manage_roles=True)
    async def sar_remove(self, ctx: commands.Context, *, role: discord.Role):
        """Remove a role from the self-assignable list. Usage: sar remove <role>"""
        if not ctx.guild:
            return
        role_ids = self._self_role_list(ctx.guild.id)
        if role.id not in role_ids:
            await ctx.send(embed=embeds.error_x0(f"{role.mention} is not in the self-assignable list."))
            return
        role_ids.remove(role.id)
        await ctx.send(embed=embeds.success_x0(f"{role.mention} removed from self-assignable roles."))

    @sar.command(name="get", aliases=["assign"])
    @commands.bot_has_permissions(manage_roles=True)
    async def sar_get(self, ctx: commands.Context, *, role: discord.Role):
        """Assign yourself a self-assignable role. Usage: sar get <role>"""
        if not ctx.guild or not isinstance(ctx.author, discord.Member):
            return
        role_ids = self._self_role_list(ctx.guild.id)
        if role.id not in role_ids:
            await ctx.send(embed=embeds.error_x0(f"{role.mention} is not self-assignable."))
            return
        if role in ctx.author.roles:
            await ctx.send(embed=embeds.error_x0(f"You already have {role.mention}."))
            return
        await ctx.author.add_roles(role, reason="Self-assigned via sar get")
        await ctx.send(embed=embeds.role_added_x0(ctx.author, role))

    @sar.command(name="drop", aliases=["unassign"])
    @commands.bot_has_permissions(manage_roles=True)
    async def sar_drop(self, ctx: commands.Context, *, role: discord.Role):
        """Remove a self-assignable role from yourself. Usage: sar drop <role>"""
        if not ctx.guild or not isinstance(ctx.author, discord.Member):
            return
        role_ids = self._self_role_list(ctx.guild.id)
        if role.id not in role_ids:
            await ctx.send(embed=embeds.error_x0(f"{role.mention} is not self-assignable."))
            return
        if role not in ctx.author.roles:
            await ctx.send(embed=embeds.error_x0(f"You don't have {role.mention}."))
            return
        await ctx.author.remove_roles(role, reason="Self-removed via sar drop")
        await ctx.send(embed=embeds.role_removed_x0(ctx.author, role))

    # ── Nickname Utility (bonus, pairs with roles) ────────────────────────

    @commands.command(name="nick", aliases=["setnick", "nickname"])
    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def nick(self, ctx: commands.Context, member: discord.Member, *, nickname: str = ""):
        """Set or clear a member's nickname. Leave nickname blank to reset.
        Usage: nick <@member> [new nickname]"""
        new_nick = nickname or None
        await member.edit(nick=new_nick, reason=f"Nickname changed by {ctx.author}")
        if new_nick:
            await ctx.send(embed=embeds.success_x0(f"Changed {member.mention}'s nickname to **{new_nick}**."))
        else:
            await ctx.send(embed=embeds.success_x0(f"Reset {member.mention}'s nickname."))

    @commands.command(name="massnick")
    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def massnick(self, ctx: commands.Context, *, nickname: str = ""):
        """Set or reset all members' nicknames. Leave blank to reset all.
        ⚠️ This may take time for large servers."""
        if not ctx.guild:
            return
        new_nick = nickname or None
        msg = await ctx.send(embed=embeds.info_x0("Processing mass nickname change… This may take a moment."))
        count = 0
        for member in ctx.guild.members:
            if member == ctx.guild.me:
                continue
            try:
                await member.edit(nick=new_nick, reason=f"Mass nick by {ctx.author}")
                count += 1
            except discord.Forbidden:
                continue
        action = f"set to **{nickname}**" if new_nick else "reset"
        await msg.edit(embed=embeds.success_x0(f"Nickname {action} for **{count}** member(s)."))


async def setup(bot: commands.Bot):
    await bot.add_cog(roleCommands(bot))
