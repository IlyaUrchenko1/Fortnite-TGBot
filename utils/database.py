import sqlite3


class Database:
    def __init__(self, db_name="fortnite_shop.db"):
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id TEXT,
                    balance INTEGER DEFAULT 0,
                    refferer_id INTEGER,
                    is_banned BOOLEAN DEFAULT 0
            )
        ''')
        self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS promocodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL,
                    amount_of_money INTEGER DEFAULT 0,
                    who_created_telegram_id TEXT,
                    max_amount_uses INTEGER DEFAULT 1,
                    amount_uses INTEGER DEFAULT 0,
                    valid_until TEXT
            )
        ''')

    #region Users
    def add_user(self, telegram_id: str, refferer_id: int = None) -> None:
        self.cursor.execute('INSERT INTO users (telegram_id, refferer_id) VALUES (?, ?)', (telegram_id, refferer_id, ))
        self.connection.commit()

    def get_user(self, telegram_id: str) -> tuple:
        return self.cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,)).fetchone()

    def update_balance(self, telegram_id: str, amount: int) -> None:
        self.cursor.execute('UPDATE users SET balance = balance + ? WHERE telegram_id = ?', (amount, telegram_id))
        self.connection.commit()

    def ban_user(self, telegram_id: str) -> None:
        self.cursor.execute('UPDATE users SET is_banned = 1 WHERE telegram_id = ?', (telegram_id,))
        self.connection.commit()

    def unban_user(self, telegram_id: str) -> None:
        self.cursor.execute('UPDATE users SET is_banned = 0 WHERE telegram_id = ?', (telegram_id,))
        self.connection.commit()

    def is_exists(self, telegram_id: str) -> bool:
        result = self.cursor.execute('SELECT EXISTS(SELECT 1 FROM users WHERE telegram_id=?)', (telegram_id,)).fetchone()
        return bool(result[0])
        
    #endregion

    #region Promocodes
    def add_promocode(self, code: str, amount: int, creator_id: str, max_uses: int, valid_until: str) -> None:
        self.cursor.execute(
            'INSERT INTO promocodes (code, amount_of_money, who_created_telegram_id, max_amount_uses, valid_until) VALUES (?, ?, ?, ?, ?)',
            (code, amount, creator_id, max_uses, valid_until)
        )
        self.connection.commit()

    def get_promocode(self, code: str) -> tuple:
        return self.cursor.execute('SELECT * FROM promocodes WHERE code = ?', (code,)).fetchone()

    def use_promocode(self, code: str) -> None:
        self.cursor.execute('UPDATE promocodes SET amount_uses = amount_uses + 1 WHERE code = ?', (code,))
        self.connection.commit()

    def delete_promocode(self, code: str) -> None:
        self.cursor.execute('DELETE FROM promocodes WHERE code = ?', (code,))
        self.connection.commit()

    #endregion
