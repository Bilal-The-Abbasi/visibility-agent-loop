"""
Auditor Agent: Evaluates website visibility across SEO, AEO, GEO, and AIO.
"""
import re
import json
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from src.agents.base_agent import BaseAgent
from src.models.audit_models import (
    AuditReport,
    Finding,
    PageMetadata,
    VisibilityScores,
)


class AuditorAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="AuditorAgent", role="Visibility & AI Search Auditor")

    def run(self, target: str, raw_html: Optional[str] = None) -> AuditReport:
        """
        Runs the audit on a URL, local file, or raw HTML content.
        """
        self.log(f"Starting comprehensive visibility audit for: {target}")
        html_content, target_type, base_url = self._load_content(target, raw_html)
        soup = BeautifulSoup(html_content, "html.parser")

        # Collect Page Metadata
        metadata = self._extract_metadata(soup, target, base_url, target_type)

        # Run Dimension Checks
        seo_findings, seo_score = self._audit_seo(soup, metadata)
        aeo_findings, aeo_score = self._audit_aeo(soup, metadata)
        geo_findings, geo_score = self._audit_geo(soup, metadata)
        aio_findings, aio_score = self._audit_aio(soup, metadata)

        all_findings = seo_findings + aeo_findings + geo_findings + aio_findings

        overall_score = round((seo_score * 0.25) + (aeo_score * 0.25) + (geo_score * 0.25) + (aio_score * 0.25), 1)

        scores = VisibilityScores(
            overall=overall_score,
            seo=round(seo_score, 1),
            aeo=round(aeo_score, 1),
            geo=round(geo_score, 1),
            aio=round(aio_score, 1),
        )

        critical_count = len([f for f in all_findings if f.severity == "critical"])
        warning_count = len([f for f in all_findings if f.severity == "warning"])
        pass_count = len([f for f in all_findings if f.severity == "pass"])

        summary = (
            f"Visibility Audit for '{target}' completed with an Overall Score of {overall_score}/100. "
            f"(SEO: {scores.seo}, AEO: {scores.aeo}, GEO: {scores.geo}, AIO: {scores.aio}). "
            f"Identified {critical_count} critical visibility bottlenecks, {warning_count} warnings, "
            f"and {pass_count} successful optimizations."
        )

        self.log(f"Audit completed. Overall score: {overall_score}/100. Critical issues: {critical_count}")

        return AuditReport(
            target=target,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=metadata,
            scores=scores,
            findings=all_findings,
            summary=summary,
        )

    def _load_content(self, target: str, raw_html: Optional[str]) -> Tuple[str, str, Optional[str]]:
        if raw_html:
            return raw_html, "raw_html", None

        if target.startswith("http://") or target.startswith("https://"):
            try:
                headers = {"User-Agent": "VisibilityBot-AI-Audit/1.0 (+https://example.com/bot)"}
                with httpx.Client(timeout=12.0, follow_redirects=True, headers=headers) as client:
                    resp = client.get(target)
                    resp.raise_for_status()
                    return resp.text, "url", target
            except Exception as e:
                self.log(f"Failed to fetch live URL {target}: {e}. Generating fallback audit shell.", level="warning")
                return f"<html><head><title>Error</title></head><body>Could not fetch {target}: {e}</body></html>", "url_error", target

        if os.path.exists(target):
            with open(target, "r", encoding="utf-8", errors="ignore") as f:
                return f.read(), "file", None

        # Fallback if raw text passed
        return target, "raw_text", None

    def _extract_metadata(self, soup: BeautifulSoup, target: str, base_url: Optional[str], target_type: str) -> PageMetadata:
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else None

        meta_desc = None
        desc_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
        if desc_tag and desc_tag.get("content"):
            meta_desc = desc_tag.get("content", "").strip()

        canonical_tag = soup.find("link", attrs={"rel": "canonical"})
        canonical_url = canonical_tag.get("href") if canonical_tag else None

        og_tags = {}
        for tag in soup.find_all("meta", attrs={"property": re.compile(r"^og:")}):
            prop = tag.get("property")
            content = tag.get("content")
            if prop and content:
                og_tags[prop] = content

        headings: Dict[str, List[str]] = {"h1": [], "h2": [], "h3": []}
        for level in ["h1", "h2", "h3"]:
            headings[level] = [h.get_text(strip=True) for h in soup.find_all(level)]

        # Word count
        body = soup.find("body")
        text = body.get_text(separator=" ", strip=True) if body else soup.get_text(separator=" ", strip=True)
        words = re.findall(r"\b\w+\b", text)
        word_count = len(words)

        # JSON-LD Schema detection
        json_ld_types = []
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            try:
                data = json.loads(script.string or "{}")
                if isinstance(data, dict):
                    if "@graph" in data:
                        for item in data["@graph"]:
                            if "@type" in item:
                                json_ld_types.append(item["@type"])
                    elif "@type" in data:
                        json_ld_types.append(data["@type"])
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "@type" in item:
                            json_ld_types.append(item["@type"])
            except Exception:
                continue

        # Check llms.txt
        has_llms_txt = False
        if target_type == "url" and base_url:
            parsed = urlparse(base_url)
            llms_url = f"{parsed.scheme}://{parsed.netloc}/llms.txt"
            try:
                with httpx.Client(timeout=3.0) as client:
                    r = client.get(llms_url)
                    if r.status_code == 200 and len(r.text) > 20:
                        has_llms_txt = True
            except Exception:
                has_llms_txt = False
        elif target_type == "file":
            dir_name = os.path.dirname(target) or "."
            has_llms_txt = os.path.exists(os.path.join(dir_name, "llms.txt"))

        # FAQ structure
        has_faq_structure = False
        if "FAQPage" in json_ld_types or soup.find(id=re.compile(r"faq", re.I)) or soup.find(class_=re.compile(r"faq", re.I)):
            has_faq_structure = True

        # Direct definitions
        has_direct_definitions = bool(soup.find("dl") or soup.find("dfn") or re.search(r"\bis defined as\b|\brefer(s)? to\b", text, re.I))

        # Statistics / quotes
        has_stats = bool(re.search(r"\b\d+%\b|\$\d+[\d,]*|\bstudy found\b|\baccording to\b|\bresearch shows\b", text, re.I))
        has_quotes = bool(soup.find("blockquote") or re.search(r'“[^”]{20,200}”|"[^"]{20,200}"', text))
        has_statistics_or_quotes = has_stats or has_quotes

        # Author / E-E-A-T
        has_author = bool(
            soup.find(attrs={"rel": "author"})
            or soup.find(class_=re.compile(r"author|byline", re.I))
            or re.search(r"\bwritten by\b|\bauthor:?\b|\breviewed by\b", text, re.I)
        )

        # Table or key takeaways
        has_table_or_summary = bool(
            soup.find("table")
            or soup.find(class_=re.compile(r"summary|takeaways|tldr|key-points", re.I))
        )

        return PageMetadata(
            url_or_path=target,
            title=title,
            meta_description=meta_desc,
            canonical_url=canonical_url,
            open_graph=og_tags,
            headings=headings,
            word_count=word_count,
            has_json_ld=len(json_ld_types) > 0,
            json_ld_types=json_ld_types,
            has_llms_txt=has_llms_txt,
            has_faq_structure=has_faq_structure,
            has_direct_definitions=has_direct_definitions,
            has_statistics_or_quotes=has_statistics_or_quotes,
            has_author_byline=has_author,
            has_table_or_summary=has_table_or_summary,
        )

    # -------------------------------------------------------------
    # 1. SEO AUDIT
    # -------------------------------------------------------------
    def _audit_seo(self, soup: BeautifulSoup, meta: PageMetadata) -> Tuple[List[Finding], float]:
        findings = []
        score = 100.0

        # Title checks
        if not meta.title:
            findings.append(Finding(
                category="seo",
                name="Missing Page Title",
                severity="critical",
                description="The page lacks a <title> tag, preventing search engines from indexing the page topic.",
                recommendation_hint="Add a descriptive title tag between 30 and 60 characters containing primary keywords.",
                score_impact=-30
            ))
            score -= 30
        elif len(meta.title) < 20:
            findings.append(Finding(
                category="seo",
                name="Short Page Title",
                severity="warning",
                description=f"Title is only {len(meta.title)} characters ('{meta.title}'). Too brief for search engines.",
                recommendation_hint="Expand title to 40-60 characters including secondary intent and brand name.",
                score_impact=-10
            ))
            score -= 10
        elif len(meta.title) > 65:
            findings.append(Finding(
                category="seo",
                name="Title Truncation Risk",
                severity="warning",
                description=f"Title is {len(meta.title)} characters, which will truncate on Google/Bing search results.",
                recommendation_hint="Trim title to under 60 characters while retaining core keyword.",
                score_impact=-5
            ))
            score -= 5
        else:
            findings.append(Finding(
                category="seo",
                name="Optimized Page Title",
                severity="pass",
                description=f"Title tag length ({len(meta.title)} chars) is optimal.",
                score_impact=0
            ))

        # Meta description
        if not meta.meta_description:
            findings.append(Finding(
                category="seo",
                name="Missing Meta Description",
                severity="critical",
                description="No meta description found. Search engines will generate random snippets.",
                recommendation_hint="Provide a compelling 120-160 character meta description with a call to action.",
                score_impact=-25
            ))
            score -= 25
        elif len(meta.meta_description) < 60:
            findings.append(Finding(
                category="seo",
                name="Short Meta Description",
                severity="warning",
                description=f"Meta description is only {len(meta.meta_description)} characters. Lacks detail for SERP snippet.",
                recommendation_hint="Expand meta description to 120-155 characters.",
                score_impact=-10
            ))
            score -= 10
        elif len(meta.meta_description) > 165:
            findings.append(Finding(
                category="seo",
                name="Meta Description Truncation",
                severity="warning",
                description=f"Meta description ({len(meta.meta_description)} chars) exceeds 160 characters and will be clipped.",
                recommendation_hint="Refine meta description to stay within 150-160 characters.",
                score_impact=-5
            ))
            score -= 5
        else:
            findings.append(Finding(
                category="seo",
                name="Optimized Meta Description",
                severity="pass",
                description="Meta description length is well-balanced for search result snippets.",
                score_impact=0
            ))

        # Headings structure
        h1_count = len(meta.headings.get("h1", []))
        if h1_count == 0:
            findings.append(Finding(
                category="seo",
                name="Missing H1 Heading",
                severity="critical",
                description="No <h1> tag found. Search crawlers use H1 to identify the central topic.",
                recommendation_hint="Add a single <h1> heading representing the core subject of the page.",
                score_impact=-20
            ))
            score -= 20
        elif h1_count > 1:
            findings.append(Finding(
                category="seo",
                name="Multiple H1 Headings",
                severity="warning",
                description=f"Found {h1_count} <h1> tags. Multiple H1 tags dilute topic clarity.",
                recommendation_hint="Keep exactly one <h1> for the primary topic and convert subordinate headings to <h2>.",
                score_impact=-10
            ))
            score -= 10
        else:
            findings.append(Finding(
                category="seo",
                name="Single H1 Structure",
                severity="pass",
                description=f"Properly configured single H1 heading: '{meta.headings['h1'][0]}'.",
                score_impact=0
            ))

        # Canonical URL
        if not meta.canonical_url:
            findings.append(Finding(
                category="seo",
                name="Missing Canonical Tag",
                severity="warning",
                description="No canonical tag found. Leaves the page susceptible to duplicate content penalties.",
                recommendation_hint="Add <link rel='canonical' href='https://yourdomain.com/path'>.",
                score_impact=-10
            ))
            score -= 10
        else:
            findings.append(Finding(
                category="seo",
                name="Canonical Tag Present",
                severity="pass",
                description=f"Canonical tag properly points to {meta.canonical_url}.",
                score_impact=0
            ))

        # Images alt text
        images = soup.find_all("img")
        missing_alt = [img for img in images if not img.get("alt")]
        if missing_alt:
            findings.append(Finding(
                category="seo",
                name="Images Missing Alt Attributes",
                severity="warning",
                description=f"{len(missing_alt)} of {len(images)} images lack alt text attributes, harming image search and accessibility.",
                recommendation_hint="Add concise, keyword-relevant alt descriptions to all content images.",
                score_impact=-10
            ))
            score -= 10
        elif images:
            findings.append(Finding(
                category="seo",
                name="Image Alt Attributes Complete",
                severity="pass",
                description=f"All {len(images)} images have alt attributes.",
                score_impact=0
            ))

        return findings, max(0.0, min(100.0, score))

    # -------------------------------------------------------------
    # 2. AEO AUDIT (Answer Engine Optimization)
    # -------------------------------------------------------------
    def _audit_aeo(self, soup: BeautifulSoup, meta: PageMetadata) -> Tuple[List[Finding], float]:
        findings = []
        score = 100.0

        # Question headings
        all_headings = meta.headings.get("h1", []) + meta.headings.get("h2", []) + meta.headings.get("h3", [])
        question_pattern = re.compile(r"^(what|how|why|can|which|where|when|is|are|who|do|does)\b|\?$", re.I)
        question_headings = [h for h in all_headings if question_pattern.search(h)]

        if not question_headings:
            findings.append(Finding(
                category="aeo",
                name="No Question-Based Headings",
                severity="critical",
                description="No headings formatted as user questions (e.g., 'What is...', 'How to...'). Answer engines prioritize direct queries.",
                recommendation_hint="Transform section headings into natural question phrases matching conversational search queries.",
                score_impact=-25
            ))
            score -= 25
        else:
            findings.append(Finding(
                category="aeo",
                name="Conversational Question Headings Present",
                severity="pass",
                description=f"Found {len(question_headings)} question-formatted headings (e.g. '{question_headings[0]}').",
                score_impact=0
            ))

        # Direct answer structure (short paragraphs directly following headings)
        concise_answers_found = 0
        for h in soup.find_all(["h2", "h3"]):
            sibling = h.find_next_sibling()
            if sibling and sibling.name == "p":
                words = sibling.get_text().split()
                if 25 <= len(words) <= 70:
                    concise_answers_found += 1

        if concise_answers_found == 0:
            findings.append(Finding(
                category="aeo",
                name="Lack of Direct Answer Snippets",
                severity="warning",
                description="Answer engines (Perplexity, Google AI Overviews, Siri) look for concise 40-60 word answer summaries immediately under question headers.",
                recommendation_hint="Place a 40-50 word direct, definitive answer block right after each question heading before diving into detailed explanation.",
                score_impact=-25
            ))
            score -= 25
        else:
            findings.append(Finding(
                category="aeo",
                name="Direct Answer Paragraphs Detected",
                severity="pass",
                description=f"Found {concise_answers_found} concise answer snippets structured for featured snippet extraction.",
                score_impact=0
            ))

        # Lists & Procedural steps
        lists = soup.find_all(["ul", "ol"])
        if len(lists) == 0:
            findings.append(Finding(
                category="aeo",
                name="Missing Structured Lists",
                severity="warning",
                description="No unordered or ordered lists detected. AI answer engines heavily favor list structures for multi-item queries.",
                recommendation_hint="Convert multi-part processes or key attributes into bulleted <ul> or numbered <ol> lists.",
                score_impact=-20
            ))
            score -= 20
        else:
            findings.append(Finding(
                category="aeo",
                name="Structured List Formats Present",
                severity="pass",
                description=f"Found {len(lists)} list elements providing easy-to-parse structure for answer engines.",
                score_impact=0
            ))

        # Direct definition terms
        if not meta.has_direct_definitions:
            findings.append(Finding(
                category="aeo",
                name="No Formal Definitions",
                severity="warning",
                description="Content lacks explicit definition syntax ('X is defined as...', 'X refers to...').",
                recommendation_hint="Add formal glossary or definition blocks for core terms and concepts.",
                score_impact=-15
            ))
            score -= 15
        else:
            findings.append(Finding(
                category="aeo",
                name="Definition Markup Detected",
                severity="pass",
                description="Page includes explicit terminology definitions matching informational search intent.",
                score_impact=0
            ))

        # FAQ Section
        if not meta.has_faq_structure:
            findings.append(Finding(
                category="aeo",
                name="Missing Dedicated FAQ Section",
                severity="warning",
                description="No explicit FAQ section found on page. FAQ sections have the highest citation rate in voice and answer engines.",
                recommendation_hint="Add a dedicated FAQ section with 3-5 high-volume user questions and concise answers.",
                score_impact=-15
            ))
            score -= 15
        else:
            findings.append(Finding(
                category="aeo",
                name="FAQ Section Detected",
                severity="pass",
                description="Page includes a recognized FAQ section for conversational answer capture.",
                score_impact=0
            ))

        return findings, max(0.0, min(100.0, score))

    # -------------------------------------------------------------
    # 3. GEO AUDIT (Generative Engine Optimization)
    # -------------------------------------------------------------
    def _audit_geo(self, soup: BeautifulSoup, meta: PageMetadata) -> Tuple[List[Finding], float]:
        findings = []
        score = 100.0

        # Author E-E-A-T signals
        if not meta.has_author_byline:
            findings.append(Finding(
                category="geo",
                name="Missing E-E-A-T Author Byline",
                severity="critical",
                description="Generative engines (Gemini, ChatGPT Search, Claude) favor authoritative, attributed sources with named authors and verifiable credentials.",
                recommendation_hint="Add a visible author byline with credentials, bio, and linked profile (schema Author).",
                score_impact=-30
            ))
            score -= 30
        else:
            findings.append(Finding(
                category="geo",
                name="E-E-A-T Author Signal Present",
                severity="pass",
                description="Author byline or credentials detected, supporting content credibility.",
                score_impact=0
            ))

        # Statistics and quantitative facts
        if not meta.has_statistics_or_quotes:
            findings.append(Finding(
                category="geo",
                name="Lack of Hard Statistics and Citations",
                severity="critical",
                description="LLMs look for cited statistics, benchmark percentages, and research facts to quote as evidence in generated answers.",
                recommendation_hint="Incorporate 2-4 verified statistics, benchmark percentages, or external research citations.",
                score_impact=-30
            ))
            score -= 30
        else:
            findings.append(Finding(
                category="geo",
                name="Quantitative Data & Citations Found",
                severity="pass",
                description="Page contains verifiable statistics, research citations, or quote blocks that LLMs cite.",
                score_impact=0
            ))

        # External citations / outbound links
        external_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("http://") or href.startswith("https://"):
                external_links.append(href)

        if len(external_links) == 0:
            findings.append(Finding(
                category="geo",
                name="No Outbound Authority Citations",
                severity="warning",
                description="No external citation links found. Generative models evaluate source credibility by reference topology.",
                recommendation_hint="Include authoritative external references linking to original studies, documentation, or standards bodies.",
                score_impact=-20
            ))
            score -= 20
        else:
            findings.append(Finding(
                category="geo",
                name="External Authority Citations Present",
                severity="pass",
                description=f"Found {len(external_links)} outbound reference links supporting content veracity.",
                score_impact=0
            ))

        # Content Depth / Substance
        if meta.word_count < 300:
            findings.append(Finding(
                category="geo",
                name="Thin Content for Generative Synthesis",
                severity="warning",
                description=f"Word count is only {meta.word_count} words. Generative engines consider thin pages insufficient for deep synthesis.",
                recommendation_hint="Expand substantive content to at least 600-1000 words covering subtopics comprehensively.",
                score_impact=-20
            ))
            score -= 20
        else:
            findings.append(Finding(
                category="geo",
                name="Sufficient Content Depth",
                severity="pass",
                description=f"Content volume ({meta.word_count} words) is adequate for LLM grounding and synthesis.",
                score_impact=0
            ))

        return findings, max(0.0, min(100.0, score))

    # -------------------------------------------------------------
    # 4. AIO AUDIT (AI Overview Optimization)
    # -------------------------------------------------------------
    def _audit_aio(self, soup: BeautifulSoup, meta: PageMetadata) -> Tuple[List[Finding], float]:
        findings = []
        score = 100.0

        # Structured Schema Markup (JSON-LD)
        if not meta.has_json_ld:
            findings.append(Finding(
                category="aio",
                name="Missing JSON-LD Structured Data",
                severity="critical",
                description="No JSON-LD structured schema found. AI Overviews and Google Knowledge Graph rely heavily on schema.org entities.",
                recommendation_hint="Implement JSON-LD structured data with Organization, Article, or FAQPage schemas.",
                score_impact=-35
            ))
            score -= 35
        else:
            has_rich_schema = any(t in ["FAQPage", "Article", "TechArticle", "Product", "Organization"] for t in meta.json_ld_types)
            if not has_rich_schema:
                findings.append(Finding(
                    category="aio",
                    name="Generic JSON-LD Schema",
                    severity="warning",
                    description=f"JSON-LD types detected ({meta.json_ld_types}) lack rich entity types like FAQPage, Article, or Organization.",
                    recommendation_hint="Upgrade JSON-LD schema to include specific entities: FAQPage, Article, and Person (Author).",
                    score_impact=-15
                ))
                score -= 15
            else:
                findings.append(Finding(
                    category="aio",
                    name="Rich JSON-LD Schema Present",
                    severity="pass",
                    description=f"Rich structured schema detected: {', '.join(meta.json_ld_types)}.",
                    score_impact=0
                ))

        # llms.txt standard
        if not meta.has_llms_txt:
            findings.append(Finding(
                category="aio",
                name="Missing /llms.txt File",
                severity="warning",
                description="No /llms.txt file found. The llms.txt standard guides AI web crawlers (ChatGPT, Claude, Gemini) to the most authoritative context.",
                recommendation_hint="Deploy an /llms.txt markdown file in the website root outlining project architecture, documentation, and core concepts.",
                score_impact=-25
            ))
            score -= 25
        else:
            findings.append(Finding(
                category="aio",
                name="llms.txt File Implemented",
                severity="pass",
                description="/llms.txt file detected, establishing structured indexation for AI agents.",
                score_impact=0
            ))

        # Summary / Takeaways block
        if not meta.has_table_or_summary:
            findings.append(Finding(
                category="aio",
                name="Missing Key Takeaways or Comparison Table",
                severity="warning",
                description="No dedicated 'Key Takeaways', TL;DR summary, or structured comparison table found. AI Overviews prioritize tabular and summary data.",
                recommendation_hint="Add a structured 'Key Takeaways' bulleted box or comparison table at the top of the content.",
                score_impact=-20
            ))
            score -= 20
        else:
            findings.append(Finding(
                category="aio",
                name="Summary or Comparison Elements Detected",
                severity="pass",
                description="Structured comparison table or summary block detected for rapid AI Overview extraction.",
                score_impact=0
            ))

        # Open Graph tags (used by AI social search & preview cards)
        og_essentials = ["og:title", "og:description", "og:image"]
        missing_og = [og for og in og_essentials if og not in meta.open_graph]
        if missing_og:
            findings.append(Finding(
                category="aio",
                name="Incomplete Open Graph Metadata",
                severity="warning",
                description=f"Missing essential Open Graph tags: {', '.join(missing_og)}.",
                recommendation_hint="Add complete Open Graph meta tags (og:title, og:description, og:image, og:url).",
                score_impact=-10
            ))
            score -= 10
        else:
            findings.append(Finding(
                category="aio",
                name="Complete Open Graph Metadata",
                severity="pass",
                description="Open Graph protocol tags fully specified.",
                score_impact=0
            ))

        return findings, max(0.0, min(100.0, score))
