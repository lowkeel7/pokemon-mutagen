# Type roots (DP-01): draft

Status: **draft for review**. Decided: roots are a layer over the 18 types; total types stay ≤ 32.
Everything below is a proposal; ❓ marks a place where the source notes allow two readings.

## 1. Root of every type

The source tree lists some types under two roots (Grass, Water, Bug, Fighting). A type needs one
primary root for the matchup layer; the second listing becomes a **secondary** root that only
matters for learnsets and stones (SG-04/05), not for damage.

| Type | Primary root | Secondary | Note |
|---|---|---|---|
| Normal | Chi | | |
| Fighting | Chi | Vibration ("fight+") | |
| Fire | Chi | | parent of Electric |
| Electric | Chi | | subtype of Fire |
| Bug | Chi ("bug+") | Spirit | ❓ swap if Bug should read as spiritual |
| Dragon | Mana | | parent of Draco Fire |
| Poison | Mana | | |
| Grass | Mana ("grass+") | Vibration | |
| Water | Vibration | Mana ("water+") | parent of Ice, Mist |
| Ice | Vibration | | subtype of Water |
| Rock | Vibration | | parent of Steel |
| Steel | Vibration | | subtype of Rock |
| Ground | Vibration | | |
| Flying | Vibration | | subtype of Air |
| Fairy | Spirit | | |
| Dark | Spirit | | parent of Ghost |
| Ghost | Spirit | | subtype of Dark |
| Psychic | Spirit | | parent of Telekinesis |

"Fight elementals" under Mana ❓: read as "Mana fights the elementals" (a matchup), not a type.

## 2. New subtypes (6)

| New type | Parent | Feel | Example users |
|---|---|---|---|
| Air | Vibration (parent of Flying) | wind, pressure, gusts | Pidgeot line, Swablu, Tropius |
| Voice | Vibration under Air | sound, noise, song | Loudred, Jigglypuff, Chatot |
| Mist | Water | fog, vapour, haze | Vaporeon, Weezing (dual), Lapras |
| Telekinesis | Psychic | moving matter by mind | Alakazam, Metagross, Hypno |
| Spirit | Dark (parent of Ghost) | souls, possession, the dead | Spiritomb, Duskull line, ghost forms |
| Draco Fire | Dragon | blue dragon flame | Charizard line (as third type), Salamence |

A subtype is a full type with its own chart row. It inherits its parent's row as a starting point,
then differs in 2–4 cells, so it plays as a specialist version of the parent. The total is
18 + 6 = 24 real types (+ Mystery, Stellar, None in the engine), so 27 ≤ 32 and the third type
fits SG-01's 5 bits.

## 3. The root layer

A move's root vs the target's primary root adds one step **after** the type chart:

```
       Mana  →  Chi  →  Vibration  →  Spirit  →  Mana      (each beats the next)
```

| Attacker root vs target root | Multiplier |
|---|---|
| beats it (Mana → Chi, Chi → Vibration, Vibration → Spirit, Spirit → Mana) | ×1.2 |
| is beaten by it (the reverse) | ×0.85 |
| same root, or opposite on the cycle | ×1.0 |

Why mild: the type chart already does 2× / 0.5×. A 4-cycle at ×1.2 / ×0.85 makes the root a
tie-breaker and a team-building axis, not a second chart that doubles every swing. It is one more
factor in `GetTypeModifier`'s caller (`battle_util.c:8530`), so the AI, effectiveness display and
type icons pick it up from one place.

Dual and third types: use the **primary type's** root for a defender (the first type), and the
move's type root for the attacker. The third type doesn't change the root.

## 4. Physical / special subcategories (DP-02)

Kept as flags on the move, not new types; they feed held items (SG-08), abilities and statuses.

| Category | Sub | Engine head start |
|---|---|---|
| Physical | Blunt | `punchingMove` + hammer/body moves |
| | Slash | `slicingMove` |
| | Stab | `bitingMove`, horn/drill moves (new flag) |
| | Indirect | thrown / ballistic `ballisticMove` |
| Special | Mana | dragon, poison, grass, water energy moves |
| | Chi | fire, electric, normal beams |
| | Vibration | `soundMove`, `pulseMove`, `windMove` |
| | Spirit | psychic, ghost, dark, fairy |

The special subcategory defaults to the move type's root, so it costs no data entry except for
exceptions.

## 5. Toggle

`TYPE ROOTS` option: OFF (HnS chart only) / ROOTS (layer on) / FULL (layer + the 6 subtypes in
species and move data). OFF is 0. With FULL off, the six subtypes don't appear anywhere.

## Open for review
- The Bug and Grass/Water primary roots (§1).
- The cycle order (§3): it's the one fixed point everything else hangs on.
- ×1.2 / ×0.85, versus ×1.25 / ×0.8.
- Which existing species gain a subtype as their **second** type (FULL mode), not just as a third.
