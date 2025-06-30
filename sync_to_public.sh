#!/bin/bash

# Скрипт для синхронизации Bitget API с отдельным публичным репозиторием
# Использование: ./sync_to_public.sh

set -e

echo "🔄 Синхронизация Bitget API с публичным репозиторием..."

# Проверяем есть ли изменения
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "📝 Обнаружены изменения в репозитории"
    
    # Добавляем все изменения (config.json и личные скрипты исключены через .gitignore)
    git add .
    
    # Коммитим с текущей датой
    COMMIT_MSG="Update: $(date '+%Y-%m-%d %H:%M:%S')"
    git commit -m "$COMMIT_MSG"
    
    echo "✅ Изменения закоммичены: $COMMIT_MSG"
else
    echo "ℹ️  Нет изменений для коммита"
fi

# Пушим в публичный репозиторий
echo "🚀 Отправляем изменения в публичный репозиторий..."
git push origin main

echo "✅ Синхронизация завершена!"
echo "🔗 Публичный репозиторий: https://github.com/trueamperror/bitget-api"
echo ""
echo "⚠️  Убедитесь, что ваши API ключи остаются только в локальном config.json"
