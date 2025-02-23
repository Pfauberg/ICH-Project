# 🎬 Sakila Telegram Bot

A **Telegram bot** that allows users to search for movies by **keywords, genres, and years**. The bot keeps track of the most popular queries. 

## 🚀 Features

- **Search by keyword** – find movies by title or description.
- **Search by genre & year** – browse movies by categories and release years.
- **Top queries tracking** – displays the most searched terms.

## 🛠️ Installation

### 1️⃣ Clone the repository

```sh
git clone https://github.com/Pfauberg/ICH-Project
cd ICH-Project
```

### 2️⃣ Install dependencies

Install the required dependencies:

```sh
pip install -r requirements.txt
```

### 3️⃣ Configure the bot

Copy the example configuration file and update it with your **Telegram bot token** and **MySQL database credentials**:

```sh
cp config_example.ini config.ini
```

Edit `config.ini`:

```ini
[TELEGRAM]
TOKEN = YOUR_TELEGRAM_BOT_TOKEN

[DATABASE]
HOST = YOUR_DATABASE_HOST
USER = YOUR_DATABASE_USER
PASSWORD = YOUR_DATABASE_PASSWORD
DBNAME = YOUR_DATABASE_NAME
```

### 4️⃣ Run the bot

```sh
python main.py
```

## 📌 Usage

Start the bot by sending the `/start` command. The bot will present a menu with three options:

1. **🔍 Search by keyword** – Enter any keyword, and the bot will find relevant movies.
2. **🎭 Search by genre & year** – Select a genre and a release year to filter movies.
3. **🏆 Top queries** – View the most searched queries.

## 📄 License

MIT License. Feel free to use and modify.
