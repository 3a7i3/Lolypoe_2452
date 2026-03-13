MAX_DRAWDOWN = 0.20


def check_risk(drawdown: float) -> str:
    if drawdown > MAX_DRAWDOWN:
        return "STOP_TRADING"
    return "OK"
