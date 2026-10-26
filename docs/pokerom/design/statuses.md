# Status escalation (DP-04): draft

Status: **draft for review**. Decided: the same status inflicted again upgrades it; bleed is a
poison variant from slicing moves; one in-battle tier bit per battler, no save cost.

## Rules
- Tier 1 is today's status, unchanged. Inflicting the same status on a battler that already has it
  normally fails ("already paralyzed"); with escalation on, it upgrades to tier 2 instead.
- Tier 2 lasts until the battle ends or it's cured, then drops back to tier 1 outside battle
  (the tier bit isn't saved). Cures that remove the status remove both tiers.
- Each tier-2 status has one counter: Full Heal cures everything; the targeted cure (Paralyze Heal
  etc.) only takes tier 2 back down to tier 1.
- Immunities stay type-based, as now (Electric can't be paralyzed, so it can't be prone).

## The tiers

| Tier 1 | Tier 2 | Tier-2 effect (proposal) |
|---|---|---|
| Paralysis | **Prone** | Speed ×¼ (vs ×½), 50% chance to lose the turn (vs 25%). Being hit by a contact move ends Prone back to Paralysis (knocked upright). |
| Poison | **Septic** | Damage 1/8 → 1/6 of max HP per turn, and healing received is halved. |
| Badly poisoned | **Septic** | Toxic's growing counter keeps going, and healing is halved. |
| Sleep | **Coma** | Doesn't wake on its own; only a cure, a switch-out *and* 3 turns, or a hit with a super-effective move wakes it. Can't use Sleep Talk or Snore. |
| Burn | Scorch ❓ | Not in the notes. Proposal: 1/8 → 1/6, and the Attack drop also hits Special Attack. Or no tier 2. |
| Frostbite | ❓ | Already in the engine (`STATUS1_FROSTBITE`); HnS+ uses it to replace freeze. Proposal: no tier 2. |

## Bleed (a new tier-1 status, poison family)
- Inflicted by slicing moves (`slicingMove`): 20% chance on a hit, 30% with a slicing-boost item.
- 1/16 max HP per turn; stacks up to 3 (1/16, 2/16, 3/16); each new slicing hit adds one stack.
- Doesn't affect Rock, Steel or Ghost (no blood). Poison types *can* bleed (it's a wound, not a toxin).
- Battle-only, like confusion: it ends on switch-out or when the battle ends. An Antidote or Full Heal cures it in battle.
- Counts as poisoned for Venoshock, Hex and Merciless (it's a poison variant).
- Escalation: Bleed at 3 stacks + another slicing hit → **Septic** (the wound gets infected).

## Engine notes
- Status bits: `STATUS1_*` uses bits 0–12 of a `u32` (`include/constants/battle.h:151-168`), but
  `status1` is saved with each party Pokémon. Tier and bleed are battle-only, so both go in the
  per-battler battle struct (`u8 statusTier:1, bleedStacks:2`), cleared on switch-out like
  confusion; `status1` and the save are untouched.
- Every status move's "already has it" branch is the hook: battle scripts in
  `data/battle_scripts_1.s` call it through the "can inflict status" check.
- AI: score an escalating status move as a status move when the target already has tier 1.
- Toggle: `STATUS TIERS` OFF / ON (0 = HnS).

## Open for review
- The tier-2 numbers above.
- Burn and Frostbite: tier 2 or not.
- Limb loss (DP-13) as a Bleed consequence in scenario battles: a story-only effect, not a status.
