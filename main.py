import os
import pymysql
import sqlite3
import configparser
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

config = configparser.ConfigParser()
config.read("config.ini")

server_db_config = {
    "host": config["DATABASE"]["HOST"],
    "user": config["DATABASE"]["USER"],
    "password": config["DATABASE"]["PASSWORD"],
    "database": config["DATABASE"]["DBNAME"],
    "cursorclass": pymysql.cursors.DictCursor
}

TOP_DB_PATH = os.path.join(os.path.dirname(__file__), "top_queries.sqlite")
TOKEN = config["TELEGRAM"]["TOKEN"]

MODE = "mode"
MSG_ID = "msg_id"
GENRE = "genre_value"
YEAR = "year_value"

rating_map = {
    "G": "0+",
    "PG": "6+",
    "PG-13": "12+",
    "R": "16+",
    "NC-17": "18+"
}

MAIN_MENU_TEXT = (
    "🎬 Welcome to the <b>S A K I L A</b> Bot! 🎬\n\n"
    "Choose an option below to get started.\n"
    "Browse by a keyword, pick a genre with a specific year, "
    "or explore the top queries from other users.\n\n"
    "Have fun searching! 😎"
)

KEYWORD_MENU_TEXT = (
    "🔎 <b>Search by Keyword</b>\n\n"
    "Type a word or phrase below to find matching films.\n"
    "For example, you can try <i>love</i>, <i>action</i>, or <i>space</i>."
)

GENRE_MENU_HEADER = (
    "🎭 <b>Genre & Year Search</b>\n\n"
    "Below are the available genres (with the number of films):"
)

BACK_BUTTON_TEXT = "⬅️ Back"

def init_top_db():
    if not os.path.exists(TOP_DB_PATH):
        conn = sqlite3.connect(TOP_DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS search_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_type TEXT,
                search_value TEXT
            )
        """)
        conn.commit()
        conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("🔍 Search by keyword", callback_data="go_keyword_start")],
        [InlineKeyboardButton("🎭 Search by genre & year", callback_data="go_genre_start")],
        [InlineKeyboardButton("🏆 Top queries", callback_data="go_top_queries")]
    ]
    if update.message:
        m = await update.message.reply_text(
            MAIN_MENU_TEXT,
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="HTML"
        )
        context.user_data[MSG_ID] = m.message_id
    else:
        q = update.callback_query
        m = await q.edit_message_text(
            MAIN_MENU_TEXT,
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="HTML"
        )
        context.user_data[MSG_ID] = m.message_id
    context.user_data[MODE] = None

async def show_genre_page(query, context):
    genres = await get_available_genres()
    formatted = ", ".join(f"{g} ({cnt})" for g, cnt in genres)
    txt = f"{GENRE_MENU_HEADER}\n\n{formatted}\n\nSend me one."
    await query.edit_message_text(
        txt,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data="back_to_main_menu")]
        ]),
        parse_mode="HTML"
    )
    context.user_data[MSG_ID] = query.message.message_id
    context.user_data[MODE] = "genre_start"
    context.user_data[GENRE] = None
    context.user_data[YEAR] = None

async def callback_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data

    if data == "go_keyword_start":
        m = await q.edit_message_text(
            KEYWORD_MENU_TEXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data="back_to_main_menu")]
            ]),
            parse_mode="HTML"
        )
        context.user_data[MSG_ID] = m.message_id
        context.user_data[MODE] = "keyword_start"

    elif data == "back_to_main_menu":
        kb = [
            [InlineKeyboardButton("🔍 Search by keyword", callback_data="go_keyword_start")],
            [InlineKeyboardButton("🎭 Search by genre & year", callback_data="go_genre_start")],
            [InlineKeyboardButton("🏆 Top queries", callback_data="go_top_queries")]
        ]
        m = await q.edit_message_text(
            MAIN_MENU_TEXT,
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="HTML"
        )
        context.user_data[MSG_ID] = m.message_id
        context.user_data.clear()

    elif data == "go_keyword_result_back":
        m = await q.edit_message_text(
            KEYWORD_MENU_TEXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data="back_to_main_menu")]
            ]),
            parse_mode="HTML"
        )
        context.user_data[MSG_ID] = m.message_id
        context.user_data[MODE] = "keyword_start"

    elif data == "go_genre_start":
        await show_genre_page(q, context)

    elif data == "go_year_back_to_genre":
        await show_genre_page(q, context)

    elif data == "go_genre_result_back":
        await show_genre_page(q, context)

    elif data == "go_top_queries":
        r = await get_top_queries()
        lines = [f"{row['search_value']} - used {row['cnt']} times" for row in r]
        txt = "🏆 <b>Top Queries</b>\n\n"
        if lines:
            txt += "\n".join(lines)
        else:
            txt += "No data"
        m = await q.edit_message_text(
            txt,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data="back_to_main_menu")]
            ]),
            parse_mode="HTML"
        )
        context.user_data[MSG_ID] = m.message_id
        context.user_data[MODE] = None

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mid = context.user_data.get(MSG_ID)
    if not mid:
        return
    await update.message.delete()
    mode = context.user_data.get(MODE)
    if mode == "keyword_start":
        kw = update.message.text
        films = await search_by_keyword(kw)
        text_result = format_films(films) or "No results found."
        await insert_query("keyword", kw)
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=mid,
            text=text_result,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data="go_keyword_result_back")]
            ]),
            parse_mode="HTML"
        )
        context.user_data[MODE] = "keyword_result"

    elif mode == "keyword_result":
        pass

    elif mode == "genre_start":
        context.user_data[GENRE] = update.message.text.upper().strip()
        years = await get_years_for_genre(context.user_data[GENRE])
        if not years:
            genres = await get_available_genres()
            formatted = ", ".join(f"{g} ({cnt})" for g, cnt in genres)
            txt = (
                f"Genre '{context.user_data[GENRE]}' not found.\n\n"
                "Available genres:\n"
                f"{formatted}\n\n"
                "Send me one."
            )
            rmk = InlineKeyboardMarkup([
                [InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data="back_to_main_menu")]
            ])
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=mid,
                text=txt,
                reply_markup=rmk,
                parse_mode="HTML"
            )
            context.user_data[MODE] = "genre_start"
        else:
            txt = (
                f"Genre '{context.user_data[GENRE]}' found!\n\n"
                "Possible release years:\n"
            )
            year_parts = [f"{y}({cnt})" for y, cnt in years]
            txt += ", ".join(year_parts)
            txt += "\n\nPlease send one of these years."
            rmk = InlineKeyboardMarkup([
                [InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data="go_year_back_to_genre")]
            ])
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=mid,
                text=txt,
                reply_markup=rmk,
                parse_mode="HTML"
            )
            context.user_data[MODE] = "year_start"

    elif mode == "year_start":
        g = context.user_data.get(GENRE, "")
        try:
            y = int(update.message.text.strip())
        except:
            y = 0
        films = await search_by_genre_and_year(g, y)
        if not films:
            available_years = await get_years_for_genre(g)
            parts = [f"{yr}({cnt})" for yr, cnt in available_years]
            txt = (
                f"Year '{update.message.text.strip()}' not found for genre '{g}'.\n\n"
                "Available years:\n"
                f"{', '.join(parts)}\n\n"
                "Please send one."
            )
            rmk = InlineKeyboardMarkup([
                [InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data="go_year_back_to_genre")]
            ])
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=mid,
                text=txt,
                reply_markup=rmk,
                parse_mode="HTML"
            )
            context.user_data[MODE] = "year_start"
        else:
            text_result = format_films(films)
            await insert_query("genre_year", f"{g},{y}")
            rmk = InlineKeyboardMarkup([
                [InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data="go_genre_result_back")]
            ])
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=mid,
                text=text_result,
                reply_markup=rmk,
                parse_mode="HTML"
            )
            context.user_data[MODE] = "genre_result"

    elif mode == "genre_result":
        pass

async def search_by_keyword(keyword: str):
    sql = """
    SELECT film_id, title, release_year, description, rating, imdb_id,
           length
    FROM film
    WHERE title LIKE %s OR description LIKE %s
    LIMIT 10
    """
    like_pattern = f"%{keyword}%"
    try:
        conn = pymysql.connect(**server_db_config)
        with conn.cursor() as cursor:
            cursor.execute(sql, (like_pattern, like_pattern))
            rows = cursor.fetchall()
        conn.close()
        return rows
    except:
        return []

async def search_by_genre_and_year(genre: str, year: int):
    sql = """
    SELECT f.film_id, f.title, f.release_year, f.description,
           f.rating, f.imdb_id, f.length
    FROM film f
    JOIN film_category fc ON f.film_id = fc.film_id
    JOIN category c ON fc.category_id = c.category_id
    WHERE c.name = %s AND f.release_year = %s
    LIMIT 10
    """
    try:
        conn = pymysql.connect(**server_db_config)
        with conn.cursor() as cursor:
            cursor.execute(sql, (genre, year))
            rows = cursor.fetchall()
        conn.close()
        return rows
    except:
        return []

async def get_available_genres():
    sql = """
    SELECT c.name, COUNT(f.film_id) as film_count
    FROM category c
    JOIN film_category fc ON c.category_id = fc.category_id
    JOIN film f ON fc.film_id = f.film_id
    GROUP BY c.name
    ORDER BY c.name
    """
    try:
        conn = pymysql.connect(**server_db_config)
        with conn.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
        conn.close()
        return [(r["name"], r["film_count"]) for r in rows]
    except:
        return []

async def get_years_for_genre(genre: str):
    sql = """
    SELECT f.release_year AS yr, COUNT(f.film_id) as film_count
    FROM film f
    JOIN film_category fc ON f.film_id = fc.film_id
    JOIN category c ON fc.category_id = c.category_id
    WHERE c.name = %s
    GROUP BY f.release_year
    ORDER BY f.release_year
    """
    try:
        conn = pymysql.connect(**server_db_config)
        with conn.cursor() as cursor:
            cursor.execute(sql, (genre,))
            rows = cursor.fetchall()
        conn.close()
        return [(r["yr"], r["film_count"]) for r in rows]
    except:
        return []

async def get_top_queries():
    sql = """
    SELECT search_value, COUNT(*) AS cnt
    FROM search_results
    GROUP BY search_value
    ORDER BY cnt DESC
    LIMIT 10
    """
    try:
        conn = sqlite3.connect(TOP_DB_PATH)
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        conn.close()
        return [{"search_value": r[0].title(), "cnt": r[1]} for r in rows]
    except:
        return []

async def insert_query(stype: str, sval: str):
    sql = "INSERT INTO search_results (search_type, search_value) VALUES (?, ?)"
    try:
        conn = sqlite3.connect(TOP_DB_PATH)
        cur = conn.cursor()
        cur.execute(sql, (stype, sval.lower()))
        conn.commit()
        conn.close()
    except:
        pass

def format_films(rows):
    if not rows:
        return ""
    lines = []
    for r in rows:
        title = r["title"]
        year = r["release_year"]
        desc = r["description"] or ""
        mpaa_rating = r.get("rating", "Unknown")
        local_rating = rating_map.get(mpaa_rating, "Unknown")
        length = r.get("length") or 0
        lines.append(
            f"<b>{title}</b> ({local_rating})\n"
            f"📅 {year}\n"
            f"⏳ {length} min\n"
            f"<blockquote>📖 {desc[:100]}...</blockquote>\n"
            "============================\n"
        )
    return "".join(lines)

def main():
    init_top_db()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
