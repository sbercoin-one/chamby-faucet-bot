# -*- coding: utf-8 -*-
"""
Файл конфигурации Telegram бота для раздачи токенов Chamby
ВЕРСИЯ С ПОДДЕРЖКОЙ .env ФАЙЛА ДЛЯ БЕЗОПАСНОСТИ
"""

from dotenv import load_dotenv
import os

# Загружаем переменные из .env файла (если существует)
load_dotenv()

# ======= НАСТРОЙКИ TELEGRAM БОТА =======
# Получите токен у @BotFather в Telegram
# Рекомендуется хранить в .env файле
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', "YOUR_BOT_TOKEN_HERE")

# ======= НАСТРОЙКИ TON БЛОКЧЕЙНА =======
# Адрес контракта Chamby Jetton
CHAMBY_JETTON_CONTRACT = os.getenv(
    'CHAMBY_JETTON_CONTRACT',
    "EQBajWYb-dNy0skElmij1onJjXk_ONCx_N1xBOyTaPaRvQ5r"
)

# Адрес вашего кошелька-отправителя (откуда будут раздаваться токены)
# ВАЖНО: Используйте отдельный кошелек только для раздачи!
SENDER_WALLET_ADDRESS = os.getenv('SENDER_WALLET_ADDRESS', "YOUR_WALLET_ADDRESS_HERE")

# Seed фраза (24 слова через пробел) или приватный ключ отправителя
# КРИТИЧНО: ХРАНИТЕ В БЕЗОПАСНОСТИ! Используйте .env файл!
SENDER_WALLET_SEED = os.getenv('SENDER_WALLET_SEED', "YOUR_WALLET_SEED_PHRASE_HERE")

# Количество токенов для раздачи (10000 токенов)
TOKENS_AMOUNT = int(os.getenv('TOKENS_AMOUNT', 10000))

# Минимальный баланс токенов на кошельке-отправителе (для проверки)
# Если баланс меньше этого значения, выдача прекращается
MIN_SENDER_BALANCE = int(os.getenv('MIN_SENDER_BALANCE', 10000))

# ======= НАСТРОЙКИ ЛИМИТОВ =======
# Максимальное количество выдач токенов на пользователя в сутки
MAX_REQUESTS_PER_DAY = int(os.getenv('MAX_REQUESTS_PER_DAY', 3))

# ======= НАСТРОЙКИ TON API =======
# TON API endpoints (используем toncenter)
TON_API_BASE_URL = os.getenv('TON_API_BASE_URL', "https://toncenter.com/api/v2")
TON_API_KEY = os.getenv('TON_API_KEY', "")  # Опционально, для увеличения лимита запросов

# Альтернативный API (tonapi.io)
TONAPI_BASE_URL = os.getenv('TONAPI_BASE_URL', "https://tonapi.io/v2")
# TONAPI_KEY = os.getenv('TONAPI_KEY', "")  # Получите на https://tonapi.io
TON_API_KEY = os.getenv('TON_API_KEY', "")

# ======= НАСТРОЙКИ БАЗЫ ДАННЫХ =======
DATABASE_NAME = os.getenv('DATABASE_NAME', "faucet_bot.db")

# ======= ТЕКСТОВЫЕ СООБЩЕНИЯ =======
WELCOME_MESSAGE = """
🎉 Welcome to Chamby Faucet Bot!

📋 Token Distribution Rules:

✅ Each user can receive tokens up to 3 times per day
✅ You get 10,000 CHAMBY tokens per request
✅ TON address must be valid
✅ Address must NOT have Chamby tokens (balance = 0)

🚀 How to get tokens:
Use the command: /get_chamby <your_TON_address>

Example:
/get_chamby EQDtFpEwcFAEcRe5mLVh2N6C0x-_hJEM7W61_JLnSF74p4q2

⚠️ Important: Address must start with EQ or UQ
"""

ERROR_INVALID_ADDRESS = "❌ Invalid TON address format. Address must start with EQ or UQ and contain 48 characters."
ERROR_HAS_TOKENS = "❌ This address already has Chamby tokens. Tokens are only distributed to new addresses."
ERROR_LIMIT_REACHED = "❌ You have reached your daily limit ({} of {}). Please try again tomorrow."
ERROR_SENDING_FAILED = "❌ Error sending tokens. Please try again later."
ERROR_API_UNAVAILABLE = "❌ Service temporarily unavailable. Please try again later."
ERROR_BOT_BUSY = "⏳ Bot is currently processing another request. Please wait 10 seconds and try again."
ERROR_FAUCET_EMPTY = "❌ Faucet is empty! Free Chamby tokens have run out. Please contact the administrator to refill the faucet."

SUCCESS_MESSAGE = """
✅ Success!

Sent: {} CHAMBY tokens
To address: {}
Check: {}

Tokens will appear in your wallet soon!
Remaining requests today: {} of {}
"""

# ======= РЕЖИМ РАБОТЫ =======
# Автоматически определяется: если SENDER_WALLET_ADDRESS настроен, то реальный режим
IS_REAL_MODE = SENDER_WALLET_ADDRESS != "YOUR_WALLET_ADDRESS_HERE"

# Вывод режима работы при импорте (для отладки)
if __name__ != '__main__':
    if IS_REAL_MODE:
        print("⚙️  Конфигурация: РЕАЛЬНЫЙ РЕЖИМ отправки токенов")
    else:
        print("⚙️  Конфигурация: ДЕМО РЕЖИМ (токены не отправляются)")
        
# ============== SIGNING SERVICE ==============
# URL вашего VPS с signing-service
SIGNING_SERVICE_URL = os.getenv('SIGNING_SERVICE_URL', "http://localhost:5000")

# API ключ для signing-service
SIGNING_SERVICE_API_KEY = os.getenv('SIGNING_SERVICE_API_KEY', "")
# =============================================
