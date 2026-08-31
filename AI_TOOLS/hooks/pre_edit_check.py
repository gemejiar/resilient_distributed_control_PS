import json

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "additionalContext": (
            "pre_edit_check (advisory, non-blocking): (1) Read AGENTS.md if not "
            "already read this session. (2) Confirm the target file is allowed at "
            "the current phase gate (see ops/sted/decision_log.md and "
            "plan_maestro.md). (3) Check whether the requested content depends on "
            "evidence that is still missing before writing it."
        ),
    }
}))
