"""
Strategist Agent: Analyzes visibility audit findings and generates prioritized recommendations.
"""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from src.agents.base_agent import BaseAgent
from src.models.audit_models import AuditReport, VisibilityScores
from src.models.recommendation_models import ActionPlan, RecommendationItem


class StrategistAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="StrategistAgent", role="Visibility & Optimization Strategist")

    def run(self, audit_report: AuditReport) -> ActionPlan:
        """
        Analyzes the audit report and generates an actionable, prioritized optimization plan.
        """
        self.log(f"Formulating optimization strategy for: {audit_report.target}")

        recommendations: List[RecommendationItem] = []
        rec_counter = 1

        # 1. Technical & AIO Schema Recommendations
        missing_schema_findings = [f for f in audit_report.findings if "JSON-LD" in f.name and f.severity in ["critical", "warning"]]
        if missing_schema_findings:
            recommendations.append(RecommendationItem(
                id=f"REC-{rec_counter:02d}",
                pillar="technical",
                priority="high",
                category="aio",
                title="Deploy JSON-LD Structured Data (FAQPage & Organization)",
                rationale="AI Overviews and generative search models require machine-readable schema to ingest entity data with high confidence.",
                implementation_steps=[
                    "Generate and insert Schema.org JSON-LD script into the <head> of the document.",
                    "Include Organization schema with name, URL, logo, and social profiles.",
                    "Include FAQPage schema mapping direct Q&A pairs for featured snippet indexing."
                ],
                expected_impact="+25 AIO Score; enables rich Google SERP snippets and direct citation in AI Overviews.",
                technical_specs={"schema_types": ["Organization", "FAQPage", "TechArticle"]}
            ))
            rec_counter += 1

        # 2. llms.txt Crawler Configuration
        llms_findings = [f for f in audit_report.findings if "llms.txt" in f.name and f.severity != "pass"]
        if llms_findings:
            recommendations.append(RecommendationItem(
                id=f"REC-{rec_counter:02d}",
                pillar="technical",
                priority="high",
                category="aio",
                title="Create and Deploy /llms.txt Standard Manifest",
                rationale="Leading AI crawlers (OpenAI GPTBot, Anthropic ClaudeBot, Google-Extended) parse /llms.txt to index essential documentation and avoid crawler traps.",
                implementation_steps=[
                    "Create an /llms.txt file in the site root or repository root.",
                    "Provide a markdown summary of the project purpose, architecture, and canonical resource links.",
                    "Ensure robots.txt allows access to AI search agents."
                ],
                expected_impact="+20 AIO Score; improves context retrieval quality in conversational AI search engines.",
                technical_specs={"file_target": "/llms.txt"}
            ))
            rec_counter += 1

        # 3. AEO Question & Direct Answer Optimization
        aeo_critical = [f for f in audit_report.findings if f.category == "aeo" and f.severity in ["critical", "warning"]]
        if aeo_critical:
            recommendations.append(RecommendationItem(
                id=f"REC-{rec_counter:02d}",
                pillar="content",
                priority="high",
                category="aeo",
                title="Implement Conversational Q&A & Direct Answer Snippets",
                rationale="Voice assistants and Answer Engines (Perplexity, Siri, Google AI) extract 40-50 word direct answers formatted immediately below question headings.",
                implementation_steps=[
                    "Add an FAQ section with 3-5 high-volume query headings (e.g., 'What is...', 'How does... work?').",
                    "Place a crisp, 40-50 word definition or answer immediately following each question header.",
                    "Format process steps as ordered or unordered bulleted lists."
                ],
                expected_impact="+25 AEO Score; drastically increases probability of being selected as the primary voice/AI answer snippet.",
                target_keywords=[
                    "how to use " + (audit_report.metadata.title or "this solution"),
                    "what is " + (audit_report.metadata.title or "this product"),
                    "best practices for visibility"
                ]
            ))
            rec_counter += 1

        # 4. GEO Authority, E-E-A-T & Citations
        geo_critical = [f for f in audit_report.findings if f.category == "geo" and f.severity in ["critical", "warning"]]
        if geo_critical:
            recommendations.append(RecommendationItem(
                id=f"REC-{rec_counter:02d}",
                pillar="authority",
                priority="medium",
                category="geo",
                title="Incorporate E-E-A-T Author Credentials and Statistical Evidence",
                rationale="Generative models (Gemini, ChatGPT) weigh source credibility based on named authors, verifiable expertise, and cited empirical metrics.",
                implementation_steps=[
                    "Add an author byline with credentials, role, and link to author profile.",
                    "Inject 2-3 specific statistical benchmarks or research data points into the copy.",
                    "Add external outbound citation links to respected industry documentation or peer-reviewed benchmarks."
                ],
                expected_impact="+25 GEO Score; increases likelihood of AI models referencing the page as an authoritative source in synthesized summaries."
            ))
            rec_counter += 1

        # 5. Core SEO Hygiene (Title, Meta Description, Canonical, Headings)
        seo_critical = [f for f in audit_report.findings if f.category == "seo" and f.severity in ["critical", "warning"]]
        if seo_critical:
            recommendations.append(RecommendationItem(
                id=f"REC-{rec_counter:02d}",
                pillar="technical",
                priority="high",
                category="seo",
                title="Correct Core SEO Metadata and Heading Hierarchy",
                rationale="Search engines rely on well-formed title tags, meta descriptions, and clean H1-H3 hierarchies for canonical topic indexing.",
                implementation_steps=[
                    "Ensure title tag is between 40-60 characters with primary target keywords.",
                    "Write a compelling 130-155 character meta description with a clear call-to-action.",
                    "Ensure exactly one <h1> exists on the page, with logical subordinate <h2> and <h3> tags."
                ],
                expected_impact="+20 SEO Score; optimizes click-through rates on search engine result pages."
            ))
            rec_counter += 1

        # Calculate Projected Target Scores
        target_seo = min(100.0, audit_report.scores.seo + 25.0)
        target_aeo = min(100.0, audit_report.scores.aeo + 30.0)
        target_geo = min(100.0, audit_report.scores.geo + 30.0)
        target_aio = min(100.0, audit_report.scores.aio + 35.0)
        target_overall = round((target_seo * 0.25) + (target_aeo * 0.25) + (target_geo * 0.25) + (target_aio * 0.25), 1)

        target_scores = VisibilityScores(
            overall=target_overall,
            seo=round(target_seo, 1),
            aeo=round(target_aeo, 1),
            geo=round(target_geo, 1),
            aio=round(target_aio, 1),
        )

        # Keyword expansion opportunities
        page_title = audit_report.metadata.title or "Target Platform"
        keyword_opportunities = [
            f"{page_title} guide",
            f"how {page_title} works",
            f"{page_title} best practices",
            f"what is {page_title}",
            f"{page_title} comparison and review",
            f"{page_title} architecture overview"
        ]

        schema_requirements = [
            "schema.org/Organization",
            "schema.org/WebSite",
            "schema.org/FAQPage",
            "schema.org/Person (Author)"
        ]

        summary = (
            f"Strategic roadmap for '{audit_report.target}' contains {len(recommendations)} high-leverage recommendations. "
            f"Executing this plan is projected to increase overall visibility from {audit_report.scores.overall}/100 "
            f"to {target_overall}/100 (AEO: +{round(target_aeo - audit_report.scores.aeo, 1)}, "
            f"AIO: +{round(target_aio - audit_report.scores.aio, 1)}, "
            f"GEO: +{round(target_geo - audit_report.scores.geo, 1)}, "
            f"SEO: +{round(target_seo - audit_report.scores.seo, 1)})."
        )

        self.log(f"Strategy formulated with {len(recommendations)} recommendations. Target score: {target_overall}/100")

        return ActionPlan(
            target=audit_report.target,
            created_at=datetime.now(timezone.utc).isoformat(),
            current_scores=audit_report.scores,
            target_scores=target_scores,
            strategic_summary=summary,
            recommendations=recommendations,
            keyword_opportunities=keyword_opportunities,
            schema_requirements=schema_requirements,
        )
