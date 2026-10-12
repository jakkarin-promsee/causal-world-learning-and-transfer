---
name: commit
description: Stage and commit current repository changes locally in coherent groups with messages that explain the actual work. Use when the user invokes $commit or asks Codex to commit current work.
---

---

**Commit-Progress** — the categorized, readable commit (so the log reads as _progress_, not "wip").

# Commit current work

Invoking this skill authorizes local Git commits of the current working tree without another confirmation. Do not push, rewrite existing commits, edit project files, or run tests unless the user explicitly asks for that work.

Background and detail: This repo is research type, not a web/app development. So, the commit detail will use to track the experiment progress first.

1. `git status` — see what changed since HEAD. **Never `git add -A` blindly**; stage by group.
2. Group related changes by their actual purpose. Use `doc`, `test`, `feat`, `fix`, or `chore` when the contents support that type, and add a scope when it improves clarity. A commit subject must say what was added or changed, such as `feat(core): add exact inference over Boolean worlds`. Avoid generic subjects such as `back up files`, `update code`, or `misc changes`. Add a short body when one subject cannot explain the important parts.
3. Each commit: a conventional `type: subject` **plus a real body** (what + why, written for a reader — same bar as a phase log).
4. Commit on the **current working branch**. **Do not push** unless asked — offer it, and note HTTPS may want a login (run `!git push …` so the auth prompt works).
5. Report the new log + confirm a clean tree. `LF→CRLF` warnings are benign (Windows), not errors.
