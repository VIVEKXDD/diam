# Diamond Shapes

Diamond shape refers to the geometric form of the stone when viewed face-up. Shape affects brilliance, fire, price, and perceived size.

---

## Shape Codes Used in This Dataset

| Code | Full Name | Description |
|------|-----------|-------------|
| RBC / RD / Round | Round Brilliant Cut | Most popular shape worldwide. 57 or 58 facets. Only shape with an official GIA Cut grade. Highest brilliance and fire due to optimized facet angles. |
| EM | Emerald Cut | Rectangular step-cut with cropped corners. Hall-of-mirrors effect; less sparkle but more elegance. Clarity is very visible — higher clarity recommended. |
| PR | Princess Cut | Square or rectangular brilliant cut. Second most popular. Good brilliance; pointed corners require protective settings. |
| OV | Oval | Elliptical brilliant cut. Appears larger than a round of equal carat weight. |
| MQ | Marquise | Boat-shaped brilliant cut with pointed ends. Maximizes perceived size per carat. |
| PS | Pear | Teardrop shape; combination of round and marquise. |
| RD | Radiant | Rectangular or square brilliant cut with cropped corners. More sparkle than Emerald. |
| CU | Cushion | Square or rectangular with rounded corners and large facets. Vintage look. "Old mine" style cushions have chunky facets. |
| AS | Asscher | Square step-cut, similar to Emerald. Very Art Deco. High-clarity stones show best. |
| HT | Heart | Heart-shaped brilliant cut. Skill-intensive and requires expert cutting. |

**Note**: In the dataset, "Round" and "RBC" (Round Brilliant Cut) refer to the same shape.

---

## Shape Pricing Relative to Round Brilliant

Round Brilliants command the highest prices because cutting them wastes the most rough diamond material. Fancy shapes (all non-rounds) are priced lower per carat for the same color and clarity.

| Shape | Typical Discount vs. Round (same C-C-W) |
|-------|----------------------------------------|
| Princess | ~20–30% less |
| Cushion | ~25–35% less |
| Oval | ~15–25% less |
| Emerald | ~20–30% less |
| Asscher | ~25–35% less |
| Pear | ~15–25% less |
| Marquise | ~15–25% less |
| Radiant | ~25–35% less |
| Heart | ~20–30% less |

These are approximate ranges; actual discounts vary by market conditions.

---

## Shape-Specific Quality Notes

**Emerald and Asscher (step cuts)**:
- Their large open table facets make inclusions much more visible than in brilliant cuts.
- Clarity of VS1 or better is typically recommended.
- Color is also more visible — D-H is preferred.

**Oval, Pear, Marquise (elongated brilliants)**:
- Prone to the "bow-tie effect" — a dark shadow across the center in poorly cut stones.
- Length-to-width ratio significantly affects appearance; typical preferences: Oval 1.30–1.50, Pear 1.45–1.75, Marquise 1.85–2.10.

**Round Brilliant**:
- The only shape for which GIA issues an overall Cut grade.
- Ideal proportions: Table 53–58%, Depth 59–62.5%, Crown angle 34–35°, Pavilion depth 42–43.5%.

---

## Measurements Field

The `measurements` field records physical dimensions in millimeters.

- **Round stones**: `diameter1 - diameter2 × depth` (two diameter measurements because rounds are not perfectly circular — slight variance is normal)
  - Example: `6.51 - 6.53 × 4.01` means 6.51mm min diameter, 6.53mm max diameter, 4.01mm depth
- **Fancy shapes**: `length × width × depth`
  - Example: `15.28 × 10.27 × 6.60` for an Emerald cut

**Ratio** (`ratio` field) = length / width. For rounds this is always ~1.0. For fancy shapes it describes the elongation.
