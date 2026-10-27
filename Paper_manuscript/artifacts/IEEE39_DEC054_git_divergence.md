# DEC-054 P0 — Git divergence diagnosis (read-only; nothing was changed)

Commands (read-only): `git fetch rdc`, `git ls-remote rdc`, `git branch -vv`, `git merge-base main rdc/main`, `git rev-list --left-right --count main...rdc/main`, `git log --left-right main...rdc/main`.

| Item | Value |
|---|---|
| remote `main` (rdc) | `1a023d8fa333e62eb716e57a4d67561bb63ea3d0` (matches the frozen reference) |
| local `main` | `acab954a35cc313a489b7a13fe5f37b727750cb6` |
| merge-base(main, rdc/main) | `1a023d8fa333e62eb716e57a4d67561bb63ea3d0` |
| left-right count | local 6 ahead, 0 behind (pure fast-forward divergence; no conflicting history) |
| remote `review/b3-equilibrium` | `acab954…` = local `main` tip |

The six local-only commits on `main` (oldest first): `4fb8ab5` B3 step 1 (DEC-037); `0d9da24` B3-A verification (DEC-038); `07024ff` B3-S0 (DEC-039); `493b237` B3-P+ (DEC-040); `26965fd` B3-Q+ (DEC-041/042); `acab954` E9-A preparation (DEC-043).

Diagnosis: local `main` contains B3/E9-A work that was committed on `main` locally but published only as the branch `review/b3-equilibrium`; remote `main` was never advanced. All six commits are reachable from the remote branch `review/b3-equilibrium` and from the bundle `rdc_all_refs_dec054.bundle` (clone test: `acab954` present). The DEC-051..DEC-053 branches descend from this history (merge-base with `rdc/main` is `1a023d8`).

Preservation: neither local nor remote `main` was modified, rebased, merged or pushed. Local `main` still equals `acab954`; remote `main` still equals `1a023d8`. A decision on whether to publish or reconcile `main` is left to the investigator.
