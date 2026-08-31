Delegate to the `academic-paper-reviewer` skill.

This skill runs a 7-agent parallel peer review: EIC + 3 domain reviewers + Devil's Advocate + Synthesizer + Reproducibility auditor.

## Modes available

| Mode | When to use |
|---|---|
| `quick` | Fast triage: contribution, gap, fatal flaws only. Use for rapid go/no-go. |
| `standard` | Full review: all sections, methodology, experiments, writing. Use for own drafts or assigned reviews. |
| `revision` | Re-review after author response. Requires original review + revised manuscript. |
| `targeted` | Focus on one specific weakness (e.g., baseline comparison, statistical analysis). |
| `summary` | Structured digest for literature review context. Not a critical review. |

## Inputs required

- Paper (PDF or full text pasted)
- Target venue (journal or conference name)
- Review mode (default: `standard`)
- Any specific concerns the user wants addressed

If the user has not specified a mode, ask only if the paper purpose is ambiguous. Default to `standard` for journal submissions and own drafts.

## Output format

Follow the `academic-paper-reviewer` skill output structure:
- EIC decision with justification
- Per-reviewer findings (strength, weakness, recommendation)
- Devil's Advocate rebuttal
- Synthesized final recommendation
- Reproducibility audit summary
- Actionable revision list (Critical / Important / Minor)
