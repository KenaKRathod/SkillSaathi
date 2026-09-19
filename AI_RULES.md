# AI_RULES.md — SkillSaathi

Read this file fully before touching any code. If a rule here conflicts with a user prompt, follow the "Conflict Rules" section.

> Items marked `[TODO]` are not decided yet. Do NOT guess them. Ask the human.

---

## 1. Project Identity

- **Name:** SkillSaathi
- **What it is:** A voice-first agent that talks to a rural worker in their own language, maps what they say to structured skill (NSQF) categories, and recommends government skilling programs with reasons.
- **Context:** Capabl National Level AI Hackathon 2026, Problem C1 (19–20 Sept 2026, 24-hour build).
- **Target users:** Rural / informal-sector workers, NGO field workers, a future IVR helpline.
- **Pipeline (4 stages, keep this order):**
  1. Speech-to-text (voice → text)
  2. Conversational agent (asks follow-ups, fills the profile)
  3. Skill mapper (free text → NSQF categories)
  4. Recommender (skills → programs, with reasoning)
  - Optional: text-to-speech output, SMS/WhatsApp handoff, NGO dashboard.
- **Scope of the demo:** 1 Indian language `[TODO: which one]`, ~20 NSQF categories, ~15 programs.
- **Stack:** `[TODO: confirm — Streamlit or React frontend, Whisper/faster-whisper or Google STT, which LLM]`

---

## 2. Repo Structure

**Expected layout** (`[TODO: edit to match the real repo]`):

```
skillsaathi/
├── app/                 # frontend / UI (mic button, chat, program cards)
├── backend/
│   ├── stt/             # speech-to-text
│   ├── agent/           # dialogue agent + conversation state
│   ├── mapper/          # free text -> NSQF categories
│   ├── recommender/     # filter + rank + reasoning
│   └── tts/             # optional voice output
├── data/
│   ├── nsqf_categories.*   # curated category list
│   └── programs.*          # curated program list
├── prompts/             # all LLM prompts as files
├── tests/
├── docs/                # architecture, prompt docs, change log
├── AI_RULES.md
├── .env.example
└── README.md
```

**Do not restructure:**
- Do not move, rename, or merge folders or files without asking.
- Do not split one module into many, or merge many into one, "for cleanliness".
- Do not create new top-level folders.
- Do not move prompts out of `prompts/` or hardcode them inside code.
- Do not rewrite the project in a different framework or language.

**New files:** put them in the folder that matches their pipeline stage. If unsure where, ask.

---

## 3. Critical Contracts

These are the interfaces between stages. Changing them breaks other people's work. **Never change them silently.**

1. **Stage boundaries:** each stage takes the previous stage's output and nothing else. No stage reaches into another stage's internals.
2. **Profile schema:** the structured profile the agent fills (e.g. occupation, years of experience, tools, education, district, wage goal, mobility) is a shared contract. `[TODO: link/path to schema file]`. Do not add, rename, or remove fields without approval.
3. **Mapper output schema:** JSON with fields such as `primary_category`, `secondary_category`, `evidence_quotes`, `confidence`. Keep field names and types stable.
4. **Data file formats:** `nsqf_categories` and `programs` columns/keys are contracts. Do not rename columns.
5. **Program facts are data, not model output.** The LLM may only *explain* rows from `programs`. It must NEVER invent or "fill in" program names, duration, cost, eligibility, or NSQF levels.
6. **Low confidence rule:** if mapper confidence is low, the agent asks one more question. It does not guess.
7. **Transcripts stay raw:** do not "clean up" or translate the STT transcript before it reaches the agent (code-mixed speech is expected).
8. **User consent:** the consent notice at the start of a conversation must stay.
9. **Secrets:** API keys live only in `.env`. `.env.example` lists variable names only.

---

## 4. What AI May Do Without Asking

- Fix bugs inside the file/function you were asked to work on.
- Add or improve tests for code you touched.
- Add comments, docstrings, and type hints.
- Rename local variables inside a function.
- Small refactors inside one function that do not change its inputs or outputs.
- Add error handling, logging, and input validation without changing behavior.
- Update `README.md` or `docs/` to reflect a change you just made.
- Add new sample/mock data under `tests/` only.
- Fix typos and formatting in code you are already editing.

---

## 5. What AI Must Never Do Silently

If you need to do any of these, **stop, say so, and wait for approval**:

- Change any contract in Section 3.
- Add, remove, or upgrade a dependency.
- Move, rename, or delete files or folders.
- Delete or overwrite data files (`nsqf_categories`, `programs`) or prompts.
- Change an LLM prompt's meaning (wording tweaks that alter behavior count).
- Change the STT / LLM / TTS provider or model.
- Change environment variables, config, or deploy settings.
- Touch anything with secrets, API keys, or credentials.
- Add new features, screens, or languages that were not requested.
- Make network calls to a new external service.
- Store or log personal data (voice, name, phone, location) in a new place.
- Disable, skip, or delete a failing test.
- Rewrite large parts of a file when asked for a small change.
- Invent data: program details, NSQF levels, scheme names, URLs, or library functions.

---

## 6. Task Workflow

For every task, follow this order:

1. **Understand:** restate the task in 1–2 lines. If anything is unclear, ask before coding.
2. **Locate:** say which files you will touch. Keep this list small.
3. **Plan:** for anything bigger than a small fix, give a short plan and wait for a go-ahead.
4. **Implement:** smallest change that solves the task. One task at a time.
5. **Test:** run the relevant tests / do a quick manual check (see Section 9).
6. **Summarize:** what changed, which files, what you did NOT do, and anything uncertain.
7. **Document:** add a change note (see Section 11).

If a task grows bigger than expected, stop and say so instead of expanding scope.

---

## 7. Dependency Rules

- Prefer what is already installed. Check `requirements.txt` / `package.json` before adding anything.
- Ask before adding any new dependency, and say why the existing ones are not enough.
- Pin versions in the dependency file.
- Do not add heavy libraries for small tasks (e.g. a full framework for one helper).
- Never invent library functions or arguments. If you are not sure a function exists, say so and tell the human to verify it in the current docs.
- Do not upgrade major versions unless asked.
- Keep the app runnable on a normal laptop and a basic phone browser (low-resource users matter).

---

## 8. Conflict Rules

If instructions conflict, use this priority (top wins):

1. Safety, privacy, and consent (Section 3, items 5 and 8)
2. Critical contracts (Section 3)
3. MVP scope (Section 12)
4. The current explicit task from the human
5. This file's style and workflow rules
6. Your own preferences

Also:
- If the human's prompt conflicts with this file, **point out the conflict and ask** — do not pick silently.
- If two files or docs disagree, say so and ask which is correct.
- If you are unsure, ask. A short question beats a wrong assumption.

---

## 9. Testing Rules

- Every change must be checked before you say it is done. State exactly what you ran and what happened.
- Never claim "it works" or "tests pass" unless you actually ran them.
- Add or update a test for each bug fix and each new function.
- Minimum checks per stage:
  - **STT:** a sample audio clip returns a transcript.
  - **Agent:** a mock worker persona completes a conversation and fills the profile.
  - **Mapper:** known sample inputs map to the expected category; low-confidence input triggers a follow-up question.
  - **Recommender:** eligibility filter and ranking work on sample profiles; output only uses rows from `programs`.
- Do not delete, weaken, or skip a failing test to make things green. Report it instead.
- If you cannot run tests (no environment, no network), say that clearly.

---

## 10. Git Rules

- Never commit directly to `main`. Work on a branch: `feat/<short-name>`, `fix/<short-name>`.
- Do not commit, push, merge, rebase, or force-push unless asked.
- Small commits, one purpose each. Message format: `type: short description` (e.g. `fix: handle empty transcript`).
- Never commit `.env`, API keys, audio recordings, or real user data.
- Do not rewrite git history.
- Before finishing, list the files changed so the human can review the diff.

---

## 11. Change Documentation

After every meaningful change, add an entry to `docs/CHANGELOG.md`:

```
## YYYY-MM-DD — short title
- What changed:
- Files touched:
- Why:
- Contracts affected: none / <which>
- Known issues / TODO:
```

Also:
- If you changed a prompt, note the old vs new intent in `docs/` (prompt documentation is part of the hackathon submission).
- If you changed how to run the project, update `README.md`.
- Write what you did NOT finish, not only what you finished.

---

## 12. MVP Scope Protection

The goal is a working, demo-able end-to-end voice loop, not a big product.

**In scope (MVP):**
- Voice input in 1 Indian language
- Conversational agent that asks follow-ups and fills the profile
- Mapping to ~20 simplified NSQF categories
- Recommendation from ~15 curated programs with spoken/plain reasoning
- Consent notice and profile read-back for confirmation

**Nice-to-have (only after MVP works end to end, and only if asked):**
- TTS voice output
- SMS/WhatsApp handoff
- NGO dashboard

**Out of scope unless the human explicitly says so:**
- Extra languages, extra categories, extra programs
- User accounts / login / payments
- Real IVR / telephony integration
- Admin panels, analytics, complex databases
- Big refactors, "cleanup", or "future-proofing"

**Rules:**
- Do not add features nobody asked for, even if they seem useful.
- If you think something is missing, suggest it in a note. Do not build it.
- Working and simple beats clever and unfinished. Always keep the demo path runnable.
