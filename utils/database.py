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
                    amount_of_sale INTEGER DEFAULT 0,
                    is_banned BOOLEAN DEFAULT 0
            )
        ''')
        self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS promocodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL,
                    who_created_telegram_id TEXT,
                    max_amount_uses INTEGER DEFAULT 1,
                    amount_uses INTEGER DEFAULT 0,
                    valid_until TEXT,
                    who_used_telegram_id TEXT,
                    amount_of_money INTEGER DEFAULT 0,
                    amount_of_sale INTEGER DEFAULT 0
            )
        ''')

    #region Users
    def add_user(self, telegram_id: str, refferer_id: int = None) -> None:
        self.cursor.execute('INSERT INTO users (telegram_id, refferer_id) VALUES (?, ?)', (telegram_id, refferer_id, ))
        self.connection.commit()

    def get_user(self, telegram_id: str) -> tuple:
        return self.cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,)).fetchone()

    def update_user(self, telegram_id: str, balance: int = None, amount_of_sale: int = None, 
                   is_banned: bool = None, refferer_id: int = None) -> None:
        """
        Обновляет данные пользователя. Все параметры кроме telegram_id опциональны.
        """
        update_parts = []
        params = []

        if balance is not None:
            update_parts.append("balance = balance + ?")
            params.append(balance)
            
        if amount_of_sale is not None:
            update_parts.append("amount_of_sale = ?")
            params.append(amount_of_sale)
            
        if is_banned is not None:
            update_parts.append("is_banned = ?")
            params.append(1 if is_banned else 0)
            
        if refferer_id is not None:
            update_parts.append("refferer_id = ?")
            params.append(refferer_id)

        if update_parts:
            query = f"UPDATE users SET {', '.join(update_parts)} WHERE telegram_id = ?"
            params.append(telegram_id)
            self.cursor.execute(query, params)
            self.connection.commit()

    def get_and_reset_sale(self, telegram_id: str) -> int:
        sale = self.cursor.execute('SELECT amount_of_sale FROM users WHERE telegram_id = ?', (telegram_id,)).fetchone()[0]
        self.update_user(telegram_id, amount_of_sale=0)
        return sale

    def is_exists(self, telegram_id: str) -> bool:
        result = self.cursor.execute('SELECT EXISTS(SELECT 1 FROM users WHERE telegram_id=?)', (telegram_id,)).fetchone()
        return bool(result[0])

    def get_referrals(self, telegram_id: str) -> list[tuple]:
        return self.cursor.execute('SELECT * FROM users WHERE refferer_id = ?', (telegram_id,)).fetchall()
        
    #endregion

    #region Promocodes
    def add_promocode(self, code: str, creator_id: str, max_uses: int, valid_until: str, amount_of_money: int | None, amount_of_sale: int | None) -> None:
        self.cursor.execute(
            'INSERT INTO promocodes (code, who_created_telegram_id, max_amount_uses, valid_until, amount_of_money, amount_of_sale) VALUES (?, ?, ?, ?, ?, ?)',
            (code, creator_id, max_uses, valid_until, amount_of_money, amount_of_sale)
        )
        self.connection.commit()

    def get_promocode(self, code: str) -> tuple:
        return self.cursor.execute('SELECT * FROM promocodes WHERE code = ?', (code,)).fetchone()

    def get_all_promocodes(self) -> list[tuple]:
        return self.cursor.execute('SELECT * FROM promocodes').fetchall()

    def update_promocode(self, code: str, amount_uses: int = None, who_used_telegram_id: str = None, 
                        max_amount_uses: int = None, valid_until: str = None, 
                        amount_of_money: int = None, amount_of_sale: int = None) -> None:
        """
        Обновляет данные промокода. Обязателен только параметр code, остальные опциональны.
        """
        update_parts = []
        params = []

        if amount_uses is not None:
            update_parts.append("amount_uses = amount_uses + ?")
            params.append(amount_uses)
            
        if who_used_telegram_id is not None:
            current_users = self.get_promocode(code)[6]
            if current_users:
                new_users = f"{current_users},{who_used_telegram_id}"
            else:
                new_users = who_used_telegram_id
            update_parts.append("who_used_telegram_id = ?")
            params.append(new_users)
            
        if max_amount_uses is not None:
            update_parts.append("max_amount_uses = ?")
            params.append(max_amount_uses)
            
        if valid_until is not None:
            update_parts.append("valid_until = ?")
            params.append(valid_until)
            
        if amount_of_money is not None:
            update_parts.append("amount_of_money = ?")
            params.append(amount_of_money)
            
        if amount_of_sale is not None:
            update_parts.append("amount_of_sale = ?")
            params.append(amount_of_sale)

        if update_parts:
            query = f"UPDATE promocodes SET {', '.join(update_parts)} WHERE code = ?"
            params.append(code)
            self.cursor.execute(query, params)
            self.connection.commit()

    def get_promo_users(self, code: str) -> list[str]:
        users = self.cursor.execute('SELECT who_used_telegram_id FROM promocodes WHERE code = ?', (code,)).fetchone()[0]
        if users:
            return users.split(',')
        return []
        
    def delete_promocode(self, code: str) -> None:
        """
        Удаляет промокод из базы данных
        """
        self.cursor.execute('DELETE FROM promocodes WHERE code = ?', (code,))
        self.connection.commit()

    #endregion
