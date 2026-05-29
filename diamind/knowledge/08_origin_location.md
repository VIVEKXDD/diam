# Diamond Origin, Location, and Supplier Context

## Diamond Origin (`origin`)

The geographic origin of the rough diamond — where it was mined. Origin affects both pricing and ethical considerations (conflict diamonds vs. responsibly sourced goods).

### Major Origins in This Dataset

| Origin | Notes |
|--------|-------|
| **Angola** | Major producer; rough historically associated with conflict (though situation improved post-2002 peace). Fine large stones common. Some premium in certain markets. |
| **Canada** | Premium origin. Canadian diamonds are associated with strict environmental and labor standards. No conflict history. Often command a small premium (3–10%) in European and North American markets. Traceable supply chain. |
| **Botswana** | World's second-largest producer by value. Debswana (De Beers/Botswana govt joint venture). High-quality, conflict-free goods. Good reputation. |
| **South Africa** | Historic origin; De Beers originated here. Good reputation; varied quality. |
| **Russia** | Alrosa mines produce ~30% of world rough supply. Fine white goods. Geopolitical sanctions since 2022 have affected trading; EU/G7 sanctions restrict import of Russian diamonds in some markets. |
| **Congo (DRC)** | Democratic Republic of Congo. Complex history with conflict stones. Kimberley Process certified goods are legitimate but due diligence required. |
| **Zimbabwe** | Historically controversial (Marange fields). Kimberley Process suspended Zimbabwe diamonds temporarily. Current status: KP-compliant but some buyers remain cautious. |
| **Zambia** | Primarily colored gemstones (emeralds) but also some diamonds. |
| **Mix / Unknown** | Unspecified or multiple origins. Most common in melee/parcel goods. |

### Kimberley Process (KP)
International certification scheme established in 2003 to prevent conflict (blood) diamonds from entering the mainstream market. All diamonds in legitimate supply chains must be KP-certified. All suppliers in this dataset are assumed to operate within KP compliance.

### Origin Premium/Discount Summary
| Origin | Market Treatment |
|--------|-----------------|
| Canada | +3–10% in some markets; strong ethical premium |
| Botswana | Neutral to slight positive |
| South Africa | Neutral |
| Russia | Currently complex due to sanctions; some buyers paying discount |
| Angola | Neutral in most markets |
| DRC/Congo | Due diligence required; slight discount in sensitive markets |

---

## Location (`location`)

The physical location where the stone is currently held (inventory location). Affects delivery time, logistics costs, and applicable import duties.

| Location | Meaning |
|----------|---------|
| India / IND | Stone is in India (typically Mumbai/Surat, the global diamond cutting and trading hub) |
| United States / USA | Stone is in the US |
| Belgium | Stone is in Antwerp (the global rough diamond trading hub) |
| Hong Kong / HK | Stock held in Hong Kong (major Asian trading center) |
| Israel | Stock in Israel (traditional cutting and trading center) |
| Dubai / UAE | Stock in UAE |

**Practical implications**:
- Stones in India can typically ship internationally with 2–5 day lead time.
- Import duties vary by destination country and stone value.
- US-stocked stones have no import duty for US buyers; EU buyers face duties.

---

## Supplier Context

### Glowstar
Large wholesale supplier with significant inventory across multiple size ranges. Stocks exclusively GIA-certified Round Brilliant Cuts. Data contains three sheets — Sheet1 is the main stock; Sheet2 and Sheet3 appear mostly empty/header rows.

### Ratnakala
Mid-size Indian dealer. Round Brilliants, primarily GIA. Some stones show NaN for lab (uncertified). Strong in 0.20–1.00ct range. Uses separate white/black visibility fields for inclusions.

### Vaibhav
Smaller dealer. Exclusively GIA-certified 1.50ct Round Brilliants in the sample data. **Critical note**: Vaibhav's "Amount" column = price per carat (not total price). All other suppliers use "Amount" for total price.

### Zhaveri
Mid-large dealer. Primarily GIA Round Brilliants, 1.00ct+. Provides `availability` field (AV/Hold) and `eye_clean` assessment. Strong on proportion data. Uses `depth_pct` for what other suppliers call depth percent (their "Depth" raw column maps to depth%, not raw depth in mm).

### Karigar (not in current dataset)
Melee goods dealer — sells small parcels of diamonds by size sieve (not individual certified stones). Has no stone IDs, cert numbers, or lab data. Uses `item_type`, `batch`, `mm_size`, `sieve_size`, `company_grade`, `vendor_name` fields. "Vendor Price" = Karigar's own cost, not ask price.

---

## Sheet Date (`sheet_date`)

The date when the supplier generated this price sheet. Important because:
- Rap prices are as of this date.
- Availability may have changed since then.
- Stones from older sheets may already be sold.

Always check `sheet_date` when assessing how current a price is.