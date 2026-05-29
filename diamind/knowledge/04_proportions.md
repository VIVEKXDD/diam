# Diamond Proportions and Light Performance

Proportions determine how a diamond handles light — its brilliance (white light return), fire (dispersion into spectral colors), and scintillation (sparkle). All proportion measurements are percentages of the stone's average diameter (for rounds) or width (for fancy shapes).

---

## Table Percentage (`table_pct`)

The table is the largest flat facet on the top of the diamond. Table% = table diameter / average girdle diameter × 100.

| Table % | Assessment |
|---------|-----------|
| 52–54% | Very small; may reduce brilliance slightly |
| 54–57% | Excellent range (GIA Excellent cut) |
| 57–62% | Very Good to Good range |
| 63–66% | Getting large; fire diminishes |
| 66%+ | Too large; fish-eye effect possible |

---

## Depth Percentage (`depth_pct`)

Total depth from table to culet, as a percentage of average diameter.
`depth_pct = depth_mm / average_diameter × 100`

| Depth % | Assessment |
|---------|-----------|
| Below 56% | Too shallow; light leaks through bottom ("fish-eye") |
| 58–60% | Slightly shallow; still good |
| 60–62.5% | Excellent range |
| 62.5–64% | Slightly deep; good but slightly smaller face-up |
| 64–66% | Deep; noticeably smaller face-up than weight suggests |
| 66%+ | Too deep; nailhead effect; significant light loss |

A deep stone looks smaller face-up than its carat weight implies. A shallow stone looks large but loses brilliance. The best balance is typically 59–62.5%.

---

## Crown Angle (`crown_angle`)

The angle of the crown facets relative to the girdle plane.

| Crown Angle | Assessment |
|-------------|-----------|
| 31–33° | Low crown; less fire |
| 33–35° | Excellent range |
| 35–36.5° | Very Good; slightly high |
| 36.5°+ | High crown; more fire but may appear smaller |

---

## Crown Height (`crown_height`)

Crown height as a percentage of average diameter.

| Crown Height | Assessment |
|--------------|-----------|
| 11–14% | Excellent range |
| 14–16% | Very Good |
| Below 11% or above 17% | Less ideal |

---

## Pavilion Angle (`pav_angle`)

The angle of the pavilion (bottom) facets. The most critical proportion for brilliance — the pavilion acts as a mirror reflecting light back up through the table.

| Pavilion Angle | Assessment |
|----------------|-----------|
| 40.6–41.0° | Excellent; optimal light return |
| 41.0–41.8° | Very Good |
| 41.8–42.4° | Good |
| Below 40.4° | Shallow pavilion; light leaks |
| Above 42.4° | Deep pavilion; "nailhead" dark center |

---

## Pavilion Depth (`pav_depth`)

Pavilion depth as a percentage of average diameter. Works in tandem with pavilion angle.

| Pavilion Depth | Assessment |
|----------------|-----------|
| 42–43.5% | Excellent range |
| 43.5–44.5% | Very Good |
| 44.5–46% | Good |
| Above 46% | Deep; significant light loss |

---

## Lower Half (`lower_half`)

The lower half facets (also called lower girdle facets) are the 16 facets below the girdle that border the pavilion. Their length affects scintillation pattern.

| Lower Half % | Effect |
|--------------|--------|
| 75–80% | Chunky, "old mine" look; large flashes |
| 80–85% | Balanced scintillation |
| 85–90% | More needle-like flashes; modern look |

---

## Girdle (`girdle` and `girdle_pct`)

The girdle is the narrow band around the widest part of the diamond, where the crown meets the pavilion. It is the setting edge.

**Girdle thickness descriptions** (in the `girdle` field):
| Code | Description | Assessment |
|------|-------------|-----------|
| ETN | Extremely Thin | Risk of chipping; avoid |
| VTN | Very Thin | Vulnerable |
| TN | Thin | Acceptable |
| MED | Medium | Excellent |
| STK | Slightly Thick | Very Good |
| THK | Thick | Good |
| VTK | Very Thick | Acceptable but stone looks smaller |
| ETK | Extremely Thick | Weight hidden in girdle; poor value |

Ranges like "MED to STK" or "MED-STK" indicate the girdle varies in thickness around the stone (normal). The `girdle_pct` is the girdle thickness as a percentage of average diameter (ideal: 1–3%).

---

## Culet (`culet`)

The culet is the tiny facet (or point) at the very bottom of the diamond.

| Culet | Assessment |
|-------|-----------|
| NON / NONE | No culet; a point. Standard in modern diamonds. |
| VS (Very Small) | Acceptable |
| SM (Small) | Very Good |
| MED (Medium) | Good; visible face-up in some lighting |
| LG (Large) | Visible as a circle when viewed face-up; undesirable |
| VL (Very Large) | Very undesirable |

---

## Hearts and Arrows (`hna`)

Hearts and Arrows (H&A) is a visual pattern visible in specially cut Round Brilliant diamonds under a H&A viewer:
- **8 arrows** visible through the table (face-up)
- **8 hearts** visible through the pavilion (face-down)

Achieving H&A requires near-perfect symmetry, consistent facet angles, and precise cutting. H&A stones command a premium and are generally EX/EX/EX graded.

Values in dataset:
- `80` or `H&A`: Hearts and Arrows present
- `NON` or blank: Not H&A
- `NaN` / missing: Not assessed
