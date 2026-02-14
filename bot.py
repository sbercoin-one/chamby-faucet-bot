# -*- coding: utf-8 -*-
"""
Telegram бот для раздачи токенов Chamby в сети TON
Основной файл с обработчиками команд
"""

import logging
import time
import threading
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import config
from database import Database
from ton_utils import TONUtils

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class ChambyFaucetBot:
    """Класс Telegram бота для раздачи токенов Chamby"""
    
    def __init__(self):
        """Инициализация бота"""
        self.database = Database()
        self.ton_utils = TONUtils()
        self.updater = Updater(token=config.TELEGRAM_BOT_TOKEN, use_context=True)
        self.dispatcher = self.updater.dispatcher
        
        # Механизм блокировки для предотвращения одновременных запросов
        self.processing_lock = threading.Lock()
        self.last_process_time = 0
        self.lock_timeout = 10  # секунд
        
        # Регистрация обработчиков команд
        self.register_handlers()
    
    def register_handlers(self):
        """Регистрация обработчиков команд бота"""
        self.dispatcher.add_handler(CommandHandler("start", self.start_command))
        self.dispatcher.add_handler(CommandHandler("help", self.start_command))
        self.dispatcher.add_handler(CommandHandler(
    ["get_chamby", "getchamby", "chamby", "get_tokens"], 
    self.get_chamby_command
))
        self.dispatcher.add_handler(CommandHandler("stats", self.stats_command))
    
    def start_command(self, update: Update, context: CallbackContext):
        """
        Обработчик команды /start
        Показывает приветствие и правила
        """
        user = update.effective_user
        logger.info(f"User {user.id} (@{user.username}) started the bot")
        
        update.message.reply_text(
            config.WELCOME_MESSAGE,
            parse_mode='Markdown'
        )
    
    def get_chamby_command(self, update: Update, context: CallbackContext):
        """
        Обработчик команды /get_chamby <ton_address>
        Основная функция выдачи токенов
        """
        user = update.effective_user
        user_id = user.id
        username = user.username
        
        # Проверка блокировки - предотвращение одновременных запросов
        if not self.processing_lock.acquire(blocking=False):
            # Бот уже обрабатывает другой запрос
            current_time = time.time()
            time_since_last = current_time - self.last_process_time
            
            if time_since_last < self.lock_timeout:
                logger.warning(f"User {user_id} tried to request while bot is busy")
                update.message.reply_text(config.ERROR_BOT_BUSY)
                return
        
        try:
            # Обновляем время последней обработки
            self.last_process_time = time.time()
            
            # Проверка наличия аргумента (TON адреса)
            if not context.args or len(context.args) == 0:
                update.message.reply_text(
                    "❌ Please specify a TON address!\n\n"
                    "Usage example:\n"
                    "/get_chamby EQDtFpEwcFAEcRe5mLVh2N6C0x-_hJEM7W61_JLnSF74p4q2"
                )
                return
            
            ton_address = context.args[0]
            logger.info(f"User {user_id} (@{username}) requested tokens for address: {ton_address}")
            
            # Шаг 1: Нормализация адреса
            ton_address = self.ton_utils.normalize_address(ton_address)
            
            # Шаг 2: Валидация TON адреса
            if not self.ton_utils.is_valid_ton_address(ton_address):
                logger.warning(f"Invalid TON address: {ton_address}")
                update.message.reply_text(config.ERROR_INVALID_ADDRESS)
                return
            
            # Шаг 3: Проверка лимита запросов пользователя
            can_request, remaining = self.database.can_request_tokens(user_id)
            
            if not can_request:
                logger.warning(f"User {user_id} reached daily limit")
                update.message.reply_text(
                    config.ERROR_LIMIT_REACHED.format(
                        config.MAX_REQUESTS_PER_DAY,
                        config.MAX_REQUESTS_PER_DAY
                    )
                )
                return
            
            # Отправка сообщения о начале проверки
            status_message = update.message.reply_text(
                "⏳ Checking address and token balance...",
                parse_mode='Markdown'
            )
            
            # Шаг 4: Проверка баланса Chamby токенов на адресе
            success, balance, error = self.ton_utils.get_jetton_balance(
                ton_address,
                config.CHAMBY_JETTON_CONTRACT
            )
            
            if not success:
                logger.error(f"Error checking balance: {error}")
                status_message.edit_text(config.ERROR_API_UNAVAILABLE)
                return
            
            # Шаг 5: Проверка что на адресе нет токенов (баланс = 0)
            if balance > 0:
                logger.warning(f"Address {ton_address} already has {balance} tokens")
                status_message.edit_text(config.ERROR_HAS_TOKENS)
                return
            
            # Шаг 5.5: Проверка баланса кошелька-отправителя
            logger.info("Checking sender wallet balance...")
            sender_check, sender_balance, sender_error = self.ton_utils.check_sender_balance()
            
            #if not sender_check:
            #    logger.error(f"Error checking sender balance: {sender_error}")
            #    status_message.edit_text(config.ERROR_API_UNAVAILABLE)
            #    return
            
            # Проверка что на кошельке-отправителе достаточно токенов
            #if sender_balance < config.MIN_SENDER_BALANCE:
            #    logger.warning(f"Sender wallet balance too low: {sender_balance} < {config.MIN_SENDER_BALANCE}")
            #    status_message.edit_text(config.ERROR_FAUCET_EMPTY)
                
                # Записываем неудачную попытку в БД
             #   self.database.add_request(
              #      user_id=user_id,
               #     username=username,
              #      ton_address=ton_address,
              #      tokens_amount=config.TOKENS_AMOUNT,
              #      success=False,
              #      error_message="Faucet is empty"
              #  )
              #  return
            
            logger.info(f"Sender wallet balance: {sender_balance} tokens")
            
            # Шаг 6: Отправка токенов
            status_message.edit_text("🚀 Sending tokens...")
            
            send_success, tx_hash, send_error = self.ton_utils.send_jettons(
                ton_address,
                config.TOKENS_AMOUNT
            )
            
            if not send_success:
                logger.error(f"Error sending tokens: {send_error}")
                status_message.edit_text(config.ERROR_SENDING_FAILED)
                
                # Записываем неудачную попытку в БД
                self.database.add_request(
                    user_id=user_id,
                    username=username,
                    ton_address=ton_address,
                    tokens_amount=config.TOKENS_AMOUNT,
                    success=False,
                    error_message=send_error
                )
                return
            
            # Шаг 7: Успешная отправка
            logger.info(f"Successfully sent {config.TOKENS_AMOUNT} tokens to {ton_address}, tx: {tx_hash}")
            
            # Записываем успешную транзакцию в БД
            self.database.add_request(
                user_id=user_id,
                username=username,
                ton_address=ton_address,
                tokens_amount=config.TOKENS_AMOUNT,
                success=True,
                tx_hash=tx_hash
            )
            
            # Обновляем количество оставшихся запросов
            _, remaining = self.database.can_request_tokens(user_id)
            
            # Отправка сообщения об успехе
            status_message.edit_text(
                config.SUCCESS_MESSAGE.format(
                    config.TOKENS_AMOUNT,
                    ton_address,
                    tx_hash,
                    remaining,
                    config.MAX_REQUESTS_PER_DAY
                ),
                parse_mode=None
            )
            
        finally:
            # Освобождаем блокировку в любом случае
            self.processing_lock.release()
            logger.info("Processing lock released")
    
    def stats_command(self, update: Update, context: CallbackContext):
        """
        Обработчик команды /stats
        Показывает общую статистику бота
        """
        user = update.effective_user
        logger.info(f"User {user.id} requested stats")
        
        # Получаем статистику из БД
        stats = self.database.get_total_statistics()
        
        # Получаем персональную статистику пользователя
        requests_today = self.database.get_user_requests_today(user.id)
        can_request, remaining = self.database.can_request_tokens(user.id)
        
        stats_message = f"""
📊 Chamby Faucet Bot Statistics

🌐 Global Statistics:
• Total tokens distributed: {stats['total_tokens']:,} CHAMBY
• Successful transactions: {stats['total_successful']:,}
• Unique users: {stats['unique_users']:,}
• Unique addresses: {stats['unique_addresses']:,}

👤 Your Statistics:
• Requests today: {requests_today} of {config.MAX_REQUESTS_PER_DAY}
• Remaining requests: {remaining}

💎 Token: Chamby (CHAMBY)
📝 Contract: {config.CHAMBY_JETTON_CONTRACT[:20]}...
        """
        
        update.message.reply_text(stats_message)
    
    def error_handler(self, update: Update, context: CallbackContext):
        """Обработчик ошибок"""
        logger.error(f"Update {update} caused error {context.error}")
        
        if update and update.effective_message:
            update.effective_message.reply_text(
                "❌ An error occurred. Please try again later."
            )
    
    def run(self):
        """Запуск бота"""
        logger.info("Starting Chamby Faucet Bot...")
        
        # Добавляем обработчик ошибок
        self.dispatcher.add_error_handler(self.error_handler)
        
        # Запускаем бота
        self.updater.start_polling()
        logger.info("Bot is running! Press Ctrl+C to stop.")
        
        # Ожидание остановки
        self.updater.idle()


def main():
    """Точка входа в программу"""
    # Проверка конфигурации
    if config.TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("Please set TELEGRAM_BOT_TOKEN in config.py")
        print("\n❌ ERROR: Bot token is not set!")
        print("1. Get a token from @BotFather in Telegram")
        print("2. Open config.py")
        print("3. Replace YOUR_BOT_TOKEN_HERE with your token")
        return
    
    if config.SENDER_WALLET_ADDRESS == "YOUR_WALLET_ADDRESS_HERE":
        logger.warning("SENDER_WALLET_ADDRESS not set - bot will work in demo mode")
        print("\n⚠️ WARNING: Bot is running in DEMO mode!")
        print("Tokens will not be sent for real.")
        print("Configure SENDER_WALLET_ADDRESS and SENDER_WALLET_SEED in config.py")
        print("for real operation.\n")
    
    # Создание и запуск бота
    bot = ChambyFaucetBot()
    bot.run()


if __name__ == '__main__':
    main()
