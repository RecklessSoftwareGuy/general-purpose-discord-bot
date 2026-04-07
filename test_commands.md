# General Purpose Discord Bot - Test Guide

This guide contains the terminal commands to run the bot and the Discord commands to test its features.

## 1. Terminal Commands
Run these in your terminal to start the bot:

# To activate the virtual environment
source .venv/bin/activate

# To run the bot
python main.py

---

## 2. Bot Commands (Prefix: -)
Use these in your Discord server to test functionality. High-level categories are listed below.

### 🛡️ Moderation & Management
- `-mute <@user> [duration_in_hours] [reason]` - Timeout a member.
- `-unmute <@user>` - Remove timeout.
- `-kick <@user> [reason]` - Kick a member.
- `-ban <@user> [reason]` - Ban a member.
- `-tempban <@user> [duration] [reason]` - Ban for a set time (e.g., 1d, 12h).
- `-warn <@user> [reason]` - Issue a warning.
- `-warnings <@user>` - View warnings for a member.
- `-purge [limit]` - Delete many messages (max 1000).
- `-lock`/`-unlock` - Lock or unlock the current channel.
- `-slowmode [seconds]` - Set channel slowmode.
- `-setmodlog <#channel>` - Set the mod log channel.

### 🏷️ Roles
- `-giverole <@member> <role>` - Add a role to a member.
- `-takerole <@member> <role>` - Remove a role from a member.
- `-togglerole <@member> <role>` - Toggle a role on a member.
- `-createrole [#hex] [hoist] [mentionable] <name>` - Create a new role.
  - Example: `-createrole #ff5733 True False Moderator`
- `-delrole <role>` - Delete a role.
- `-editrole <role> <name|color|hoist|mentionable> <value>` - Edit a role property.
  - Example: `-editrole Mod color #ff0000`
- `-roleinfo <role>` - Detailed info about a role.
- `-rolemembers <role>` - List all members with a role.
- `-roles` - List all server roles.
- `-massrole add/remove <role>` - Mass add/remove a role for ALL members.
- `-masshumansrole add/remove <role>` - Mass role for humans only.
- `-massbotsrole add/remove <role>` - Mass role for bots only.
- `-nick <@member> [nickname]` - Set or reset a member's nickname.
- `-massnick [nickname]` - Set or reset all member nicknames.

**Self-Assignable Roles (SAR):**
- `-sar` - List all self-assignable roles.
- `-sar add <role>` - (Admin) Mark role as self-assignable.
- `-sar remove <role>` - (Admin) Unmark a self-assignable role.
- `-sar get <role>` - Assign yourself a self-assignable role.
- `-sar drop <role>` - Remove a self-assignable role from yourself.

### 📊 Leveling & XP
- `-rank [@user]` - View your or another user's rank card.
- `-leaderboard` - View the server XP leaderboard.
- `-enableleveling` / `-disableleveling` - Toggle XP system.
- `-setlevelchannel <#channel>` - Set notification channel.
- `-levelroles` - View current role rewards.

### 🔧 Utility & Info
- `-ping` - Check bot latency.
- `-userinfo [@user]` - Detailed info about a member.
- `-serverinfo` - Info about the server.
- `-afk [reason]` - Set AFK status.
- `-remind [duration] [message]` - Set a reminder (e.g., -remind 1h take a break).
- `-calc [expression]` - Evaluate math (e.g., -calc 2+2).
- `-embed "Title" [Description]` - Create a simple embed.
- `-membercount` - Show server member statistics.
- `-botinfo` - About the bot.

### 🎫 Support Tickets
- `-ticket setup` - Send the ticket entry panel.
- `-ticket setcategory <category>` - Set where tickets are created.
- `-ticket setlog <#channel>` - Set ticket log channel.
- `-ticket close` - Close the current ticket (in a ticket channel).
- `-ticket add <@user>` / `-ticket remove <@user>` - Manage ticket access.

### ⭐ Starboard
- `-starboard setup <#channel> [threshold]` - Set up the starboard.
- `-starboard threshold <number>` - Change star requirement.
- `-starboard emoji <emoji>` - Change the reaction emoji (default: ⭐).

### 🎮 Fun & Entertainment
- `-8ball [question]` - Ask the magic 8-ball.
- `-coinflip` - Flip a coin.
- `-roll [sides] [count]` - Roll dice.
- `-rps [rock/paper/scissors]` - Play rock-paper-scissors.
- `-meme` - Get a random meme from Reddit.
- `-joke` - Get a random joke.
- `-poll [question]` - Create a thumbs up/down poll.
- `-avatar [@user]` / `-banner [@user]` - View user profile images.

---

## 3. Configuration Notes
- Ensure your token in `assets/config.json` is correct.
- The prefix is currently set to `-`. You can change this in `assets/config.json`.
- SAR (self-assignable roles) list resets on bot restart — persistence can be added to the DB later.
- Mass role operations may be slow on large servers due to Discord rate limits.
