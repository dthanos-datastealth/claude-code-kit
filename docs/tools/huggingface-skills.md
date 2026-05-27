# huggingface-skills — ML workflows on the Hugging Face Hub

**What it does:**
The `huggingface-skills` plugin installs a dozen-plus skills that turn
Claude Code into a competent ML-engineering partner for anything that
touches the Hugging Face Hub — model selection, training, inference,
publication, datasets, and infrastructure.

Skills installed (selection):
- `huggingface-best` — recommend a model for a given task, hardware, or
  benchmark; the entry point for "what model should I use?" questions.
- `huggingface-local-models` — run GGUF models locally with llama.cpp on
  CPU, Mac Metal, CUDA, or ROCm; covers quant selection and OpenAI-
  compatible local serving.
- `huggingface-llm-trainer` — SFT, DPO, GRPO, and reward modeling via
  TRL or Unsloth on Hugging Face Jobs cloud GPUs, plus GGUF conversion.
- `train-sentence-transformers` — train bi-encoders, cross-encoders, and
  sparse encoders for retrieval, reranking, and classification.
- `huggingface-vision-trainer` — fine-tune detection, classification,
  and SAM/SAM2 segmentation models with COCO-format data.
- `huggingface-community-evals` — local evals with inspect-ai and
  lighteval; backend selection across vLLM / Transformers / accelerate.
- `huggingface-zerogpu` — write Gradio Spaces that target ZeroGPU
  (`@spaces.GPU`), handling pickle isolation, AoTI, and CUDA wheel-only
  build constraints.
- `huggingface-gradio` — build Gradio UIs (components, layouts, event
  listeners, chatbots).
- `huggingface-datasets` — Dataset Viewer API workflows: subsets,
  splits, pagination, filtering, parquet downloads, statistics.
- `huggingface-papers` — fetch HF paper pages and arXiv metadata in
  markdown; structured authors / linked models / datasets / spaces.
- `huggingface-trackio` — log training metrics, fire alerts, retrieve
  runs from the Trackio dashboard.
- `huggingface-paper-publisher` — publish papers to the Hub, link them
  to models/datasets, claim authorship.
- `huggingface-tool-builder` — generate reusable scripts that combine HF
  API calls for repeated or automated workflows.
- `hf-cli` — drive the `hf` CLI for auth, cache, repos, jobs, buckets,
  endpoints, collections, webhooks, discussions, and pull requests.
- `transformers-js` — run Transformers.js models in browser or Node /
  Bun / Deno using WebGPU or WASM.

**Why it's in this kit:**
ML work on the Hugging Face Hub spans many surfaces — model cards,
datasets, training jobs, inference endpoints, ZeroGPU Spaces, the `hf`
CLI, the Hub Python client, TRL, sentence-transformers, lighteval — and
each has its own conventions, gotchas, and API churn. Without these
skills Claude tends to hallucinate stale `huggingface-cli` flags,
incorrect TRL APIs, or impractical model choices for the user's
hardware. The bundle gives Claude an authoritative path for every
common HF-adjacent question, so an "ML partner" mode of working is
available without bolting on separate tooling each time.

The `huggingface-best` and `huggingface-local-models` skills are
particularly load-bearing: they turn vague model-selection questions
into grounded recommendations rather than training-data guesses.

**When you'd disable it:**
- Pure backend / infra / web projects with no ML surface at all.
- Environments where Hugging Face Hub access is blocked (corporate
  firewall, air-gapped network) and you do not intend to run any HF
  workflows.
- Strict-budget sessions where loading a dozen rarely-used skill
  prompts would dilute the context for a non-ML task.

Do not disable it when the project trains, evaluates, fine-tunes, or
deploys any model the team would normally publish to or pull from the
Hugging Face Hub.

**Source:**
GitHub: <https://github.com/anthropics/claude-plugins-official>
Marketplace: `anthropics/claude-plugins-official`
Plugin name: `huggingface-skills`

Install via the kit's `install.sh`, which registers the marketplace and
runs `claude plugin install huggingface-skills@anthropics/claude-plugins-official`.

Several skills assume the `hf` CLI is installed (`pip install -U huggingface_hub[cli]`)
and that the user has run `hf auth login` with an API token. Training
and Jobs skills additionally assume a Hugging Face account with quota
for cloud GPUs.

**Cost / footprint:**
- Disk: the plugin itself is markdown skill prompts — well under 10 MB.
  Models, datasets, and llama.cpp builds invoked by the skills can each
  consume many GB, but those are downloaded on demand outside the
  plugin directory.
- Memory / CPU / GPU: zero at idle. Skill prompts only add tokens to
  the context when invoked. The actual workloads (training, local
  inference, evals) consume whatever the user explicitly asks for —
  ZeroGPU Spaces, Jobs cloud GPUs, or local GPU/CPU.
- Network: required for any Hub interaction — model downloads, dataset
  queries, Jobs submissions, Trackio sync, paper page fetches.
- Dependencies: `hf` CLI for several skills; HF API token for any
  account-bound operation; optionally llama.cpp, vLLM, TRL, Unsloth,
  Transformers, depending on the skill invoked.

The plugin is cheap to keep installed even on partly-ML projects: idle
cost is zero, and the first time someone asks "what's the best small
embedding model for laptop inference?" it earns its keep.
