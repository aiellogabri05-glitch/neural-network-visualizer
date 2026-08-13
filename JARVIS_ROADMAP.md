# Jarvis Roadmap
 
This project currently visualizes a trained digit-classifier network. To evolve it toward a Jarvis-style AI assistant, keep the visualizer as the learning lab and add a separate agent runtime around it.
 
## Current State
 
- Browser-based 3D neural network visualizer.
- Python training scripts for the scikit-learn `digits` dataset.
- Exported `weights.json` used by JavaScript inference.
- First local text-agent shell in `agent/`.
- Basic local tools: project summary, file reading, text search, Git status, diff, health checks, weight validation, and guarded training.
- Local LLM-backed question answering over project files with `ask <question>`, using a local Ollama model (Llama 3.2 3B) for RAG-based synthesis, with a keyword-extraction fallback if Ollama is unreachable.
- Hybrid planner: fixed keyword commands run instantly with no LLM call; anything else is interpreted by the local LLM and mapped to a known action.
- LLM-picked actions are validated against a whitelist and required-argument checks before execution, with confirmation gates preserved for risky actions (train, commit, push) even when routed through the LLM.
- Automated test suite (`tests/test_agent.py`, unittest) covering fixed commands, LLM-routed commands, and a safety invariant: unknown/nonsensical input never triggers a state-changing action.
- Persistent local memory and todos in `.agent_memory.json`.
- Semantic memory recall: each remembered fact is stored with a local embedding (Ollama `nomic-embed-text`), and `recall <query>` ranks memories by cosine similarity instead of exact keyword matching, so a query can find a memory phrased with completely different words.
- Atomic writes for the memory store: `_save` writes to a temporary file and replaces the real file only after the write succeeds, so an interruption mid-write cannot corrupt `.agent_memory.json`.
- Guarded Git tools for commit and push.
- No voice interface yet.
- No file-modification tool yet (read-only by design, on purpose, until planner reliability is proven).
## Principle
 
Do not try to turn this small classifier into a general intelligence. Use it as your neural-network foundation and visualization layer, then add an agent system that can call tools, remember context, and communicate through text or voice.
 
## Phase 1: Stabilize The Visualizer
 
- Keep model metadata explicit: input size, hidden layer sizes, output labels, activation, normalization.
- Add a small validation script that checks `weights.json` dimensions before the browser loads it.
- Split the frontend into clearer modules when it grows: `model`, `scene`, `drawing`, `ui`.
- Add one repeatable local run command.
## Phase 2: Build A Text Agent Shell
 
Target loop:
 
```text
user input -> understand -> plan -> choose tool -> run tool -> observe -> answer
```
 
Suggested modules:
 
```text
agent/
  agent_loop.py
  messages.py
  planner.py
  permissions.py
  tools/
    __init__.py
    filesystem.py
    shell.py
    web.py
```
 
Start with a command-line assistant before voice. It is easier to debug and safer.
 
Status: local LLM connected via Ollama (`llama3.2:3b`), running fully offline with no API costs. Tested against project-context questions; the model correctly declines to answer when context is missing or insufficient, reducing hallucination risk.
 
Status: the planner now understands free-form natural language, not just fixed keywords. Known limitations observed and tested: argument extraction can pick up filler words (mitigated with a cleanup pass), and rare colloquial phrasing can be misclassified (mitigated with a safety net that only allows read-only fallback actions, never state-changing ones).
 
## Phase 3: Add Tools
 
Start with low-risk local tools:
 
- Read project files.
- Search text in files.
- Summarize a folder.
- Run approved commands.
Then add higher-impact tools behind confirmation gates:
 
- Modify files.
- Send messages or emails.
- Control browser actions.
- Schedule reminders.
- Run automations.
Before building the file-modification tool: the planner's reliability has been hardened (action whitelist, argument validation, confirmation gates preserved through the LLM path, automated regression tests). This was done deliberately before adding any tool that writes to disk, since a misrouted command is far more costly once it can modify real files. Next concrete step: a `modify_file` tool with a restricted workspace path, a shown diff before applying, and mandatory confirmation.
 
## Phase 4: Add Memory
 
Use two memory layers:
 
- Short-term memory: active conversation and current task state.
- Long-term memory: user preferences, project facts, recurring decisions, and useful summaries.
A simple first version can use SQLite plus JSON. Later, add vector search for semantic recall.
 
Status: long-term memory now uses vector search for semantic recall. Each memory is embedded locally via Ollama (`nomic-embed-text`, 768-dimension vectors) at write time; `recall` embeds the query at search time and ranks stored memories by cosine similarity, keeping only matches above a similarity threshold. Verified to correctly retrieve a memory phrased with different words than the query, and to correctly return no match for unrelated queries. The memory store also writes atomically (temp file + replace) to avoid corruption on interruption. Short-term memory (`SessionMemory` in `messages.py`) not yet reviewed or upgraded.
 
## Phase 5: Add Voice
 
Voice stack:
 
```text
microphone -> speech-to-text -> agent loop -> text-to-speech -> speaker
```
 
Build voice after the text agent is reliable. Voice makes failures feel bigger, so the core loop should be boringly dependable first.
 
## Phase 6: Add Autonomy
 
Jarvis-like behavior comes from controlled autonomy:
 
- Background tasks.
- Timed reminders.
- Event monitors.
- Periodic project checkups.
- Explicit approvals for sensitive actions.
The assistant should always know what it is allowed to do without asking and what requires confirmation.
 
## First Concrete Milestone
 
Build a local text agent that can:
 
- Answer questions about this repo.
- Explain the neural network pipeline.
- Read files through a tool.
- Refuse or ask confirmation before risky actions.
- Keep a short task memory during the session.
Once that works, voice and richer automation become much easier.
 
Status: initial version added in `agent/`. LLM synthesis layer added on top of the extractive retrieval, connected to a local Ollama model. Planner hardened with validation and automated tests before any write-capable tool is introduced. Long-term memory upgraded from keyword matching to semantic (embedding-based) recall, with atomic file writes.