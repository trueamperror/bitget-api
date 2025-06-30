#!/bin/bash

# Скрипт для синхронизации Bitget API с отдельным публичным репозиторием
# Использование: ./sync_bitget.sh

set -e

BITGET_DIR="/Users/timurbogatyrev/Documents/VS Code/Algo/ExchangeAPI/Bitget"
MAIN_REPO_DIR="/Users/timurbogatyrev/Documents/VS Code/Algo"

echo "🔄 Синхронизация Bitget API репозитория..."

# Переходим в папку Bitget
cd "$BITGET_DIR"

# Проверяем есть ли изменения
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "📝 Обнаружены изменения в Bitget репозитории"
    
    # Добавляем все изменения (кроме config.json - он в .gitignore)
    git add .
    
    # Коммитим с текущей датой
    COMMIT_MSG="Update: $(date '+%Y-%m-%d %H:%M:%S')"
    git commit -m "$COMMIT_MSG"
    
    echo "✅ Изменения закоммичены: $COMMIT_MSG"
else
    echo "ℹ️  Нет изменений для коммита в Bitget репозитории"
fi

# Пушим в публичный репозиторий
echo "🚀 Отправляем изменения в публичный репозиторий..."
git push origin main

echo "✅ Синхронизация завершена!"
echo "🔗 Публичный репозиторий: https://github.com/trueamperror/bitget-api"
