#!/usr/bin/env python3
"""
Knowledge Base CLI — consolidated interface for research agents.
"""

import sys
import json
from researcher import KnowledgeBase, get_db_path

def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    cmd = sys.argv[1]
    args = sys.argv[2:]

    # ── Init (no DB needed) ──────────────────────────────────────
    if cmd == "init":
        _init_project()
        return

    kb = KnowledgeBase(get_db_path())
    
    try:
        # ── Entity CRUD ──────────────────────────────────────────────

        if cmd == "add":
            title = args[0]
            content = args[1] if len(args) > 1 else ""
            metadata = json.loads(args[2]) if len(args) > 2 else {}
            eid = kb.add_entity(title, content, metadata)
            print(json.dumps({"id": eid, "title": title}))

        elif cmd == "get":
            print(json.dumps(kb.get_entity(args[0]), indent=2))

        elif cmd == "update":
            eid = args[0]
            title = args[1] if len(args) > 1 else None
            content = args[2] if len(args) > 2 else None
            metadata = json.loads(args[3]) if len(args) > 3 else None
            kb.update_entity(eid, title, content, metadata)
            print(json.dumps({"ok": True, "id": eid}))

        elif cmd == "list":
            limit = int(args[0]) if args else None
            print(json.dumps(kb.list_entities(limit), indent=2))

        elif cmd == "search":
            query = args[0]
            if len(args) > 1 and args[1] == '--all':
                print(json.dumps(kb.find_prior_research(query), indent=2))
            else:
                print(json.dumps(kb.search_entities(query), indent=2))

        elif cmd == "stats":
            print(json.dumps(kb.get_stats(), indent=2))

        elif cmd == "export":
            md = kb.export_entity_markdown(args[0])
            print(md if md else f"Not found: {args[0]}")

        elif cmd == "graph":
            fmt = args[0] if args else "dot"
            print(kb.visualize_graph(fmt))

        # ── Links ────────────────────────────────────────────────────

        elif cmd == "link":
            lt = args[2] if len(args) > 2 else "related"
            lid = kb.add_link(args[0], args[1], lt)
            print(json.dumps({"link_id": lid, "from": args[0], "to": args[1], "type": lt}))

        elif cmd == "links":
            direction = args[1] if len(args) > 1 else "from"
            fn = kb.get_links_to if direction == "to" else kb.get_links_from
            print(json.dumps(fn(args[0]), indent=2))

        # ── Tasks ────────────────────────────────────────────────────

        elif cmd == "add-task":
            title = args[0]
            desc = args[1] if len(args) > 1 else ""
            eid = args[2] if len(args) > 2 and args[2] != "null" else None
            meta = json.loads(args[3]) if len(args) > 3 else {}
            tid = kb.add_task(title, desc, eid, meta)
            print(json.dumps({"task_id": tid, "title": title}))

        elif cmd == "tasks":
            status = args[0] if args and args[0] != "null" else None
            eid = args[1] if len(args) > 1 else None
            print(json.dumps(kb.get_tasks(status, eid), indent=2))

        elif cmd == "update-task":
            tid = int(args[0])
            status = args[1]
            kb.update_task_status(tid, status)
            print(json.dumps({"task_id": tid, "status": status}))

        # ── Sources ──────────────────────────────────────────────────

        elif cmd == "add-source":
            url = args[0]
            title = args[1] if len(args) > 1 else ""
            snippet = args[2] if len(args) > 2 else ""
            stype = args[3] if len(args) > 3 else "web"
            meta = json.loads(args[4]) if len(args) > 4 else None
            sid = kb.add_source(url, title, snippet, stype, meta)
            cred = kb.get_source(sid)['credibility']
            print(json.dumps({"source_id": sid, "url": url, "credibility": cred}))

        elif cmd == "sources":
            eid = args[0] if args and args[0] != "null" else None
            mc = float(args[1]) if len(args) > 1 else 0.0
            print(json.dumps(kb.list_sources(eid, mc), indent=2))

        # ── Claims ───────────────────────────────────────────────────

        elif cmd == "add-claim":
            text = args[0]
            eid = args[1] if len(args) > 1 and args[1] != "null" else None
            sids = json.loads(args[2]) if len(args) > 2 else None
            meta = json.loads(args[3]) if len(args) > 3 else None
            cid = kb.add_claim(text, eid, sids, meta)
            c = kb.get_claim(cid)
            print(json.dumps({"claim_id": cid, "grade": c['evidence_grade'], "confidence": c['confidence']}))

        elif cmd == "add-claim-source":
            cid, sid = int(args[0]), int(args[1])
            rel = args[2] if len(args) > 2 else "supports"
            ok = kb.add_claim_source(cid, sid, rel)
            c = kb.get_claim(cid)
            print(json.dumps({"ok": ok, "claim_id": cid, "grade": c['evidence_grade']}))

        elif cmd == "claim":
            print(json.dumps(kb.get_claim(int(args[0])), indent=2))

        elif cmd == "claims":
            eid = args[0] if args and args[0] != "null" else None
            grade = args[1] if len(args) > 1 and args[1] != "null" else None
            print(json.dumps(kb.list_claims(eid, grade), indent=2))

        elif cmd == "decompose":
            cid = int(args[0])
            method = args[1] if len(args) > 1 else 'auto'
            atom_ids = kb.decompose_claim(cid, method)
            if atom_ids:
                atoms = kb.get_atomic_claims(cid)
                print(json.dumps({'parent_id': cid, 'atoms': [
                    {'id': a['id'], 'text': a['claim_text'], 'grade': a['evidence_grade']} for a in atoms
                ]}, indent=2))
            else:
                print(json.dumps({'parent_id': cid, 'result': 'singleton'}))

        elif cmd == "quote":
            print(json.dumps(kb.extract_quotes(int(args[0])), indent=2, default=str))

        elif cmd == "claim-from-quote":
            qt = args[0]; sid = int(args[1])
            eid = args[2] if len(args) > 2 else None
            ct = args[3] if len(args) > 3 else None
            print(json.dumps(kb.claim_from_quote(qt, sid, eid, ct), indent=2, default=str))

        # ── Review (unified: reflect + critique + gaps + quantities) ─

        elif cmd == "review":
            eid = args[0]
            depth = args[1] if len(args) > 1 else 'full'
            print(json.dumps(kb.review(eid, depth), indent=2, default=str))

        # ── QA (unified: SC grading + SAFE verification) ────────────

        elif cmd == "qa":
            eid = args[0]
            n = int(args[1]) if len(args) > 1 else 5
            print(json.dumps(kb.qa(eid, n_samples=n), indent=2, default=str))

        elif cmd == "verify":
            print(json.dumps(kb.verify_claim(int(args[0])), indent=2, default=str))

        elif cmd == "grade-sc":
            cid = int(args[0])
            n = int(args[1]) if len(args) > 1 else 5
            print(json.dumps(kb.grade_claim_sc(cid, n), indent=2, default=str))

        # ── Report (unified: report + synthesize + outline) ──────────

        elif cmd == "report":
            eid = args[0]
            fmt = args[1] if len(args) > 1 else 'full'
            audience = args[2] if len(args) > 2 else 'technical'
            if fmt == 'outline':
                result = kb.generate_outline(eid)
                print(json.dumps(result, indent=2) if result else "Not found")
            elif fmt == 'synthesize':
                print(json.dumps(kb.synthesize_entity(eid, audience), indent=2, default=str))
            else:
                report = kb.generate_report(eid, include_children=True)
                print(report if report else "Not found")

        # ── Evidence analysis ────────────────────────────────────────

        elif cmd == "contradictions":
            eid = args[0] if args else None
            print(json.dumps(kb.check_contradictions(eid), indent=2))

        elif cmd == "corroboration":
            eid = args[0] if args else None
            print(json.dumps(kb.check_corroboration(eid), indent=2))

        elif cmd == "decay":
            days = int(args[0]) if args else 30
            rate = float(args[1]) if len(args) > 1 else 0.02
            affected = kb.apply_confidence_decay(days, rate)
            print(json.dumps({"affected": len(affected)}, indent=2))

        # ── Evaluation loop ──────────────────────────────────────────

        elif cmd == "add-eval":
            pid = args[0]
            mi = int(args[1]) if len(args) > 1 else 5
            crit = json.loads(args[2]) if len(args) > 2 else None
            eid = kb.add_evaluation(pid, mi, crit)
            print(json.dumps({"eval_id": eid, "parent_id": pid}))

        elif cmd == "eval":
            print(json.dumps(kb.get_evaluation(int(args[0])), indent=2))

        elif cmd == "evals":
            print(json.dumps(kb.get_evaluations_for(args[0]), indent=2))

        elif cmd == "update-eval":
            eid = int(args[0]); u = json.loads(args[1])
            kb.update_evaluation(eid, confidence=u.get('confidence'), gaps=u.get('gaps'),
                contradictions=u.get('contradictions'), decision=u.get('decision'),
                rationale=u.get('rationale'), status=u.get('status'), iteration=u.get('iteration'))
            print(json.dumps({"ok": True, "eval_id": eid}))

        elif cmd == "converged":
            print(json.dumps(kb.check_convergence(int(args[0])), indent=2))

        # ── Traces ───────────────────────────────────────────────────

        elif cmd == "trace":
            eid = args[0]; action = args[1]
            inp = args[2] if len(args) > 2 else ""
            out = args[3] if len(args) > 3 else ""
            reas = args[4] if len(args) > 4 else ""
            tool = args[5] if len(args) > 5 else ""
            tid = kb.add_trace(eid, action, inp, out, reas, tool)
            print(json.dumps({"trace_id": tid, "entity_id": eid}))

        elif cmd == "traces":
            eid = args[0]
            if len(args) > 1 and args[1] == '--summary':
                print(kb.get_trace_summary(eid))
            else:
                print(json.dumps(kb.get_traces(eid), indent=2))

        # ── Perspectives ─────────────────────────────────────────────

        elif cmd == "perspectives":
            print(json.dumps(kb.discover_perspectives(args[0]), indent=2))

        # ── Router ───────────────────────────────────────────────────

        elif cmd == "route":
            desc = args[0]
            meta = json.loads(args[1]) if len(args) > 1 else None
            print(json.dumps(kb.route_task(desc, meta), indent=2))

        # ── Spawning ─────────────────────────────────────────────────

        elif cmd == "spawn":
            pid = args[0]; title = args[1]
            content = args[2] if len(args) > 2 else ""
            atype = args[3] if len(args) > 3 else "researcher"
            meta = json.loads(args[4]) if len(args) > 4 else {}
            print(json.dumps(kb.record_spawn(pid, title, content, atype, meta), indent=2))

        elif cmd == "budget":
            eid = args[0]
            md = int(args[1]) if len(args) > 1 else 8
            mt = int(args[2]) if len(args) > 2 else 400
            print(json.dumps(kb.check_spawn_budget(eid, md, mt), indent=2))

        elif cmd == "context":
            print(json.dumps(kb.get_spawn_context(args[0]), indent=2))

        # ── Monitor ──────────────────────────────────────────────────

        elif cmd == "monitor":
            print(json.dumps(kb.monitor_tree(args[0]), indent=2, default=str))

        # ── Domain Expert ────────────────────────────────────────────

        elif cmd == "expert":
            subcmd = args[0] if args else "list"
            if subcmd == "match":
                print(json.dumps(kb.match_domain_expert(args[1]), indent=2, default=str))
            elif subcmd == "review":
                print(json.dumps(kb.domain_review(args[1], args[2]), indent=2, default=str))
            elif subcmd == "list":
                for d, p in kb.DOMAIN_PROFILES.items():
                    print(f"  {d:20s} | {p['role']}")
            else:
                print(f"Unknown expert subcommand: {subcmd}", file=sys.stderr)

        # ── Decisions (MCDA) ─────────────────────────────────────────

        elif cmd == "decide":
            subcmd = args[0]
            if subcmd == "add":
                title = args[1]; crit = json.loads(args[2]); alts = json.loads(args[3])
                eid = args[4] if len(args) > 4 and args[4] != "null" else None
                w = json.loads(args[5]) if len(args) > 5 else None
                did = kb.add_decision(title, crit, alts, eid, w)
                print(json.dumps({"decision_id": did}))
            elif subcmd == "score":
                print(json.dumps(kb.score_alternatives(int(args[1]), json.loads(args[2])), indent=2))
            elif subcmd == "sensitivity":
                p = float(args[2]) if len(args) > 2 else 0.1
                print(json.dumps(kb.sensitivity_analysis(int(args[1]), p), indent=2))
            elif subcmd == "get":
                print(json.dumps(kb.get_decision(int(args[1])), indent=2))

        # ── Embed & Search ───────────────────────────────────────────

        elif cmd == "embed":
            subcmd = args[0] if args else "all"
            if subcmd == "all":
                print(json.dumps(kb.embed_all(), indent=2))
            elif subcmd == "entity":
                print(json.dumps({"entity_id": args[1], "ok": kb.embed_entity(args[1])}))
            elif subcmd == "claim":
                print(json.dumps({"claim_id": int(args[1]), "ok": kb.embed_claim(int(args[1]))}))

        elif cmd == "semantic":
            q = args[0]; lim = int(args[1]) if len(args) > 1 else 10
            print(json.dumps(kb.semantic_search(q, lim), indent=2))

        elif cmd == "hybrid":
            q = args[0]; lim = int(args[1]) if len(args) > 1 else 10
            print(json.dumps(kb.hybrid_search(q, lim), indent=2))

        # ── Thompson Sampling ────────────────────────────────────────

        elif cmd == "gaps":
            subcmd = args[0]
            if subcmd == "select":
                eid = int(args[1]); n = int(args[2]) if len(args) > 2 else 3
                print(json.dumps(kb.select_next_gaps(eid, n), indent=2))
            elif subcmd == "register":
                kb.register_gap_topics(int(args[1]), json.loads(args[2]))
                print(json.dumps({"ok": True}))

        else:
            print(f"Unknown command: {cmd}", file=sys.stderr)
            print_usage()
            sys.exit(1)

    finally:
        kb.close()

def print_usage():
    print("""
Knowledge Base CLI — Research Agent Interface

Usage: kb-cli <command> [args...]

CORE
  add <title> [content] [meta_json]              Create entity
  get <id>                                        Get entity
  update <id> [title] [content] [meta_json]       Update entity
  list [limit]                                    List entities
  search <query> [--all]                          Search (--all includes claims)
  stats                                           DB statistics

LINKS
  link <from> <to> [type]                         Create link
  links <id> [from|to]                            Get links

TASKS
  add-task <title> [desc] [entity_id] [meta]      Create task
  tasks [status] [entity_id]                       List tasks
  update-task <task_id> <status>                   Update task status

SOURCES
  add-source <url> [title] [snippet] [type]        Add source (auto-scores)
  sources [entity_id] [min_credibility]             List sources

CLAIMS
  add-claim <text> [entity_id] [source_ids] [meta]  Add claim (auto-grades)
  add-claim-source <claim_id> <source_id> [rel]      Link source to claim
  claim <id>                                          Get claim with sources
  claims [entity_id] [grade]                          List claims
  decompose <claim_id> [method]                       Split into atomic claims
  quote <source_id>                                   Extract quotable snippets
  claim-from-quote <quote> <source_id> [eid] [text]   FRONT: grounded claim

REVIEW (unified quality checks)
  review <entity_id> [quick|full]                 All-in-one review (reflect+critique+gaps+quant)

QUALITY ASSURANCE
  qa <entity_id> [n_samples]                      SC grading + SAFE verification in one pass
  verify <claim_id>                                SAFE-verify single claim
  grade-sc <claim_id> [n_samples]                  Self-consistency grade single claim

REPORT (unified output)
  report <entity_id> [full|outline|synthesize] [audience]
                                                   full=cited report, outline=structured, synthesize=themed

EVIDENCE
  contradictions [entity_id]                       Find contradicted claims
  corroboration [entity_id]                        Score claim support ratios
  decay [days] [rate]                               Apply confidence decay

EVALUATION LOOP
  add-eval <parent_id> [max_iter] [criteria]       Start evaluation
  eval <eval_id>                                    Get evaluation state
  evals <parent_id>                                 Get all evals for entity
  update-eval <eval_id> <json_updates>              Update evaluation
  converged <eval_id>                               Check convergence

TRACES
  trace <entity_id> <action> [in] [out] [reason]   Log reasoning step
  traces <entity_id> [--summary]                    Get traces (--summary for compact)

ROUTING & SPAWNING
  route "description" [meta_json]                  Auto-select coordinator
  spawn <parent> <title> [content] [agent_type]    Spawn sub-entity
  budget <entity_id> [max_depth] [max_total]       Check spawn budget
  context <entity_id>                               Get parent/sibling context

MONITORING
  monitor <root_entity_id>                         Tree health & progress dashboard

DOMAIN EXPERT
  expert list                                      List domain profiles
  expert match "topic text"                        Match topic to experts
  expert review <entity_id> <domain>               Domain-specific review

PERSPECTIVES
  perspectives <topic>                             Discover research angles

DECISIONS (MCDA)
  decide add <title> <criteria> <alts> [eid]       Create decision
  decide score <id> <scores_json>                  Score alternatives
  decide sensitivity <id> [perturbation]           Test robustness
  decide get <id>                                  Get decision

EMBEDDING & SEARCH
  embed [all|entity <id>|claim <id>]               Vector embeddings
  semantic <query> [limit]                          Semantic search
  hybrid <query> [limit]                            FTS5 + vector RRF search

THOMPSON SAMPLING
  gaps select <eval_id> [n]                        Select next gaps to investigate
  gaps register <eval_id> <topics_json>            Register gap topics

EXPORT
  export <entity_id>                               Export entity as markdown
  graph [dot|json]                                  Visualize knowledge graph

SETUP
  init                                              Scaffold project with KB + agent instructions
""")


_COPILOT_INSTRUCTIONS = """# Copilot Instructions — Researcher

This project has a research knowledge base. Use the `kb` command to interact with it.

## Quick Start

```bash
kb stats                                    # What's in the KB
kb search "your topic"                      # Find existing research
kb add "Research: Topic" "Description"      # Start new research
kb add-claim <entity_id> "Finding" 0.8 0.9  # Add claims
kb review <entity_id> full                  # Quality review
kb report <entity_id> synthesize executive  # Generate report
kb route "Task description"                 # Pick coordinator
```

## Key Commands

| Command | Purpose |
|---------|---------|
| `kb stats` | DB overview |
| `kb search <q> [--all]` | Find existing research |
| `kb add / get / update / list` | Entity CRUD |
| `kb add-claim / claims` | Claim management |
| `kb review <eid> full` | Quality review (4 checks) |
| `kb qa <eid>` | Batch verification + grading |
| `kb report <eid> synthesize` | Themed report |
| `kb route <desc>` | Pick best coordinator |
| `kb spawn / budget / context` | Sub-agent tracking |
| `kb monitor <eid>` | Tree health |
| `kb help` | Full command reference |

All output is JSON. Entity IDs are 12-char hex strings. Run `kb help` for the full command list.
"""


def _init_project():
    """Scaffold current directory with KB and copilot instructions."""
    import os
    from pathlib import Path

    created = []

    # Create knowledge-base directory
    kb_dir = Path("knowledge-base")
    if not kb_dir.exists():
        kb_dir.mkdir()
        created.append("knowledge-base/")

    # Create .copilot-instructions.md
    instructions = Path(".copilot-instructions.md")
    if not instructions.exists():
        instructions.write_text(_COPILOT_INSTRUCTIONS)
        created.append(".copilot-instructions.md")
    else:
        print(f"  exists: {instructions}")

    # Initialize DB
    db_path = kb_dir / "kb.db"
    if not db_path.exists():
        kb = KnowledgeBase(str(db_path))
        kb.close()
        created.append("knowledge-base/kb.db")

    if created:
        print("Initialized researcher KB:")
        for f in created:
            print(f"  + {f}")
    else:
        print("Already initialized.")
    print(f"\nRun `kb stats` to verify.")


if __name__ == "__main__":
    main()
