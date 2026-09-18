"""
Recommendation Models for Strategist Agent
"""
from typing import List, Dict, Optional, Any, Literal
from pydantic import BaseModel, Field
from src.models.audit_models import VisibilityScores


class RecommendationItem(BaseModel):
    id: str
    pillar: Literal["content", "technical", "semantic", "authority"]
    priority: Literal["high", "medium", "low"]
    category: Literal["seo", "aeo", "geo", "aio", "cross-cutting"]
    title: str
    rationale: str
    implementation_steps: List[str] = Field(default_factory=list)
    expected_impact: str
    target_keywords: Optional[List[str]] = Field(default_factory=list)
    technical_specs: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ActionPlan(BaseModel):
    target: str
    created_at: str
    current_scores: VisibilityScores
    target_scores: VisibilityScores
    strategic_summary: str
    recommendations: List[RecommendationItem] = Field(default_factory=list)
    keyword_opportunities: List[str] = Field(default_factory=list)
    schema_requirements: List[str] = Field(default_factory=list)

    def get_by_priority(self, priority: str) -> List[RecommendationItem]:
        return [r for r in self.recommendations if r.priority == priority]

    def get_by_pillar(self, pillar: str) -> List[RecommendationItem]:
        return [r for r in self.recommendations if r.pillar == pillar]
