# 🎉 Welcome to MCP-Link-Server!

Thanks for installing **MCP-Link-Server** — the powerful local engine that lets AI agents control tools, automate tasks, and perform real-world operations on your machine!

Whether you're using ChatGPT, Claude, or another AI model, **MCP-Link-Server** provides the computational backbone for secure, local AI automation.

---

## 🚀 What is MCP-Link-Server?

MCP-Link-Server IS the powerful **MCP (Model Context Protocol) server** that AI agents connect to. This server enables AI agents to:

* 🧠 Execute local tools like file operations, system commands, database queries, and more
* 🔍 Automate browser interactions through the "browser" tool when connected to the extension
* 🔄 Chain tool outputs across services for complex local automation
* 🔒 Keep you in full control with per-tool permissions and Docker sandboxing

This gives AIs real power — safely — using *your* rules, *your* tools, and *your* local machine.

---

## ♿ Empowering Accessibility and Inclusion

**MCP-Link-Server** was built with accessibility in mind from the very beginning. For users with visual impairments, mobility challenges, or cognitive limitations, managing files, running commands, and controlling their computer can be challenging.

With MCP-Link-Server, those barriers start to fade.

By providing AI agents with secure access to local tools and operations, MCP-Link-Server enables smart assistants that can **manage files, execute commands, and automate system tasks — all under your complete control**.

Whether it's organizing documents, running scripts, or automating routine maintenance, **MCP-Link-Server gives users a powerful voice and control mechanism for their local environment**.

This is more than convenience — it's **digital empowerment** in action.

---

## ✅ Getting Started

**MCP-Link-Server is designed to "just work" for everyone - no Python knowledge required!**

### 📦 **Option 1: Easy Installation (Recommended)**

1. **Download the Installer**
   - Visit [GitHub Releases](https://github.com/AuraFriday/mcp-link-server/releases/tag/latest)
   - Choose your platform:
     - **Windows**: `mcp-link-server-windows.exe` 
     - **macOS (Intel)**: `mcp-link-server-macos-intel.pkg`
     - **macOS (Apple Silicon)**: `mcp-link-server-macos-arm.pkg`
     - **Linux**: `mcp-link-server-linux.run`

2. **Install & Launch**
   - Run the installer and follow the simple prompts
   - Launch "MCP Link Server" from your applications menu
   - The server starts automatically with optimal settings!

> ✨ **That's it!** The server includes everything: Python runtime, CUDA/ROCm support, SQLite with semantic search, hardware-accelerated embeddings, and enhanced security features.

### 🛠️ **Option 2: Developer Setup (Custom Python)**

For developers who prefer using their own Python environment:

```bash
# Clone and install
git clone https://github.com/AuraFriday/mcp-link-server.git
cd mcp-link-server
pip install -r requirements.txt

# Run the server
python server.py
```

> ⚠️ **Note**: Our static build includes many enhanced features that standard Python installations lack.

### 🔧 **Configure Tools & Permissions**

Review and adjust tool permissions in the server configuration:

* Edit `config.json` to enable/disable specific tools
* Set permission levels for each tool (ask, allow, sandbox)
* Configure Docker settings for sandboxed execution

---

## 💬 4. Connect AI Clients

Now connect AI clients to your server:

**Option A: Use with MCP Link Browser Extension**
* Install the [MCP Link extension](https://github.com/AuraFriday/mcp-link) in your browser
* Add your server URL to the extension settings
* Visit [chatgpt.com](https://chatgpt.com) or [claude.ai](https://claude.ai) and let AIs discover your tools

**Option B: Direct MCP Client Integration**
* Use Claude Desktop, VS Code extensions, or other MCP-compatible clients
* Connect directly to your server's SSE endpoint
* Enjoy powerful local tool execution with complete privacy

Your MCP server provides tools ready to help AI agents:

* Execute file operations and system commands
* Run database queries and data processing
* Automate complex local workflows
* Maintain complete data privacy

The server will ask for confirmation before any sensitive tools are used — you remain in control at all times.

---

## 🙌 Thanks for joining us!

MCP-Link-Server is built for power users like you. Expect more tools, more integrations, and more powerful features in every update.

For support, new tool ideas, or just to say hi, visit:

* GitHub: [https://github.com/AuraFriday/mcp-link-server](https://github.com/AuraFriday/mcp-link-server)
* Email: [ask@aurafriday.com](mailto:ask@aurafriday.com)
* [Privacy Policy](PRIVACY.md) & [EULA](EULA.md): Available in this repository

---

> ⚠️ Reminder: Tools only execute *with your explicit permission*. You can always review, configure, or disable any tool in the server configuration.

Enjoy the power of secure, local AI automation, on your terms.
**— The Aura Friday Team**

---

<small><sup>Copyright © 2025 Christopher Drake. All rights reserved. "signature": "ƬᴜpZᗷⅮҳꓓνɪꓝ𝛢NÐ9fÐЕΡᎠᑕ𝟢𐓒ⲟᏎɌf7Օᴠսу3𝟦aᏎᒿzᏴⲞƏ6𝛢𝟤ƛƟΡᏎ𝛢ꓧᏟWƌꞇƵցꓝΟոƶVЅƐеƶ𝟛GlᏟ𝕌ꓣҮƘlᒿΜһɌȠҳꓜɗQþPК𝟨C𝟧bꓑОΗⲔƛⴹΚꓠER𝟥ꙅѡmΗսʈꓪʈ". "signdate":"2025-09-03T14:39:56.487Z" </sup></small>
