# Associations Between Physical Activity and Interoception

[![DOI](https://img.shields.io/badge/DOI-10.1080%2F1612197X.2026.2665662-blue)](https://doi.org/10.1080/1612197X.2026.2665662)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python 3.11](https://img.shields.io/badge/python-3.11-blue)
[![Lint](https://github.com/JesperMulder/interoception-physical-activity/actions/workflows/lint.yml/badge.svg)](https://github.com/JesperMulder/interoception-physical-activity/actions/workflows/lint.yml)

Analysis code for the research paper: **"Associations Between Physical Activity Intensity and Experience, Self-Regulation, and Self-Reported Interoceptive Accuracy and Attention"**

## Publication Information

**Publication:** https://doi.org/10.1080/1612197X.2026.2665662 (published 11-05-2026)

**Authors:** J. Mulder, J.C. Kiefte-de Jong, J.D. de Vries, M.T. Elferink-Gemser

## Research Objectives

The script tests how these variables relate to interoception:

1. **Physical activity intensities** (walking, moderate, vigorous exercise)
2. **Years of PA experience**
3. **Self-regulation abilities** (SSRQ)
4. **Self-reported interoceptive accuracy** (IAS) and **attention** (IATS)

## Requirements

* **Python 3.11**
* Conda environment (`environment.yml`, recommended) or pip (`requirements.txt`)

### Installation

1. Clone this repository:

```bash
git clone https://github.com/JesperMulder/interoception-physical-activity.git
cd interoception-physical-activity
```

2. Create the environment:

```bash
conda env create -f environment.yml
conda activate interoception-physical-activity
```

or, with pip:

```bash
pip install -r requirements.txt
```

## Usage

1. **Prepare your data:** Place your SPSS dataset in the `data/` directory (see `data/README.md`)
2. **Set the data path:** Edit the `file_path` variable near the top of `interoception_PA_analyses.py` (it is intentionally left blank)
3. **Run the analysis:**

```bash
python interoception_PA_analyses.py
```

4. **View results:** Check the `output/` directory for generated files

### Expected Runtime

* Complete analysis: ~5-10 minutes
* Generates 8 output files including statistical results and visualizations

## Repository Structure

```
interoception-physical-activity/
├── README.md                 # This file
├── LICENSE                   # MIT License
├── .gitignore               # Git ignore rules
├── CITATION.cff             # Citation metadata
├── CHANGELOG.md             # Version history
├── CONTRIBUTING.md          # Contribution guide
├── environment.yml          # Conda environment
├── requirements.txt         # Python dependencies
├── interoception_PA_analyses.py  # Main analysis script
├── .github/                 # Issue templates and lint workflow
├── data/                    # Data directory
│   └── README.md           # Data information
├── output/                  # Results directory
│   └── README.md           # Output information
└── docs/                    # Documentation
    └── README.md           # Additional documentation
```

## Generated Outputs

The analysis produces the following files in `output/`:

### Statistical Results

* `reliability_results.csv` - Internal consistency (Cronbach's α) for all scales
* `lognorm_results.xlsx` - Main regression analyses (univariate, multivariate, stepwise)
* `lognorm_interaction_results.xlsx` - Analyses with PA × self-regulation interactions
* `lognorm_results_by_SSRQ.xlsx` - Sensitivity analyses by self-regulation levels
* `descriptive_table.xlsx` - Descriptive statistics

### Visualizations

* `continuous_variables_histograms.png` - Distribution plots for continuous variables
* `categorical_variables_histograms.png` - Distribution plots for categorical variables
* `correlation_matrix.png` - Correlation heatmap for all continuous measures

## Analysis Pipeline

1. **Data Loading & Preprocessing**

   * Import SPSS dataset with final variable selection
   * Handle inactive participants and experience variables
   * Data quality checks and validation
2. **Missing Data Analysis**

   * Missing At Random (MAR) assessment using logistic regression
   * Multiple imputation using MICE (5 datasets, 20 iterations)
   * Post-imputation validation
3. **Outlier Detection & Removal**

   * Z-score based outlier detection (±3 SD threshold)
   * Applied to key outcome and predictor variables
4. **Internal Consistency Analysis**

   * Cronbach's alpha for IAS (21 items), IATS (21 items), SSRQ (31 items)
   * Reliability interpretation and reporting
5. **Descriptive Statistics**

   * Summary statistics for all variables
   * Age, sex, and socioeconomic status distributions
   * Correlation analysis between continuous measures
6. **Main Regression Analyses**

   * **Log-normalization** of all continuous variables
   * **Univariate models:** Each predictor vs. IAS/IATS separately
   * **Model 1:** Core PA variables (walking, moderate, vigorous hours + experience + self-regulation)
   * **Model 2:** Stepwise addition of demographic variables (sex, age, SES)
7. **Interaction Analyses**

   * PA intensity × self-regulation interaction terms
   * Enhanced model testing for moderation effects
8. **Sensitivity Analyses**

   * Median split based on self-regulation scores
   * Separate analyses for high vs. low self-regulation groups

## Variables Analyzed

### Outcome Variables

* **IAS_Totaal:** Interoceptive Accuracy Scale total score
* **IATS_Totaal:** Interoceptive Attention Scale total score

### Predictor Variables

* **Wandel_UrenWeek:** Walking hours per week
* **Moderate_UrenWeek:** Moderate intensity PA hours per week
* **Vigorous_UrenWeek:** Vigorous intensity PA hours per week
* **IPAQ_SportErvaring:** Years of sport/PA experience
* **SSRQ_Totaal:** Short Self-Regulation Questionnaire total score

### Control Variables

* **Geslacht:** Sex (1=male, 2=female)
* **Leeftijd:** Age in years
* **SES:** Socioeconomic status (1=low, 2=high)

## Data Privacy

**Important:** Raw data is **not included** in this repository to protect participant privacy and comply with ethical guidelines. The analysis script is provided for transparency and reproducibility of statistical methods.

For data access requests or replication purposes, please contact the corresponding author.

## Citation

If you use this code in your research, please cite:

```
Mulder, J., Kiefte-de Jong, J. C., de Vries, J. D., & Elferink-Gemser, M. T. (2026). Associations Between Physical Activity Intensity and Experience, Self-Regulation, and Self-Reported Interoceptive Accuracy and Attention. https://doi.org/10.1080/1612197X.2026.2665662
```

GitHub's "Cite this repository" button uses `CITATION.cff`. An earlier preprint version is available at https://doi.org/10.1101/2025.05.06.25326015.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Keywords:** interoception, physical activity, self-regulation, regression analysis, Python, reproducible research

