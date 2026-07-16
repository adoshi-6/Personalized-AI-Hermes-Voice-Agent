# CHRONOS — Master Ideas & Implementation Log

> This file tracks all ideas, future plans, implementation decisions, and research findings for the CHRONOS AI assistant project.
> It is the single source of truth for where CHRONOS is going.
> **Rule:** Any new idea discussed in any session should be added here.

---

## Current Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python / Flask (`server.py`) |
| LLM Inference | Ollama (remote server at `100.88.1.86` via Tailscale) |
| Fast Model | `qwen3:1.7b` |
| Smart Model | `qwen3:4b` |
| TTS | Edge-TTS with sentence streaming (`audio_provider.py`) |
| STT | SpeechRecognition (Google) |
| Frontend | Vanilla HTML/JS/CSS (`index.html`) |
| Multi-Agent | Hermes Agent v0.18.2 (Nous Research) — installed, configured |
| Desktop Control | pyautogui |
| Browser Harness | Playwright / requests |
| Memory | Lessons JSON (`chronos_memory/`) |
| Config | `config.py` (personal, never pushed to GitHub) |

---

## Implementation Plan — Version Roadmap

### ✅ Version 1.0: Foundation, Aesthetics & Quick Wins (COMPLETE — July 2026)
- [x] Full ACE → CHRONOS rename (personal files)
- [x] Fix audio feedback loop (mic muted while CHRONOS speaks)
- [x] Dashboard redesign — dark theme with teal/purple gradients
- [x] 3D orb animation upgrade (electron cloud style)
- [x] Clock/date display on dashboard
- [x] "Sir" address style enforced in system prompt
- [x] Remove Qwen 2.5 Coder (rely on Claude/Antigravity for coding)
- [x] Local sentence-by-sentence streaming playback (major latency improvement)
- [x] UUID-cached audio files with thread-safe counter for mic control
- [x] Push generic changes to GitHub

---

### 🔄 Version 1.1: Multi-Agent Architecture & Desktop Control (NEXT)
- [ ] Sub-Agent Spawning via Hermes — `DynamicAgentSpawner` class in `server.py`
- [ ] Shared Memory Layer — thread-safe locking JSON store for parallel agents
- [ ] 3D Brain Neural Network Display — Three.js node graph of agent connections
- [ ] Claude Code-Style Computer Control — screenshot + vision + mouse/keyboard
- [ ] Skills Library Framework — `skills/` plugin directory with manifest loader
- [ ] Custom Ollama Model (`Modelfile`) — Package CHRONOS system prompt and parameters directly into a local Ollama model binary (`ollama create chronos -f ./Modelfile`)

---

### Version 1.2: Advanced Input, Output & Workflows
- [ ] File Uploads — drag-and-drop for PDF, Word, Excel, images, DXF, F3D
- [ ] Claude Artifacts Equivalent — dedicated panel for interactive HTML widgets, charts, live code
- [ ] n8n Workflow Automation — local n8n + API endpoint for CHRONOS to trigger workflows
- [ ] Expandable Chat — full-window chat UI mode

---

### Version 1.3: The STEM & Analytical Core
- [ ] STEM Personality Shift — system prompt tuned for engineering, physics, math
- [ ] Judgement Mode — mode where CHRONOS only critiques and finds flaws
- [ ] Physics Simulations — Cannon.js/Rapier in browser, SciPy/FEniCS in Python
- [ ] 3D Modeling & CAD Pipeline — DXF generation, OpenSCAD code, Fusion 360 hooks
- [ ] Drafting Mode — upload sketch → vision model interprets → CAD pipeline

---

### Version 1.4: Integrations & Proactive Behavior
- [ ] GitHub Repo Downloader — download specific repo parts (PIN protected)
- [ ] Email Integration (Gmail/Notion/Calendar) — drafts first, PIN to send/delete
- [ ] Current Events Morning Briefing — news + weather + calendar + email summary
- [ ] Sam Altman Startup Playbook — ingest into CHRONOS knowledge base
- [ ] Chess Suite — Stockfish + analysis + chess.com MCP hook

---

### Version 1.5: Platform Independence & Quality of Life
- [ ] Minimize to System Tray — run in background without terminal
- [ ] Auto-Boot without Terminal — Windows Task Scheduler silent startup
- [ ] PWA Conversion & Telegram Bot — mobile access via Tailscale
- [ ] **CHRONOS Phone Widget** — iOS/Android home screen widget for quick voice/text access
- [ ] Touch/Face ID for Mobile — biometric auth on mobile web interface
- [ ] Remote Wake / Wake on LAN — wake server remotely from iPhone
- [ ] Finger/Gesture Camera Controls — MediaPipe hand tracking for UI

---

### Version 2.0: Next-Gen Capabilities
- [ ] Fable 5 System Prompt — integrate Fable 5 persona
- [ ] Voice Identification (Diarization) — `pyannote-audio` for speaker recognition
- [ ] Contacts & VoIP Calling — Google People API + Twilio
- [ ] Self-Improving Financial Market Prediction — RL loop + market data API
- [ ] Media Generation — Stable Diffusion (RTX 3060), Runway API, QR codes
- [ ] **Local Model Fine-Tuning (QLoRA)** — Train local base models (Qwen/Llama) using Unsloth/Axolotl on custom chat logs, coding standards, and private data for personalized responses.

---

## App/Website Building Stack (For Future Projects CHRONOS Helps Build)

| Purpose | Tool |
|---------|------|
| Framework | React Native |
| Database | Supabase |
| Publishing | Expo (App Store) |
| Domains | Squarespace |
| Deployment | Vercel |
| Coding Agent | CHRONOS coding agent |

---

## Ideas & Research Backlog

> Items below are ideas to explore. They are NOT yet approved for implementation.
> Analysis results will be added as research is completed.

### GitHub Repositories — Analyzed July 16, 2026

| Repo | Verdict | Key Idea to Steal |
|------|---------|------------------|
| `openclaudecode` | ❌ Skip — security risk | Nothing |
| `1jehuang/jcode` | ✅ Borrow pattern | File-lock conflict detection for concurrent agents |
| `thesysdev/openclaw-os` | ✅✅ High priority | Generative UI — render responses as live interactive widgets |
| `XiaomiMiMo/MiMo-Code` | ✅ High priority | Dream/Distill memory compression → reusable skills |
| `affaan-m/ECC` | ✅ High priority | orch-* fan-out orchestration + AgentShield security auditing |
| `thedotmack/claude-mem` | ✅✅ High priority | SQLite-backed auto memory with AI compression |
| `headroomlabs-ai/headroom` | ✅ Easy win | Context compression proxy (60-95% reduction) |
| `diegosouzapw/OmniRoute` | ✅ Later | Cloud model fallback routing |
| `microsoft/playwright-mcp` | ✅✅ Urgent | Replace browser harness with real Playwright browser control |
| `garrytan/gstack` | ✅✅ High priority | Garry Tan's specialized roles prompts library. Turn CHRONOS into virtual teams (Advisor, QA, Security, Architect modes) |
| `nanoclaw (DobotAI/nanoclaw)` | ✅ V1.2 | Chris Pathway's nanoclaw background daemon setup. Inbox monitoring + Telegram summaries + auto drafting replies. |
| `Agentic OS (Fable 5 Loop)` | ✅✅ V1.1 | RayCFu's autonomous software engineering loop. Steal: strict constitutional rules, multi-agent separation (maker/checker), trust ledger for skills graduation, and daily goal/predicate checks. |
| `Graphify-Labs/graphify` | ✅ V1.3 | Structural knowledge graph of CHRONOS codebase |
| `asgeirtj/system_prompts_leaks` | ✅✅ Now | Read Fable 5 + frontier prompt patterns |
| `Fable 6 Setup (BALL)` | ✅✅ Now | 4-part Claude Code optimization blueprint. Steal: global/project-level prompt configurations (`CLAUDE.md`), auto-generation of custom MCP servers when tool is missing, sub-agent fanning, and tool lifecycle check hooks. |

### Potential Models — Analyzed July 16, 2026
- **GLM-5.2**: 744B params, cloud-only on Ollama, not locally runnable. Monitor for small distilled variants.
- **Orca Coding Agent**: Not a separate tool — describes the parallel multi-agent pattern already in V1.1 plan.

### Websites — Analyzed July 16, 2026
- **firecrawl.dev** ✅✅ — Self-hostable web scraping API → clean LLM Markdown. Upgrade browser harness in V1.2.
- **reactnative.dev** ✅ — For CHRONOS mobile app / phone widget in V1.5.
- **same.new** ✅ — AI website cloner, useful for CHRONOS web app building mode.

### Design Libraries — Analyzed July 16, 2026
- **animmasterlib.dev** ✅✅ — Premium micro-animations for CHRONOS dashboard
- **skiper-ui.com** ✅✅ — Dark glassmorphism UI components, perfect aesthetic match
- **horizonx.so** ✅✅ — 3D WebGL animations, perfect for V1.1 neural brain display
- **21st.dev** ✅ — AI-generated UI components for rapid frontend iteration
- **vengenceui.com** ✅ — Dark premium UI components
- **flowgpt.com** ✅ — Prompt marketplace for system prompt ideas

### Remotion — Analyzed July 16, 2026
- Video-as-code (React → MP4). Log for V2.0 media generation pipeline.



### Websites to Evaluate (Completed July 16, 2026)
- [x] freebuff.com
- [x] cohere.com/blog/north-mini-code
- [x] firecrawl.dev
- [x] founderpal.ai
- [x] validatorai.com
- [x] salesexec.ai
- [x] same.new
- [x] recast.studio
- [x] glasp.co
- [x] bluehost.com

### Design Libraries to Evaluate (Completed July 16, 2026)
- [x] animmasterlib.dev
- [x] skiper-ui.com
- [x] vengenceui.com
- [x] 21st.dev
- [x] horizonx.so
- [x] flowgpt.com

### Vibecoding Checklists (Completed July 16, 2026)
- [x] dev.to/patrickudo2004/vibe-coding-my-ultimate-checklist-for-building-software-with-ai-magic-284e
- [x] vibeorigin.dev/pre-launch-checklist

### YouTube Channels — Research for Ideas (Completed July 16, 2026)
- [x] Ben AI
- [x] Varun Mayya
- [x] Liam Ottley
- [x] AI Edge
- [x] The MIT Monk
- [x] Jeff Su
- [x] Dan Martell

### Plugins & Integrations to Explore
- [ ] **Remotion** — programmatic video generation from React components
- [ ] **React Native** — for CHRONOS mobile app / phone widget
- [ ] **Firecrawl** — web scraping API, could replace/enhance browser harness

### Hermes Skills to Install
- [ ] document skills
- [ ] mcp-builder
- [ ] web-app-testing
- [ ] frontend-design
- [ ] skill-creator

---

## Prompts & System Prompt Ideas

> Prompts discovered or written that may be incorporated into CHRONOS's system prompt or modes.

*(To be populated — add any interesting prompts found during research here)*

---

## Session Log

| Date | What Was Done |
|------|--------------|
| July 2026 | ACE → CHRONOS rename complete |
| July 2026 | Audio streaming, UUID cache, thread-safe mic control |
| July 2026 | Hermes Agent v0.18.2 installed, pointed at Ollama server (`100.88.1.86`) |
| July 15, 2026 | Confirmed V1.0 complete. Began planning V1.1. |
| July 16, 2026 | Large research batch submitted — GitHub repos, websites, YouTube channels, models |
