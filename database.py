# -*- coding: utf-8 -*-
"""
Модуль для работы с базой данных SQLite
Хранит информацию о запросах пользователей и транзакциях
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Tuple
import config


class Database:
    """Класс для работы с базой данных фаукета"""
    
    def __init__(self, db_name: str = config.DATABASE_NAME):
        """
        Инициализация подключения к базе данных
        
        Args:
            db_name: Имя файла базы данных
        """
        self.db_name = db_name
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Получить соединение с базой данных"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Создание таблиц базы данных"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Таблица для хранения запросов пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                ton_address TEXT NOT NULL,
                tokens_amount INTEGER NOT NULL,
                request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN NOT NULL,
                tx_hash TEXT,
                error_message TEXT
            )
        ''')
        
        # Таблица для хранения статистики по адресам
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS address_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ton_address TEXT NOT NULL UNIQUE,
                first_request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_requests INTEGER DEFAULT 1,
                total_tokens_received INTEGER DEFAULT 0
            )
        ''')
        
        # Индексы для ускорения запросов
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_user_requests_user_id 
            ON user_requests(user_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_user_requests_date 
            ON user_requests(request_date)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_address_history_address 
            ON address_history(ton_address)
        ''')
        
        conn.commit()
        conn.close()
    
    def get_user_requests_today(self, user_id: int) -> int:
        """
        Получить количество успешных запросов пользователя за сегодня
        
        Args:
            user_id: ID пользователя Telegram
            
        Returns:
            Количество запросов за сегодня
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Начало сегодняшнего дня
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        cursor.execute('''
            SELECT COUNT(*) as count FROM user_requests
            WHERE user_id = ? 
            AND success = 1
            AND request_date >= ?
        ''', (user_id, today_start))
        
        result = cursor.fetchone()
        conn.close()
        
        return result['count'] if result else 0
    
    def can_request_tokens(self, user_id: int) -> Tuple[bool, int]:
        """
        Проверить, может ли пользователь запросить токены
        
        Args:
            user_id: ID пользователя Telegram
            
        Returns:
            Кортеж (можно_ли_запросить, количество_оставшихся_запросов)
        """
        requests_today = self.get_user_requests_today(user_id)
        remaining = config.MAX_REQUESTS_PER_DAY - requests_today
        can_request = remaining > 0
        
        return can_request, remaining
    
    def add_request(self, user_id: int, username: Optional[str], 
                   ton_address: str, tokens_amount: int, 
                   success: bool, tx_hash: Optional[str] = None, 
                   error_message: Optional[str] = None):
        """
        Добавить запись о запросе токенов
        
        Args:
            user_id: ID пользователя Telegram
            username: Имя пользователя Telegram
            ton_address: TON адрес получателя
            tokens_amount: Количество токенов
            success: Успешна ли транзакция
            tx_hash: Хэш транзакции (если успешна)
            error_message: Сообщение об ошибке (если не успешна)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_requests 
            (user_id, username, ton_address, tokens_amount, success, tx_hash, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, username, ton_address, tokens_amount, success, tx_hash, error_message))
        
        # Обновляем историю адреса
        if success:
            cursor.execute('''
                INSERT INTO address_history (ton_address, total_requests, total_tokens_received)
                VALUES (?, 1, ?)
                ON CONFLICT(ton_address) DO UPDATE SET
                    last_request_date = CURRENT_TIMESTAMP,
                    total_requests = total_requests + 1,
                    total_tokens_received = total_tokens_received + ?
            ''', (ton_address, tokens_amount, tokens_amount))
        
        conn.commit()
        conn.close()
    
    def get_total_statistics(self) -> dict:
        """
        Получить общую статистику бота
        
        Returns:
            Словарь со статистикой
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Общее количество успешных транзакций
        cursor.execute('SELECT COUNT(*) as count FROM user_requests WHERE success = 1')
        total_successful = cursor.fetchone()['count']
        
        # Общее количество выданных токенов
        cursor.execute('SELECT SUM(tokens_amount) as total FROM user_requests WHERE success = 1')
        total_tokens = cursor.fetchone()['total'] or 0
        
        # Уникальные пользователи
        cursor.execute('SELECT COUNT(DISTINCT user_id) as count FROM user_requests WHERE success = 1')
        unique_users = cursor.fetchone()['count']
        
        # Уникальные адреса
        cursor.execute('SELECT COUNT(*) as count FROM address_history')
        unique_addresses = cursor.fetchone()['count']
        
        conn.close()
        
        return {
            'total_successful': total_successful,
            'total_tokens': total_tokens,
            'unique_users': unique_users,
            'unique_addresses': unique_addresses
        }
    
    def has_address_received_tokens(self, ton_address: str) -> bool:
        """
        Проверить, получал ли адрес токены ранее
        
        Args:
            ton_address: TON адрес для проверки
            
        Returns:
            True если адрес уже получал токены
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) as count FROM address_history
            WHERE ton_address = ?
        ''', (ton_address,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result['count'] > 0
