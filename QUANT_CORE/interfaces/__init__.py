# QUANT_CORE Interfaces

This module connects secondary layers (dashboards, agents, Telegram, etc.) to QUANT_CORE.

## Responsibilities
- Provide APIs and connectors for external modules
- Route strategy execution requests through QUANT_CORE
- Ensure all strategies are validated and backtested

## Entry Point
Implement `CoreInterface` class with connector methods.
