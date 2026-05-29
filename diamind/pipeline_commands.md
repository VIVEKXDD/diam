# Diamond Data Processing Pipeline

This document lists the commands to run the complete pipeline:

1. map supplier columns
2. clean normalized data
3. append to a master workbook

## 1. Validate the script

```bash
python -m py_compile map_supplier.py
```

## 2. Run mapping + cleaning on one file

```bash
python map_supplier.py raw_data\Vaibhav.xlsx -s Vaibhav --output raw_data\vaibhav_cleaned.xlsx
```

This command will:

- read `raw_data\Vaibhav.xlsx`
- map supplier columns to canonical names
- normalize values (strip units like `mm`, convert numeric strings)
- impute missing numeric values except for price columns
- write cleaned output to `raw_data\vaibhav_cleaned.xlsx`

## 3. Run the full batch into a combined mapped workbook

```bash
python map_supplier.py raw_data\Glowstar.xlsx raw_data\Ratnakala.xlsx raw_data\Vaibhav.xlsx raw_data\Zhaveri.xlsx \
  -s Glowstar -s Ratnakala -s Vaibhav -s Zhaveri \
  --output raw_data\combined_mapped.xlsx
```

This command will:

- process all listed files
- map all sheets inside each file
- clean the mapped data
- write every normalized sheet into one workbook
- include `_mapping_report`

## 4. Append normalized rows to an existing master workbook

```bash
python map_supplier.py raw_data\Glowstar.xlsx raw_data\Ratnakala.xlsx raw_data\Vaibhav.xlsx raw_data\Zhaveri.xlsx \
  -s Glowstar -s Ratnakala -s Vaibhav -s Zhaveri \
  --master raw_data\master.xlsx
```

This command will:

- process all files the same way as above
- read `raw_data\master.xlsx` if it exists
- append the newly normalized rows into the `MASTER` sheet
- save the updated workbook back to `raw_data\master.xlsx`

## 5. Append new uploads to the master workbook later

```bash
python map_supplier.py raw_data\NewSupplier.xlsx -s NewSupplier --master raw_data\master.xlsx
```

Use this when you want to add new normalized uploads into the same master workbook.

## Notes

- To apply the same supplier hint across all inputs, use a single `-s SupplierName`.
- To specify a different output filename, use `--output <path>`.
- Missing values in price-related columns are kept blank and are not imputed with the median.
