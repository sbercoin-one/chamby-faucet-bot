# Chamby Faucet Bot

Telegram-бот для раздачи токенов **Chamby (CHAMBY)** в сети TON.

## Архитектура

Проект состоит из двух частей:

1. **Telegram Bot** (Python) — принимает запросы от пользователей, проверяет лимиты и балансы, отправляет команды на подписание транзакций.
2. **Signing Service** (Node.js) — отдельный сервис на VPS, который хранит приватный ключ и подписывает транзакции отправки токенов.

## Установка

### 1. Telegram Bot

```bash
# Клонируйте репозиторий
git clone https://github.com/sbercoin-one/chamby-faucet-bot.git
cd chamby-faucet-bot

# Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или: venv\Scripts\activate  # Windows

# Установите зависимости
pip install -r requirements.txt

# Скопируйте и заполните конфигурацию
cp .env.example .env
# Отредактируйте .env — заполните все необходимые значения

# Запустите бота
python bot.py
```

### 2. Signing Service

```bash
cd signing-service

# Скопируйте и заполните конфигурацию
cp .env.example .env
# Отредактируйте .env

# Запуск через Docker
docker-compose up -d

# Или без Docker
npm install
node signing_service.js
```

## Конфигурация

Все секреты хранятся в файле `.env` (не коммитится в git). Пример — в `.env.example`.

| Переменная | Описание |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Токен бота от @BotFather |
| `SENDER_WALLET_ADDRESS` | TON-адрес кошелька-отправителя |
| `SENDER_WALLET_SEED` | Seed-фраза кошелька (24 слова) |
| `SIGNING_SERVICE_URL` | URL signing-service (например `http://your-vps-ip:5000`) |
| `SIGNING_SERVICE_API_KEY` | API-ключ для авторизации в signing-service |
| `TON_API_KEY` | Ключ от toncenter.com API |

## Команды бота

- `/start` — приветствие и правила
- `/get_chamby <TON_address>` — получить токены
- `/stats` — статистика бота

## Signing Service

Отдельный Node.js-сервис, который хранит приватный ключ кошелька и подписывает транзакции отправки Jetton-токенов. Разворачивается на отдельном VPS для безопасности — seed-фраза никогда не покидает сервер.

**Стек:** Express.js, tonweb, tonweb-mnemonic

**API эндпоинты:**

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/health` | Проверка работоспособности сервиса |
| `POST` | `/api/v1/send_tokens` | Отправка Jetton-токенов (требует `X-API-Key`) |
| `GET` | `/api/v1/balance` | Баланс TON на кошельке-отправителе (требует `X-API-Key`) |

**Конфигурация signing-service** (файл `signing-service/.env`):

| Переменная | Описание |
|---|---|
| `API_SECRET_KEY` | Секретный ключ для авторизации запросов от бота |
| `SENDER_WALLET_SEED` | Seed-фраза кошелька (24 слова) |
| `CHAMBY_JETTON_CONTRACT` | Адрес контракта Chamby Jetton |
| `TONCENTER_API_KEY` | Ключ от toncenter.com API |
| `MAX_AMOUNT_PER_TX` | Максимум токенов за одну транзакцию (по умолчанию 100000) |
| `RATE_LIMIT_PER_MINUTE` | Лимит запросов в минуту (по умолчанию 10) |

**Запуск через Docker:**

```bash
cd signing-service
cp .env.example .env
# Заполните .env
docker-compose up -d
```

## Правила раздачи

- До 3 запросов в сутки на пользователя
- 10 000 CHAMBY за запрос
- Адрес должен быть валидным (EQ/UQ)
- На адресе не должно быть токенов CHAMBY (баланс = 0)
