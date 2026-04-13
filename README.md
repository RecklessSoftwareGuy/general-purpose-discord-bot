<div align="center">

# 🤖 General Purpose Discord Bot (GPDB)  
**A Premium, All-in-One Community Management Solution**

[![Python](https://img.shields.io/badge/Python-3.14%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Discord.py](https://img.shields.io/badge/Discord.py-2.4.0+-blueviolet?style=for-the-badge&logo=discord&logoColor=white)](https://github.com/Rapptz/discord.py)
[![License](https://img.shields.io/badge/License-GPL--3.0-green?style=for-the-badge)](LICENSE)
[![Uptime](https://img.shields.io/badge/Uptime-99.9%25-success?style=for-the-badge)](https://github.com/RecklessSoftwareGuy/general-purpose-discord-bot)

---

**GPDB** is a feature-rich, modular Discord bot built for power users and server administrators.  
It combines high-performance moderation, interactive ticketing, deep role management, and engaging leveling systems into a single, sleek package.

[Key Features](#-key-features) • [Installation](#-installation) • [Interactive UI](#-interactive-interfaces) • [Tech Stack](#-tech-stack)

</div>

---

## 🔥 Key Features

GPDB is built on a modular **Cog-based architecture**, allowing for easy scaling and customization.

### 🛡️ Industry-Standard Moderation
*   **Timeouts & Bans**: Support for temporary bans, mutes, and warnings with automated tracking.
*   **Automod Engine**: Intelligent word filtering and spam prevention.
*   **Granular Logging**: Detailed event tracking in dedicated mod-log channels.
*   **Mass Purge**: Clean up to 1000 messages instantly.

### 🏷️ Advanced Role Dynamics
*   **Self-Assignable Roles (SAR)**: Powerful interactive menus for user-led role selection.
*   **Mass Operations**: Add/Remove roles for humans, bots, or everyone at scale.
*   **Role Metadata**: Deep-dive into role permissions, members, and hoist settings.

### 📊 Leveling & Social
*   **Global Leaderboards**: Competitive XP system with beautifully formatted rank cards.
*   **Role Rewards**: Automate server progression by granting roles at specific milestones.
*   **Giveaway System**: Integrated interactive giveaway management with persistent buttons.

### 🎫 Professional Support Tickets
*   **One-Click Creation**: Professional panels for users to open support inquiry channels.
*   **Transcript Engine**: Automated session logging sent to staff logs upon ticket closure.
*   **Access Control**: Staff-only management commands to add/remove members from tickets.

---

## 🎨 Interactive Interfaces

GPDB leverages **Discord Components (Buttons, Select Menus)** to provide a premium user experience.

| Feature | Interface Type | Description |
| :--- | :--- | :--- |
| **Support** | `Persistent Buttons` | Seamless ticket creation and channel management. |
| **Help** | `Paginated List` | Interactive navigation with Home and directional buttons. |
| **Moderation** | `Confirm Views` | Danger-zone actions require a secondary confirmation click. |
| **Engagement** | `Action Rows` | One-click entry for giveaways and polls. |

---

## 🚀 Installation & Setup

### 1. Prerequisites
*   **Python 3.10+** (Recommend 3.14 for best performance)
*   **Discord Bot Token** from the [Developer Portal](https://discord.com/developers/applications)
*   **Privileged Gateway Intents** (Server Members, Message Content, Presence) enabled in portal.

### 2. Quick Start
```bash
# Clone the repository
git clone https://github.com/RecklessSoftwareGuy/general-purpose-discord-bot.git
cd general-purpose-discord-bot

# Set up virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
Edit `assets/config.json` with your credentials:
```json
{
    "prefix": ["-"],
    "token": "YOUR_SUPER_SECRET_TOKEN",
    "owners": [1234567890],
    "default_color": "#5865F2"
}
```

### 4. Run
```bash
python main.py
```

---

## 🛠️ Tech Stack

*   **Logic**: [discord.py](https://github.com/Rapptz/discord.py) — The backbone of the interaction.
*   **Storage**: [aiosqlite](https://github.com/omnilib/aiosqlite) — Asynchronous SQLite for robust data persistence.
*   **Requests**: [aiohttp](https://github.com/aio-libs/aiohttp) — High-speed API fetching for Memes/Jokes.
*   **UI/UX**: Custom-built `discord.ui` views for buttons and select menus.

---

## 📁 Repository Anatomy

```text
├── assets/             # Persistent data, Configs, and Core Bot Protocols
├── cogs/               # Individual feature modules (Extensible)
├── functions/          # Backend logic & Database CRUD operations
├── views/              # Premium Discord UI Components (Buttons/Embeds)
├── main.py             # Entry point & Extension loader
└── requirements.txt    # Mandatory dependencies
```

---

<div align="center">

### Built by **RecklessSoftwareGuy**  
*Empowering Discord communities with modern software.*

[Report Bug](https://github.com/RecklessSoftwareGuy/general-purpose-discord-bot/issues) • [Request Feature](https://github.com/RecklessSoftwareGuy/general-purpose-discord-bot/issues)

</div>
