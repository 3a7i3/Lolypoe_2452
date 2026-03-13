from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass
class PaperInsight:
    title: str
    novelty_score: float
    relevance_score: float


class PaperAnalyzer:
    """Scores strategy ideas extracted from papers or notes."""

    def analyze(self, papers: Iterable[dict]) -> List[PaperInsight]:
        insights: List[PaperInsight] = []
        for item in papers:
            title = str(item.get("title", "untitled"))
            novelty = float(item.get("novelty", 0.5))
            relevance = float(item.get("relevance", 0.5))
            insights.append(PaperInsight(title=title, novelty_score=novelty, relevance_score=relevance))
        return sorted(insights, key=lambda x: (x.relevance_score, x.novelty_score), reverse=True)
