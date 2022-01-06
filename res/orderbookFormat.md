# Order Book Format

This document shows how the order book data is stored and interpreted.

### Fixed columns

These values contain critical information, and should not be modified manually.

- **Column 1:** Price:
  - Positive only

- **Column 2:** Quantity + Side:
  - Quantity is indicated by absolute value, Side is indicated by sign
  - _Positive:_ A BUY of x quantity:
    - 304 = BUY, 304 qty.
  - _Negative:_ A SELL of -x quantity:
    - -40 = SELL, 40 qty.

### Dynamic columns

These columns are stored for performance reasons, but can be reconstructed if necessary. Reconstruction formulas/procedures are also shown here.

- **Column 3:** Total
  - Price<sub>same row</sub> × Quantity<sub>same row</sub>

- **Column 4:** Sum
  - Sum<sub>above row</sub> + Total<sub>same row</sub>

### Example data
Here is some sample CSV data (represented as a table), with its interpretation in this format:
| demo.csv |       |             |           |
|----------|-------|-------------|-----------|
| 5940.5   | 5     | 29702.5     | 29702.5   |
| 5946.4   | 324   | 1926633.6   | 1956336.1 |
| 9452.5   | -5    | 47262.5    | 1909073.6 |

Interpreted into a more standard order book format, it would become:
| Side     | Price  | Quantity | Total     | Sum       |
|----------|--------|----------|-----------|-----------|
| BUY      | 5940.5 | 5        | 29702.5   | 29702.5   |
| BUY      | 5946.4 | 324      | 1926633.6 | 1956336.1 |
| SELL     | 9452.5 | 5        | -47262.5  | 1909073.6 |
