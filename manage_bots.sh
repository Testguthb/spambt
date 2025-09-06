#!/bin/bash

# Скрипт для управління п'ятьма екземплярами Telegram бота

case "$1" in
    start)
        echo "🚀 Запускаю всі боти..."
        pm2 start ecosystem.config.js
        echo "✅ Боти запущені!"
        pm2 status
        ;;
    stop)
        echo "🛑 Зупиняю всі боти..."
        pm2 stop bot1 bot2 bot3 bot4 bot5
        echo "✅ Боти зупинені!"
        ;;
    restart)
        echo "🔄 Перезапускаю всі боти..."
        pm2 restart bot1 bot2 bot3 bot4 bot5
        echo "✅ Боти перезапущені!"
        ;;
    status)
        echo "📊 Статус ботів:"
        pm2 status
        ;;
    logs)
        if [ -z "$2" ]; then
            echo "📜 Показую логи всіх ботів:"
            pm2 logs
        else
            echo "📜 Показую логи бота $2:"
            pm2 logs "$2"
        fi
        ;;
    logs-follow)
        if [ -z "$2" ]; then
            echo "📜 Слідкую за логами всіх ботів:"
            pm2 logs --lines 50
        else
            echo "📜 Слідкую за логами бота $2:"
            pm2 logs "$2" --lines 50
        fi
        ;;
    monit)
        echo "📈 Відкриваю моніторинг PM2:"
        pm2 monit
        ;;
    setup)
        echo "⚙️ Налаштовую конфігураційні файли..."
        
        for i in {1..5}; do
            if [ ! -f ".env.bot$i" ]; then
                echo "📝 Створюю .env.bot$i..."
                cat > .env.bot$i << EOF
# Конфигурация для экземпляра бота $i
API_ID=your_api_id_$i
API_HASH=your_api_hash_$i
BOT_TOKEN=your_bot_token_$i
ADMIN_ID_LIST=your_admin_ids
DATABASE_NAME=sessions_bot$i.db
BOT_NAME=bot$i
EOF
                echo "✅ Файл .env.bot$i створено. Відредагуйте його з вашими даними!"
            else
                echo "⚠️ Файл .env.bot$i вже існує"
            fi
        done
        
        echo ""
        echo "📋 Не забудьте відредагувати файли .env.bot1 - .env.bot5 з вашими даними:"
        echo "   - API_ID та API_HASH отримайте з https://my.telegram.org"
        echo "   - BOT_TOKEN отримайте від @BotFather"
        echo "   - ADMIN_ID_LIST - ваші Telegram ID через кому"
        ;;
    start-bot)
        if [ -z "$2" ]; then
            echo "❌ Потрібно вказати номер бота (1-5)"
            echo "Приклад: $0 start-bot 1"
        else
            echo "🚀 Запускаю бота $2..."
            pm2 start bot$2
            echo "✅ Бот $2 запущений!"
        fi
        ;;
    stop-bot)
        if [ -z "$2" ]; then
            echo "❌ Потрібно вказати номер бота (1-5)"
            echo "Приклад: $0 stop-bot 1"
        else
            echo "🛑 Зупиняю бота $2..."
            pm2 stop bot$2
            echo "✅ Бот $2 зупинений!"
        fi
        ;;
    restart-bot)
        if [ -z "$2" ]; then
            echo "❌ Потрібно вказати номер бота (1-5)"
            echo "Приклад: $0 restart-bot 1"
        else
            echo "🔄 Перезапускаю бота $2..."
            pm2 restart bot$2
            echo "✅ Бот $2 перезапущений!"
        fi
        ;;
    *)
        echo "🤖 Управління п'ятьма екземплярами Telegram бота"
        echo ""
        echo "Використання: $0 {start|stop|restart|status|logs|logs-follow|monit|setup|start-bot|stop-bot|restart-bot}"
        echo ""
        echo "Команди для всіх ботів:"
        echo "  start        - Запустити всі боти"
        echo "  stop         - Зупинити всі боти"
        echo "  restart      - Перезапустити всі боти"
        echo "  status       - Показати статус ботів"
        echo "  logs [bot]   - Показати логи (bot1-bot5 або всі)"
        echo "  logs-follow [bot] - Слідкувати за логами в реальному часі"
        echo "  monit        - Відкрити PM2 монітор"
        echo "  setup        - Створити конфігураційні файли"
        echo ""
        echo "Команди для окремих ботів:"
        echo "  start-bot N  - Запустити бота N (1-5)"
        echo "  stop-bot N   - Зупинити бота N (1-5)"
        echo "  restart-bot N - Перезапустити бота N (1-5)"
        echo ""
        echo "Приклади:"
        echo "  $0 start                 # Запустити всі боти"
        echo "  $0 logs bot1            # Показати логи першого бота"
        echo "  $0 logs-follow bot2     # Слідкувати за логами другого бота"
        echo "  $0 start-bot 3          # Запустити тільки третій бот"
        echo "  $0 setup                # Створити .env файли"
        ;;
esac