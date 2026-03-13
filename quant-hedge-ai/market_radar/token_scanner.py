"""Token Scanner — detects new tokens and scores them for trading viability."""

from __future__ import annotations

import logging
import os
import random
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class TokenInfo:
    """Represents a discovered token with scoring metadata."""

    symbol: str
    name: str
    platform: str
    liquidity_usd: float = 0.0
    volume_24h_usd: float = 0.0
    price_usd: float = 0.0
    holder_count: int = 0
    whale_holders: int = 0
    age_seconds: int = 0
    market_cap_usd: float = 0.0
    score: float = 0.0
    flags: list[str] = field(default_factory=list)


class TokenScanner:
    """Scans multiple DEX platforms for new token opportunities.

    In simulation mode (default), generates synthetic token data.
    When API keys are configured, connects to real data sources.
    """

    PLATFORMS = [
        "pumpfun",
        "dexscreener",
        "birdeye",
        "geckoterminal",
        "raydium",
        "jupiter",
    ]

    def __init__(
        self,
        min_liquidity_usd: float = 1_000.0,
        min_volume_usd: float = 500.0,
        max_token_age_s: int = 3600,
        platforms: list[str] | None = None,
    ) -> None:
        self.min_liquidity_usd = min_liquidity_usd
        self.min_volume_usd = min_volume_usd
        self.max_token_age_s = max_token_age_s
        self.platforms = platforms or self.PLATFORMS
        self._use_live = bool(os.environ.get("RADAR_LIVE_MODE"))

    def scan(self) -> list[TokenInfo]:
        """Scan all platforms and return discovered tokens."""
        all_tokens: list[TokenInfo] = []
        for platform in self.platforms:
            tokens = self._scan_platform(platform)
            all_tokens.extend(tokens)
        logger.info("TokenScanner: found %d raw tokens across %d platforms", len(all_tokens), len(self.platforms))
        return all_tokens

    def filter_tokens(self, tokens: list[TokenInfo]) -> list[TokenInfo]:
        """Filter tokens by minimum thresholds."""
        filtered = [
            t
            for t in tokens
            if t.liquidity_usd >= self.min_liquidity_usd
            and t.volume_24h_usd >= self.min_volume_usd
            and t.age_seconds <= self.max_token_age_s
        ]
        logger.info("TokenScanner: %d tokens passed filters (from %d)", len(filtered), len(tokens))
        return filtered

    def score_token(self, token: TokenInfo) -> float:
        """Score a token from 0-10 based on trading viability.

        Factors: liquidity, volume, holder count, whale presence, age.
        """
        score = 0.0

        # Liquidity score (0-3)
        if token.liquidity_usd >= 50_000:
            score += 3.0
        elif token.liquidity_usd >= 10_000:
            score += 2.0
        elif token.liquidity_usd >= 1_000:
            score += 1.0

        # Volume score (0-2)
        if token.volume_24h_usd >= 100_000:
            score += 2.0
        elif token.volume_24h_usd >= 10_000:
            score += 1.5
        elif token.volume_24h_usd >= 1_000:
            score += 0.5

        # Holder diversity (0-2)
        if token.holder_count >= 500:
            score += 2.0
        elif token.holder_count >= 100:
            score += 1.0
        elif token.holder_count >= 20:
            score += 0.5

        # Whale interest (0-2)
        if token.whale_holders >= 3:
            score += 2.0
        elif token.whale_holders >= 1:
            score += 1.0

        # Freshness bonus (0-1)
        if token.age_seconds <= 300:
            score += 1.0
        elif token.age_seconds <= 900:
            score += 0.5

        token.score = min(10.0, score)
        return token.score

    def score_all(self, tokens: list[TokenInfo]) -> list[TokenInfo]:
        """Score and sort tokens by score descending."""
        for t in tokens:
            self.score_token(t)
        tokens.sort(key=lambda t: t.score, reverse=True)
        return tokens

    # ------------------------------------------------------------------
    # Platform scanning (simulation / future live)
    # ------------------------------------------------------------------

    def _scan_platform(self, platform: str) -> list[TokenInfo]:
        """Scan a single platform. Returns synthetic data in simulation mode."""
        if self._use_live:
            return self._scan_platform_live(platform)
        return self._scan_platform_simulated(platform)

    def _scan_platform_simulated(self, platform: str) -> list[TokenInfo]:
        """Generate synthetic tokens for paper trading and development."""
        names = [
            ("MEMEAI", "MemeAI Token"),
            ("PEPE2", "Pepe 2.0"),
            ("WOJAK", "Wojak Finance"),
            ("DOGE10", "Doge 10X"),
            ("AIBOT", "AI Bot Token"),
            ("MOONX", "MoonX"),
            ("SOLCAT", "Solana Cat"),
            ("BONK2", "Bonk 2.0"),
        ]
        tokens = []
        count = random.randint(2, 5)
        for _ in range(count):
            sym, name = random.choice(names)
            tokens.append(
                TokenInfo(
                    symbol=f"{sym}_{platform[:4].upper()}",
                    name=name,
                    platform=platform,
                    liquidity_usd=random.uniform(500, 200_000),
                    volume_24h_usd=random.uniform(100, 500_000),
                    price_usd=random.uniform(0.00001, 5.0),
                    holder_count=random.randint(5, 2000),
                    whale_holders=random.randint(0, 5),
                    age_seconds=random.randint(30, 7200),
                    market_cap_usd=random.uniform(1_000, 10_000_000),
                )
            )
        return tokens

    def _scan_platform_live(self, platform: str) -> list[TokenInfo]:
        """Placeholder for real API integration. Falls back to simulation."""
        logger.warning("Live scanning for %s not yet implemented — using simulation", platform)
        return self._scan_platform_simulated(platform)
