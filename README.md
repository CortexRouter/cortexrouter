# CortexRouter

**Open security models for vulnerability verification.**

---

## What it is

A family of open models that read evidence from security tests and produce a
**structured decision report**.

```
1) Target environment    2) Vulnerability ID   3) Category
4) Test steps            5) Observed evidence  6) Decision
7) Rationale             8) Confidence         9) Source
```

**Decision classes:** `DOĞRULANDI` (Confirmed) · `ETKİSİZ` (Ineffective) · `YANLIŞ_POZİTİF` (False positive)

> Output language is Turkish by design. Field labels and decision classes are Turkish.

---

## Models

| Model | Base | License |
|---|---|---|
| **[judge-v1](https://huggingface.co/cortexrouter/judge-v1)** | Qwen3-8B (LoRA adapter) | Apache 2.0 |

---

## Quick start

```bash
pip install transformers peft accelerate torch
```

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch

BASE = "Qwen/Qwen3-8B"

tok = AutoTokenizer.from_pretrained(BASE)
model = PeftModel.from_pretrained(
    AutoModelForCausalLM.from_pretrained(
        BASE, torch_dtype=torch.bfloat16, device_map="auto"
    ),
    "cortexrouter/judge-v1",
).eval()

QUESTION = """HEDEF: Apache 2.4.49 (izole lab)
Test çıktısı: HTTP 200
root:x:0:0:root:/root:/bin/bash

Soru: CVE-2021-41773 sınıfı bir açık bu çıktıyla doğrulanır mı?"""

ids = tok.apply_chat_template(
    [{"role": "user", "content": QUESTION}],
    add_generation_prompt=True, return_tensors="pt",
).to(model.device)

with torch.no_grad():
    out = model.generate(
        ids, max_new_tokens=700, do_sample=False,
        pad_token_id=tok.eos_token_id,
    )

print(tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True))
```

**Serving with vLLM**

```bash
vllm serve Qwen/Qwen3-8B --enable-lora \
  --lora-modules judge=cortexrouter/judge-v1 --port 8000
```

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"judge","messages":[{"role":"user","content":"HEDEF: ..."}],"temperature":0}'
```

---

## Evaluation

```bash
python eval/run_eval.py --api http://localhost:8000/v1 --model judge
```

**Clean holdout — 20 CVEs × 4 scenarios = 80 questions** (unseen during training)

| Scenario | Description | Score |
|---|---|---|
| A | Evidence present | 20/20 = 100% |
| B | Patched (404) | 20/20 = 100% |
| C | Module disabled | 20/20 = 100% |
| D | Ambiguous (200 + login page) | 20/20 = 100% |
| **Total** | | **80/80 = 100%** |

> The holdout is published — verify it yourself.
> Results may vary with different prompts.

---

## Repository layout

```
cortexrouter/
├── README.md
├── LICENSE
└── eval/
    ├── run_eval.py
    └── holdout.jsonl
```

---

## Limitations

| Limitation | Description |
|---|---|
| **Output language** | Turkish (field labels and decisions) |
| **Input language** | Turkish preferred; English understood |
| **Scope** | Web application vulnerabilities |
| **Evidence type** | Text only (no binary/hex) |
| **Evidence length** | ~768 tokens |
| **Non-decision fields** | May hallucinate on unknown context |
| **Production use** | Not standalone — interprets evidence from a scanning engine |

**What this is NOT:**
- Not a new foundation model — a LoRA adapter on Qwen3-8B
- Not general-purpose — specialised for vulnerability verification
- Not a replacement for human review

**Do not use for:** unauthorised targets, automated exploitation,
legal decisions, or critical infrastructure without human review.

---

## Ethics

Designed for **authorised security testing**. Use only on targets with verified
ownership. Disclose vulnerabilities responsibly (CVD). All reports must be
reviewed by a human before action.

---

## License

**Apache 2.0** — see [LICENSE](LICENSE).

Base model: [Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B) (Apache 2.0, Alibaba Group).
LoRA adapter trained; base model weights unchanged.

---

## Citation

```bibtex
@misc{cortexrouter-judge-v1,
  title  = {CortexRouter Judge v1},
  author = {CortexRouter},
  year   = {2026},
  url    = {https://github.com/CortexRouter/cortexrouter}
}
```
