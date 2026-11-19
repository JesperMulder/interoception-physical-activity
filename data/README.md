# Data Directory

This directory contains the research dataset for the interoception and physical activity study.

## Data Not Included

**We do not include the data in this repository**, to protect participant privacy.

## Expected Data Structure

The analysis script expects an SPSS file (`.sav` format) with the following variables:

### Required Variables

| Variable | Type | Description | Coding |
|----------|------|-------------|---------|
| `Persoon_ID` | Numeric | Unique participant identifier | Sequential numbers |
| `Geen_ChronischeAandoening` | Numeric | No chronic conditions | 0=No, 1=Yes |
| `IPAQ_SportErvaring` | Numeric | Years of sport/PA experience | Years |
| `Geslacht` | Numeric | Sex | 1=Male, 2=Female |
| `Leeftijd` | Numeric | Age in years | Years |
| `Opleiding_Cat` | Numeric | Education category | 1=Low, 2=Middle, 3=High |
| `Inkomen_Cat` | Numeric | Income category | 1=Below average, 2=Average, 3=Above average |
| `SES` | Numeric | Socioeconomic status | 1=Low, 2=High |
| `IAS_Totaal` | Numeric | Interoceptive Accuracy Scale total | Sum score (21-105) |
| `IATS_Totaal` | Numeric | Interoceptive Attention Scale total | Sum score (21-105) |
| `Wandel_UrenWeek` | Numeric | Walking hours per week | Hours |
| `Moderate_UrenWeek` | Numeric | Moderate PA hours per week | Hours |
| `Vigorous_UrenWeek` | Numeric | Vigorous PA hours per week | Hours |
| `IPAQ_Uren_Totaal` | Numeric | Total IPAQ hours per week | Hours |
| `SSRQ_Totaal` | Numeric | Self-Regulation Questionnaire total | Sum score (31-155) |

### Additional Variables for Reliability Analysis

For internal consistency calculations, the script also expects individual questionnaire items:

- **IAS items:** `IAS_1` through `IAS_21` (21 items)
- **IATS items:** `IATS_1` through `IATS_21` (21 items)  
- **SSRQ items:** `SSRQ_1` through `SSRQ_31` (31 items)

## File Requirements

### Expected File Structure
```
data/
├── README.md          # This file
└── dataset.sav        # Your SPSS data file (not included)
```

### File Format
- **Format:** SPSS (.sav) file
- **Encoding:** UTF-8 recommended
- **Missing values:** Should be coded as system missing (blank) in SPSS

## Privacy

### Privacy Protection Measures

The original dataset has been protected through:
- **De-identification:** All direct identifiers removed
- **Participant ID scrambling:** Original IDs replaced with study codes
- **Location anonymization:** No geographic identifiers included
- **Ethical approval:** Study conducted under institutional review board oversight

## Data Preparation Notes

If you have access to the dataset, ensure:

1. **File naming:** Save your SPSS file as `dataset.sav` in this directory
2. **Update `file_path`:** Set the `file_path` variable near the top of `interoception_PA_analyses.py` to the location of your file (e.g. `data/dataset.sav`)
3. **Variable names:** Must match exactly as listed above (case-sensitive)
4. **Missing data:** Use SPSS system missing (not numeric codes like -999)
5. **Data types:** Ensure numeric variables are properly formatted
6. **Value labels:** Optional but recommended for categorical variables

---

**Note:** This study was conducted in compliance with ethical guidelines and institutional review board approval. All participants provided informed consent for their data to be used for research purposes.