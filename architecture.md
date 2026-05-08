# Discord Bot Architecture & Coding Standards

> **Purpose:** This document defines the project structure, file responsibilities, naming conventions, and coding patterns for this Discord bot. Any agent or developer reading this file should be able to add new features, create new cogs, or extend the bot **in the exact same style** as the existing codebase.

---

## 1. Tech Stack

| Layer       | Technology                                     |
| :---------- | :--------------------------------------------- |
| **Runtime** | Python 3.10+ (discord.py 2.4+)                |
| **Database**| aiosqlite (async SQLite, file: `assets/database.db`) |
| **HTTP**    | aiohttp (for external API calls)               |
| **UI/UX**   | `discord.ui` (Buttons, Select Menus, Views)    |

All dependencies are listed in `requirements.txt`.

---

## 2. Main Paradigms

The architecture is built around the following strict paradigms:

1. **Cogs**: All cogs MUST go into the `cogs/` directory.
2. **Logic & Functions**: All large/complex code/logic blocks in the cogs or `main.py` MUST be moved into the `functions/` directory and go under an appropriate file name.
3. **Views**: All views are to be imported from `views/views.py`.
4. **Embeds**: All embeds are to be imported from `views/embeds.py`.
5. **Developer Configurations**: All developer-defined modules must be in `assets/config.json`. A developer merely wanting to add a cog or modify a base setting can do so by editing only 1 file (`config.json`).
6. **Database**: The whole bot uses 1 database file and may have multiple tables. **All table queries must be asynchronous.**

---

## 3. Directory Structure

```
├── main.py                     # Entry point — bot instantiation & startup
├── requirements.txt            # Python dependencies
├── architecture.md             # THIS FILE — project conventions
├── assets/                     # Core bot internals & persistent data
│   ├── __init__.py             # Empty — makes `assets` a Python package
│   ├── config.json             # Developer configurations (tokens, active cogs, etc.)
│   ├── database.db             # SQLite database (auto-created on startup)
│   └── protocols.py            # Bot subclass, extension loader, global error handler
├── cogs/                       # Feature modules (one cog = one feature domain)
│   ├── [feature_name].py
│   └── ...
├── functions/                  # Backend logic & database CRUD
│   ├── __init__.py             # Empty — makes `functions` a Python package
│   ├── database_functions.py   # ALL database operations (single source of truth)
│   ├── [feature]_functions.py
│   └── ...
└── views/                      # Discord UI components & embed factories
    ├── __init__.py             # Empty — makes `views` a Python package
    ├── embeds.py               # ALL embed builder functions (single file)
    └── views.py                # ALL discord.ui.View subclasses (single file)
```

---

## 4. File Responsibilities — The Golden Rules

### 4.1 `main.py` — Entry Point

- Instantiates the bot using the subclass from `assets.protocols`.
- Loads config from `assets/config.json`.
- Defines the `on_ready` listener (presence, startup message).
- Calls `protocols.extensions(bot, "load")` to load all cogs defined in `config.json`.
- Contains **only** minimal commands (like ping).
- **NEVER** put feature commands directly in `main.py`. All commands go into cogs.

### 4.2 `assets/protocols.py` — Bot Core

- Defines the custom Bot class (subclass of `commands.Bot`).
- `setup_hook()` — called once on startup; initializes the database schema.
- `is_owner()` — extends ownership check with the `owners` list from config.
- `on_command_error()` — global error handler for common discord.py exceptions.
- Defines `extensions()` — loads/reads cog extensions based on `config.json`.

### 4.3 `assets/config.json` — Configuration

```json
{
    "prefix" : ["-"],
    "token" : "YOUR_TOKEN",
    "owners" : [],
    "default_color" : "#5865F2",
    "extensions": [
        "moderation",
        "help",
        "utility"
    ]
}
```

- `prefix`: List of command prefixes (bot also responds to mentions).
- `token`: Discord bot token (**gitignored**, never commit).
- `owners`: List of user IDs with owner-level permissions.
- `default_color`: Default hex color for embeds.
- `extensions`: **Developer defined modules**. Add the name of your cog here to have it load on startup.

### 4.4 `cogs/*.py` — Feature Modules

**Every feature lives in its own cog file.** Each cog file follows this exact template:

```python
import discord
from discord.ext import commands
from functions import database_functions as db    # if DB access needed
from functions import <feature>_functions as <alias>  # if complex logic exists
from views import embeds                           # ALWAYS — for sending embeds
from views.views import SomeView                   # if UI views are needed

class featureNameCommands(commands.Cog):
    """<emoji> Short description of the feature."""
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # Register persistent views here (if any)
        # Start background tasks here (if any)
        print(f"Initialized: {self.__cog_name__}")
        super().__init__()

    # Listeners go here (@commands.Cog.listener)
    # Commands go here (@commands.command or @commands.group)

async def setup(bot: commands.Bot):
    await bot.add_cog(featureNameCommands(bot))
```

**Rules:**
1. Class name: `<featureName>Commands` (camelCase, ends with `Commands`). The docstring must start with an emoji and a short description — this is displayed in the help menu.
2. Every cog file **must** end with `async def setup(bot)` — this is how discord.py discovers cogs.
3. Cogs **never** construct embeds inline. They call functions from `views/embeds.py`.
4. Cogs **never** write SQL or touch the database directly. They call functions from `functions/`.
5. Large or complex logic blocks MUST be moved to a corresponding file in the `functions/` directory.

### 4.5 `views/embeds.py` — ALL Embeds

**Every `discord.Embed` in the entire bot is built by a function in this file.** No exceptions.

**Naming convention:** `<action>_x<tier>(params) -> discord.Embed`

- `x0` = the embed sent in the **channel** (public, visible to everyone).
- `x1` = the embed sent as a **DM** to the target user.

**Examples:**
```python
def success_x0(message) -> discord.Embed:           # Generic green success
def error_x0(message) -> discord.Embed:             # Generic red error
```

**Rules:**
1. Every function returns a `discord.Embed`. Nothing else.
2. Functions are pure — no side effects, no database calls, no API calls.
3. No `await` in embed functions. They are synchronous.

### 4.6 `views/views.py` — ALL Discord UI Views

**Every `discord.ui.View` subclass lives in this single file.**

**Rules:**
1. Persistent views (`timeout=None`) must have `custom_id` on every button/component.
2. Views can import from `views.embeds` and `functions.*` for their callbacks.
3. Views should be registered as persistent in their respective cog's `__init__` using `self.bot.add_view()`.

### 4.7 `functions/database_functions.py` — Database Layer (Single Source of Truth)

**ALL database access goes through this file.** No other file should import `aiosqlite` or construct SQL.

**Rules:**
1. Every function uses `async with aiosqlite.connect(DB_PATH) as db:` — no connection pooling; each call opens/closes.
2. **ALL table queries must be asynchronous.**
3. Read functions return `dict`, `list[dict]`, `int`, or `None`. Use `db.row_factory = aiosqlite.Row` for dict rows.
4. Write functions commit with `await db.commit()` before exiting.

### 4.8 `functions/<feature>_functions.py` — Feature Logic

**Business logic that is too complex for a cog callback but doesn't touch the database directly.**

**What goes here:**
- Processing pipelines.
- Embed builders that need database context.
- Utility logic.

**Rules:**
1. Function files call `functions.database_functions` for DB access — never raw SQL.
2. They can import `discord` for type hints and embed construction.

---

## 5. Import Conventions

All imports follow a strict aliasing pattern:

```python
# Database — always aliased as `db`
from functions import database_functions as db

# Feature functions — aliased as 2-letter abbreviation
from functions import moderation_functions as mf
from functions import utility_functions as uf

# Embeds — always imported as module
from views import embeds
# Usage: embeds.success_x0(message)

# Views — import specific classes when needed
from views.views import HelpView
from views import views
# Usage: views.HelpView()
```

---

## 6. Adding a New Feature — Step-by-Step Checklist

1. **Database schema** — If the feature needs persistence, add a new table in `database_functions.py → initialize_database()`. Add async CRUD functions in the same file.
2. **Embeds** — Add all embed builder functions to `views/embeds.py`.
3. **Views** (if needed) — Add any `discord.ui.View` subclasses to `views/views.py`.
4. **Feature functions** (if needed) — Create `functions/<feature>_functions.py` for complex business logic. Keep it focused.
5. **Cog** — Create `cogs/<feature>.py` following the cog template. Import from the layers above — never inline embeds or SQL.
6. **Register** — Add the cog's name to the `extensions` list in `assets/config.json`.

---

## 7. Data Flow Diagram

```
User sends command
        │
        ▼
   main.py (bot.run)
        │
        ▼
   cogs/<feature>.py          ← Command handler / listener
        │
        ├──▶ views/embeds.py       ← Build the embed to send
        │
        ├──▶ views/views.py        ← Attach UI (buttons, menus)
        │
        ├──▶ functions/<feature>_functions.py  ← Business logic
        │         │
        │         ▼
        │    functions/database_functions.py    ← DB read/write
        │
        ▼
   ctx.send(embed=..., view=...)   ← Response to Discord
```

**Key principle:** Data flows **downward**. Cogs call functions and views. Functions call the database layer. Nothing flows upward.

---

## 8. Configuration Flow

Per-guild settings follow this pattern:

1. Admin runs a config command (e.g., `-setchannel #general`).
2. The cog calls `db.update_guild_config(guild_id, target_channel_id=channel.id)`.
3. The cog sends a confirmation embed: `embeds.config_set_x0("Target Channel", channel.mention)`.
4. When the feature triggers, the listener calls `db.get_guild_config(guild_id)` and reads the stored values.
