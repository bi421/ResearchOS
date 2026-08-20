import json
import numpy as np
from statsmodels.stats.multitest import multipletests

# Үр дүнгийн файлыг унших
with open('data/curated/xauusd/phase51_h1_horizon_sweep.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

# Бүх p-value-г цуглуулах
p_values = [r['p_value'] for r in results]

# Benjamini-Hochberg FDR аргаар засварлах (alpha = 0.05)
reject_fdr, pvals_corrected, _, _ = multipletests(p_values, alpha=0.05, method='fdr_bh')

# Үр дүнг шинэчлэх
passed_fdr_count = 0
for i, r in enumerate(results):
    r['sig_fdr'] = bool(reject_fdr[i])
    r['p_value_fdr_corrected'] = float(pvals_corrected[i])
    if r['sig_fdr']:
        passed_fdr_count += 1

print("=" * 60)
print("🔧 AUTO-FIXER: FDR (Benjamini-Hochberg) Шинжилгээ")
print("=" * 60)
print(f"Нийт тестийн тоо: {len(results)}")
print(f"Бонферрониор давсан: {sum(1 for r in results if r.get('sig_bonferroni', False))}")
print(f"FDR-ээр давсан (alpha=0.05): {passed_fdr_count}")
print("-" * 60)

if passed_fdr_count > 0:
    print("✅ FDR-ээр давсан хослолууд:")
    for r in results:
        if r['sig_fdr']:
            print(f"  h={r['horizon']:2d}, t={r['threshold']:.4f} | Model: {r['model_acc']:.4f} vs Base: {r['baseline_acc']:.4f} | p(FDR): {r['p_value_fdr_corrected']:.5f}")
else:
    print("⚠️ FDR-ээр ч гэсэн ямар ч хослол дахисангүй.")
    print("   Дүгнэлт: Загварт бодит таамаглах чадвар байхгүй, өгөгдлийг бүрэн өөрчлөх (Feature Engineering) шаардлагатай.")

# Шинэчилсэн үр дүнг хадгалах
with open('data/curated/xauusd/phase51_h1_horizon_sweep_fdr.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2)
print(f"\n💾 Шинэчилсэн үр дүн хадгалагдлаа: data/curated/xauusd/phase51_h1_horizon_sweep_fdr.json")
print("=" * 60)
