"""
Audit Models for Website Visibility (SEO, AEO, GEO, AIO)
"""
from typing import List, Dict, Optional, Any, Literal
from pydantic import BaseModel, Field


class Finding(BaseModel):
    category: Literal["seo", "aeo", "geo", "aio"]
    name: str
    severity: Literal["critical", "warning", "info", "pass"]
    description: str
    recommendation_hint: Optional[str] = None
    score_impact: int = 0
    raw_data: Optional[Dict[str, Any]] = None


class VisibilityScores(BaseModel):
    overall: float = Field(..., ge=0, le=100, description="Weighted average overall visibility score")
    seo: float = Field(..., ge=0, le=100, description="Traditional Search Engine Optimization score")
    aeo: float = Field(..., ge=0, le=100, description="Answer Engine Optimization score (direct answers, voice, featured snippets)")
    geo: float = Field(..., ge=0, le=100, description="Generative Engine Optimization score (E-E-A-T, sources, statistics)")
    aio: float = Field(..., ge=0, le=100, description="AI Overview Optimization score (structured schema, llms.txt, key takeaways)")


class PageMetadata(BaseModel):
    url_or_path: str
    title: Optional[str] = None
    meta_description: Optional[str] = None
    canonical_url: Optional[str] = None
    open_graph: Dict[str, str] = Field(default_factory=dict)
    headings: Dict[str, List[str]] = Field(default_factory=dict)
    word_count: int = 0
    has_json_ld: bool = False
    json_ld_types: List[str] = Field(default_factory=list)
    has_llms_txt: bool = False
    has_faq_structure: bool = False
    has_direct_definitions: bool = False
    has_statistics_or_quotes: bool = False
    has_author_byline: bool = False
    has_table_or_summary: bool = False


class AuditReport(BaseModel):
    target: str
    timestamp: str
    metadata: PageMetadata
    scores: VisibilityScores
    findings: List[Finding] = Field(default_factory=list)
    summary: str

    def get_findings_by_severity(self, severity: str) -> List[Finding]:
        return [f for f in self.findings if f.severity == severity]

    def get_findings_by_category(self, category: str) -> List[Finding]:
        return [f for f in self.findings if f.category == category]
