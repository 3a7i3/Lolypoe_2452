# QUANT_CORE Architecture

This module is the central hub for research-driven quant trading. It orchestrates:
- Data collection
- Feature engineering
- Massive backtesting
- Risk management
- Portfolio allocation
- Strategy validation

Secondary layers (dashboards, agents, Telegram, etc.) interface via QUANT_CORE/interfaces.

All strategies must pass backtesting and Bot Doctor validation before execution.

## Directory Structure
- data/: Data collection and ingestion
- features/: Feature engineering
- backtesting/: Backtesting pipeline
- risk/: Risk management
- portfolio/: Portfolio allocation
- strategy/: Strategy generation and selection
- validation/: Strategy validation (Bot Doctor integration)
- interfaces/: Connectors for dashboards, agents, Telegram, etc.
