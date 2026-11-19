# Documentation

This directory contains additional documentation and methodological details for the interoception and physical activity analysis.

## Contents

This documentation supplements the analysis script with:

- Variable definitions and coding
- The statistical approach and analytical decisions
- Software and reproducibility notes
- Quality control measures

## Key Documents

### Study Methodology
For complete methodological details, refer to the published article:
**https://doi.org/10.1080/1612197X.2026.2665662**

An earlier version of the manuscript is available as a preprint: https://doi.org/10.1101/2025.05.06.25326015

### Variable Definitions

#### Outcome Variables
- **IAS (Interoceptive Accuracy Scale):** 21-item self-report measure assessing perceived ability to detect internal bodily signals
- **IATS (Interoceptive Attention Scale):** 21-item self-report measure assessing tendency to focus attention on internal bodily signals

#### Physical Activity Variables
- **Walking, Moderate, Vigorous Hours:** Weekly hours spent in each intensity level based on IPAQ guidelines
- **Years of PA experience:** Total years of regular sport or physical activity participation
- **Total PA Hours:** Combined weekly physical activity across all intensities

#### Self-Regulation Variable
- **SSRQ (Short Self-Regulation Questionnaire):** 31-item measure of general self-regulatory capacity

#### Control Variables
- **Demographics:** Age, sex, education level, income category
- **SES:** Composite socioeconomic status indicator

### Statistical Approach

#### Log-Normalization Rationale
- Applied to address skewed distributions common in physical activity and psychological data
- Uses `log1p` transformation: log(1 + x) to handle zero values
- Improves model assumptions and interpretation

#### Model Building Strategy
1. **Univariate models:** Test each predictor individually
2. **Model 1:** Walking, moderate and vigorous hours, years of PA experience and self-regulation (SSRQ)
3. **Model 2:** Stepwise addition of confounding variables
4. **Interaction models:** PA intensity × self-regulation interactions
5. **Sensitivity analyses:** Median split by self-regulation level

#### Missing Data Handling
- **Assessment:** Missing At Random (MAR) testing using logistic regression
- **Imputation:** Multiple Imputation by Chained Equations (MICE)
- **Parameters:** 5 datasets, 20 iterations, predictive mean matching

#### Outlier Detection
- **Method:** Z-score based detection (±3 standard deviations)
- **Variables:** Applied to key outcome and predictor variables
- **Rationale:** Remove extreme values that could distort regression estimates

## Analytical Decisions

### Sample Size Considerations
- **Final N:** Determined after missing data imputation and outlier removal
- **Power analysis:** Based on expected small-to-medium effect sizes (r = 0.15-0.30)
- **Minimum requirement:** N ≥ 200 for stable regression estimates

### Statistical Significance
- **Alpha level:** p < 0.05, and p < 0.0071 for multiple comparisons
- **Multiple comparisons:** Bonferroni correction applied where appropriate
- **Effect size reporting:** Standardized coefficients and confidence intervals

### Model Selection Criteria
- **AIC/BIC:** Information criteria for nested model comparisons
- **Adjusted R²:** Variance explained accounting for model complexity
- **Cross-validation:** Internal validation using k-fold procedures

## Software and Reproducibility

### Python Environment
- **Version:** Python 3.11 (see `environment.yml`)
- **Key packages:** statsmodels, pandas, numpy, scipy, scikit-learn, miceforest, pyreadstat (full list in `requirements.txt`)
- **Environment:** `conda env create -f environment.yml` (recommended) or `pip install -r requirements.txt`

### Code Organization
```python
# Main analysis sections:
1. Data loading and preprocessing
2. Missing data analysis and imputation  
3. Outlier detection and removal
4. Internal consistency analysis
5. Descriptive statistics
6. Main regression analyses
7. Interaction term analyses
8. Sensitivity analyses
```

### Reproducibility Checklist
- [ ] Python version documented
- [ ] Package versions specified in requirements.txt
- [ ] Random seeds set for imputation (seed = 42)
- [ ] Analysis script fully automated
- [ ] Output files systematically organized
- [ ] Code comments explain analytical decisions

## Quality Control Measures

### Data Validation
- **Range checks:** Verify all variables within expected ranges
- **Logic checks:** Ensure consistent responses (e.g., total PA = sum of components)
- **Missingness patterns:** Analyze systematic missing data

### Statistical Assumptions
- **Linearity:** Assessed via residual plots
- **Homoscedasticity:** Tested using Breusch-Pagan test
- **Normality:** Q-Q plots and Shapiro-Wilk tests
- **Multicollinearity:** Variance Inflation Factor (VIF) assessment

### Sensitivity Analyses
- **Alternative specifications:** Different transformation approaches
- **Subgroup analyses:** Split by demographic characteristics
- **Robustness checks:** Alternative outlier thresholds

## Updates and Versions

### Version History
- **v1.0:** Initial analysis for preprint submission
- **v1.1:** Repository aligned with the published article (11-05-2026)
- See [CHANGELOG.md](../CHANGELOG.md) for details

### Change Log
- All substantial changes to methodology or analysis code will be documented
- Reproducible analysis pipeline maintains consistency
