# Order Book Format

This document shows how the order book data is stored and interpreted.

### Fixed columns

These values contain critical information, and should not be modified manually.

- **Column 1:** Order ID:
  - Represented in file as hes
  - Output as decimal

- **Column 2:** Timestamp:
  - Represented in file as seconds elapsed since midnight, start of trading day (UTC)
  - Output as `YYYY-MM-DD HH:MM:SS UTC`

- **Column 3:** Symbol:
  - Represented as ISO-esque codes:
    - `BTC` : Bitcoin
    - `ETH` : Ethereum
    - `LTC` : LiteCoin
    - `BNB` : Binance

- **Column 4:** Price + Side:
  - Quantity is indicated by absolute value, Side is indicated by sign
  - _Positive:_ A BUY for x price:
    - 5940.5 = BUY, 304 price.
  - _Negative:_ A SELL of -x quantity:
    - 09452.5 = SELL, 40 qty.

- **Column 5:** Quantity:
  - Indicated as integer

### Dynamic columns

These columns are stored for performance reasons, but can be reconstructed if necessary. Reconstruction formulas/procedures are also shown here.

- **Column 6:** Total
  - Price<sub>same row</sub> × Quantity<sub>same row</sub>

- **Column 7:** Sum
  - Sum<sub>above row</sub> + Total<sub>same row</sub>

### Example data
Here is some sample CSV data, along with it's processed form:
```
00000000, 41987, ETH, 5940.5, 5, 29702.5, 29702.5
00000001, 41988, ETH, 5946.4, 324, 1926633.6, 1956336.1
00000002, 41993, ETH, -9452.5, 5, -47262.5, 1909073.6
```

Interpreted into a more standard order book format, it would become:
| Order ID | Timestamp               | Side | Symbol | Quantity | Price  | Total     | Sum       |
|----------|-------------------------|------|--------|----------|--------|-----------|-----------|
| 00000000 | 2022-01-07 11:39:47 UTC | BUY  | ETH    | 5        | 5940.5 | 29702.5   | 29702.5   |
| 00000001 | 2022-01-07 11:39:48 UTC | BUY  | ETH    | 324      | 5946.4 | 1926633.6 | 1956336.1 |
| 00000002 | 2022-01-07 11:39:53 UTC | SELL | ETH    | 5        | 9452.5 | 47262.5   | 1909073.6 |
