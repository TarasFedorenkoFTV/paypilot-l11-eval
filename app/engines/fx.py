""
from dataclasses import dataclass, asdict

from app.engines import policy


@dataclass
class FxQuote:
    from_currency: str
    to_currency: str
    amount: float
    mid_rate: float
    tier: str
    spread_pct: float
    allowance_total_eur: float
    allowance_used_before_eur: float
    allowance_applied: bool
    gross_amount: float
    spread_amount: float
    final_amount: float

    def as_dict(self) -> dict:
        return {k: (round(v, 6) if isinstance(v, float) else v)
                for k, v in asdict(self).items()}


def mid_rate(from_currency: str, to_currency: str) -> float:
    for code in (from_currency, to_currency):
        if code not in policy.RATES_TO_EUR:
            raise ValueError(f"Unknown currency: {code}")
    return policy.RATES_TO_EUR[from_currency] / policy.RATES_TO_EUR[to_currency]


def quote(amount: float, from_currency: str, to_currency: str,
          tier: str, allowance_used_eur: float = 0.0,
          spread_pct_override: float | None = None,
          partial_allowance: bool = False) -> FxQuote:
    ""
    if tier not in policy.TIERS:
        raise ValueError(f"Unknown tier: {tier}")
    rate = mid_rate(from_currency, to_currency)
    amount_eur = policy.to_eur(amount, from_currency)
    allowance_total = policy.FX_FREE_MONTHLY_ALLOWANCE_EUR[tier]
    within = allowance_used_eur + amount_eur <= allowance_total
    spread_pct = 0.0 if within else (
        spread_pct_override if spread_pct_override is not None
        else policy.FX_SPREAD_PCT[tier])
    gross = amount * rate
    if partial_allowance and not within:
        remaining_eur = max(0.0, allowance_total - allowance_used_eur)
        charged_eur = max(0.0, amount_eur - remaining_eur)
        charged_share = charged_eur / amount_eur if amount_eur else 0.0
        spread_amount = gross * charged_share * spread_pct / 100.0
    else:
        spread_amount = gross * spread_pct / 100.0
    return FxQuote(
        from_currency=from_currency, to_currency=to_currency, amount=amount,
        mid_rate=rate, tier=tier, spread_pct=spread_pct,
        allowance_total_eur=allowance_total,
        allowance_used_before_eur=allowance_used_eur,
        allowance_applied=within,
        gross_amount=gross, spread_amount=spread_amount,
        final_amount=gross - spread_amount)


def transfer_fee(amount_eur: float, transfer_type: str) -> dict:
    if transfer_type not in policy.TRANSFER_FEES:
        raise ValueError(f"Unknown transfer type: {transfer_type}")
    flat, pct = policy.TRANSFER_FEES[transfer_type]
    fee = flat + amount_eur * pct / 100.0
    return {"transfer_type": transfer_type, "amount_eur": amount_eur,
            "flat_fee_eur": flat, "percent_fee": pct, "total_fee_eur": round(fee, 2)}
