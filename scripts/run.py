import argparse
import sys


def cmd_backtest(a):
    print(f"Backtest: strategy={a.strategy}, asset={a.asset}, timeframe={a.timeframe}")
    if a.dry_run:
        print("  [DRY RUN]")
        return
    print("  Not yet implemented.")


def cmd_analysis(a):
    print(f"Analysis: type={a.type}, asset={a.asset}")
    if a.dry_run:
        print("  [DRY RUN]")
        return
    print("  Not yet implemented.")


def cmd_live(a):
    if a.mode not in ("research", "data-collection"):
        print("ERROR: Invalid mode")
        sys.exit(1)
    print(f"Live {a.mode}: assets={a.assets}")
    if a.dry_run:
        print("  [DRY RUN]")
        return
    print("  Not yet implemented.")


def cmd_ml(a):
    print(f"ML: model={a.model}, asset={a.asset}")
    if a.dry_run:
        print("  [DRY RUN]")
        return
    print("  Not yet implemented.")


def cmd_grid(a):
    print(f"Grid: strategy={a.strategy}")
    if a.dry_run:
        print("  [DRY RUN]")
        return
    print("  Not yet implemented.")


def cmd_dashboard(a):
    print(f"Dashboard: port={a.port}")
    if a.dry_run:
        print("  [DRY RUN]")
        return
    print("  Not yet implemented.")


def cmd_audit(a):
    print(f"Audit: type={a.type}")
    if a.dry_run:
        print("  [DRY RUN]")
        return
    print("  Not yet implemented.")


def main():
    p = argparse.ArgumentParser(prog="researchos")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--verbose", action="store_true")
    sub = p.add_subparsers(dest="command", required=True)
    x = sub.add_parser("backtest")
    x.add_argument("--strategy", required=True)
    x.add_argument("--asset", required=True)
    x.add_argument("--timeframe", required=True)
    x.set_defaults(func=cmd_backtest)
    x = sub.add_parser("analysis")
    x.add_argument("--type", required=True, choices=["evidence", "trend"])
    x.add_argument("--asset", required=True)
    x.set_defaults(func=cmd_analysis)
    x = sub.add_parser("live")
    x.add_argument("--mode", required=True, choices=["research", "data-collection"])
    x.add_argument("--assets", required=True)
    x.set_defaults(func=cmd_live)
    x = sub.add_parser("ml")
    x.add_argument("--model", required=True, choices=["xgboost", "lstm", "auto"])
    x.add_argument("--asset", required=True)
    x.set_defaults(func=cmd_ml)
    x = sub.add_parser("grid")
    x.add_argument("--strategy", required=True)
    x.add_argument("--params", required=True)
    x.set_defaults(func=cmd_grid)
    x = sub.add_parser("dashboard")
    x.add_argument("--port", type=int, default=8050)
    x.set_defaults(func=cmd_dashboard)
    x = sub.add_parser("audit")
    x.add_argument("--type", required=True)
    x.set_defaults(func=cmd_audit)
    a = p.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
