# Кіт лабораторної L11: два набори тестів на одному модулі

Порядок дій описано в темі L11. Цей файл пояснює, що де лежить і якими командами запускати.

Стенд для цього заняття запускати не потрібно. Модуль під тестом — знімок `app/engines/fx.py` і `app/engines/policy.py` зі стенду PayPilot (коміт `74f1995`). Код у кіті такий самий, як у вашому стенді. Він лежить тут, щоб мутанти й асистент не торкалися стенду.

## Що в папці

| Файл | Що це | Крок |
| --- | --- | --- |
| `app/engines/fx.py` | модуль під тестом, функція `fx.quote(...)` | 1–6 |
| `app/engines/policy.py` | таблиця тарифів: спред і безкоштовний ліміт за тіром | 1 (звідси очікувані значення) |
| `tests/manual/` | ваш ручний baseline | 1 |
| `mutants.example.toml` | зразок списку мутантів, один мутант заповнено | 2 |
| `prompts/` | сюди кладете критерії й промпт генерації | 3 |
| `tests/generated/` | сюди асистент пише згенеровані тести | 4 |
| `tests/rewritten/` | сюди ви кладете тести, переписані з відхилених | 5 |
| `tools/run_mutants.py` | прогін списку мутантів на наборі | 2, 6 |
| `tools/generation_summary.py` | підсумок генерації: час машини, вартість, кількість тестів | 4 |
| `agent-prompt/` | base.v4 системного промпту PayPilot: чернетка асистента, журнал рев'ю, прийнята версія, як підставити у стенд | теорія, L12 |
| `ai-adoption-impact-report.template.md` | шаблон артефакту: скопіюйте в `ai-adoption-impact-report.md` | 1–6, ДЗ |
| `.claude/settings.json` | забороняє асистентові змінювати модуль, ваш набір, список мутантів і промпт | 4 |

## Підготовка

```bash
git clone https://github.com/TarasFedorenkoFTV/paypilot-l11-eval ~/paypilot/l11
cd ~/paypilot/l11
# Windows PowerShell: git clone https://github.com/TarasFedorenkoFTV/paypilot-l11-eval "$HOME\paypilot\l11"; cd "$HOME\paypilot\l11"
```

Далі один із двох способів.

**Локальний Python 3.11+:**

```bash
python -m venv .venv
# macOS / Linux / WSL:
source .venv/bin/activate
# Git Bash на Windows:
source .venv/Scripts/activate
# Windows PowerShell:
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Windows PowerShell: якщо `Activate.ps1` або `claude` падає з «running scripts is disabled on this system», один раз виконайте `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` і відкрийте термінал заново.

**Без Python, через Docker** — перед кожною командою нижче додайте `docker compose run --rm kit`:

```bash
docker compose run --rm kit pytest tests/manual
```

## Генерація (крок 4)

Асистент — Claude Code з вашим `ANTHROPIC_API_KEY`. Встановлення: `npm install -g @anthropic-ai/claude-code` (потрібен Node.js 18+).

Що бачить асистент, задає `.claude/settings.json` у цьому кіті: він читає `app/engines/fx.py`, але **не бачить** таблиці тарифів `app/engines/policy.py`, вашого ручного набору, списку мутантів і цього README. Так і задумано: тарифи — це вимоги, а не код, і асистент їх не знає. Змінювати модуль і ваші файли він не може.

Запуск із кореня кіта, промпт береться з вашого файлу:

```bash
# macOS / Linux / WSL / Git Bash
claude -p "$(cat prompts/generation-prompt.md)" --model sonnet \
  --allowedTools "Read,Write,Glob,Grep" --output-format json > reports/generation.json
```

```powershell
# Windows PowerShell
[Console]::OutputEncoding = [Text.Encoding]::UTF8
claude -p (Get-Content prompts/generation-prompt.md -Raw -Encoding UTF8) --model sonnet `
  --allowedTools "Read,Write,Glob,Grep" --output-format json > reports/generation.json
```

Підсумок для шаблону (час машини, вартість, кількість тестів):

```bash
python tools/generation_summary.py reports/generation.json
```

Генерація триває 2–4 хвилини й коштує $0.40–0.70 з вашого ключа (чотири прогони на `sonnet`, 10.11.2026). Результат щоразу трохи інший: кількість тестів і вбитих мутантів у вас можуть відрізнятися від прикладів у темі.

## Команди за кроками

| Крок | Команда |
| --- | --- |
| 1. Тести зелені на оригінальному модулі | `pytest tests/manual` |
| 2. Список мутантів застосовується до коду | `python tools/run_mutants.py --check` |
| 4. Покриття ручного набору | `pytest tests/manual --cov=app.engines.fx` |
| 4. Покриття згенерованого набору | `pytest tests/generated --cov=app.engines.fx` |
| 6. Мутанти на ручному наборі | `python tools/run_mutants.py --set manual` |
| 6. Мутанти на згенерованому наборі | `python tools/run_mutants.py --set generated` |
| 6. Мутанти на об'єднаному наборі | `python tools/run_mutants.py --set all` |

Кожен прогін мутантів друкує розклад по класах і перелік вцілілих та зберігає звіт у `reports/`. Звіти комітьте: за ними ментор бачить, що список мутантів закомічено раніше за перший прогін.

У Windows PowerShell 5.1 немає `&&`: замість `git add X && git commit -m "…"` пишіть дві команди через `;` або окремими рядками.

Відсоток покриття залежить від версії Python (на 3.12 і 3.14 той самий набір дає різне число). Порівнюйте два свої числа між собою. Mutation score від версії не залежить.

## Чого не робити

- Не змінюйте `mutants.toml` після першого прогону. Якщо мутант не застосовується, скрипт скаже про це до прогону: виправте рядок `find` і закомітьте список ще раз до першого прогону.
- Не змінюйте `app/`: мутант — це тимчасова копія, яку робить скрипт.
- Не комітьте `.env` і ключі.
