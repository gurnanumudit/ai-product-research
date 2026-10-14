# All Phase 1 decision rates

Every cell uses 2,000 simulated experiments. Rates are percentages; brackets are pointwise 95% Wilson Monte Carlo intervals. These intervals describe simulation precision, not external validity. Correct ship/hold breakdowns, integrity/statistical inconclusives, consumption distributions, and every prespecified paired contrast are in analysis.json.

Forced row-fixed is an operational recoding, not a seventh statistical estimator: its “false hold” means a missed worthwhile change after mapping an inconclusive result to hold. It must not be interpreted as a false evidence-based claim.

## w00_clean_iid: true gain -4 points

| Method | False ship | False hold | Correct decision | Inconclusive | Mean contexts | Point screen |
|---|---:|---:|---:|---:|---:|---|
| row_fixed | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 77.00 [75.10, 78.79] | 23.00 [21.21, 24.90] | 200.00 | meets |
| row_peek | 0.15 [0.05, 0.44] | 0.00 [0.00, 0.19] | 82.90 [81.19, 84.49] | 16.95 [15.37, 18.66] | 119.30 | meets |
| context_fixed | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 76.70 [74.80, 78.50] | 23.30 [21.50, 25.20] | 200.00 | meets |
| context_peek | 0.15 [0.05, 0.44] | 0.00 [0.00, 0.19] | 82.65 [80.93, 84.25] | 17.20 [15.61, 18.92] | 118.28 | meets |
| context_adjusted | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 62.00 [59.85, 64.10] | 38.00 [35.90, 40.15] | 152.68 | does not meet |
| integrity_adjusted | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 62.00 [59.85, 64.10] | 38.00 [35.90, 40.15] | 152.68 | does not meet |
| forced_row_fixed | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 100.00 [99.81, 100.00] | 0.00 [0.00, 0.19] | 200.00 | meets |

## w01_clean_iid: true gain +2 points

| Method | False ship | False hold | Correct decision | Inconclusive | Mean contexts | Point screen |
|---|---:|---:|---:|---:|---:|---|
| row_fixed | 2.05 [1.51, 2.77] | 0.00 [0.00, 0.19] | 3.10 [2.43, 3.95] | 94.85 [93.79, 95.74] | 200.00 | boundary: not assessed |
| row_peek | 7.60 [6.52, 8.84] | 0.00 [0.00, 0.19] | 8.30 [7.17, 9.59] | 84.10 [82.43, 85.64] | 183.08 | boundary: not assessed |
| context_fixed | 2.25 [1.69, 3.00] | 0.00 [0.00, 0.19] | 2.90 [2.25, 3.73] | 94.85 [93.79, 95.74] | 200.00 | boundary: not assessed |
| context_peek | 7.95 [6.84, 9.22] | 0.00 [0.00, 0.19] | 8.45 [7.31, 9.75] | 83.60 [81.91, 85.16] | 182.12 | boundary: not assessed |
| context_adjusted | 2.55 [1.94, 3.34] | 0.00 [0.00, 0.19] | 2.35 [1.77, 3.11] | 95.10 [94.06, 95.96] | 195.02 | boundary: not assessed |
| integrity_adjusted | 2.55 [1.94, 3.34] | 0.00 [0.00, 0.19] | 2.35 [1.77, 3.11] | 95.10 [94.06, 95.96] | 195.02 | boundary: not assessed |
| forced_row_fixed | 2.05 [1.51, 2.77] | 0.00 [0.00, 0.19] | 97.95 [97.23, 98.49] | 0.00 [0.00, 0.19] | 200.00 | boundary: not assessed |

## w02_clean_iid: true gain +10 points

| Method | False ship | False hold | Correct decision | Inconclusive | Mean contexts | Point screen |
|---|---:|---:|---:|---:|---:|---|
| row_fixed | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 95.05 [94.01, 95.92] | 4.95 [4.08, 5.99] | 200.00 | meets |
| row_peek | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 96.70 [95.82, 97.40] | 3.30 [2.60, 4.18] | 90.30 | meets |
| context_fixed | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 95.05 [94.01, 95.92] | 4.95 [4.08, 5.99] | 200.00 | meets |
| context_peek | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 96.85 [95.99, 97.53] | 3.15 [2.47, 4.01] | 89.72 | meets |
| context_adjusted | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 86.45 [84.88, 87.88] | 13.55 [12.12, 15.12] | 121.62 | meets |
| integrity_adjusted | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 86.45 [84.88, 87.88] | 13.55 [12.12, 15.12] | 121.62 | meets |
| forced_row_fixed | 0.00 [0.00, 0.19] | 4.95 [4.08, 5.99] | 95.05 [94.01, 95.92] | 0.00 [0.00, 0.19] | 200.00 | meets |

## w03_clustered_complete: true gain -4 points

| Method | False ship | False hold | Correct decision | Inconclusive | Mean contexts | Point screen |
|---|---:|---:|---:|---:|---:|---|
| row_fixed | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 70.30 [68.26, 72.26] | 29.70 [27.74, 31.74] | 200.00 | meets |
| row_peek | 1.00 [0.65, 1.54] | 0.00 [0.00, 0.19] | 78.20 [76.34, 79.95] | 20.80 [19.08, 22.63] | 114.44 | meets |
| context_fixed | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 53.65 [51.46, 55.83] | 46.35 [44.17, 48.54] | 200.00 | does not meet |
| context_peek | 0.30 [0.14, 0.65] | 0.00 [0.00, 0.19] | 61.75 [59.60, 63.86] | 37.95 [35.85, 40.10] | 142.90 | does not meet |
| context_adjusted | 0.05 [0.01, 0.28] | 0.00 [0.00, 0.19] | 38.50 [36.39, 40.65] | 61.45 [59.30, 63.56] | 171.32 | does not meet |
| integrity_adjusted | 0.05 [0.01, 0.28] | 0.00 [0.00, 0.19] | 38.50 [36.39, 40.65] | 61.45 [59.30, 63.56] | 171.32 | does not meet |
| forced_row_fixed | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 100.00 [99.81, 100.00] | 0.00 [0.00, 0.19] | 200.00 | meets |

## w04_clustered_complete: true gain +2 points

| Method | False ship | False hold | Correct decision | Inconclusive | Mean contexts | Point screen |
|---|---:|---:|---:|---:|---:|---|
| row_fixed | 6.15 [5.18, 7.29] | 0.00 [0.00, 0.19] | 6.30 [5.32, 7.45] | 87.55 [86.03, 88.93] | 200.00 | boundary: not assessed |
| row_peek | 17.05 [15.47, 18.76] | 0.00 [0.00, 0.19] | 16.05 [14.51, 17.72] | 66.90 [64.81, 68.93] | 164.16 | boundary: not assessed |
| context_fixed | 2.55 [1.94, 3.34] | 0.00 [0.00, 0.19] | 2.50 [1.90, 3.28] | 94.95 [93.90, 95.83] | 200.00 | boundary: not assessed |
| context_peek | 7.20 [6.15, 8.42] | 0.00 [0.00, 0.19] | 6.95 [5.92, 8.15] | 85.85 [84.25, 87.31] | 185.18 | boundary: not assessed |
| context_adjusted | 1.75 [1.26, 2.42] | 0.00 [0.00, 0.19] | 1.80 [1.30, 2.48] | 96.45 [95.55, 97.18] | 196.26 | boundary: not assessed |
| integrity_adjusted | 1.75 [1.26, 2.42] | 0.00 [0.00, 0.19] | 1.80 [1.30, 2.48] | 96.45 [95.55, 97.18] | 196.26 | boundary: not assessed |
| forced_row_fixed | 6.15 [5.18, 7.29] | 0.00 [0.00, 0.19] | 93.85 [92.71, 94.82] | 0.00 [0.00, 0.19] | 200.00 | boundary: not assessed |

## w05_clustered_complete: true gain +10 points

| Method | False ship | False hold | Correct decision | Inconclusive | Mean contexts | Point screen |
|---|---:|---:|---:|---:|---:|---|
| row_fixed | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 89.95 [88.55, 91.19] | 10.05 [8.81, 11.45] | 200.00 | meets |
| row_peek | 0.00 [0.00, 0.19] | 0.45 [0.24, 0.85] | 93.45 [92.28, 94.45] | 6.10 [5.13, 7.24] | 90.24 | meets |
| context_fixed | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 78.30 [76.44, 80.05] | 21.70 [19.95, 23.56] | 200.00 | meets |
| context_peek | 0.00 [0.00, 0.19] | 0.10 [0.03, 0.36] | 83.65 [81.96, 85.21] | 16.25 [14.70, 17.93] | 116.18 | meets |
| context_adjusted | 0.00 [0.00, 0.19] | 0.05 [0.01, 0.28] | 63.00 [60.86, 65.09] | 36.95 [34.86, 39.09] | 150.98 | does not meet |
| integrity_adjusted | 0.00 [0.00, 0.19] | 0.05 [0.01, 0.28] | 63.00 [60.86, 65.09] | 36.95 [34.86, 39.09] | 150.98 | does not meet |
| forced_row_fixed | 0.00 [0.00, 0.19] | 10.05 [8.81, 11.45] | 89.95 [88.55, 91.19] | 0.00 [0.00, 0.19] | 200.00 | does not meet |

## w06_clustered_mcar: true gain -4 points

| Method | False ship | False hold | Correct decision | Inconclusive | Mean contexts | Point screen |
|---|---:|---:|---:|---:|---:|---|
| row_fixed | 0.10 [0.03, 0.36] | 0.00 [0.00, 0.19] | 64.10 [61.97, 66.17] | 35.80 [33.73, 37.93] | 200.00 | does not meet |
| row_peek | 1.25 [0.85, 1.84] | 0.00 [0.00, 0.19] | 73.30 [71.32, 75.19] | 25.45 [23.59, 27.40] | 124.08 | meets |
| context_fixed | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 46.85 [44.67, 49.04] | 53.15 [50.96, 55.33] | 200.00 | does not meet |
| context_peek | 0.55 [0.31, 0.98] | 0.00 [0.00, 0.19] | 56.75 [54.57, 58.91] | 42.70 [40.55, 44.88] | 147.28 | does not meet |
| context_adjusted | 0.05 [0.01, 0.28] | 0.00 [0.00, 0.19] | 32.60 [30.58, 34.69] | 67.35 [65.26, 69.37] | 175.08 | does not meet |
| integrity_adjusted | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 100.00 [99.81, 100.00] | 200.00 | does not meet |
| forced_row_fixed | 0.10 [0.03, 0.36] | 0.00 [0.00, 0.19] | 99.90 [99.64, 99.97] | 0.00 [0.00, 0.19] | 200.00 | meets |

## w07_clustered_mcar: true gain +2 points

| Method | False ship | False hold | Correct decision | Inconclusive | Mean contexts | Point screen |
|---|---:|---:|---:|---:|---:|---|
| row_fixed | 6.10 [5.13, 7.24] | 0.00 [0.00, 0.19] | 5.80 [4.86, 6.91] | 88.10 [86.61, 89.45] | 200.00 | boundary: not assessed |
| row_peek | 15.00 [13.50, 16.63] | 0.00 [0.00, 0.19] | 15.15 [13.65, 16.79] | 69.85 [67.80, 71.82] | 166.76 | boundary: not assessed |
| context_fixed | 2.70 [2.08, 3.51] | 0.00 [0.00, 0.19] | 2.60 [1.99, 3.39] | 94.70 [93.63, 95.60] | 200.00 | boundary: not assessed |
| context_peek | 7.40 [6.33, 8.63] | 0.00 [0.00, 0.19] | 7.30 [6.24, 8.52] | 85.30 [83.68, 86.78] | 184.02 | boundary: not assessed |
| context_adjusted | 2.40 [1.81, 3.17] | 0.00 [0.00, 0.19] | 2.10 [1.56, 2.83] | 95.50 [94.50, 96.32] | 195.46 | boundary: not assessed |
| integrity_adjusted | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 100.00 [99.81, 100.00] | 200.00 | boundary: not assessed |
| forced_row_fixed | 6.10 [5.13, 7.24] | 0.00 [0.00, 0.19] | 93.90 [92.76, 94.87] | 0.00 [0.00, 0.19] | 200.00 | boundary: not assessed |

## w08_clustered_mcar: true gain +10 points

| Method | False ship | False hold | Correct decision | Inconclusive | Mean contexts | Point screen |
|---|---:|---:|---:|---:|---:|---|
| row_fixed | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 84.55 [82.90, 86.07] | 15.45 [13.93, 17.10] | 200.00 | meets |
| row_peek | 0.00 [0.00, 0.19] | 0.40 [0.20, 0.79] | 89.55 [88.13, 90.82] | 10.05 [8.81, 11.45] | 100.36 | meets |
| context_fixed | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 71.75 [69.74, 73.68] | 28.25 [26.32, 30.26] | 200.00 | meets |
| context_peek | 0.00 [0.00, 0.19] | 0.25 [0.11, 0.58] | 78.10 [76.23, 79.86] | 21.65 [19.90, 23.51] | 124.14 | meets |
| context_adjusted | 0.00 [0.00, 0.19] | 0.05 [0.01, 0.28] | 54.90 [52.71, 57.07] | 45.05 [42.88, 47.24] | 156.64 | does not meet |
| integrity_adjusted | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 100.00 [99.81, 100.00] | 200.00 | does not meet |
| forced_row_fixed | 0.00 [0.00, 0.19] | 15.45 [13.93, 17.10] | 84.55 [82.90, 86.07] | 0.00 [0.00, 0.19] | 200.00 | does not meet |

## w09_clustered_mnar: true gain -4 points

| Method | False ship | False hold | Correct decision | Inconclusive | Mean contexts | Point screen |
|---|---:|---:|---:|---:|---:|---|
| row_fixed | 55.05 [52.86, 57.22] | 0.00 [0.00, 0.19] | 0.05 [0.01, 0.28] | 44.90 [42.73, 47.09] | 200.00 | does not meet |
| row_peek | 66.05 [63.95, 68.09] | 0.00 [0.00, 0.19] | 1.10 [0.73, 1.66] | 32.85 [30.83, 34.94] | 130.78 | does not meet |
| context_fixed | 17.90 [16.28, 19.64] | 0.00 [0.00, 0.19] | 0.25 [0.11, 0.58] | 81.85 [80.10, 83.48] | 200.00 | does not meet |
| context_peek | 28.90 [26.96, 30.93] | 0.00 [0.00, 0.19] | 1.40 [0.97, 2.02] | 69.70 [67.65, 71.67] | 169.94 | does not meet |
| context_adjusted | 11.65 [10.32, 13.13] | 0.00 [0.00, 0.19] | 0.20 [0.08, 0.51] | 88.15 [86.66, 89.49] | 189.92 | does not meet |
| integrity_adjusted | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 100.00 [99.81, 100.00] | 200.00 | does not meet |
| forced_row_fixed | 55.05 [52.86, 57.22] | 0.00 [0.00, 0.19] | 44.95 [42.78, 47.14] | 0.00 [0.00, 0.19] | 200.00 | does not meet |

## w10_clustered_mnar: true gain +2 points

| Method | False ship | False hold | Correct decision | Inconclusive | Mean contexts | Point screen |
|---|---:|---:|---:|---:|---:|---|
| row_fixed | 97.85 [97.12, 98.40] | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 2.15 [1.60, 2.88] | 200.00 | boundary: not assessed |
| row_peek | 98.45 [97.81, 98.91] | 0.00 [0.00, 0.19] | 0.05 [0.01, 0.28] | 1.50 [1.05, 2.13] | 73.24 | boundary: not assessed |
| context_fixed | 83.05 [81.34, 84.63] | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 16.95 [15.37, 18.66] | 200.00 | boundary: not assessed |
| context_peek | 87.85 [86.35, 89.21] | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 12.15 [10.79, 13.65] | 109.62 | boundary: not assessed |
| context_adjusted | 70.35 [68.31, 72.31] | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 29.65 [27.69, 31.69] | 143.18 | boundary: not assessed |
| integrity_adjusted | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 100.00 [99.81, 100.00] | 200.00 | boundary: not assessed |
| forced_row_fixed | 97.85 [97.12, 98.40] | 0.00 [0.00, 0.19] | 2.15 [1.60, 2.88] | 0.00 [0.00, 0.19] | 200.00 | boundary: not assessed |

## w11_clustered_mnar: true gain +10 points

| Method | False ship | False hold | Correct decision | Inconclusive | Mean contexts | Point screen |
|---|---:|---:|---:|---:|---:|---|
| row_fixed | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 100.00 [99.81, 100.00] | 0.00 [0.00, 0.19] | 200.00 | meets |
| row_peek | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 100.00 [99.81, 100.00] | 0.00 [0.00, 0.19] | 45.26 | meets |
| context_fixed | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 100.00 [99.81, 100.00] | 0.00 [0.00, 0.19] | 200.00 | meets |
| context_peek | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 100.00 [99.81, 100.00] | 0.00 [0.00, 0.19] | 56.50 | meets |
| context_adjusted | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 99.75 [99.42, 99.89] | 0.25 [0.11, 0.58] | 71.98 | meets |
| integrity_adjusted | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 100.00 [99.81, 100.00] | 200.00 | does not meet |
| forced_row_fixed | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 100.00 [99.81, 100.00] | 0.00 [0.00, 0.19] | 200.00 | meets |

## w12_clustered_duplicate: true gain -4 points

| Method | False ship | False hold | Correct decision | Inconclusive | Mean contexts | Point screen |
|---|---:|---:|---:|---:|---:|---|
| row_fixed | 99.25 [98.77, 99.54] | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 0.75 [0.46, 1.23] | 200.00 | does not meet |
| row_peek | 99.20 [98.70, 99.51] | 0.00 [0.00, 0.19] | 0.35 [0.17, 0.72] | 0.45 [0.24, 0.85] | 59.40 | does not meet |
| context_fixed | 39.30 [37.18, 41.46] | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 60.70 [58.54, 62.82] | 200.00 | does not meet |
| context_peek | 50.00 [47.81, 52.19] | 0.00 [0.00, 0.19] | 0.55 [0.31, 0.98] | 49.45 [47.26, 51.64] | 154.16 | does not meet |
| context_adjusted | 26.55 [24.66, 28.53] | 0.00 [0.00, 0.19] | 0.15 [0.05, 0.44] | 73.30 [71.32, 75.19] | 179.68 | does not meet |
| integrity_adjusted | 0.10 [0.03, 0.36] | 0.00 [0.00, 0.19] | 38.30 [36.19, 40.45] | 61.60 [59.45, 63.71] | 172.18 | does not meet |
| forced_row_fixed | 99.25 [98.77, 99.54] | 0.00 [0.00, 0.19] | 0.75 [0.46, 1.23] | 0.00 [0.00, 0.19] | 200.00 | does not meet |

## w13_clustered_duplicate: true gain +2 points

| Method | False ship | False hold | Correct decision | Inconclusive | Mean contexts | Point screen |
|---|---:|---:|---:|---:|---:|---|
| row_fixed | 100.00 [99.81, 100.00] | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 200.00 | boundary: not assessed |
| row_peek | 100.00 [99.81, 100.00] | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 43.88 | boundary: not assessed |
| context_fixed | 96.70 [95.82, 97.40] | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 3.30 [2.60, 4.18] | 200.00 | boundary: not assessed |
| context_peek | 97.55 [96.78, 98.14] | 0.00 [0.00, 0.19] | 0.05 [0.01, 0.28] | 2.40 [1.81, 3.17] | 85.12 | boundary: not assessed |
| context_adjusted | 90.45 [89.08, 91.66] | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 9.55 [8.34, 10.92] | 114.72 | boundary: not assessed |
| integrity_adjusted | 1.95 [1.43, 2.65] | 0.00 [0.00, 0.19] | 1.65 [1.18, 2.31] | 96.40 [95.49, 97.13] | 196.60 | boundary: not assessed |
| forced_row_fixed | 100.00 [99.81, 100.00] | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 200.00 | boundary: not assessed |

## w14_clustered_duplicate: true gain +10 points

| Method | False ship | False hold | Correct decision | Inconclusive | Mean contexts | Point screen |
|---|---:|---:|---:|---:|---:|---|
| row_fixed | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 100.00 [99.81, 100.00] | 0.00 [0.00, 0.19] | 200.00 | meets |
| row_peek | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 100.00 [99.81, 100.00] | 0.00 [0.00, 0.19] | 40.12 | meets |
| context_fixed | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 100.00 [99.81, 100.00] | 0.00 [0.00, 0.19] | 200.00 | meets |
| context_peek | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 100.00 [99.81, 100.00] | 0.00 [0.00, 0.19] | 48.20 | meets |
| context_adjusted | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 100.00 [99.81, 100.00] | 0.00 [0.00, 0.19] | 57.12 | meets |
| integrity_adjusted | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 63.40 [61.27, 65.48] | 36.60 [34.52, 38.73] | 149.46 | does not meet |
| forced_row_fixed | 0.00 [0.00, 0.19] | 0.00 [0.00, 0.19] | 100.00 [99.81, 100.00] | 0.00 [0.00, 0.19] | 200.00 | meets |

The prespecified nonboundary point screen requires false decisions at most 5% and correct decisions at least 70%. Meeting it in one world does not validate the method in other worlds; a biased method can meet it when the bias happens to favor the true answer. It is not a hypothesis test or a universal deployment recommendation.
