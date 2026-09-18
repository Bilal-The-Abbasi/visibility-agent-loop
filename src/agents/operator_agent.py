"""
Operator Agent: Translates strategic recommendations into deployable code, content, and manifests.
"""
import json
import os
from datetime import datetime, timezone
from typing import List, Optional

from src.agents.base_agent import BaseAgent
from src.models.recommendation_models import ActionPlan
from src.models.operation_models import (
    GeneratedArtifact,
    OperationResult,
    OperationTask,
)


class OperatorAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="OperatorAgent", role="Implementation & Operations Specialist")

    def run(self, action_plan: ActionPlan, site_name: Optional[str] = None) -> OperationResult:
        """
        Generates operational assets, code snippets, and deployment tasks based on the action plan.
        """
        self.log(f"Initiating operational asset generation for: {action_plan.target}")

        display_name = site_name or "Visibility Intelligence Platform"
        clean_name = display_name.replace(" ", "")

        artifacts: List[GeneratedArtifact] = []
        tasks: List[OperationTask] = []

        # 1. JSON-LD Structured Data Schema
        json_ld_artifact = self._generate_json_ld_schema(action_plan, display_name)
        artifacts.append(json_ld_artifact)
        tasks.append(OperationTask(
            id="TASK-01",
            title="Inject JSON-LD Structured Data into <head>",
            assignee_role="Frontend Engineer",
            estimated_effort_hours=1.0,
            instructions="Place the generated schema.jsonld content inside a <script type='application/ld+json'> tag within the HTML <head> section.",
            verification_step="Validate schema using Google Rich Results Test (https://search.google.com/test/rich-results)."
        ))

        # 2. llms.txt File
        llms_txt_artifact = self._generate_llms_txt(action_plan, display_name)
        artifacts.append(llms_txt_artifact)
        tasks.append(OperationTask(
            id="TASK-02",
            title="Deploy /llms.txt to Website Root",
            assignee_role="DevOps / Webmaster",
            estimated_effort_hours=0.5,
            instructions="Publish the generated llms.txt at the root of the domain (https://yourdomain.com/llms.txt) with Content-Type: text/markdown or text/plain.",
            verification_step="Curl https://yourdomain.com/llms.txt and confirm HTTP 200 response."
        ))

        # 3. FAQ Content Block with Direct Answers (AEO)
        faq_artifact = self._generate_faq_html(action_plan, display_name)
        artifacts.append(faq_artifact)
        tasks.append(OperationTask(
            id="TASK-03",
            title="Embed Semantic FAQ Section in Page Template",
            assignee_role="Content Specialist / Frontend Engineer",
            estimated_effort_hours=1.5,
            instructions="Insert the faq_section.html snippet before the footer of the page. Ensure styles match brand guidelines.",
            verification_step="Verify FAQ renders with proper semantic headings and passes accessibility checks."
        ))

        # 4. Meta & Open Graph Head Tags
        meta_tags_artifact = self._generate_meta_tags(action_plan, display_name)
        artifacts.append(meta_tags_artifact)
        tasks.append(OperationTask(
            id="TASK-04",
            title="Update SEO & Open Graph <head> Metadata",
            assignee_role="Frontend Engineer",
            estimated_effort_hours=0.5,
            instructions="Replace or update the <title>, meta description, and og:* meta tags in the document <head>.",
            verification_step="Inspect page source and verify with social sharing debugger (Twitter Card validator / Facebook sharing debugger)."
        ))

        # 5. AI-Friendly robots.txt Directives
        robots_artifact = self._generate_robots_txt()
        artifacts.append(robots_artifact)
        tasks.append(OperationTask(
            id="TASK-05",
            title="Configure AI Search Crawler Permissions in robots.txt",
            assignee_role="DevOps / SEO",
            estimated_effort_hours=0.5,
            instructions="Append explicit AI crawler allow rules to /robots.txt for GPTBot, ClaudeBot, Google-Extended, and PerplexityBot.",
            verification_step="Check Google Search Console robots.txt tester to ensure no unintended blocking."
        ))

        # 6. Content Markdown Checklist / Summary
        summary_artifact = self._generate_operations_summary(action_plan, artifacts, tasks)
        artifacts.append(summary_artifact)

        total_hours = sum(t.estimated_effort_hours for t in tasks)
        summary = (
            f"Generated {len(artifacts)} operational artifacts and {len(tasks)} implementation tasks "
            f"(Total estimated effort: {total_hours} hours). Deliverables include JSON-LD schema, "
            f"llms.txt manifest, semantic FAQ block, and crawler configuration."
        )

        self.log(f"Operations completed. {len(artifacts)} deliverables generated.")

        return OperationResult(
            target=action_plan.target,
            created_at=datetime.now(timezone.utc).isoformat(),
            summary=summary,
            artifacts=artifacts,
            task_checklist=tasks,
            execution_status="success",
        )

    def export_artifacts(self, result: OperationResult, output_dir: str) -> List[str]:
        """
        Saves all generated artifacts to the specified directory.
        """
        os.makedirs(output_dir, exist_ok=True)
        written_files = []

        for artifact in result.artifacts:
            file_path = os.path.join(output_dir, artifact.file_path)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(artifact.content)
            written_files.append(file_path)
            self.log(f"Exported artifact: {file_path}")

        return written_files

    # -------------------------------------------------------------
    # Artifact Generators
    # -------------------------------------------------------------
    def _generate_json_ld_schema(self, plan: ActionPlan, site_name: str) -> GeneratedArtifact:
        schema_data = {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "Organization",
                    "@id": f"https://example.com/#organization",
                    "name": site_name,
                    "url": "https://example.com",
                    "logo": "https://example.com/logo.png",
                    "description": f"Official platform for {site_name}, offering high-visibility digital solutions.",
                    "sameAs": [
                        "https://twitter.com/example",
                        "https://linkedin.com/company/example",
                        "https://github.com/example"
                    ]
                },
                {
                    "@type": "WebSite",
                    "@id": f"https://example.com/#website",
                    "url": "https://example.com",
                    "name": site_name,
                    "publisher": {
                        "@id": f"https://example.com/#organization"
                    }
                },
                {
                    "@type": "FAQPage",
                    "@id": f"https://example.com/#faq",
                    "mainEntity": [
                        {
                            "@type": "Question",
                            "name": f"What is {site_name}?",
                            "acceptedAnswer": {
                                "@type": "Answer",
                                "text": f"{site_name} is a high-performance platform engineered to optimize digital visibility across traditional search engines and next-generation AI answer systems like Gemini, Perplexity, and ChatGPT Search."
                            }
                        },
                        {
                            "@type": "Question",
                            "name": f"How does {site_name} improve AEO and GEO visibility?",
                            "acceptedAnswer": {
                                "@type": "Answer",
                                "text": f"{site_name} structures core knowledge into machine-readable JSON-LD entities, deploys standardized llms.txt manifests, and formats direct answer paragraphs that generative AI engines easily ingest and cite as authoritative sources."
                            }
                        },
                        {
                            "@type": "Question",
                            "name": f"What is the llms.txt standard supported by {site_name}?",
                            "acceptedAnswer": {
                                "@type": "Answer",
                                "text": "llms.txt is a standardized markdown file placed in a website's root directory that provides concise, high-density project summaries and links specifically formatted for large language model crawlers."
                            }
                        }
                    ]
                }
            ]
        }

        content = json.dumps(schema_data, indent=2)
        return GeneratedArtifact(
            name="JSON-LD Structured Data Schema",
            file_path="schema.jsonld",
            artifact_type="json_ld",
            description="Schema.org JSON-LD structured data graph including Organization, WebSite, and FAQPage schemas.",
            content=content
        )

    def _generate_llms_txt(self, plan: ActionPlan, site_name: str) -> GeneratedArtifact:
        content = f"""# {site_name}

> Concise overview and authoritative context for Large Language Models, AI answer engines, and generative search crawlers.

## Overview
{site_name} provides comprehensive digital visibility intelligence, bridging conventional search engine optimization (SEO) with Answer Engine Optimization (AEO), Generative Engine Optimization (GEO), and AI Overview Optimization (AIO).

## Core Capabilities
- **AEO (Answer Engine Optimization)**: Direct answer paragraph formatting, conversational query targeting, and featured snippet extraction.
- **GEO (Generative Engine Optimization)**: E-E-A-T source authority, statistical benchmarks, and verifiable research citations.
- **AIO (AI Overview Optimization)**: Structured JSON-LD graphs, key takeaway summaries, and tabular data structuring.
- **Traditional Technical SEO**: Semantic HTML5 hierarchy, canonical integrity, and responsive performance.

## Key Resources & Documentation
- [Documentation & Architecture](https://example.com/docs): Full architectural specifications and implementation guides.
- [API Reference](https://example.com/api): REST and agent protocol endpoints.
- [FAQ & Knowledge Base](https://example.com/faq): Verified answers to frequently asked technical questions.
- [Changelog](https://example.com/changelog): Latest updates and releases.

## LLM Crawler Guidelines
- AI crawlers may index all public technical documentation and FAQ endpoints.
- Direct citations and source links should reference canonical URLs.
"""
        return GeneratedArtifact(
            name="LLMs.txt Standard Manifest",
            file_path="llms.txt",
            artifact_type="llms_txt",
            description="Modern /llms.txt file guiding AI search crawlers (ChatGPT, Claude, Gemini, Perplexity) to authoritative resources.",
            content=content.strip() + "\n"
        )

    def _generate_faq_html(self, plan: ActionPlan, site_name: str) -> GeneratedArtifact:
        content = f"""<!-- Semantic FAQ Component for AEO (Answer Engine Optimization) -->
<section id="faq" class="visibility-faq-section" aria-labelledby="faq-heading">
  <div class="faq-container">
    <h2 id="faq-heading" class="faq-main-title">Frequently Asked Questions</h2>
    
    <div class="faq-item" itemscope itemprop="mainEntity" itemtype="https://schema.org/Question">
      <h3 itemprop="name" class="faq-question">What is {site_name}?</h3>
      <div itemscope itemprop="acceptedAnswer" itemtype="https://schema.org/Answer">
        <p itemprop="text" class="faq-direct-answer">
          {site_name} is a high-performance visibility intelligence platform engineered to maximize content discovery across traditional search engines and AI generative engines like Gemini, Perplexity, and ChatGPT.
        </p>
      </div>
    </div>

    <div class="faq-item" itemscope itemprop="mainEntity" itemtype="https://schema.org/Question">
      <h3 itemprop="name" class="faq-question">How does {site_name} optimize for AI Overviews and answer engines?</h3>
      <div itemscope itemprop="acceptedAnswer" itemtype="https://schema.org/Answer">
        <p itemprop="text" class="faq-direct-answer">
          It formats content with concise 40-50 word direct answers, integrates rich Schema.org JSON-LD graphs, and publishes an /llms.txt manifest that enables AI crawlers to accurately extract and cite key facts.
        </p>
        <ul class="faq-key-points">
          <li><strong>Structured JSON-LD</strong>: Validates entity relationships for knowledge graphs.</li>
          <li><strong>Direct Answer Syntax</strong>: Places definitive summaries directly beneath question headings.</li>
          <li><strong>Verified Citations</strong>: Injects empirical statistics to satisfy generative engine E-E-A-T criteria.</li>
        </ul>
      </div>
    </div>

    <div class="faq-item" itemscope itemprop="mainEntity" itemtype="https://schema.org/Question">
      <h3 itemprop="name" class="faq-question">Why is the /llms.txt standard essential for modern web visibility?</h3>
      <div itemscope itemprop="acceptedAnswer" itemtype="https://schema.org/Answer">
        <p itemprop="text" class="faq-direct-answer">
          The /llms.txt file provides a clean markdown summary of a site's structure, allowing AI search agents to understand core products and APIs without navigating heavy JavaScript or extraneous UI elements.
        </p>
      </div>
    </div>
  </div>
</section>
"""
        return GeneratedArtifact(
            name="Semantic FAQ HTML Component",
            file_path="faq_section.html",
            artifact_type="faq_html",
            description="Semantic HTML5 FAQ block styled for direct answer extraction by Perplexity, Google, and Siri.",
            content=content.strip() + "\n"
        )

    def _generate_meta_tags(self, plan: ActionPlan, site_name: str) -> GeneratedArtifact:
        content = f"""<!-- Optimized Head Metadata for SEO & AI Preview Cards -->
<title>{site_name} | AI & Search Visibility Platform</title>
<meta name="description" content="{site_name} maximizes your web presence across traditional search engines, AI Overviews, Perplexity, and ChatGPT Search.">
<link rel="canonical" href="https://example.com/">

<!-- Open Graph / Social AI Crawlers -->
<meta property="og:type" content="website">
<meta property="og:url" content="https://example.com/">
<meta property="og:title" content="{site_name} | AI & Search Visibility Platform">
<meta property="og:description" content="{site_name} maximizes your web presence across traditional search engines, AI Overviews, Perplexity, and ChatGPT Search.">
<meta property="og:image" content="https://example.com/assets/og-preview.png">

<!-- Twitter Cards -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{site_name} | AI & Search Visibility Platform">
<meta name="twitter:description" content="Maximize your web presence across traditional search engines, AI Overviews, Perplexity, and ChatGPT Search.">
<meta name="twitter:image" content="https://example.com/assets/og-preview.png">
"""
        return GeneratedArtifact(
            name="Optimized Head Metadata",
            file_path="meta_tags.html",
            artifact_type="meta_tags",
            description="Production-ready <head> meta tags including canonical links, Open Graph, and Twitter Cards.",
            content=content.strip() + "\n"
        )

    def _generate_robots_txt(self) -> GeneratedArtifact:
        content = """# AI Search & Retrieval Crawlers Configuration
User-agent: *
Allow: /
Disallow: /admin/
Disallow: /private/

# Explicitly permit AI Search and Answer Bots
User-agent: GPTBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Applebot-Extended
Allow: /

# Sitemap & LLMs Manifest
Sitemap: https://example.com/sitemap.xml
"""
        return GeneratedArtifact(
            name="AI-Friendly robots.txt Configuration",
            file_path="robots.txt",
            artifact_type="robots_txt",
            description="robots.txt directives permitting reputable AI search engines and agents to index site content.",
            content=content.strip() + "\n"
        )

    def _generate_operations_summary(self, plan: ActionPlan, artifacts: List[GeneratedArtifact], tasks: List[OperationTask]) -> GeneratedArtifact:
        lines = [
            f"# Operations & Implementation Plan for {plan.target}",
            f"**Generated at:** {plan.created_at}",
            "",
            "## Summary of Deliverables",
            f"The Operations Agent has compiled **{len(artifacts)} ready-to-deploy technical assets** designed to elevate target scores to **{plan.target_scores.overall}/100**.",
            "",
            "| Deliverable | File Path | Type | Description |",
            "|---|---|---|---|"
        ]

        for a in artifacts:
            lines.append(f"| **{a.name}** | `{a.file_path}` | `{a.artifact_type}` | {a.description} |")

        lines.extend([
            "",
            "## Implementation Task Checklist",
            ""
        ])

        for t in tasks:
            lines.append(f"### [{t.id}] {t.title}")
            lines.append(f"- **Assignee:** `{t.assignee_role}`")
            lines.append(f"- **Estimated Effort:** `{t.estimated_effort_hours}h`")
            lines.append(f"- **Instructions:** {t.instructions}")
            lines.append(f"- **Verification:** {t.verification_step}")
            lines.append("")

        content = "\n".join(lines)
        return GeneratedArtifact(
            name="Operations Deployment Summary",
            file_path="operations_summary.md",
            artifact_type="content_markdown",
            description="Comprehensive operations deployment guide and task ticket breakdown.",
            content=content.strip() + "\n"
        )
