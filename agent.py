import os
import json
import logging
from faster_whisper import WhisperModel
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CallbackQueryHandler, CommandHandler, InlineQueryHandler, filters
from telegram import InlineQueryResultArticle, InputTextMessageContent
import uuid

# ==================== CONFIGURATION ====================
TOKEN = "9070118980:AAH9NFjPKjG26q4LRnAQ-ho8bniX0W6mYwc"  # Your Bot Token
TASKS_FILE = "tasks.json"
# =======================================================

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

print("Loading Faster-Whisper model...", flush=True)
# Optimized for CPU on Raspberry Pi using int8 quantization for lightning speed & low memory
model = WhisperModel("base", device="cpu", compute_type="int8")

def load_tasks():
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_tasks(tasks):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hello! Send me voice notes or text anytime to log tasks. Use /view to check the list or /newweek to clear completed tasks."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 Task Bot Commands:\n\n"
        "• Voice/Text (Anytime): Send a task.\n"
        "• /view: View all tasks (completed ones are marked as [DONE]).\n"
        "• /newweek: Erase all completed tasks and keep unfinished leftovers.\n"
        "• /help: Show this menu."
    )
    await update.message.reply_text(help_text)

async def newweek_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tasks = load_tasks()
    remaining_tasks = [t for t in tasks if not t.get("done", False)]
    
    for new_id, task in enumerate(remaining_tasks, start=1):
        task["id"] = new_id
        
    save_tasks(remaining_tasks)
    
    removed_count = len(tasks) - len(remaining_tasks)
    await update.message.reply_text(
        f"🧹 New Week Reset Complete!\n\n"
        f"• Cleared {removed_count} completed task(s).\n"
        f"• Kept {len(remaining_tasks)} unfinished leftover(s).\n\n"
        f"Use /view to see your fresh list."
    )

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_name = update.effective_user.first_name or "Someone"
        await update.message.reply_text(f"🎙️ Processing voice note from {user_name}...")
        
        voice_file = await context.bot.get_file(update.message.voice.file_id)
        ogg_path = "voice_note.ogg"
        await voice_file.download_to_drive(ogg_path)
        
        print("Transcribing voice note with faster-whisper...", flush=True)
        # faster-whisper reads the OGG file directly without needing external audio libraries
        segments, info = model.transcribe(ogg_path, beam_size=5)
        transcribed_text = " ".join([segment.text for segment in segments]).strip()
        
        if os.path.exists(ogg_path):
            os.remove(ogg_path)
            
        if not transcribed_text:
            await update.message.reply_text("⚠️ Could not detect any speech in the audio.")
            return

        context.user_data["pending_task"] = transcribed_text
        context.user_data["author"] = user_name

        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm & Save", callback_data="task_correct"),
                InlineKeyboardButton("✏️ Edit", switch_inline_query_current_chat=transcribed_text)
            ],
            [
                InlineKeyboardButton("❌ Ignore", callback_data="task_ignore")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"🎙️ {user_name} said:\n\n\"{transcribed_text}\"",
            reply_markup=reply_markup
        )
    except Exception as e:
        print(f"ERROR in handle_voice: {e}", flush=True)
        await update.message.reply_text(f"❌ Error processing voice note: {e}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.is_bot:
        return
        
    text = update.message.text.strip()
    user_name = update.effective_user.first_name or "Someone"
    
    tasks = load_tasks()
    new_task = {"id": len(tasks) + 1, "text": text, "author": user_name, "done": False}
    tasks.append(new_task)
    save_tasks(tasks)
    
    await update.message.reply_text(f"✅ Task added by {user_name}!\n\n• {text}")

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    results = [
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title="Edit Task",
            input_message_content=InputTextMessageContent(query if query else "Task"),
            description=query
        )
    ]
    await update.inline_query.answer(results, cache_time=1)

async def view_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tasks = load_tasks()
    
    if not tasks:
        await update.message.reply_text("🎉 Your task list is completely empty!")
        return

    text = "📋 All Shared Weekend Tasks:\n\n"
    keyboard = []
    
    for idx, task in enumerate(tasks):
        author = task.get("author", "Unknown")
        task_text = task['text']
        is_done = task.get("done", False)
        
        if is_done:
            text += f"{idx + 1}. [DONE] {task_text} (by {author})\n"
        else:
            text += f"{idx + 1}. {task_text} (by {author})\n"
            keyboard.append([InlineKeyboardButton(f"✔️ Done: {task_text[:20]}...", callback_data=f"done_{task['id']}")])

    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    await update.message.reply_text(text, reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "task_correct":
        task_text = context.user_data.get("pending_task")
        author = context.user_data.get("author", "Someone")
        if task_text:
            tasks = load_tasks()
            new_task = {"id": len(tasks) + 1, "text": task_text, "author": author, "done": False}
            tasks.append(new_task)
            save_tasks(tasks)
            await query.edit_message_text(text=f"✅ Task Saved to Shared List!\n\n• {task_text} ({author})")
        else:
            await query.edit_message_text(text="⚠️ Session expired.")
            
    elif data == "task_ignore":
        await query.edit_message_text(text="❌ Task discarded.")
        
    elif data.startswith("done_"):
        task_id = int(data.split("_")[1])
        tasks = load_tasks()
        
        for t in tasks:
            if t["id"] == task_id:
                t["done"] = True
                
        save_tasks(tasks)
        await query.edit_message_text(text="🎉 Task marked as completed! Use /view to see the updated list.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("view", view_tasks))
    app.add_handler(CommandHandler("newweek", newweek_command))
    app.add_handler(MessageHandler(filters.VOICE & (~filters.COMMAND), handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app.add_handler(InlineQueryHandler(inline_query_handler))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("Agent is running with Faster-Whisper... Press Ctrl+C to stop.", flush=True)
    app.run_polling()