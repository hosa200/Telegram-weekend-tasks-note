# 🎙️ Telegram Voice & Text Task Agent (Raspberry Pi)

A lightweight, 24/7 shared task management bot for Telegram powered by local speech-to-text transcription (`faster-whisper`) and designed to run efficiently on a **Raspberry Pi**. 

Users can log tasks via text or voice notes (with multi-lingual support including English and Arabic), edit transcribed text inline before saving, mark items as completed, and reset weekly lists with a single command.

---

## ✨ Features

* **Local Speech-to-Text (`faster-whisper`):** Converts Telegram `.ogg` voice notes directly into text on the Raspberry Pi's CPU using `int8` quantization—requiring minimal disk space and zero cloud API fees.
* **Interactive Voice Confirmation & Inline Editing:** After transcribing a voice note, the bot presents inline buttons to **Confirm & Save**, **Edit** (pre-filling your Telegram chat input box via Inline Mode), or **Ignore**.
* **Shared Task Management:**
  * Send any plain text message to immediately add it to the shared list.
  * `/view` — Displays all tasks (marking completed ones with `[DONE]`) alongside interactive **Done** buttons for pending items.
  * `/newweek` — Purges all completed tasks, preserves unfinished leftovers, and re-indexes the remaining list sequentially.
  * `/start` & `/help` — Quick command overview.
* **Persistent JSON Storage:** Stores all tasks cleanly in a local `tasks.json` file with UTF-8 encoding.
* **24/7 Background Service & Automated Deployment:** Includes a Windows batch script (`piRun.bat`) to check SD card space, transfer files via `scp`, install dependencies, and configure a `systemd` service (`telegram-agent.service`) for automatic startup and crash recovery.

---

## 🏗️ Tech Stack

* **Language:** Python 3
* **Telegram Framework:** `python-telegram-bot` (v22+)
* **Speech Recognition:** `faster-whisper` (`CTranslate2` backend, `base` model, `int8` compute type)
* **Host Environment:** Raspberry Pi OS (Linux/ARM) managed via `systemd`
* **Deployment Automation:** Windows Batch (`.bat`) using native OpenSSH (`ssh` & `scp`)

---

## 📁 Project Structure

```text
weekend_agent/
├── agent.py        # Main Telegram bot & Faster-Whisper transcription logic
├── tasks.json      # Local JSON database storing active and completed tasks
├── piRun.bat       # Windows one-click SSH/SCP deployment & systemd setup script
└── README.md       # Project documentation
```

---

## 🚀 Prerequisites

### 1. Telegram BotFather Setup
1. Message **`@BotFather`** on Telegram and create a new bot with `/newbot` to get your **Bot Token**.
2. Enable **Inline Mode** (required for the **✏️ Edit** button to pre-fill your input bar):
   * Send `/setinline` to `@BotFather`
   * Select your bot and enter a placeholder prompt (e.g., `Edit task...`).
3. *(Optional)* If using the bot in a shared group chat, send `/setprivacy` to `@BotFather` and set it to **Disable** so the bot can read standard text and voice messages in the group.

### 2. Raspberry Pi Setup
* A Raspberry Pi running Raspberry Pi OS with **SSH enabled** and internet access.
* At least 2–3 GB of free space on your SD card for system audio packages (`ffmpeg`, `libsndfile1`) and Whisper model weights.

---

## 🛠️ Installation & Automated Deployment

1. **Clone or download this repository** to your local machine.
2. **Add your Bot Token:** Open `agent.py` and replace `TOKEN` with your token from `@BotFather`:
   ```python
   TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
   ```
   *(Security tip: Never commit your real bot token to a public GitHub repository—use an environment variable or `.env` file before pushing publicly).*
3. **Run the Deployment Script (Windows):**
   Open Command Prompt (`cmd`) in the project directory and run:
   ```cmd
   piRun.bat
   ```
   Enter your Raspberry Pi's **IP address**, **username**, and **sudo password** when prompted. The script will automatically:
   * Check available SD card disk space (`df -h /`).
   * Create `/home/<user>/weekend_agent` and copy `agent.py` and `tasks.json`.
   * Install OS dependencies (`python3-venv`, `libsndfile1`, `ffmpeg`) and Python packages (`faster-whisper`, `python-telegram-bot`).
   * Register, enable, and start `telegram-agent.service`.

---

## 🖥️ Managing the Bot on Raspberry Pi

Once deployed, the bot runs continuously in the background via `systemd`. Connect to your Pi via SSH to manage or monitor it:

* **Check service status:**
  ```bash
  sudo systemctl status telegram-agent.service
  ```
  *(Press `q` to exit the status view).*

* **View real-time logs:**
  ```bash
  journalctl -u telegram-agent.service -f
  ```
  *(Press `Ctrl+C` to exit live logs).*

* **Restart the bot manually:**
  ```bash
  sudo systemctl restart telegram-agent.service
  ```

---

## 💬 Bot Commands

| Command / Input | Description |
| :--- | :--- |
| **Text Message** | Directly adds a new task to the shared list under your Telegram name. |
| **Voice Note** | Transcribes audio locally and lets you **Confirm**, **Edit** inline, or **Ignore**. |
| `/view` | Displays all tasks (completed items marked `[DONE]`) with buttons to mark pending tasks complete. |
| `/newweek` | Removes all `[DONE]` tasks, keeps unfinished items, and resets task numbering. |
| `/help` | Lists available commands and usage instructions. |

---

## 📝 License

This project is open-source and available under the [MIT License](LICENSE).