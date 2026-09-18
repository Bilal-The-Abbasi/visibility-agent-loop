# AI Website Visibility & Operations Agent Loop

An autonomous 3-agent pipeline that audits website visibility across traditional search and generative AI engines, formulates strategic recommendations, generates production-ready code/content assets, and executes closed-loop re-audit verification.

---

## 🤖 The 3-Agent Architecture

```
                               ┌────────────────────────┐
                               │  Target Website / URL  │
                               └───────────┬────────────┘
                                           │
                                           ▼
  ┌─────────────────────────────────────────────────────────────────────────────────┐
  │ [Agent 1: AuditorAgent]                                                         │
  │ • Traditional SEO: Title, meta description, H1-H3 hierarchy, canonical, OpenGraph│
  │ • AEO (Answer Engine Optimization): Direct answers, question headings, FAQs    │
  │ • GEO (Generative Engine Optimization): E-E-A-T credentials, citations, stats   │
  │ • AIO (AI Overview Optimization): Schema.org JSON-LD, /llms.txt manifest        │
  └────────────────────────────────────────┬────────────────────────────────────────┘
                                           │ Emits: AuditReport (JSON + MD)
                                           ▼
  ┌─────────────────────────────────────────────────────────────────────────────────┐
  │ [Agent 2: StrategistAgent]                                                      │
  │ • Prioritizes visibility bottlenecks by impact and effort                       │
  │ • Maps keyword expansion clusters and search intent                             │
  │ • Computes target visibility score projections                                  │
  └────────────────────────────────────────┬────────────────────────────────────────┘
                                           │ Emits: ActionPlan (JSON + MD)
                                           ▼
  ┌─────────────────────────────────────────────────────────────────────────────────┐
  │ [Agent 3: OperatorAgent]                                                        │
  │ • Generates schema.jsonld (Organization, WebSite, FAQPage)                      │
  │ • Generates /llms.txt manifest for AI crawlers (GPTBot, ClaudeBot, Gemini)      │
  │ • Generates semantic faq_section.html with 40-50 word direct answers            │
  │ • Generates meta_tags.html & robots.txt                                         │
  │ • Creates engineer/content deployment checklists (operations_summary.md)        │
  └────────────────────────────────────────┬────────────────────────────────────────┘
                                           │ Emits: Generated Deliverables
                                           ▼
  ┌─────────────────────────────────────────────────────────────────────────────────┐
  │ [Loopback Verification]                                                         │
  │ • Applies generated deliverables into optimized HTML                           │
  │ • Re-audits the patched site to calculate verified score improvements          │
  └─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quickstart

### 1. Prerequisites
- Python 3.9+

### 2. Activate Virtual Environment & Run Demo
```bash
# Activate virtual environment
source .venv/bin/activate

# Run the test loop on the bundled demo site
python3 -m src.main --demo --output-dir output
```

### 3. Run on Any Local File or Live Website
```bash
# Audit a local HTML file
python3 -m src.main --file path/to/index.html --output-dir output

# Audit a live website URL
python3 -m src.main --url https://example.com --output-dir output
```

---

## 📦 Generated Deliverables (`output/`)

When you run the pipeline, the following files are produced:

| File | Purpose |
|---|---|
| `audit_report.json` & `.md` | Detailed breakdown of SEO, AEO, GEO, and AIO scores with critical findings |
| `action_plan.json` & `.md` | Prioritized strategic roadmap and target projections |
| `schema.jsonld` | Schema.org JSON-LD graph (Organization, WebSite, FAQPage) |
| `llms.txt` | Standardized AI crawler guide for Perplexity, ChatGPT Search, Claude |
| `faq_section.html` | Semantic HTML FAQ component optimized for direct answers |
| `meta_tags.html` | Optimized `<head>` tags with Open Graph and canonical tags |
| `robots.txt` | Crawler permissions allowing AI search engines |
| `operations_summary.md` | Actionable engineering & content task tickets |
| `optimized_site.html` | Synthesized page with all fixes injected for loopback testing |

---

## 🧪 Running Automated Tests
```bash
.venv/bin/pytest tests/ -v
```
