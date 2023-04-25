import sqlite3

import tgbot.config

db_file = tgbot.config.load_config('bot.ini').data.db_file
db = sqlite3.connect(db_file)
cursor = db.cursor()
cursor.execute('ALTER TABLE Users ADD COLUMN login TEXT')
cursor.execute('ALTER TABLE Users ADD COLUMN password TEXT')
db.commit()