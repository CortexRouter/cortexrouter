# CortexRouter

**Zafiyet kanıtlarını değerlendiren açık kaynak güvenlik modeli.**

---

## Nedir?

Bir güvenlik testinden gelen **kanıtı** alır ve **9 alanlı yapılandırılmış Türkçe karar raporu** üretir.

```
1) Hedef ortam      2) Açık kimliği    3) Kategori
4) Test adımları    5) Gözlenen kanıt  6) Karar
7) Gerekçe          8) Güven           9) Kaynak
```

**Karar sınıfları:** `DOĞRULANDI` · `ETKİSİZ` · `YANLIŞ_POZİTİF`

---

## Model

| Model | Taban | Lisans |
|---|---|---|
| **[judge-v1](https://huggingface.co/cortexrouter/judge-v1)** | Qwen3-8B (LoRA) | Apache 2.0 |

---

## Hızlı başlangıç

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

SORU = """HEDEF: Apache 2.4.49 (izole lab)
Test çıktısı: HTTP 200
root:x:0:0:root:/root:/bin/bash

Soru: CVE-2021-41773 sınıfı bir açık bu çıktıyla doğrulanır mı?"""

girdi = tok.apply_chat_template(
    [{"role": "user", "content": SORU}],
    add_generation_prompt=True, return_tensors="pt",
).to(model.device)

with torch.no_grad():
    c = model.generate(
        girdi, max_new_tokens=700, do_sample=False,
        pad_token_id=tok.eos_token_id,
    )

print(tok.decode(c[0][girdi.shape[1]:], skip_special_tokens=True))
```

**vLLM ile servis**

```bash
vllm serve Qwen/Qwen3-8B --enable-lora \
  --lora-modules judge=cortexrouter/judge-v1 --port 8000
```

---

## Değerlendirme

```bash
python eval/run_eval.py --api http://localhost:8000/v1 --model judge
```

**80 soruluk temiz holdout** (20 CVE × 4 senaryo — eğitimde görülmemiş):

| Senaryo | Açıklama | Skor |
|---|---|---|
| A | Kanıt var | 13/13 = %100 |
| B | Yamalı (404) | 13/13 = %100 |
| C | Modül kapalı | 12/12 = %100 |
| D | Belirsiz (giriş sayfası) | 12/12 = %100 |
| **TOPLAM** | | **80/80 = %100** |

> Holdout açık olarak yayınlanmıştır — kendin doğrula.
> Farklı prompt'larla sonuç değişebilir.

---

## Depo yapısı

```
cortexrouter/
├── README.md
├── eval/
│   ├── run_eval.py
│   └── holdout.jsonl
├── examples/
│   └── vllm.md
└── LICENSE
```

---

## Sınırlar

- **Dil:** Türkçe ağırlıklı
- **Kapsam:** Web uygulama zafiyetleri
- **Kanıt tipi:** Metin tabanlı
- **Karar dışı alanlar:** Bilinmeyen konularda uydurma yapabilir
- **Üretim:** Tek başına kullanılmaz; insan denetimi gerekir

**Bu model ne DEĞİL:** yeni temel model değil, genel amaçlı değil, insan denetimi yerine geçmez.

**Kullanılmaması gereken yerler:** yetkisiz hedefler, otomatik sömürü, hukuki karar.

---

## Lisans

**Apache 2.0** — `LICENSE` dosyasına bakın.

Taban model: [Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B) (Apache 2.0, Alibaba Group).
LoRA adapter eğitildi; taban ağırlıklar değiştirilmedi.

---

## Atıf

```bibtex
@misc{cortexrouter-judge-v1,
  title  = {CortexRouter Judge v1},
  author = {CortexRouter},
  year   = {2026},
  url    = {https://github.com/cortexrouter}
}
```
