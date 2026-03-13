description: "Use when writing or modifying Bot Doctor modules, risk validation logic, trade safety checks, or health scoring systems. Ensures all trading modules integrate proper risk validation before execution."
applyTo: "**/bot_doctor*, **/prompt_doctor*, **/risk_validator*, **/risk_engine*"

# Bot Doctor — Risk Validation Standards

## Validation Rules

- Every trade execution path MUST call Bot Doctor validation before placing orders
- A blocked trade must log the reason and never silently proceed
- Health scores use 0-100 scale: >=80 healthy, 50-79 warning, <50 critical
- Findings must include: severity (info/warning/critical), component name, issue description, and recommendation

## Integration Pattern

All trading modules must follow this pattern:

```python
def execute_trade(self, token, metrics):
    doctor_result = run_bot_doctor(metrics)
    if doctor_result["health_score"] < 50:
        logger.warning(f"Trade blocked: {doctor_result['top_recommendation']}")
        return None
    return self._place_order(token)
```

## Safety Thresholds (defaults)

| Metric | Warning | Critical |
|--------|---------|----------|
| decision_conf | < 0.6 | < 0.3 |
| drawdown | > 5% | > 10% |
| spread | > 0.5% | > 1.0% |
| feed_age_s | > 30s | > 60s |
| regime_conf | < 0.5 | < 0.3 |

## Correction Patterns

When auto-healing invalid fields (as in `prompt_doctor_agent.py`):
- `trade_signal` → must be one of: BUY, SELL, HOLD
- `allocation` → clamp to 0.0–1.0 range
- `risk_level` → must be one of: low, medium, high
- Log every correction with before/after values

## Testing Requirements

- Test with edge-case metrics (zero values, negative values, missing keys)
- Test that trades are actually blocked when health_score < 50
- Test correction logic with invalid input combinations
- Never make real API or exchange calls in tests — use mock data
