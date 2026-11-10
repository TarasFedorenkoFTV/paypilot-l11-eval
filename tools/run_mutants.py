"""L11: прогін списку мутантів на одному наборі тестів.

    python tools/run_mutants.py --set manual
    python tools/run_mutants.py --set generated
    python tools/run_mutants.py --set all          # об'єднаний набір

Що робить:
1. Читає ваш список мутантів із mutants.toml (крок 2 лабораторної).
2. Перевіряє, що набір зелений на оригінальному модулі. Інакше прогін
   мутантів нічого не означає, і скрипт зупиняється.
3. Для кожного мутанта робить тимчасову копію кіта, вносить у копію рівно
   одну зміну й запускає набір. Ваші файли не змінюються.
   Мутанта вбито, якщо набір упав. Мутант вижив, якщо набір зелений.
4. Друкує розклад по класах і перелік вцілілих, зберігає звіт у reports/.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SETS = {
    "manual": ["tests/manual"],
    "generated": ["tests/generated"],
    "all": ["tests/manual", "tests/generated"],
}
COPY_IGNORE = shutil.ignore_patterns(
    ".git", ".venv", "venv", "reports", "__pycache__", ".pytest_cache",
    ".coverage", "htmlcov", "*.pyc")

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


def load_mutants(path: Path) -> list[dict]:
    with path.open("rb") as fh:
        data = tomllib.load(fh)
    mutants = data.get("mutant", [])
    required = ("id", "class", "file", "find", "replace")
    problems = []
    for i, m in enumerate(mutants, 1):
        missing = [k for k in required if not str(m.get(k, "")).strip()]
        if missing:
            problems.append(f"мутант №{i} ({m.get('id', '?')}): немає полів {missing}")
    ids = [m.get("id") for m in mutants]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        problems.append(f"повторені id: {dupes}")
    if problems:
        sys.exit("Список мутантів не читається:\n  " + "\n  ".join(problems))
    return mutants


def check_applicable(mutants: list[dict]) -> None:
    """Кожен мутант має знаходити свій рядок у коді рівно один раз."""
    problems = []
    for m in mutants:
        target = ROOT / m["file"]
        if not target.exists():
            problems.append(f"{m['id']}: файлу {m['file']} немає")
            continue
        n = target.read_text(encoding="utf-8").count(m["find"])
        if n != 1:
            problems.append(
                f"{m['id']}: рядок find знайдено {n} разів у {m['file']} "
                f"(має бути рівно 1)")
        if m["find"] == m["replace"]:
            problems.append(f"{m['id']}: find і replace однакові, це не мутант")
    if problems:
        sys.exit("Ці мутанти не застосовуються до коду:\n  "
                 + "\n  ".join(problems)
                 + "\nВиправте рядок find так, щоб він збігався з кодом дослівно "
                   "(з пробілами), і закомітьте список до першого прогону.")


def run_pytest(workdir: Path, paths: list[str]) -> tuple[bool, str]:
    """True, якщо набір зелений."""
    env = {**os.environ, "PYTHONPATH": str(workdir), "PYTHONDONTWRITEBYTECODE": "1"}
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *paths, "-q", "-x", "--no-header",
         "-p", "no:cacheprovider", "-p", "no:cov"],
        cwd=str(workdir), env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace")
    return proc.returncode == 0, proc.stdout + proc.stderr


def git_info(path: Path) -> dict:
    def git(*args):
        try:
            return subprocess.run(["git", *args], cwd=str(ROOT), capture_output=True,
                                  text=True, encoding="utf-8").stdout.strip()
        except OSError:
            return ""
    rel = str(path.relative_to(ROOT))
    if shutil.which("git") is None or not git("rev-parse", "--git-dir"):
        return {"committed_at": None, "commit": None, "uncommitted": None,
                "head": None, "no_git": True}
    return {
        "committed_at": git("log", "-1", "--format=%cI", "--", rel) or None,
        "commit": git("log", "-1", "--format=%h", "--", rel) or None,
        "uncommitted": bool(git("status", "--porcelain", "--", rel)),
        "head": git("rev-parse", "--short", "HEAD") or None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--set", choices=SETS, required=True,
                    help="manual · generated · all (об'єднаний)")
    ap.add_argument("--mutants", default="mutants.toml",
                    help="файл списку мутантів (за замовчуванням mutants.toml)")
    args = ap.parse_args()

    mutants_path = (ROOT / args.mutants).resolve()
    if not mutants_path.exists():
        sys.exit(f"Немає файлу {args.mutants}. Скопіюйте mutants.example.toml "
                 f"у mutants.toml і впишіть свої 12 мутантів (крок 2).")
    mutants = load_mutants(mutants_path)
    check_applicable(mutants)
    paths = SETS[args.set]
    for p in paths:
        if not any((ROOT / p).glob("test_*.py")):
            sys.exit(f"У {p}/ немає файлів test_*.py. Набір {args.set} порожній.")

    info = git_info(mutants_path)
    print(f"Набір: {args.set} ({', '.join(paths)})")
    print(f"Список: {mutants_path.name}, мутантів: {len(mutants)}")
    if info.get("no_git"):
        print("git тут недоступний: дату коміту списку перевірте на хості "
              "командою  git log -1 -- mutants.toml")
    elif info["uncommitted"] or not info["committed_at"]:
        print("УВАГА: список мутантів не закомічено або змінено після коміту. "
              "Для ДЗ список має бути закомічений до першого прогону (критерій 2).")
    else:
        print(f"Список закомічено: {info['committed_at']} ({info['commit']})")

    started = dt.datetime.now().astimezone()
    with tempfile.TemporaryDirectory(prefix="l11-mut-") as tmp:
        base = Path(tmp) / "kit"
        shutil.copytree(ROOT, base, ignore=COPY_IGNORE)

        ok, out = run_pytest(base, paths)
        if not ok and "no tests ran" in out:
            print("\nУ наборі немає жодного тесту. Напишіть тести й запустіть знову.")
            return 2
        if not ok:
            print("\nНабір червоний на оригінальному модулі. Спершу зробіть його "
                  "зеленим: мутанти міряють лише зелений набір.\n")
            print(out[-3000:])
            return 2
        print("Оригінальний модуль: набір зелений.\n")

        rows = []
        for m in mutants:
            work = Path(tmp) / f"m-{m['id']}"
            shutil.copytree(base, work)
            target = work / m["file"]
            src = target.read_text(encoding="utf-8")
            target.write_text(src.replace(m["find"], m["replace"], 1), encoding="utf-8")
            survived, _ = run_pytest(work, paths)
            shutil.rmtree(work, ignore_errors=True)
            rows.append({"id": m["id"], "class": m["class"],
                         "description": m.get("description", ""),
                         "killed": not survived})
            print(f"  {m['id']:<6} {'вбито ' if not survived else 'ВИЖИВ'}  "
                  f"[{m['class']}] {m.get('description', '')}")

    by_class: "OrderedDict[str, dict]" = OrderedDict()
    for r in rows:
        c = by_class.setdefault(r["class"], {"total": 0, "killed": 0})
        c["total"] += 1
        c["killed"] += int(r["killed"])
    killed = sum(r["killed"] for r in rows)
    total = len(rows)
    survivors = [r["id"] for r in rows if not r["killed"]]

    print("\nклас мутанта".ljust(26) + "| вбито")
    print("-" * 25 + "+-------")
    for name, c in by_class.items():
        print(f"{name:<25}| {c['killed']}/{c['total']}")
    print("-" * 25 + "+-------")
    print(f"{'разом':<25}| {killed}/{total}")
    print(f"{'mutation score':<25}| {killed / total:.0%}")
    print(f"\nВцілілі: {', '.join(survivors) if survivors else 'немає'}")

    report = {
        "set": args.set, "paths": paths, "started_at": started.isoformat(),
        "mutants_file": mutants_path.name, "mutants_git": info,
        "killed": killed, "total": total,
        "mutation_score": round(killed / total, 4) if total else None,
        "by_class": by_class, "survived": survivors, "rows": rows,
    }
    out_dir = ROOT / "reports"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"mutants-{args.set}-{started:%Y%m%d-%H%M%S}.json"
    out_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Звіт: {out_file.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
