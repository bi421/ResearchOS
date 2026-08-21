import json
from datetime import datetime
from pathlib import Path


class DiagnosticEngine:
    def __init__(self, results_file):
        self.results_file = results_file
        self.results = self._load_results()
        self.issues = []

    def _load_results(self):
        with open(self.results_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def diagnose(self):
        self._check_model_vs_baseline()
        self._check_statistical_significance()
        self._check_class_imbalance()
        self._check_learning_signal()
        return self.issues

    def _check_model_vs_baseline(self):
        model_worse = sum(1 for r in self.results if r["model_acc"] < r["baseline_acc"])
        model_equal = sum(
            1 for r in self.results if abs(r["model_acc"] - r["baseline_acc"]) < 0.001
        )
        total = len(self.results)

        if model_worse > total * 0.3:
            desc = f"Загвар {model_worse}/{total} тохиолдолд суурь шугамаас муу"
            self.issues.append(
                {
                    "type": "model_underperforming",
                    "severity": "high",
                    "description": desc,
                    "fix": "class_weight_balanced",
                    "priority": 1,
                }
            )
        if model_equal > total * 0.7:
            desc = f"Загвар {model_equal}/{total} тохиолдолд суурь шугамтай ижил (majority class)"
            self.issues.append(
                {
                    "type": "model_not_learning",
                    "severity": "critical",
                    "description": desc,
                    "fix": "feature_engineering",
                    "priority": 0,
                }
            )

    def _check_statistical_significance(self):
        passed = [r for r in self.results if r.get("sig_bonferroni", False)]
        if len(passed) == 0:
            best_p = min(self.results, key=lambda r: r["p_value"])
            self.issues.append(
                {
                    "type": "no_significance",
                    "severity": "medium",
                    "description": f"Бонферронийн засварыг давсан хослол 0. Хамгийн ойр p={best_p['p_value']:.4f}",
                    "fix": "fdr_correction",
                    "priority": 2,
                }
            )

    def _check_class_imbalance(self):
        high_acc_results = [r for r in self.results if r["model_acc"] > 0.95]
        if len(high_acc_results) > len(self.results) * 0.5:
            self.issues.append(
                {
                    "type": "class_imbalance",
                    "severity": "high",
                    "description": f"{len(high_acc_results)}/{len(self.results)} үр дүн 95%-аас дээш нарийвчлалтай (majority class)",
                    "fix": "smote_undersampling",
                    "priority": 1,
                }
            )

    def _check_learning_signal(self):
        improving_results = [r for r in self.results if r["model_acc"] > r["baseline_acc"] + 0.01]
        if len(improving_results) == 0:
            self.issues.append(
                {
                    "type": "no_learning_signal",
                    "severity": "critical",
                    "description": "Загвар суурь шугамаас 1%-аас илүү сайжруулалт гаргаагүй",
                    "fix": "regime_filtering",
                    "priority": 0,
                }
            )


class FixEngine:
    def __init__(self, issues):
        self.issues = sorted(issues, key=lambda x: x["priority"])
        self.fixes = []

    def generate_fixes(self):
        for issue in self.issues:
            fix = self._get_fix(issue)
            if fix:
                self.fixes.append(fix)
        return self.fixes

    def _get_fix(self, issue):
        fix_map = {
            "class_weight_balanced": {
                "action": "modify_training_script",
                "target": "scripts/train_model.py",
                "change": 'Add class_weight="balanced" to model',
                "code_snippet": 'model = RandomForestClassifier(class_weight="balanced")',
                "impact": "high",
                "effort": "low",
            },
            "feature_engineering": {
                "action": "add_features",
                "target": "scripts/preprocess_data.py",
                "change": "Add volatility and momentum indicators",
                "code_snippet": "Add: ATR, RSI, Bollinger Bands width",
                "impact": "critical",
                "effort": "medium",
            },
            "fdr_correction": {
                "action": "change_statistical_method",
                "target": "scripts/h1_horizon_sweep.py",
                "change": "Replace Bonferroni with Benjamini-Hochberg FDR",
                "code_snippet": "from statsmodels.stats.multitest import multipletests",
                "impact": "medium",
                "effort": "low",
            },
            "smote_undersampling": {
                "action": "balance_classes",
                "target": "scripts/train_model.py",
                "change": "Apply SMOTE or undersampling before training",
                "code_snippet": "from imblearn.over_sampling import SMOTE",
                "impact": "high",
                "effort": "medium",
            },
            "regime_filtering": {
                "action": "filter_by_regime",
                "target": "scripts/preprocess_data.py",
                "change": "Filter data by market regime (high volatility hours)",
                "code_snippet": "Filter: London/NY overlap (15:00-19:00 UTC)",
                "impact": "critical",
                "effort": "medium",
            },
        }
        return fix_map.get(issue["fix"])


class ImprovementEngine:
    def __init__(self, results):
        self.results = results

    def suggest_improvements(self):
        suggestions = []
        best_p = min(self.results, key=lambda r: r["p_value"])
        suggestions.append(
            {
                "action": "focus_on_horizon",
                "horizon": best_p["horizon"],
                "threshold": best_p["threshold"],
                "reason": f"Хамгийн бага p-value: {best_p['p_value']:.4f}",
                "next_step": f"Test horizon={best_p['horizon']} with additional features",
            }
        )

        best_model = max(self.results, key=lambda r: r["model_acc"] - r["baseline_acc"])
        suggestions.append(
            {
                "action": "optimize_best_model",
                "horizon": best_model["horizon"],
                "threshold": best_model["threshold"],
                "reason": f"Хамгийн их сайжруулалт: {best_model['model_acc'] - best_model['baseline_acc']:.4f}",
                "next_step": "Hyperparameter tuning on this configuration",
            }
        )

        suggestions.append(
            {
                "action": "test_new_hypothesis",
                "hypothesis": "XAUUSD H1 has regime-dependent predictability",
                "experiment": "Split data by volatility regime and test separately",
                "expected_outcome": "Higher accuracy in high-volatility periods",
            }
        )
        return suggestions


class AutoHealer:
    def __init__(self, results_file):
        self.results_file = results_file
        self.log_dir = Path("scripts/healer_logs")
        self.log_dir.mkdir(exist_ok=True)

    def run(self):
        print("=" * 60)
        print("🔍 AUTO-HEALER: Starting diagnostic...")
        print("=" * 60)

        diagnostic = DiagnosticEngine(self.results_file)
        issues = diagnostic.diagnose()
        print(f"\n✅ Issues found: {len(issues)}")
        for issue in issues:
            print(f"  [{issue['severity'].upper()}] {issue['description']}")

        fixer = FixEngine(issues)
        fixes = fixer.generate_fixes()
        print(f"\n✅ Fixes suggested: {len(fixes)}")
        for fix in fixes:
            print(f"  [{fix['impact'].upper()}] {fix['change']}")

        improver = ImprovementEngine(diagnostic.results)
        suggestions = improver.suggest_improvements()
        print(f"\n✅ Improvements suggested: {len(suggestions)}")
        for sug in suggestions:
            print(f"  → {sug['action']}: {sug.get('reason', sug.get('hypothesis', ''))}")

        report = {
            "timestamp": datetime.now().isoformat(),
            "issues": issues,
            "fixes": fixes,
            "suggestions": suggestions,
        }

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.log_dir / f"healer_report_{ts}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Report saved: {report_file}")
        print("=" * 60)
        return report


if __name__ == "__main__":
    results_file = "data/curated/xauusd/phase51_h1_horizon_sweep.json"
    healer = AutoHealer(results_file)
    report = healer.run()
    print(
        f"\n📊 Summary: Issues: {len(report['issues'])} | "
        f"Fixes: {len(report['fixes'])} | Suggestions: {len(report['suggestions'])}"
    )
