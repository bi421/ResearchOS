file_path = "scripts/h1_feature_sweep.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

old_logic = """        model_acc = d.get("model", {}).get("accuracy")
        base_acc = d.get("baseline", {}).get("accuracy")
        p_value = d.get("significance", {}).get("p_value")
        sig_raw = p_value is not None and p_value < alpha_raw
        sig_corrected = p_value is not None and p_value < alpha_corrected"""

new_logic = """        model_acc = d.get("model", {}).get("accuracy")
        base_acc = d.get("baseline", {}).get("accuracy")
        p_value = d.get("significance", {}).get("p_value")

        # DO NO HARM FILTER: Загвар суурь түвшнээсээ доош унаж байвал шууд хасагдана
        model_beats_baseline = (model_acc is not None) and (base_acc is not None) and (model_acc >= base_acc)

        # Статистик ач холбогдол нь зөвхөн загвар суурь түвшнээсээ илүү байх үед л хүчинтэй
        sig_raw = model_beats_baseline and (p_value is not None) and (p_value < alpha_raw)
        sig_corrected = model_beats_baseline and (p_value is not None) and (p_value < alpha_corrected)"""

old_dict = """        results.append(
            {
                "feature": fname,
                "model_acc": model_acc,
                "baseline_acc": base_acc,
                "p_value": p_value,
                "sig_raw_0.05": sig_raw,
                "sig_bonferroni": sig_corrected,
            }
        )"""

new_dict = """        results.append(
            {
                "feature": fname,
                "model_acc": model_acc,
                "baseline_acc": base_acc,
                "p_value": p_value,
                "model_beats_baseline": model_beats_baseline,
                "sig_raw_0.05": sig_raw,
                "sig_bonferroni": sig_corrected,
            }
        )"""

if old_logic in content and old_dict in content:
    content = content.replace(old_logic, new_logic)
    content = content.replace(old_dict, new_dict)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print('✅ "Do No Harm" шүүлтүүр амжилттай нэмэгдлээ!')
else:
    print("⚠️ Кодын блок олдсонгүй. Файлыг гараар шалгана уу.")
