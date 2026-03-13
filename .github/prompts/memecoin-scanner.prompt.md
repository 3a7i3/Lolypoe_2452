---
description: "Scaffold a memecoin scanner module for a specific DEX platform (Pump.fun, DexScreener, Birdeye, GeckoTerminal, Raydium, Jupiter). Generates scanner class with API integration, token filtering, and Bot Doctor validation hooks."
agent: "hedge-fund-architect"
tools: [read, edit, search, execute]
argument-hint: "Platform name (e.g. DexScreener, Pump.fun, Birdeye)"
---

# Scaffold Memecoin Scanner

Create a scanner module for the platform: **{{platform}}**

## Requirements

1. **Search first** — Check `quant-hedge-ai/agents/market/` and `crypto_quant_v16/core/market_scanner.py` for existing scanner patterns to follow.

2. **Scanner class** — Create under `quant-hedge-ai/market_discovery/` with:
   - `scan()` method that discovers new tokens from the platform API
   - `filter_tokens()` with configurable thresholds (min liquidity, min volume, max age)
   - `score_token()` returning a 0-10 risk/opportunity score based on liquidity, volume, holder count, whale presence
   - Async-ready design using `aiohttp` or `httpx`

3. **Bot Doctor integration** — Every token must pass validation before being forwarded:
   ```python
   from crypto_quant_v16.v26.bot_doctor import run_bot_doctor
   ```

4. **Safety defaults**:
   - Paper trading mode only
   - Rate limiting on API calls (1 req/sec default)
   - No hardcoded API keys — use environment variables
   - Timeout on all HTTP requests (10s default)

5. **Test file** — Create a matching test file with:
   - Mock API responses (no real network calls in tests)
   - Token filtering edge cases
   - Score calculation validation

## Output Structure

```
quant-hedge-ai/market_discovery/
├── __init__.py
├── {{platform_snake}}_scanner.py
└── test_{{platform_snake}}_scanner.py
```

## Platforms Reference

| Platform | Focus | Typical API |
|----------|-------|-------------|
| Pump.fun | Solana memecoin launches | WebSocket + REST |
| DexScreener | Multi-chain DEX analytics | REST v1 |
| Birdeye | Solana token analytics | REST + WebSocket |
| GeckoTerminal | Multi-chain pool data | REST v2 |
| Raydium | Solana AMM pools | On-chain + REST |
| Jupiter | Solana aggregator | REST v6 |
