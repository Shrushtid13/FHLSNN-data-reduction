---
title: "NEXUS — Crisis Coordination OS · PRD"
description: "Product Requirements Document for a distributed, offline-first crisis coordination platform for hospitality venues."
audience: [ai-agents, developers, judges]
tags: [crisis-response, offline-first, edge-computing, hospitality, gemini-ai]
created: 2026-04-15
updated: 2026-04-15
category: "product-planning"
status: draft
hackathon: "Solution Challenge 2026 India — Build with AI"
track: "Track 2 · Rapid Crisis Response"
---

# NEXUS — Product Requirements Document

> A distributed, offline-first crisis coordination OS for hospitality — giving every stakeholder the right information before they have to ask for it.

---

## 1. Executive Summary

**NEXUS** is a venue-wide crisis coordination platform that fuses sensor data, staff reports, and guest inputs into a single shared operational picture — then routes role-specific instructions to every stakeholder with **zero internet required**.

The core architectural bet: the **edge node is the primary compute unit**, not a relay to the cloud. Every design choice flows from that constraint — because crises are precisely when networks fail.

| Attribute        | Detail                                                     |
| ---------------- | ---------------------------------------------------------- |
| **Hackathon**    | Solution Challenge 2026 India · Build with AI              |
| **Track**        | Track 2 — Rapid Crisis Response in Hospitality             |
| **Team Size**    | 1–4 members                                                |
| **Build Window** | 2–3 weeks                                                  |
| **Tech Spine**   | React · Firebase · Node.js · Gemini API · TypeScript       |
| **Key Demo**     | Kill the network mid-incident → system keeps running → reconnect → state merges |

---

## 2. Problem Statement

### The Information Void

When a crisis hits a hotel or venue, the people who need information most don't have it — and those who do can't coordinate fast enough.

| Constraint                        | Reality                                                                             |
| --------------------------------- | ----------------------------------------------------------------------------------- |
| **90 seconds**                    | Window between a contained fire and a catastrophe                                   |
| **3 minutes**                     | Survivability threshold for cardiac arrest                                          |
| **400 anonymous guests**          | No shared operational picture across the venue                                      |
| **Siloed radios**                 | Housekeeper → supervisor → front desk = 4–7 min chain under best conditions         |
| **Network dependency**            | Wi-Fi, cellular, and central servers are the first things to fail during real crises |
| **Invisible guests**              | No structured channel into the response — only a busy front desk or 911             |
| **No post-incident accountability** | Information existed, but never reached the right person in time                    |

### Root Cause

Current hospitality emergency systems are **centralized, network-dependent, and role-siloed**. They assume connectivity, sequential communication chains, and that guests are passive bystanders — all assumptions that collapse under real crisis conditions.

---

## 3. Proposed Solution

### Architecture Overview — Six-Stage Pipeline

```
┌───────────────┐    ┌──────────────┐    ┌───────────────────────┐
│ 1. Signal     │───▸│ 2. Edge      │───▸│ 3. Corroboration      │
│    Ingestion  │    │    Fusion    │    │    Threshold          │
│               │    │  (< 10 sec)  │    │  Watch→Alert→Incident │
└───────────────┘    └──────────────┘    └───────────┬───────────┘
                                                     │
                                                     ▼
┌───────────────┐    ┌──────────────┐    ┌───────────────────────┐
│ 6. CRDT Sync  │◂───│ 5. Delivery  │◂───│ 4. Playbook           │
│  (merge on    │    │  (role-scoped│    │    Dispatch            │
│   reconnect)  │    │   push)      │    │  (auto task queue)     │
└───────────────┘    └──────────────┘    └───────────────────────┘
```

| Stage | What Happens | Key Benefit |
| ----- | ------------ | ----------- |
| **Signal Ingestion** | Sensors, guest QR reports, staff alerts, camera anomalies feed in simultaneously | No single source trusted alone |
| **Edge Fusion** | Each floor's edge node processes signals locally — no cloud hop | Detection-to-alert in 10 seconds |
| **Corroboration** | Watch → Alert → Incident escalation only when multiple signals agree | Eliminates "cry wolf" conditioning |
| **Playbook Dispatch** | Auto-generates a task queue per role (housekeeping, F&B, management) | Staff see only their next action |
| **Stakeholder Delivery** | Guests get browser push in their language; responders get structured briefs | Zero-friction, multilingual |
| **CRDT Sync** | Conflict-free replicated data — nodes continue independently, merge on reconnect | No data loss, no manual resolution |

---

## 4. Key Innovations

| Innovation | Description |
| ---------- | ----------- |
| **Offline-first by design** | Edge nodes are the primary compute unit. Internet loss is the default assumption, not an edge case. |
| **Corroboration before escalation** | Watch / Alert / Incident model eliminates false positives. Staff see trust levels build in real time. |
| **Role-scoped task routing** | Staff see exactly one thing: their next action. Managers see only blocked tasks and resource conflicts. |
| **Guest channel with zero friction** | QR codes in every room → no-login, no-app, four-button panic interface. Reports are geocoded by QR. |
| **First responder pre-brief** | Structured brief (floor plan, headcount, incident zone, casualties, evacuation status) before arrival. |
| **Shift handover as protocol** | Incident ownership transfer requires an acknowledgment handshake — 10-second interaction. |

---

## 5. User Personas & Flows

### 5.1 Personas

| Persona | Role | Primary Need | NEXUS Interaction |
| ------- | ---- | ------------ | ----------------- |
| **Duty Manager** | Incident commander | Full operational picture, override controls | Dashboard with floor plan overlay, blocked-task surface |
| **Staff Member** | Housekeeping, F&B, security | Exactly one clear instruction | Mobile task app — acknowledge + complete loop |
| **Guest** | Hotel visitor, no prior setup | Safety information in their language | QR-activated PWA — 4-button panic report |
| **First Responder** | Fire, medical, police | Structured pre-arrival brief | Auto-generated brief with floor plan + headcount |

### 5.2 Critical User Flows

**Flow A — Guest Reports Fire**
```
Guest scans room QR → PWA loads (no install) → Taps "Fire" →
Report geocoded by QR → Edge node ingests signal →
Corroboration engine checks for confirming signals →
If confirmed: Incident declared → Playbook dispatches tasks →
Staff get role-specific instructions → Guest gets evacuation direction in their language
```

**Flow B — Network Fails Mid-Incident**
```
Incident in progress → Network goes down →
Edge nodes continue independently → Staff keep acknowledging tasks (offline) →
Network restores → CRDT merge → All state reconciled → No data lost
```

---

## 6. MVP Scope — Hackathon Deliverables

> The MVP solves the single hardest problem first: **the information void between incident detection and staff notification**. Everything else builds on this foundation.

### 6.1 MVP Components

| # | Component | Description | Key Deliverable |
| - | --------- | ----------- | --------------- |
| 1 | **Edge Node Simulation** | Simulated floor nodes with local state, sensor signal ingestion (mock data), offline-capable sync | Demonstrate edge-first architecture without hardware |
| 2 | **Corroboration Engine** | Watch / Alert / Incident state machine, multi-source signal fusion, false positive suppression | Show graduated escalation with confidence scoring |
| 3 | **Staff Task App** | Role-based task queue (PWA), acknowledge + complete loop, offline-first with local sync | Working mobile task interface |
| 4 | **Duty Manager Dashboard** | Live incident feed with floor plan overlay, task completion by role, blocked-task surface + override | Command center for incident management |
| 5 | **Guest Panic Interface** | QR-activated PWA, no login, four-button report (fire / medical / security / other), geocoded by QR | Zero-friction guest input channel |
| 6 | **Responder Brief Generator** | Auto-generated incident summary, floor plan + headcount export, live-update via QR at venue entry | Structured first-responder handoff |

### 6.2 Out of Scope (Hackathon)

- Physical hardware deployment (Raspberry Pi edge nodes)
- Production CRDT implementation (Automerge) — Firestore offline persistence used instead
- WebRTC peer-to-peer fallback
- ONVIF camera integration
- Vertex AI migration (Gemini API direct calls sufficient)
- Real SMS/call integration with emergency services

---

## 7. Technical Architecture

### 7.1 Stack Summary

| Layer | Technology | Rationale |
| ----- | ---------- | --------- |
| **Frontend — Web** | React + Vite, Tailwind + shadcn/ui, Workbox (PWA) | Dashboard + guest PWA. Instant HMR, zero config, PWA caching for offline |
| **Frontend — Mobile** | React Native (Expo) | Staff task app on iOS/Android from single codebase |
| **Backend** | Node.js + Express, Firebase Cloud Functions, TypeScript, Zod | Serverless for cloud logic; Express for edge sim; TypeScript everywhere |
| **Database** | Firestore (cloud), IndexedDB via Dexie.js (local), SQLite (edge sim) | Document model maps to incident state; IndexedDB for offline PWA; SQLite for edge append-only log |
| **Real-Time** | Firestore listeners, Firebase Cloud Messaging, Socket.io (edge sim) | Free `onSnapshot` for live updates; FCM for push; Socket.io for mesh simulation |
| **Offline Sync** | Firestore offline persistence, Dexie.js, Workbox | CRDT-like sync for free — queue writes locally, merge on reconnect |
| **AI** | Gemini API (Google AI SDK) | Classification, corroboration scoring, brief generation, i18n — see §7.2 |
| **Deployment** | Firebase Hosting, Cloud Functions, GCP Artifact Registry, Firebase App Check, Cloud Logging | Global CDN, one CLI deploy, Docker for edge sim, abuse protection, audit trail |

### 7.2 AI Integration (Gemini)

| Capability | Model | What It Does |
| ---------- | ----- | ------------ |
| **Incident Classification** | Gemini 2.5 Flash | Classifies free-text guest reports by type and severity. Multilingual, handles panicked input. |
| **Corroboration Scoring** | Gemini + Structured Output | Given N signals, outputs Watch/Alert/Incident with confidence score and one-line rationale. |
| **Responder Brief Generation** | Gemini 2.5 Pro | Auto-drafts first responder handoff brief from incident state → structured JSON → readable brief. |
| **Guest Notification Copy** | Gemini + i18n | Translates and tone-adjusts evacuation instructions per device locale. Calibrated for panic. |

### 7.3 Architecture Diagram

```
                        ┌─────────────────────────────┐
                        │      Firebase Hosting        │
                        │  (Dashboard PWA, Guest PWA)  │
                        └─────────────┬───────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                  │
              ┌─────▼─────┐   ┌──────▼──────┐   ┌──────▼──────┐
              │  Manager   │   │  Guest PWA  │   │  Staff App  │
              │ Dashboard  │   │ (QR entry)  │   │  (Expo)     │
              │ React+Vite │   │ React+Vite  │   │ React Native│
              └─────┬──────┘   └──────┬──────┘   └──────┬──────┘
                    │                 │                  │
                    └────────┬────────┘                  │
                             │                           │
                    ┌────────▼───────────────────────────▼──┐
                    │         Firestore (Cloud)              │
                    │  incidents / tasks / roles / signals   │
                    │  + offline persistence + listeners     │
                    └────────┬──────────────────────────────┘
                             │
                    ┌────────▼──────────┐
                    │  Cloud Functions  │
                    │  · Corroboration  │
                    │  · Playbook       │
                    │  · Gemini calls   │
                    └────────┬──────────┘
                             │
                    ┌────────▼──────────┐
                    │  Edge Node Sim    │
                    │  Express+Socket.io│
                    │  SQLite local log │
                    └───────────────────┘
```

---

## 8. Evaluation Alignment

> How NEXUS maps to Solution Challenge 2026 judging criteria.

### Technical Merit — 40%

| Criterion | NEXUS Response |
| --------- | -------------- |
| **Technical Complexity** | Distributed edge-first architecture, CRDT-inspired sync, multi-source signal fusion, Gemini AI pipeline |
| **AI Integration** | Four distinct Gemini use cases — classification, corroboration, brief generation, i18n. AI is structurally necessary, not bolted on. |
| **Performance & Scalability** | Edge nodes process locally (no cloud hop). Firestore's horizontal scale handles venue-to-chain growth. |
| **Security & Privacy** | Firebase App Check blocks abuse. Append-only audit log. Guest data is ephemeral (no accounts). |

### User Experience — 10%

| Criterion | NEXUS Response |
| --------- | -------------- |
| **Design & Navigation** | Role-scoped interfaces — each persona sees only what they need |
| **User Flow** | Guest: scan → tap → done. Staff: see task → acknowledge → complete. Manager: overview → drill-down → override. |
| **Accessibility** | PWA works on any device. Multilingual via Gemini. No app install required for guests. |

### Alignment With Cause — 25%

| Criterion | NEXUS Response |
| --------- | -------------- |
| **Problem Definition** | Directly addresses the information void during hospitality crises — quantified with real time constraints (90 sec, 3 min) |
| **Relevance** | Every feature maps to a documented failure mode in current systems |
| **Expected Impact** | Reduces detection-to-notification gap from 4–7 minutes to under 15 seconds |

### Innovation & Creativity — 25%

| Criterion | NEXUS Response |
| --------- | -------------- |
| **Originality** | Edge-first + corroboration threshold + zero-friction guest input is a novel combination |
| **Creative Use of Tech** | Firestore offline persistence as a CRDT substitute; Gemini for panic-input classification; QR geocoding |
| **Future Potential** | Scales from single venue to hotel chains. Append-only log enables insurance/legal/training use cases. |

---

## 9. Requirements

### 9.1 Functional Requirements

| ID | Requirement | Priority | Component |
| -- | ----------- | -------- | --------- |
| FR-01 | System shall ingest signals from multiple sources (sensors, staff, guests) simultaneously | P0 | Edge Node Sim |
| FR-02 | System shall escalate through Watch → Alert → Incident states based on corroboration | P0 | Corroboration Engine |
| FR-03 | System shall auto-generate role-specific task queues upon incident declaration | P0 | Playbook Dispatch |
| FR-04 | Staff shall see, acknowledge, and complete tasks via mobile interface | P0 | Staff Task App |
| FR-05 | Duty manager shall view live incident feed with floor plan overlay | P0 | Manager Dashboard |
| FR-06 | Guests shall report emergencies via QR-activated, no-login PWA | P0 | Guest Panic Interface |
| FR-07 | System shall auto-generate structured first responder briefs | P1 | Responder Brief Gen |
| FR-08 | System shall classify free-text guest reports by type and severity (Gemini) | P1 | AI Integration |
| FR-09 | System shall translate evacuation instructions to guest's device locale | P1 | AI Integration |
| FR-10 | System shall continue operating when network connectivity is lost | P0 | Offline Sync |
| FR-11 | System shall merge state deterministically when connectivity is restored | P0 | Offline Sync |
| FR-12 | System shall log all events to an append-only store for post-incident review | P2 | Audit Trail |

### 9.2 Non-Functional Requirements

| ID | Requirement | Target |
| -- | ----------- | ------ |
| NFR-01 | Detection-to-alert latency | < 10 seconds (edge-local) |
| NFR-02 | Alert-to-staff-notification | < 15 seconds |
| NFR-03 | Guest PWA load time (cached) | < 2 seconds |
| NFR-04 | Offline operation duration | Indefinite (edge node) |
| NFR-05 | State merge correctness | Zero data loss on reconnect |
| NFR-06 | Concurrent staff users | 50+ per venue |
| NFR-07 | Guest report languages | 10+ via Gemini |

---

## 10. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
| ---- | ------ | ---------- | ---------- |
| Firestore offline sync doesn't cover all edge cases | MVP demo fails during network-kill moment | Medium | Test offline scenarios early and repeatedly. Have Dexie.js fallback for critical writes. |
| Gemini API rate limits during demo | AI features stall in front of judges | Medium | Cache common classifications. Use Gemini Flash for latency-sensitive calls. Pre-generate sample briefs as fallback. |
| Scope creep — building too many components | Nothing works well vs. everything working partially | High | Strictly prioritize P0 components. Cut P1/P2 before compromising P0 quality. |
| Edge sim doesn't convincingly demonstrate offline-first | Judges miss the core innovation | Medium | Script a specific demo flow: live operation → kill network → continue → reconnect → merge. Make it theatrical. |
| Team velocity — 2–3 week build window | Incomplete MVP | Medium | Use Firebase as much as possible to avoid building infrastructure. Shared components between React apps. |

---

## 11. Implementation Phases

### Phase 1 — Foundation (Days 1–3)

- [ ] Project scaffolding: monorepo with shared TypeScript config
- [ ] Firebase project setup (Firestore, Hosting, Cloud Functions, FCM)
- [ ] Firestore data model: `incidents`, `signals`, `tasks`, `roles`, `venues`
- [ ] Basic React + Vite app shell (shared between dashboard and guest PWA)

### Phase 2 — Core Engine (Days 4–7)

- [ ] Edge node simulation server (Express + Socket.io + SQLite)
- [ ] Mock signal ingestion pipeline (sensor data generator)
- [ ] Corroboration engine: Watch → Alert → Incident state machine
- [ ] Gemini integration: incident classification + corroboration scoring
- [ ] Playbook dispatch: role-based task generation on incident trigger

### Phase 3 — User Interfaces (Days 8–12)

- [ ] Duty manager dashboard: incident feed, floor plan overlay, task board, override panel
- [ ] Staff task app: role-scoped queue, acknowledge/complete flow, offline-first
- [ ] Guest panic interface: QR-activated PWA, 4-button report, geocoded
- [ ] Responder brief generator: auto-generated summary, export

### Phase 4 — Offline & Sync (Days 13–15)

- [ ] Firestore offline persistence integration across all apps
- [ ] Dexie.js for IndexedDB local storage in PWAs
- [ ] Workbox configuration for PWA shell caching
- [ ] Network-kill demo flow: operate → disconnect → reconnect → merge

### Phase 5 — Polish & Demo Prep (Days 16–18)

- [ ] End-to-end demo script with scripted incident scenario
- [ ] Gemini i18n for guest notifications
- [ ] Append-only audit log for compliance demo
- [ ] Project deck, demo video (3 min), GitHub repo cleanup
- [ ] Firebase App Check for guest interface abuse protection

---

## 12. Success Metrics

| Metric | Target | How to Measure |
| ------ | ------ | -------------- |
| Detection → staff notification | < 15 seconds | Timed demo flow |
| Offline operation | System runs indefinitely without network | Network-kill demo |
| State merge on reconnect | Zero data loss | Before/after comparison in demo |
| Guest report → classification | < 3 seconds (Gemini Flash) | Timed API call |
| Responder brief generation | < 5 seconds from incident state | Timed end-to-end |
| Guest PWA load (cached) | < 2 seconds | Lighthouse audit |
| Demo scenario completion | Full incident lifecycle in < 5 minutes | Rehearsed demo run |

---

## 13. Key Demo Moment

> **The single most important demo moment:** kill the network mid-incident, keep taking actions, reconnect, and watch state merge. This demonstrates the hardest NEXUS promise — "works with zero internet" — using Firestore's offline persistence without building a single line of sync logic.

### Scripted Demo Flow

1. **Setup** — Show venue map, staff logged in, guest PWA accessible via QR
2. **Signal** — Guest scans QR, reports fire. Staff member reports smoke on same floor.
3. **Corroboration** — System escalates Watch → Alert → Incident with Gemini confidence score
4. **Dispatch** — Role-specific tasks auto-generated. Staff app shows individual tasks.
5. **Network Kill** — Visibly disconnect from internet. System continues.
6. **Offline Ops** — Staff acknowledge tasks. Manager overrides a blocked task. Guest gets cached evacuation instruction.
7. **Reconnect** — Restore network. All state merges. Audit log complete.
8. **Brief** — Show auto-generated first responder brief with floor plan and headcount.

---

## 14. Deliverables Checklist

| Deliverable | Required By | Format |
| ----------- | ----------- | ------ |
| Problem Statement | Phase 1 submission | Text in submission form |
| Solution Overview | Phase 1 submission | Text in submission form |
| Working Prototype | Phase 1 submission | Live URL (Firebase Hosting) |
| Project Deck | Phase 1 submission | PDF/Google Slides |
| GitHub Repository | Phase 1 submission | Public repo link |
| Demo Video | Phase 1 submission | < 3 min video |
| Refined Prototype | Phase 2 (if shortlisted) | Updated live URL |
| Final Prototype | Phase 3 (if finalist) | Fully functional demo-ready URL |
| Final Demo Video | Phase 3 (if finalist) | < 3 min refined video |

---

*NEXUS: The edge node is the system. The cloud is a convenience.*
