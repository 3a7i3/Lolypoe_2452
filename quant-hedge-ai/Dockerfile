# ──────────────────────────────────────────────
# quant-hedge-ai — Dockerfile
# Image multi-stage : build léger + runtime slim
# ──────────────────────────────────────────────

# ── Étape 1 : builder ──────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Dépendances système minimales pour compiler les wheels C
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Étape 2 : runtime ──────────────────────────
FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.title="quant-hedge-ai"
LABEL org.opencontainers.image.description="V9.1 Autonomous Quant Lab — AI Portfolio Brain"
LABEL org.opencontainers.image.version="9.1"

# Copier les packages compilés
COPY --from=builder /install /usr/local

WORKDIR /app

# Copier le code source
COPY . .

# Créer les dossiers attendus au runtime
RUN mkdir -p databases/ai_evolution reports data logs

# Variables d'environnement par défaut (remplacées via docker-compose ou -e)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    V9_MAX_CYCLES=0 \
    V9_POPULATION_SIZE=300 \
    V9_SLEEP_SECONDS=60 \
    V9_CCXT_SYMBOLS="BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT" \
    V9_CCXT_TIMEFRAME="1h" \
    V9_CCXT_HISTORY_LIMIT=200 \
    V9_CCXT_EXCHANGES="binance,kraken,okx" \
    V9_TELEGRAM_BOT_TOKEN="" \
    V9_TELEGRAM_CHAT_ID=""

# Port du dashboard Panel (si activé)
EXPOSE 5013

# Point d'entrée par défaut : boucle autonome infinie
CMD ["python", "main_v91.py"]
