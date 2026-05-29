# Diamond Inclusions and Clarity Characteristics

Inclusions are internal features; blemishes are surface features. Both affect clarity grade and, in some cases, durability and appearance. The GIA Clarity Report lists the types, sizes, and positions of all clarity characteristics visible at 10x magnification.

---

## Common Inclusion Types in This Dataset

### Crystal
A mineral crystal (could be diamond, garnet, diopside, etc.) trapped inside the diamond during its formation.
- Small crystals in lower-clarity positions: minor impact.
- Large dark crystals (carbon or graphite): very visible, significant impact on value.
- "Black crystal" = opaque dark inclusion. Very undesirable in table position.

### Feather
A fracture or crack within the diamond. Appears as a white or transparent feather-like internal reflection.
- Small feathers away from the table: typically minor.
- Large feathers reaching the surface (especially girdle area): potential durability concern.
- Feathers near the table or visible face-up: significant negative impact.

### Cloud
A cluster of tiny pinpoints (3 or more) grouped together. Appears as a hazy or milky area.
- A small cloud: minor impact.
- A large cloud filling significant area: can severely reduce transparency and brilliance. "Cloudy" clarity characteristics are a common reason diamonds look hazy despite a VS or SI grade on paper.
- "Additional clouds are not shown" in cert comments: the certificate is acknowledging there are more clouds than explicitly plotted.

### Pinpoint
An extremely small crystal, too small to characterize further. Appears as a tiny white dot under magnification.
- Individually: minimal impact.
- In clusters: forms clouds.
- "Additional pinpoints are not shown" in cert comments is common and means pinpoints are so numerous they weren't all individually plotted; typically minor but worth noting.

### Needle
A thin, elongated crystal inclusion resembling a needle. Usually white or transparent.
- Small needles: minor impact.
- Multiple needles in table position: can affect appearance in certain lighting.

### Indented Natural
An area of unpolished rough diamond surface that dips below the polished surface, usually on the girdle. Technically a blemish, not an inclusion.

### Cavity
An opening or void on the diamond's surface. Can trap dirt and affect brilliance. Durability concern if large.

### Chip
A small missing piece of diamond, usually at the girdle edge, culet, or facet edge. Durability concern.

### Twinning Wisp
A series of pinpoints, clouds, and/or crystals arranged in a curved pattern, resulting from crystal growth irregularity. Common in certain rough origins.

### Graining / Internal Graining
Irregular crystal growth; appears as white, colored, or reflective lines or streaks. More common in certain rough origins (e.g., some African goods).

### Bruise
A small area of polycrystalline diamond, usually at a facet junction, resulting from impact. Looks like a small white cloud concentrated at a surface point.

### Laser Drill Hole
A tiny tunnel drilled by laser to bleach a dark inclusion. Creates a thin line (drill hole) from surface to inclusion. GIA does NOT improve a grade for laser-drilled stones. Laser drilling is disclosed on the certificate.

---

## Reading the Inclusions Field

The `inclusions` field in this dataset typically lists the GIA key to symbols — the inclusion types noted on the certificate, comma-separated.

Example: `Feather, Crystal, Cloud, Pinpoint`

This tells you the *types* present but not their size or position. For full detail, the GIA certificate must be consulted.

---

## Certificate Comments (`cert_comments`)

Common phrases and what they mean:

| Comment | Meaning |
|---------|---------|
| "Additional pinpoints are not shown." | More pinpoints exist beyond what is plotted. Typically minor. |
| "Additional clouds are not shown." | More clouds than plotted. May be significant if stone looks hazy. |
| "Minor details of polish are not shown." | Polish features present but too small to fully document. |
| "Feather reaches the girdle." | Fracture extends to the surface — durability note. |
| "Surface graining is not shown." | Graining lines on surface not mapped on the diagram. |

---

## BGM Inclusion Codes (Supplier-Specific)

Some suppliers (Glowstar) use specific codes in comments for clarity-related appearance:

| Code | Meaning |
|------|---------|
| BC0 | No brown in crown |
| BC1 | Very faint brown in crown |
| BC2 | Light brown in crown |
| BC3 | Moderate brown in crown |
| BT0 | No brown in table |
| BT1-BT3 | Brown in table (increasing severity) |
| SB | Black in side |
| SW | White in side |
| CB | Crown black |
| CW | Crown white |

---

## Impact of Inclusion Type on Value

From most to least problematic (for equal-clarity-grade stones):

1. **Black crystal in table** — highly visible dark spot; most undesirable
2. **Large feather (reaching surface)** — durability risk + visible
3. **Cloud (large, affecting transparency)** — transparency loss
4. **Crystal (dark/large)** — visible spot
5. **Cavity** — surface void, traps dirt
6. **Feather (small, not reaching surface)** — moderate
7. **Crystal (small, colorless)** — minor
8. **Twinning wisps** — moderate (depends on coverage)
9. **Needle** — minor to moderate
10. **Pinpoint(s)** — minor individually
11. **Cloud (small)** — minor
12. **Indented natural** — minor

---

## Inclusion Type Field (`inclusion_type`)

Some suppliers (Zhaveri) provide a separate `inclusion_type` field with abbreviated codes:

| Code | Meaning |
|------|---------|
| BCBS | Black Crystal (bottom/side) |
| NONE | No notable inclusion type |
| MIX | Multiple types |