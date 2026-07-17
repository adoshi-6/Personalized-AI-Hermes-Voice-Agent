# CHRONOS External Sources Registry
> Master registry of all external sources referenced, analyzed, or used during CHRONOS research and development.
> Last updated: 2026-07-16

---

## 📁 Google Docs / Pasted Documents

| # | Title | Source | Status | Notes |
|---|-------|--------|--------|-------|
| 1 | "Build the Exact Dashboard" — Doby Lanete, DobotAI | Pasted by user (Google Doc) | ✅ Analyzed | Full prompt pack (7 prompts) for building a local AI output dashboard: scanner.py + Flask + wikilink graph + timeline + suggestions panel. Directly maps to CHRONOS Memory Dashboard (V1.2). |
| 2 | "BALL — The Fable 6 Setup" | Pasted by user (Google Doc) | ✅ Analyzed | Optimization blueprint for Claude Code/Desktop focusing on 4 pillars: global/local memory overrides (`CLAUDE.md`), auto-generating custom MCP servers, markdown-configured sub-agents (`.claude/agents/`), and post-tool lifecycle verification hooks (`settings.json`). Very high relevance to CHRONOS core architecture. |
| 3 | "AI Email Agent Setup" — chrispathway (nanoclaw) | Pasted by user (Google Doc) | ✅ Analyzed | Nanoclaw email agent setup details: clones nanoclaw repo, runs background daemon, handles emails, routes summary to Telegram, drafts replies. Relevant for CHRONOS communication integrations (V1.2). |
| 4 | "Agentic OS Using Fable 5" — RayCFu | Pasted by user (Google Doc) | ✅ Analyzed | Deep-dive guide for building an autonomous agentic loop: triage → conductor → implement → verify. Features a strict constitution (CLAUDE.md), permission gates (contract.md), a statistical trust ledger, and daily goal regression tests. Critical blueprint for CHRONOS V1.1 multi-agent council and self-learning loops. |
| 5 | "Agentic_OS_Builders_Guide_Full" (Fable 5) | https://docs.google.com/document/d/1NfIe2ixwNHbXAQBDSeEGLzQEyibck9aeG2zyX7i1p20/edit?usp=sharing | ✅ Analyzed | A-Z breakdown on how to use Claude Fable 5 like a 100x engineer. Contains 8 builds/patterns for an Agentic OS. |

---

## 📄 PDFs

| # | Title | URL | Status | Notes |
|---|-------|-----|--------|-------|
| 1 | The Brain OS Hub | [Link](https://attachments.convertkitcdnn2.com/2693950/1d6f54b2-20c8-45c5-9822-7df3d6f62510/the-brain-os-hub.pdf) | ✅ Analyzed | Pasted by user. Identical content to "Build the Exact Dashboard" document. Local Flask dashboard guide (7-prompt pack) for workspace notes, scripts, and git visual tracking. |

---

## 🐙 GitHub Repositories

| # | Repo | URL | Verdict | Key CHRONOS Idea |
|---|------|-----|---------|-----------------|
| 1 | openclaudecode | https://github.com/openclaudecode | ❌ Skip | Security risk — decompiled proprietary code |
| 2 | jcode (1jehuang) | https://github.com/1jehuang/jcode | ✅ Borrow pattern | File-lock conflict detection for concurrent agents |
| 3 | openclaw-os (thesysdev) | https://github.com/thesysdev/openclaw-os | ✅✅ High | Generative UI — render responses as live interactive widgets |
| 4 | MiMo-Code (XiaomiMiMo) | https://github.com/XiaomiMiMo/MiMo-Code | ✅ High | Dream/Distill memory compression → reusable skills |
| 5 | ECC (affaan-m) | https://github.com/affaan-m/ECC | ✅ High | orch-* fan-out orchestration + AgentShield security auditing |
| 6 | claude-mem (thedotmack) | https://github.com/thedotmack/claude-mem | ✅✅ High | SQLite-backed auto memory with AI compression |
| 7 | headroom (headroomlabs-ai) | https://github.com/headroomlabs-ai/headroom | ✅ Easy win | Context compression proxy (60-95% reduction) |
| 8 | OmniRoute (diegosouzapw) | https://github.com/diegosouzapw/OmniRoute | ✅ Later | Cloud model fallback routing |
| 9 | playwright-mcp (microsoft) | https://github.com/microsoft/playwright-mcp | ✅✅ Urgent | Replace browser harness with real Playwright browser control |
| 10 | gstack (garrytan) | https://github.com/garrytan/gstack | ✅✅ High | CHRONOS Modes/Roles system (specialist AI role switching) |
| 11 | graphify (Graphify-Labs) | https://github.com/Graphify-Labs/graphify | ✅ V1.3 | Structural knowledge graph of CHRONOS codebase |
| 12 | system_prompts_leaks (asgeirtj) | https://github.com/asgeirtj/system_prompts_leaks | ✅✅ Now | Read Fable 5/6 + frontier prompt engineering patterns |
| 13 | Website-downloader (AhmadIbrahiim) | https://github.com/AhmadIbrahiim/Website-downloader | ❌ Skip | Node.js website cloner; too heavy for search, keep for offline archiving only. |
| 14 | crawl4ai (unclecode) | https://github.com/unclecode/crawl4ai | ✅✅ V1.2 | Async Python LLM-ready markdown extraction. Upgrade browser harness for cleaner search context. |
| 15 | browser-use | https://github.com/browser-use/browser-use | ✅✅ V1.3 | Playwright-based agentic web navigation. Give CHRONOS dynamic browser actions (clicking, forms). |
| 16 | Scrapling (D4Vinci) | https://github.com/D4Vinci/Scrapling | ✅ V1.2 | Stealth scraper to bypass Cloudflare/Turnstile bot blockages. |
| 17 | curl-impersonate / curl_cffi | https://github.com/lwthiker/curl-impersonate | ✅ V1.2 | Spoof TLS fingerprints for fast, raw, browserless web scraping. |
| 18 | colibri (JustVugg) | https://github.com/JustVugg/colibri | ✅ V1.4 | Pure C engine for running 744B MoE models via NVMe streaming. Good for background heavy-compute tasks. |

---

## 🌐 Websites

| # | Site | URL | Verdict | CHRONOS Relevance |
|---|------|-----|---------|------------------|
| 1 | open-design.ai | https://open-design.ai/ | ✅✅ High | Local-first AI design workspace. Generates HTML/PDF/PPTX/MP4 from prompts. Works with Ollama/Qwen. Relevant for CHRONOS Design Mode + web app builder. Apache-2.0 open source. |
| 2 | Firecrawl | https://www.firecrawl.dev/ | ✅✅ High | Web scraping → LLM-ready Markdown. Self-hostable. Upgrade for CHRONOS browser harness in V1.2. |
| 3 | React Native | https://reactnative.dev/ | ✅ Future | CHRONOS mobile app / phone widget in V1.5 |
| 4 | Cohere North Mini Code | https://cohere.com/blog/north-mini-code | ✅ Alternative | Small fast code-completion model (cloud) |
| 5 | same.new | https://same.new/ | ✅ V1.2 | AI website cloner — useful for CHRONOS web app builder mode |
| 6 | freebuff.com | https://freebuff.com/ | ❌ Skip | No CHRONOS relevance |
| 7 | founderpal.ai | https://founderpal.ai/ | ❌ Personal | Startup idea validator — personal use only |
| 8 | validatorai.com | https://validatorai.com/ | ❌ Personal | Startup idea validator — personal use only |
| 9 | salesexec.ai | https://salesexec.ai/ | ❌ Skip | No CHRONOS integration |
| 10 | recast.studio | https://recast.studio/ | ❌ Skip | Audio repurposing tool — no current fit |
| 11 | glasp.co | https://glasp.co/ | ✅ V1.3 | AI web highlighter / knowledge base — feeds CHRONOS memory |
| 12 | bluehost.com | https://www.bluehost.com/ | ✅ V1.5 | Web hosting for future public CHRONOS deployment |
| 13 | horizonx.so | https://horizonx.so/ | ✅✅ V1.1 | 3D WebGL animations — perfect for neural brain display |
| 14 | animmasterlib.dev | https://animmasterlib.dev/ | ✅✅ V1.1 | Premium micro-animations for CHRONOS dashboard |
| 15 | skiper-ui.com | https://skiper-ui.com/ | ✅✅ V1.1 | Dark glassmorphism UI — perfect CHRONOS aesthetic |
| 16 | vengenceui.com | https://www.vengenceui.com/ | ✅ V1.1 | Dark premium UI components |
| 17 | 21st.dev | https://21st.dev/ | ✅ V1.2 | AI-generated UI components for rapid frontend iteration |
| 18 | flowgpt.com | https://flowgpt.com/ | ✅ Research | Prompt marketplace for system prompt ideas |
| 19 | VibeOrigin Pre-Launch Checklist | https://vibeorigin.dev/pre-launch-checklist | ✅ V1.2 | Pre-launch QA checklist for CHRONOS web app builder |
| 20 | Dev.to Vibe Coding Checklist | https://dev.to/patrickudo2004/vibe-coding-my-ultimate-checklist-for-building-software-with-ai-magic-284e | ✅ V1.1 | Coding standards + blueprint-first workflow for coding agent mode |

---

## 📺 YouTube Channels

| # | Channel | Key Ideas for CHRONOS |
|---|---------|----------------------|
| 1 | Ben AI | n8n workflow automation (V1.2), Agent Team architecture, Second Brain templates |
| 2 | Varun Mayya | Clarity gate before tasks, Nova autonomous content agent pattern (V1.4), AI-as-manager framing |
| 3 | Liam Ottley | CHRONOS as Personal Operating System positioning, n8n stack, high-value niche automation |
| 4 | AI Edge (@AIEdgeHQ) | Sub-agent delegation patterns, skills architecture design for V1.1 |
| 5 | The MIT Monk | Power user default mode, Founder's Triangle for startup advisor, premium aesthetic alignment |
| 6 | Jeff Su | Living Prompts Database (`skills/prompts/`), auto-documentation breadcrumbs, PowerToys CHRONOS hotkey |
| 7 | Dan Martell | 4-part prompt framework (Role+Context+Command+Format), Business Audit Mode, "Systemize first" rule |

---

## 🤖 Models Evaluated

| # | Model | Source | Status | Notes |
|---|-------|--------|--------|-------|
| 1 | qwen3:8b | Ollama (server) | ✅ Active | Current CHRONOS primary model |
| 2 | GLM-5.2 | z.ai / Ollama | ❌ Cloud only | 744B params — not locally runnable at current hardware |
| 3 | MiMo-V2.5 | Xiaomi | 🔍 Evaluate | 1M context, strong reasoning, MIT licensed |
| 4 | Fable 6 (Claude) | Anthropic | ❌ Cloud | Reference for system prompt patterns only |

---

## 📚 CHRONOS Internal Files

| # | File | Path | Purpose |
|---|------|------|---------|
| 1 | CHRONOS_IDEAS.md | `C:\Users\Aryan\OneDrive\Desktop\CHRONOS\CHRONOS_IDEAS.md` | Master ideas and implementation backlog |
| 2 | CHRONOS_SOURCES.md | `C:\Users\Aryan\OneDrive\Desktop\CHRONOS\CHRONOS_SOURCES.md` | This file — external sources registry |
| 3 | implementation_plan.md | Brain artifacts dir | V1.0–V2.0 technical implementation plan |
| 4 | research_analysis.md | Brain artifacts dir | Full analysis of all external sources |
| 5 | walkthrough.md | Brain artifacts dir | V1.0 completed features walkthrough |
| 6 | hermes config | `C:\Users\Aryan\AppData\Local\hermes\config.yaml` | Hermes agent configuration (Ollama endpoint) |
| 7 | server.py | `C:\Users\Aryan\OneDrive\Desktop\CHRONOS\server.py` | Flask backend — core CHRONOS logic |
| 8 | config.py | `C:\Users\Aryan\OneDrive\Desktop\CHRONOS\config.py` | 🔒 Private — API keys, personal system prompts |
| 9 | index.html | `C:\Users\Aryan\OneDrive\Desktop\CHRONOS\index.html` | Frontend — UI, voice control, 3D orb |
| 10 | audio_provider.py | `C:\Users\Aryan\OneDrive\Desktop\CHRONOS\audio_provider.py` | TTS engine (ElevenLabs / Kokoro) |

---

## ⚠️ Pending — Need Content

*All sources are fully analyzed.*

---

> **To add a new source:** Paste the link or content in chat and it will be analyzed and added here automatically.
