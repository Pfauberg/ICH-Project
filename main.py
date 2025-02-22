import configparser
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

config = configparser.ConfigParser()
config.read("config.ini")
TOKEN = config["TELEGRAM"]["TOKEN"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Button 1", callback_data="page1")],
        [InlineKeyboardButton("Button 2", callback_data="page2")],
        [InlineKeyboardButton("Button 3", callback_data="page3")]
    ]
    await update.message.reply_text("M E N U", reply_markup=InlineKeyboardMarkup(keyboard))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    if data == "page1":
        keyboard = [[InlineKeyboardButton("Back", callback_data="back")]]
        await query.edit_message_text("Page 1 content", reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == "page2":
        keyboard = [[InlineKeyboardButton("Back", callback_data="back")]]
        await query.edit_message_text("Page 2 content", reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == "page3":
        keyboard = [[InlineKeyboardButton("Back", callback_data="back")]]
        await query.edit_message_text("Page 3 content", reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == "back":
        keyboard = [
            [InlineKeyboardButton("Button 1", callback_data="page1")],
            [InlineKeyboardButton("Button 2", callback_data="page2")],
            [InlineKeyboardButton("Button 3", callback_data="page3")]
        ]
        await query.edit_message_text("M E N U", reply_markup=InlineKeyboardMarkup(keyboard))

def main():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.run_polling()

if __name__ == "__main__":
    main()
