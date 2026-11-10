"""Ручний baseline L11 (крок 1). Пишіть тести тут, асистента не відкривайте.

Модуль під тестом: app/engines/fx.py — функція fx.quote(...).
Очікувані значення беріть із таблиці тарифів app/engines/policy.py,
а не з виводу самої функції.

    fx.quote(amount, from_currency, to_currency, tier, allowance_used_eur=0.0)
    tier: "tier1" | "tier2" | "tier3"
    повертає FxQuote: spread_pct, allowance_applied, gross_amount,
                      spread_amount, final_amount, ...
"""
import pytest

from app.engines import fx
