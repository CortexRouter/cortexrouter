#!/usr/bin/env python3
"""
CortexRouter Judge v1 — değerlendirme çalıştırıcısı

80 soruluk holdout setini çalıştırır ve karar doğruluğunu ölçer.
Herkes indirip %100 iddiasını kendisi doğrulayabilir.

Kullanım:
    python run_eval.py --model cortexrouter/judge-v1
    python run_eval.py --base Qwen/Qwen3-8B --adapter ./judge-v1
    python run_eval.py --api http://localhost:8000/v1 --model judge
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
HOLDOUT = os.path.join(HERE, "holdout.jsonl")

KARARLAR = ["DOĞRULANDI", "YANLIŞ_POZİTİF", "ETKİSİZ"]

SISTEM = (
    "Sen kıdemli bir uygulama güvenliği analistisin. "
    "Yalnızca verilen kanıta dayanarak karar verirsin. "
    "Kanıt yoksa uydurmasın. 9 alanlı yapıda Türkçe cevap ver."
)


def karar_bul(metin):
    """Cevaptan kararı çıkar (en son geçen kazanır)."""
    ust = metin.upper()
    bulunan = []
    for k in KARARLAR:
        p = ust.rfind(k)
        if p >= 0:
            bulunan.append((p, k))
    if not bulunan:
        return None
    return max(bulunan)[1]


def sor_api(soru, base, model, zaman=90):
    import urllib.request
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": SISTEM},
            {"role": "user", "content": soru},
        ],
        "temperature": 0,
        "max_tokens": 700,
        "chat_template_kwargs": {"enable_thinking": False},
    }).encode()
    req = urllib.request.Request(
        f"{base.rstrip('/')}/chat/completions",
        data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=zaman) as r:
        d = json.loads(r.read().decode())
    return (d["choices"][0]["message"].get("content") or "").strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://localhost:8000/v1")
    ap.add_argument("--model", default="judge")
    ap.add_argument("--holdout", default=HOLDOUT)
    ap.add_argument("--adet", type=int, default=0, help="0 = hepsi")
    ap.add_argument("--cikti", default="eval-sonuc.jsonl")
    args = ap.parse_args()

    sorular = []
    with open(args.holdout, encoding="utf-8") as f:
        for s in f:
            s = s.strip()
            if s:
                sorular.append(json.loads(s))

    if args.adet:
        sorular = sorular[:args.adet]

    print(f"Model : {args.model}")
    print(f"API   : {args.api}")
    print(f"Soru  : {len(sorular)}")
    print("-" * 70)

    dogru = 0
    yanlis = 0
    bos = 0
    senaryo = {}
    t0 = time.time()

    with open(args.cikti, "w", encoding="utf-8") as out:
        for i, s in enumerate(sorular, 1):
            try:
                cevap = sor_api(s["soru"], args.api, args.model)
            except Exception as e:
                cevap = ""
                print(f"  [{i:2}/{len(sorular)}] ⚠️  API hatası: {str(e)[:50]}")

            bulunan = karar_bul(cevap)
            bekl = s["beklenen_karar"]
            ok = bulunan == bekl

            sen = s.get("senaryo", "?")
            senaryo.setdefault(sen, [0, 0])
            senaryo[sen][1] += 1
            if ok:
                dogru += 1
                senaryo[sen][0] += 1
                isaret = "✓"
            elif bulunan is None:
                bos += 1
                isaret = "∅"
            else:
                yanlis += 1
                isaret = "✗"

            print(f"  [{i:2}/{len(sorular)}] {s['id']:26} "
                  f"bekl {bekl:14} bulunan {str(bulunan):14} {isaret}")

            out.write(json.dumps({
                "id": s["id"], "senaryo": sen,
                "beklenen": bekl, "bulunan": bulunan,
                "dogru": ok, "cevap": cevap[:1000],
            }, ensure_ascii=False) + "\n")

    n = len(sorular)
    sure = time.time() - t0

    print("\n" + "=" * 70)
    print("SONUÇ")
    print("=" * 70)
    print(f"Süre           : {sure:.0f} sn")
    print(f"Doğru          : {dogru}/{n} = %{100*dogru/max(1,n):.1f}")
    print(f"Yanlış         : {yanlis}")
    print(f"Karar yok      : {bos}")
    print("\nSenaryo bazında:")
    for sen in sorted(senaryo):
        d, t = senaryo[sen]
        print(f"  {sen}: {d}/{t} = %{100*d/t:.0f}")
    print(f"\nDetay: {args.cikti}")
    print("=" * 70)

    return 0 if dogru == n else 1


if __name__ == "__main__":
    sys.exit(main())
