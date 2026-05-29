# Diamond Pricing: The Rapaport System

## The Rapaport Price List

The Rapaport Price List (commonly called "the Rap") is the diamond industry's benchmark wholesale price guide, published weekly by Rapaport Group. It is the global standard for pricing polished diamonds.

- Published every Friday.
- Prices are in **US dollars per carat** for Round Brilliant Cuts and Pear shapes.
- Prices are listed in a matrix grid indexed by **color** (D–N) on one axis and **clarity** (FL–I1) on the other.
- Prices represent the **high retail/asking price** for a given color-clarity combination — they are NOT transaction prices. Actual deals are struck at a discount to Rap.

---

## Key Pricing Fields in the Dataset

### `rap_price` (Rapaport Price)
The Rapaport list price per carat for this stone's color-clarity combination at the time the sheet was produced. This is the starting benchmark — not the actual ask or transaction price.

Example: A G/VS1 Round at 1ct might have `rap_price = 9400`, meaning the Rap list is $9,400 per carat.

### `rap_value` (Rapaport Value)
The Rapaport value of the whole stone: `rap_value = rap_price × carat_weight`

Example: G/VS1, 1.5ct → `rap_value = 9400 × 1.5 = 14,100`

### `rap_discount` (Rapaport Discount)
The percentage discount (or premium) applied to the Rap list price. Almost always **negative** (a discount), meaning the stone sells below list price.

Formula: `rap_discount = ((price_per_carat / rap_price) - 1) × 100`

Example: `-35%` means the stone is offered at 35% below the Rap list.

**Reading discounts**:
- `-0% to -10%`: Very low discount. Premium stone or tight market.
- `-10% to -30%`: Normal market range for high-quality goods.
- `-30% to -50%`: Typical for commercial/SI grade goods.
- `-50% to -70%`: Heavy discount; lower clarity/color or weak demand.
- Positive rap discount (a "premium"): Stone sells above Rap. Rare; occurs for very fine, scarce goods.

### `price_per_carat` (Ask Price Per Carat)
The supplier's asking price per carat in USD. Derived from Rap and the discount:
`price_per_carat = rap_price × (1 + rap_discount / 100)`

**IMPORTANT — Supplier-Specific Rule**:
- For **Vaibhav**, the source column "Amount" is price per carat.
- For **Ratnakala**, **Glowstar**, and **Zhaveri**, the source column "Amount" is the **total price**, not per-carat.

### `price` (Total Ask Price)
The total asking price for the stone: `price = price_per_carat × carat_weight`

---

## How Rapaport Pricing Works in Practice

1. The Rap list sets a theoretical ceiling.
2. Suppliers and dealers negotiate a discount from Rap.
3. The discount reflects the stone's actual desirability — cut quality, fluorescence, milkiness, shade, inclusions, and market conditions.
4. A stone with bad BGM (brown/green/milky) or strong fluorescence trades at a deeper discount even if its color-clarity grade is high.

---

## Price Calculation Examples

**Example 1** — Glowstar Round, 1.5ct, G, VVS1, EX/EX/EX:
- `rap_price` = $12,000/ct
- `rap_discount` = -30%
- `price_per_carat` = $12,000 × 0.70 = $8,400/ct
- `price` = $8,400 × 1.5 = $12,600 total

**Example 2** — Ratnakala Round, 0.24ct, E, VS1:
- `rap_price` = $1,320/ct
- `rap_discount` = -35.5%
- `price_per_carat` = $1,320 × 0.645 = $851.40/ct
- `price` = $851.40 × 0.24 = $204.34 total

---

## Why Price Columns Are Never Imputed

Price fields (`price`, `price_per_carat`, `rap_price`, `rap_value`, `rap_discount`) are **never filled with median or estimated values** in this pipeline. A blank price means the supplier did not quote one — substituting a median would create a false price that could mislead purchasing decisions.

---

## Rap Price Limitations

- Rap prices do not exist for all color-clarity combinations (very low colors or included grades may not be on the list).
- Fancy shapes (Emerald, Oval, Pear, Princess, etc.) are not on the standard Rap grid; they trade at a discount to the Round Brilliant equivalent for the same color-clarity.
- The Rap list is not publicly free — it is a subscription service. The values in the dataset reflect the list at the time each supplier's sheet was generated, so they may differ across sheets produced on different dates.