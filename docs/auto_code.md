You are an autonomous software engineer.

Your task is to implement a complete working Python project based strictly on the provided design.

## Execution Rules (MANDATORY)
- Follow the design exactly. Do NOT invent new architecture.
- Prefer minimal, clean, production-ready code.
- No over-engineering, no unnecessary abstractions.
- Keep everything synchronous unless explicitly required.
- All components must be implemented and wired together end-to-end.
- The project must be runnable via CLI.

## Development Strategy
Implement step-by-step in this order:

Phase 1: Project scaffold
- Create Python package structure
- Add CLI entrypoint (`python -m analyzer run`)
- Define module layout matching components

Phase 2: Core infrastructure
- Implement:
  - run_state_store (JSON-based)
  - repo_updater (git fetch + fast-forward pull, clean tree check)
  - ModelProvider interface + OllamaHttpProvider

Phase 3: Diff and scope
- Implement diff_scope_builder:
  - compute last_commit..HEAD
  - extract changed files
  - aggregate into focus_paths
  - apply fallback threshold logic

Phase 4: Repo discovery
- Implement repo_discovery using filename + rg heuristics
- Detect:
  - language
  - frameworks
  - entry points
  - config files
  - sensitive dirs

Phase 5: Skill system
- Load ONLY compiled assets from `skills/compiled/`
- Implement skill_selector:
  - threat-model keywords → security-threat-model
  - otherwise → security-best-practices

Phase 6: Prompt builder
- Construct prompt in strict order:
  1. global system role
  2. skill system prompt
  3. task template
  4. repo discovery
  5. diff/focus_paths
  6. user input
  7. JSON output contract

Phase 7: Model execution
- Call ModelProvider.generate(...)
- Return raw string

Phase 8: Result handling
- Validate JSON output
- If invalid:
  - attempt ONE repair pass
- If still invalid:
  - fail and persist raw output
- If success:
  - write JSON result
  - update run_state_store

Phase 9: CLI integration
- Implement command:
  python -m analyzer run --repo ... --prompt ... --scope ... --out ...
- Wire everything through `run_analysis(...)`

## Strict Constraints
- ONLY support Git repos
- MUST fail if working tree is dirty
- MUST use last successful commit as diff base
- MUST fallback to full repo discovery if:
  - no baseline
  - diff too large
- NO AST parsing
- NO async
- NO database
- NO UI
- NO markdown output

## Output Contract (STRICT)
You must enforce this JSON schema:

{
  "skill": string,
  "task_type": string,
  "summary": string,
  "findings": [
    {
      "id": string,
      "title": string,
      "severity": string,
      "category": string,
      "description": string,
      "evidence": string,
      "recommendation": string
    }
  ],
  "metadata": {
    "repo_path": string,
    "head_commit": string,
    "diff_base": string,
    "scope_mode": string,
    "focus_paths": string[],
    "frameworks_detected": string[],
    "model_name": string,
    "partial_context": boolean
  }
}

## Testing Requirements
- Implement minimal test or validation logic for:
  - dirty repo rejection
  - diff fallback
  - skill selection
  - JSON validation

## Completion Criteria
- The project can run end-to-end on a real Git repo
- Produces valid JSON output file
- Handles failure cases correctly
- No missing components

## Now start implementing.
Proceed step by step, writing real code for each phase.
Do not skip steps.
