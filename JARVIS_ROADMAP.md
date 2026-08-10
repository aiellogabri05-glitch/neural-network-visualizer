# Jarvis Roadmap

This project currently visualizes a trained digit-classifier network. To evolve it toward a Jarvis-style AI assistant, keep the visualizer as the learning lab and add a separate agent runtime around it.

## Current State

- Browser-based 3D neural network visualizer.
- Python training scripts for the scikit-learn `digits` dataset.
- Exported `weights.json` used by JavaScript inference.
- First local text-agent shell in `agent/`.
- Basic local tools: project summary, file reading, text search, Git status, diff, health checks, weight validation, and guarded training.
- Persistent local memory and todos in `.agent_memory.json`.
- Guarded Git tools for commit and push.
- No voice interface yet.

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

## Phase 4: Add Memory

Use two memory layers:

- Short-term memory: active conversation and current task state.
- Long-term memory: user preferences, project facts, recurring decisions, and useful summaries.

A simple first version can use SQLite plus JSON. Later, add vector search for semantic recall.

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

Status: initial version added in `agent/`.
