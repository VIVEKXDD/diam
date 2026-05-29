# Diamond Quality Indicators: Fluorescence, BGM, Milky, Shade, Natts

These fields describe characteristics that affect a diamond's appearance and value beyond the standard 4Cs. They are critical for pricing and buying decisions.

---

## Fluorescence (`fluorescence` and `fluorescence_color`)

Fluorescence is the tendency of a diamond to emit a glow (usually blue) when exposed to ultraviolet (UV) light. Approximately 25–35% of diamonds fluoresce.

### Fluorescence Grades

| Grade | Description |
|-------|-------------|
| NONE / NON | No fluorescence. No impact on appearance. |
| FNT / Faint | Very slight; negligible effect in normal light. |
| MED / Medium | Moderate blue glow under UV. May slightly affect face-up color. |
| STG / SB / Strong | Strong blue glow. Can significantly affect face-up appearance. |
| VST / Very Strong | Very strong glow. Most likely to cause hazy or oily appearance. |

### How Fluorescence Affects Value

**Blue fluorescence** (most common):
- In **D–F** color diamonds: Strong/medium blue fluorescence is considered a negative — it can make the stone look hazy, milky, or oily in natural/UV-rich light. These stones trade at a **discount of 3–15%** vs. non-fluorescent equivalents.
- In **G–J** color diamonds: Blue fluorescence can actually improve the face-up appearance (makes yellowish stones look whiter in sunlight). Slight premium for faint/medium blue in these grades, or at worst neutral.
- In **K and below**: Strong blue fluorescence is generally positive — improves apparent color significantly.

**Yellow fluorescence**: Rare. Negative effect across all color grades — makes the stone appear more yellow.

**Fluorescence color** (`fluorescence_color`): Usually BLUE. Other colors (white, yellow, orange) are unusual and typically negative.

### Industry Rule on Fluorescence
A stone with **strong blue fluorescence and D color** may look hazy in direct sunlight. Such stones should be viewed in person before purchasing for high-end jewelry. Lower-color stones (G–J) with medium blue are often better value than non-fluorescing equivalents.

---

## Milky (`milky`)

Milkiness is a haziness or cloudiness in a diamond that reduces brilliance and transparency. It is distinct from fluorescence-induced haze — milkiness is inherent to the stone.

| Value | Meaning |
|-------|---------|
| NONE / 0 / ML-0 | No milkiness. Clean, bright stone. |
| ML-1 | Very slight milkiness. Usually acceptable. |
| ML-2 | Light milkiness. Affects brightness noticeably. |
| ML-3 | Moderate milkiness. Clear reduction in brilliance. |
| MILKY | Severely milky. Stone looks dull and lifeless. |

**Pricing impact**: Even ML-1 milkiness can cause a 5–10% discount. ML-2 and above can discount 15–30%+. Severe milkiness can make a high-color/clarity stone effectively unsellable at grade-commensurate prices.

Milkiness is often not captured in the GIA grading report — it is a dealer-assessed characteristic. This is why it appears separately in supplier sheets.

---

## Shade (`shade`)

Shade describes an undesirable color tint that the stone carries beyond what is captured by the GIA color grade. Common shades:

| Value | Meaning |
|-------|---------|
| NONE / NN | No undesirable shade. |
| BROWN / BR | Brown tint (also called "champagne"). Most common shade issue. |
| GREEN / GR | Green or greyish-green tint. |
| GREY / GY | Grey or steely tint. |
| MILKY | Sometimes used interchangeably with milky field. |
| MIX | Mixed or unclassified shade. |

**Pricing impact**: Brown shade is the most common and causes discounts of 10–30% or more on higher-color diamonds. A D/IF with brown shade trades far below its nominal grade price. Green and grey shades are also negative.

**Why shade matters**: Two diamonds with identical GIA grades can look very different — one bright white, one with a brownish cast. The GIA grade does not always capture subtle shades visible in normal lighting.

---

## BGM (`bgm`)

BGM stands for **Brown, Green, Milky** — a combined quality flag used primarily for Round Brilliant diamonds. It is an industry shorthand for whether a stone carries any of these undesirable characteristics.

| Value | Meaning |
|-------|---------|
| No BROWN NO MILKY | Clean stone; no brown or milky characteristics. |
| BC0 - BT0 | No brown crown (BC0), no brown table (BT0). Best. |
| BC1 - BT1 | Very slight brown in crown/table. Minor discount. |
| BC2 - BT2 | Light brown. Noticeable discount. |
| BC3 - BT3 | Moderate brown. Significant discount. |
| BCBS | Black Crystal in crown, Black in side. Specific inclusion description. |

**Reading BGM notation**: `BC` = Brown Crown, `BT` = Brown Table. The number (0–3) indicates severity. `SB` = Side Black. `SW` = Side White.

---

## Natts (`natts`)

Natts (short for "natural") refers to unpolished parts of the original rough diamond left on the surface of the finished stone, typically on the girdle. A natt is technically a blemish.

| Value | Meaning |
|-------|---------|
| NONE / NON | No natts. Clean girdle. |
| BC0 - BT0 | Used in some supplier formats for no brown characteristics. |
| Small/Minor | Tiny unpolished patch; visible only at 10x; negligible impact. |
| Large | Visible to naked eye; may affect value and setting. |

**Pricing impact**: Small natts have little impact. Large natts can cause minor discounts and may affect the choice of setting style.

---

## Eye Clean (`eye_clean`)

A stone is "eye clean" when no inclusions are visible to the naked eye under normal viewing conditions (face-up, approximately 25–30cm distance, normal lighting).

| Value | Meaning |
|-------|---------|
| Y / YES | Eye clean — no inclusions visible to the naked eye. |
| N / NO | Not eye clean — inclusions visible without magnification. |

All FL–VS2 diamonds are eye clean. Most SI1 diamonds are eye clean. SI2 stones vary. I1–I3 are typically NOT eye clean.

Eye-clean SI1 and SI2 stones are popular value picks — they have significant Rap discounts but still look clean to the eye.

---

## White Table / White Side / Table Black / Side Black

These fields describe the appearance of internal characteristics specifically visible through the table and crown facets. Used primarily by Indian dealers.

| Field | Meaning |
|-------|---------|
| `white_table` | White (reflective) inclusions visible through the table. Typically clouds or feathers. |
| `white_side` | White inclusions visible through the crown/side. |
| `table_black` | Black (opaque) inclusions visible through the table. Typically carbon spots or black crystals. |
| `side_black` | Black inclusions visible through the crown/side. |

Values 0 = none, 1 = present (sometimes graded 0–3 by severity).

**Black inclusions are particularly undesirable** — carbon or black crystal spots visible through the table face are especially noticeable in the stone's most prominent viewing angle and cause disproportionate price discounts.

---

## Availability (`availability`)

Indicates the current trading status of the stone.

| Value | Meaning |
|-------|---------|
| AV | Available — immediately available for purchase. |
| Hold | On hold — reserved for another buyer. May become available. |
| Memo | Out on memo — physically in another dealer's hands for inspection. |
| Sold | Already sold. |
| UNKNOWN | Status not provided. |