"""Fight Night Round 3 PSP overhaul host-side models.

The package began with Alpha 1 core boxer/fight systems and now also contains
the first Career Mode 2.0 implementation slice.

- RE-grounded reference modules such as fight_session and fight_stats record
  only behavior and storage boundaries supported by static evidence.
- Alpha 1 rule-engine modules such as boxer_model, stamina, damage, ai,
  judging and rules are mod-owned tunable gameplay logic.
- career2_amateur is the first Career Mode 2.0 domain model. It uses proven
  retail age/phase/physical destinations while keeping new per-rating
  potential and learning-rate data mod-owned for the C2EX extension.

No module in this package should silently assign semantics to unresolved
retail fields. PSP-side patch/hook work remains evidence-gated.
"""
