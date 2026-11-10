"""L11, крок 4: підсумок генерації для шаблону (час машини, вартість, кількість тестів).

    python tools/generation_summary.py reports/generation.json

reports/generation.json — вивід Claude Code з прапорцем --output-format json.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "reports" / "generation.json"
    if not path.exists():
        sys.exit(f"Немає файлу {path}. Запустіть генерацію з  --output-format json > {path}")
    raw = path.read_bytes()
    # Windows PowerShell 5.1 пише `>` в UTF-16; інші оболонки — в UTF-8
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        text = raw.decode("utf-16")
    else:
        text = raw.decode("utf-8-sig")
    data = json.loads(text)
    if data.get("is_error"):
        sys.exit(f"Генерація завершилась помилкою: {data.get('result')}")

    tests = 0
    for f in (ROOT / "tests" / "generated").glob("test_*.py"):
        tests += len(re.findall(r"^\s*def test_", f.read_text(encoding="utf-8"), re.M))

    models = ", ".join(data.get("modelUsage", {}) or []) or "?"
    minutes = (data.get("duration_ms") or 0) / 60000
    print(f"Модель:               {models}")
    print(f"Час машини, хв:       {minutes:.1f}")
    print(f"Кроків асистента:     {data.get('num_turns')}")
    print(f"Вартість, USD:        {data.get('total_cost_usd', 0):.2f}")
    print(f"Функцій test_ у tests/generated/: {tests}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
