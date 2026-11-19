"""
Analysis Script: Associations Between Physical Activity and Interoception
Paper: Associations Between Physical Activity Intensity and Experience, Self-Regulation,
       and Self-Reported Interoceptive Accuracy and Attention
       Mulder, Kiefte-de Jong, de Vries & Elferink-Gemser
       International Journal of Sport and Exercise Psychology, published 11-05-2026, https://doi.org/10.1080/1612197X.2026.2665662

This script examines associations between:
1. Physical activity intensities (walking, moderate, vigorous)
2. Years of PA experience  
3. Self-regulation (SSRQ)
4. Self-reported interoceptive accuracy (IAS) and attention (IATS)

Analysis uses log-normalized regression analyses.

Author: Jesper Mulder
Institution: Leiden University Medical Center
License: MIT
Repository: https://github.com/JesperMulder/interoception-physical-activity
Date: 2026

Before running: set `file_path` below (DATA LOADING AND PREPROCESSING) to the
location of your SPSS (.sav) file. Raw data are not part of this repository.
"""

# =============================================================================
# IMPORTS AND SETUP
# =============================================================================
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from scipy import stats
import miceforest as mf
from statsmodels.formula.api import ols
from statsmodels.stats.multitest import multipletests
from itertools import combinations
import arviz as az
from scipy.stats import gaussian_kde
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder

pd.set_option('display.max_columns', None)
sns.set(style="whitegrid")

# =============================================================================
# DATA LOADING AND PREPROCESSING
# =============================================================================

# Path to file
file_path = # Update to your file path

# Final columns used in analyses
cols_to_keep = ['Persoon_ID', 'IPAQ_SportErvaring', 'Geslacht', 'Leeftijd',
                'Opleiding_Cat', 'Inkomen_Cat', 'SES', 'IAS_Totaal',
                'IATS_Totaal', 'Wandel_UrenWeek', 'Moderate_UrenWeek',
                'Vigorous_UrenWeek', 'IPAQ_Uren_Totaal', 'SSRQ_Totaal']

# Load dataframe
df_analysis = pd.read_spss(file_path, usecols=cols_to_keep, convert_categoricals=False)

# Set NaNs for inactive participants to 0 years of experience (only if missing)
df_analysis.loc[(df_analysis['IPAQ_Uren_Totaal'] < 2.5) & (df_analysis['IPAQ_SportErvaring'].isna()), 'IPAQ_SportErvaring'] = 0

# =============================================================================
# DATA QUALITY CHECKS
# =============================================================================

# Sanity check: Remove unrealistic sport experience values
df_analysis['SportErvaring_check'] = df_analysis['Leeftijd'] - df_analysis['IPAQ_SportErvaring']
df_analysis = df_analysis[df_analysis['SportErvaring_check'].ge(0) | df_analysis['SportErvaring_check'].isna()]
df_analysis.drop(columns=['SportErvaring_check'], inplace=True)

# Check if data was loaded correctly
print("Dataset loaded successfully!")
print(f"Dataset shape: {df_analysis.shape}")
df_analysis.info()

# =============================================================================
# MISSING DATA ANALYSIS
# =============================================================================

# Missing data summary
missing_summary = df_analysis.isnull().sum().reset_index()
missing_summary.columns = ['Column', 'MissingValues']
missing_summary['% Missing'] = 100 * missing_summary['MissingValues'] / len(df_analysis)
missing_summary = missing_summary.sort_values(by='% Missing', ascending=False)
print("\nMissing Data Summary:")
print(missing_summary)

# Visualize missing data
plt.figure(figsize=(10, 6))
sns.heatmap(df_analysis.isnull(), cbar=True, yticklabels=False)
plt.title("Missing Data Heatmap")
plt.tight_layout()
plt.show()

# Missing at Random analyses
df_encoded = df_analysis.copy()
label_encoders = {}
for col in df_encoded.select_dtypes(include='object').columns:
    le = LabelEncoder()
    df_encoded[col] = df_encoded[col].astype(str)
    df_encoded[col] = le.fit_transform(df_encoded[col])
    label_encoders[col] = le

# Analyze whether missingness in each column is associated with values in other columns
mar_results = []

for col in df_analysis.columns:
    if df_analysis[col].isnull().sum() == 0:
        continue  # skip columns without missing data

    # Create binary target: 1 = missing, 0 = present
    target = df_analysis[col].isnull().astype(int)
    
    # Use other columns as predictors
    X = df_encoded.drop(columns=[col])
    y = target

    if X.select_dtypes(include=[np.number]).shape[1] == 0:
        continue  # skip if no numeric predictors

    model = LogisticRegression(max_iter=1000)
    try:
        model.fit(X.fillna(-999), y)
        score = model.score(X.fillna(-999), y)
        mar_results.append({'Column': col, 'Predictive_Score': score})
    except Exception as e:
        mar_results.append({'Column': col, 'Predictive_Score': np.nan, 'Error': str(e)})

mar_df = pd.DataFrame(mar_results)
print("\nMAR Logistic Analysis Results (Score ~0.5 = Not MAR, Score >>0.5 = Possibly MAR):")
print(mar_df.sort_values(by='Predictive_Score', ascending=False))

# =============================================================================
# MISSING VALUES IMPUTATION
# =============================================================================

# Reset index for imputation
df_analysis = df_analysis.reset_index(drop=True)

# Columns to impute
impute_columns = ['IPAQ_SportErvaring', 'SES']
imputation_predictors = ['Geslacht', 'Leeftijd', 'IAS_Totaal', 'IATS_Totaal',
                         'Wandel_UrenWeek', 'Moderate_UrenWeek', 'Vigorous_UrenWeek',
                         'IPAQ_Uren_Totaal', 'SSRQ_Totaal']
variable_schema = {col: imputation_predictors for col in impute_columns}

# Imputation using MICE
impute = mf.ImputationKernel(
    data=df_analysis,
    num_datasets=10,
    save_all_iterations_data=True,
    random_state=42,
    variable_schema=variable_schema
)

impute.mice(20)
impute.complete_data(0)
df_imputed = pd.concat([impute.complete_data(i) for i in range(5)]).groupby(level=0).mean()

# Round categorical variables
columns_to_round = ['SES']
df_imputed[columns_to_round] = df_imputed[columns_to_round].round()

# Check imputation outcome
print("\nImputation completed!")
df_imputed.info()
print("\nPost-imputation descriptives:")
print(df_imputed.describe())

# Post-imputation check: Ensure sport experience is not greater than age
df_imputed['SportErvaring_check'] = df_imputed['Leeftijd'] - df_imputed['IPAQ_SportErvaring']
df_imputed.loc[df_imputed['SportErvaring_check'] < 0, 'IPAQ_SportErvaring'] = df_imputed['Leeftijd']
df_imputed.drop(columns=['SportErvaring_check'], inplace=True)

# =============================================================================
# OUTLIER REMOVAL
# =============================================================================

# Variables to check for outliers
var_outliers = ['IAS_Totaal', 'IATS_Totaal', 'Wandel_UrenWeek', 'Moderate_UrenWeek',
                'Vigorous_UrenWeek', 'IPAQ_SportErvaring']

# Calculate z-scores
z_scores = np.abs(stats.zscore(df_imputed[var_outliers]))

# Create new dataframe without outliers
threshold = 3  # 3 SD threshold
df_clean = df_imputed[(z_scores < threshold).all(axis=1)]

print(f"\nOutlier removal completed!")
print(f"Original dataset: {df_imputed.shape[0]} participants")
print(f"Final dataset: {df_clean.shape[0]} participants")
print(f"Removed: {df_imputed.shape[0] - df_clean.shape[0]} participants ({((df_imputed.shape[0] - df_clean.shape[0])/df_imputed.shape[0]*100):.1f}%)")

# =============================================================================
# INTERNAL CONSISTENCY ANALYSIS
# =============================================================================

# Define questionnaire columns
ias_cols = [f'IAS_{i}' for i in range(1, 22)]  # IAS_1 through IAS_21
iats_cols = [f'IATS_{i}' for i in range(1, 22)]  # IATS_1 through IATS_21
ssrq_cols = [f'SSRQ_{i}' for i in range(1, 32)]  # SSRQ_1 through SSRQ_31

# Combine all questionnaire columns
questionnaire_cols = ias_cols + iats_cols + ssrq_cols

# Get the IDs of participants in cleaned dataset
if 'Persoon_ID' in df_clean.columns:
    clean_ids = df_clean['Persoon_ID'].values
    print(f"\nInternal consistency analysis for {len(clean_ids)} participants")
    
    # Load questionnaire data with Persoon_ID to match participants
    try:
        full_data = pd.read_spss(file_path, usecols=['Persoon_ID'] + questionnaire_cols)
        print("Full questionnaire data loaded successfully!")
        
        # Filter to only include participants from cleaned dataset
        data = full_data[full_data['Persoon_ID'].isin(clean_ids)].copy()
        print(f"Filtered questionnaire data shape: {data.shape}")
        
        # Drop Persoon_ID for reliability analysis
        data = data.drop('Persoon_ID', axis=1)
        
    except Exception as e:
        print(f"Error loading data: {e}")
        import pyreadstat
        full_data, meta = pyreadstat.read_sav(file_path, usecols=['Persoon_ID'] + questionnaire_cols)
        data = full_data[full_data['Persoon_ID'].isin(clean_ids)].copy()
        data = data.drop('Persoon_ID', axis=1)

def cronbach_alpha(df):
    """
    Calculate Cronbach's alpha for internal consistency
    
    Parameters:
    df (DataFrame): DataFrame containing the items for analysis
    
    Returns:
    float: Cronbach's alpha coefficient
    """
    # Drop rows with any missing values
    df_clean_alpha = df.dropna()
    
    if df_clean_alpha.empty:
        return np.nan
    
    # Number of items
    k = df_clean_alpha.shape[1]
    
    # Variance of each item
    item_vars = df_clean_alpha.var(axis=0, ddof=1)
    
    # Variance of the sum of items
    total_var = df_clean_alpha.sum(axis=1).var(ddof=1)
    
    # Cronbach's alpha formula
    alpha = (k / (k - 1)) * (1 - (item_vars.sum() / total_var))
    
    return alpha

def calculate_questionnaire_reliability(data, cols, questionnaire_name):
    """
    Calculate and display reliability statistics for a questionnaire
    """
    # Extract questionnaire data
    quest_data = data[cols].copy()
    
    # Basic descriptive statistics
    n_items = len(cols)
    n_complete_cases = quest_data.dropna().shape[0]
    n_total_cases = quest_data.shape[0]
    missing_percentage = ((n_total_cases - n_complete_cases) / n_total_cases) * 100
    
    # Calculate Cronbach's alpha
    alpha = cronbach_alpha(quest_data)
    
    # Display results
    print(f"\n{'='*50}")
    print(f"RELIABILITY ANALYSIS: {questionnaire_name}")
    print(f"{'='*50}")
    print(f"Number of items: {n_items}")
    print(f"Total cases: {n_total_cases}")
    print(f"Complete cases: {n_complete_cases}")
    print(f"Missing data: {missing_percentage:.1f}%")
    print(f"Cronbach's Alpha: {alpha:.3f}")
    
    # Interpretation
    if alpha >= 0.9:
        interpretation = "Excellent"
    elif alpha >= 0.8:
        interpretation = "Good"
    elif alpha >= 0.7:
        interpretation = "Acceptable"
    elif alpha >= 0.6:
        interpretation = "Questionable"
    else:
        interpretation = "Poor"
    
    print(f"Reliability: {interpretation}")
    
    return alpha, n_complete_cases, missing_percentage

# Calculate reliability for each questionnaire
print("\nINTERNAL CONSISTENCY ANALYSIS")
print("="*60)
print(f"Analysis conducted on cleaned dataset (N={data.shape[0]} participants)")
print("="*60)

# IAS (Interoceptive Accuracy Scale)
ias_alpha, ias_n, ias_missing = calculate_questionnaire_reliability(
    data, ias_cols, "IAS (Interoceptive Accuracy Scale)"
)

# IATS (Interoceptive Attention Scale)  
iats_alpha, iats_n, iats_missing = calculate_questionnaire_reliability(
    data, iats_cols, "IATS (Interoceptive Attention Scale)"
)

# SSRQ (Short Self-Regulation Questionnaire)
ssrq_alpha, ssrq_n, ssrq_missing = calculate_questionnaire_reliability(
    data, ssrq_cols, "SSRQ (Short Self-Regulation Questionnaire)"
)

# Summary table
print(f"\n{'='*60}")
print("SUMMARY OF RELIABILITY COEFFICIENTS")
print(f"{'='*60}")
print(f"{'Questionnaire':<35} {'α':<8} {'N':<6} {'Missing %':<10}")
print("-" * 60)
print(f"{'IAS':<35} {ias_alpha:.3f}   {ias_n:<6} {ias_missing:.1f}%")
print(f"{'IATS':<35} {iats_alpha:.3f}   {iats_n:<6} {iats_missing:.1f}%")
print(f"{'SSRQ':<35} {ssrq_alpha:.3f}   {ssrq_n:<6} {ssrq_missing:.1f}%")

# Save reliability results
results_df = pd.DataFrame({
    'Questionnaire': ['IAS', 'IATS', 'SSRQ'],
    'Cronbach_Alpha': [ias_alpha, iats_alpha, ssrq_alpha],
    'N_Complete_Cases': [ias_n, iats_n, ssrq_n],
    'Missing_Percentage': [ias_missing, iats_missing, ssrq_missing]
})

results_df.to_csv('output/reliability_results.csv', index=False)
print(f"\nReliability analysis completed and saved to output/reliability_results.csv")

# =============================================================================
# DESCRIPTIVE STATISTICS
# =============================================================================

# Continuous variables
cont_vars = ['IPAQ_SportErvaring', 'Leeftijd', 'IAS_Totaal', 'IATS_Totaal',
             'Wandel_UrenWeek', 'Moderate_UrenWeek', 'Vigorous_UrenWeek',
             'IPAQ_Uren_Totaal', 'SSRQ_Totaal']

print("\n" + "="*60)
print("DESCRIPTIVE STATISTICS")
print("="*60)
print("\nContinuous Variables:")
print(df_clean[cont_vars].describe().round(2))

# Categorical variables
cat_vars = ['Geslacht', 'Opleiding_Cat', 'Inkomen_Cat', 'SES']

print("\nCategorical Variables:")
for var in cat_vars:
    print(f"\n{var}:")
    print(df_clean[var].value_counts().sort_index())

# Create histograms for continuous variables
fig, axes = plt.subplots(3, 3, figsize=(15, 12))
axes = axes.ravel()

for i, var in enumerate(cont_vars):
    df_clean[var].hist(bins=30, ax=axes[i])
    axes[i].set_title(var)
    axes[i].set_xlabel(var)
    axes[i].set_ylabel('Frequency')

plt.tight_layout()
plt.savefig('output/continuous_variables_histograms.png', dpi=300, bbox_inches='tight')
plt.show()

# Create histograms for categorical variables
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
axes = axes.ravel()

for i, var in enumerate(cat_vars):
    df_clean[var].hist(bins=30, ax=axes[i])
    axes[i].set_title(var)
    axes[i].set_xlabel(var)
    axes[i].set_ylabel('Frequency')

plt.tight_layout()
plt.savefig('output/categorical_variables_histograms.png', dpi=300, bbox_inches='tight')
plt.show()

# Age and sex statistics
print(f"\n{'='*40}")
print("AGE AND SEX STATISTICS")
print(f"{'='*40}")
print(f"Average age: {df_clean['Leeftijd'].mean():.1f} ± {df_clean['Leeftijd'].std():.1f} years")
print(f"Age range: {df_clean['Leeftijd'].min():.0f} - {df_clean['Leeftijd'].max():.0f} years")

# Sex distribution
sex_count = df_clean['Geslacht'].value_counts()
sex_percentage = (sex_count / sex_count.sum() * 100).round(1)
print(f"\nSex distribution:")
print(f"Male (1): {sex_count.get(1, 0)} ({sex_percentage.get(1, 0):.1f}%)")
print(f"Female (2): {sex_count.get(2, 0)} ({sex_percentage.get(2, 0):.1f}%)")

# Mean age by sex
print(f"\nMean age by sex:")
age_by_sex = df_clean.groupby('Geslacht')['Leeftijd'].agg(['mean', 'std']).round(1)
print(age_by_sex)

# =============================================================================
# CORRELATION ANALYSIS
# =============================================================================

print(f"\n{'='*40}")
print("CORRELATION ANALYSIS")
print(f"{'='*40}")

# Calculate correlation matrix for continuous variables
corr_matrix = df_clean[cont_vars].corr()
print("\nCorrelation Matrix:")
print(corr_matrix.round(3))

# Create correlation heatmap
plt.figure(figsize=(12, 10))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt='.2f', 
            square=True, linewidths=0.5)
plt.title('Correlation Matrix - Continuous Variables')
plt.tight_layout()
plt.savefig('output/correlation_matrix.png', dpi=300, bbox_inches='tight')
plt.show()

# =============================================================================
# LOG-NORMALIZED REGRESSION ANALYSES (WITHOUT INTERACTION TERMS)
# =============================================================================

print(f"\n{'='*60}")
print("LOG-NORMALIZED REGRESSION ANALYSES")
print(f"{'='*60}")

# Dependent variables
dependent_vars = ['IAS_Totaal', 'IATS_Totaal']

# Independent variables for univariate analysis
independent_vars_univariate = ['Wandel_UrenWeek', 'Moderate_UrenWeek', 'Vigorous_UrenWeek',
                               'IPAQ_SportErvaring', 'SSRQ_Totaal', 'Geslacht',
                               'Leeftijd', 'SES']

# Independent variables for model 1
independent_vars_model_1 = ['Wandel_UrenWeek', 'Moderate_UrenWeek', 'Vigorous_UrenWeek',
                            'IPAQ_SportErvaring', 'SSRQ_Totaal']

# Variables to add to the model one by one
additional_vars = ['Geslacht', 'Leeftijd', 'SES']

# Initialize dictionaries to hold results
log_univariate_results = {}
log_multivariate_results_model_1 = {}
log_multivariate_results_stepwise_model_2 = {}
log_fit_stats_univariate = {}
log_fit_stats_model_1 = {}
log_fit_stats_stepwise_model_2 = {}

# Function to extract model fit statistics
def extract_fit_statistics(model):
    """Extract comprehensive fit statistics from a regression model"""
    y_true = model.model.endog
    y_pred = model.fittedvalues
    
    return {
        "R-squared": model.rsquared,
        "Adjusted R-squared": model.rsquared_adj,
        "F-statistic": model.fvalue,
        "F-statistic p-value": model.f_pvalue,
        "AIC": model.aic,
        "BIC": model.bic,
        "RMSE": np.sqrt(mean_squared_error(y_true, y_pred)),
        "MAE": mean_absolute_error(y_true, y_pred)
    }

# Apply log-normalization to all relevant variables
df_log = df_clean.copy()
variables_to_transform = dependent_vars + independent_vars_univariate
for var in variables_to_transform:
    df_log[var] = np.log1p(df_log[var])

print("Log-normalization completed for all variables.")

# Univariate regressions with log-normalized variables
print("\nRunning univariate regression analyses...")
for dependent_var in dependent_vars:
    for var in independent_vars_univariate:
        X = df_log[[var]]
        X = sm.add_constant(X)
        y = df_log[dependent_var]
        
        model = sm.OLS(y, X).fit()
        
        result_df = pd.DataFrame({
            "Coefficient": model.params,
            "Standard Error": model.bse,
            "t-value": model.tvalues,
            "p-value": model.pvalues,
            "Confidence Interval Lower": model.conf_int()[0],
            "Confidence Interval Upper": model.conf_int()[1]
        })
        
        sheet_name = f'{dependent_var} x {var}'
        log_univariate_results[sheet_name] = result_df
        log_fit_stats_univariate[sheet_name] = extract_fit_statistics(model)

# Multivariate regressions for Model 1 with log-normalized variables
print("Running multivariate regression analyses (Model 1)...")
for dependent_var in dependent_vars:
    X = df_log[independent_vars_model_1]
    X = sm.add_constant(X)
    y = df_log[dependent_var]
    
    model = sm.OLS(y, X).fit()
    
    result_df = pd.DataFrame({
        "Coefficients": model.params,
        "Standard Errors": model.bse,
        "t-values": model.tvalues,
        "p-values": model.pvalues,
        "Confidence Interval Lower": model.conf_int()[0],
        "Confidence Interval Upper": model.conf_int()[1]
    })
    
    log_multivariate_results_model_1[f'{dependent_var} Model 1'] = result_df
    log_fit_stats_model_1[f'{dependent_var} Model 1'] = extract_fit_statistics(model)

# Stepwise Model 2 with log-normalized variables
print("Running stepwise regression analyses (Model 2)...")
for dependent_var in dependent_vars:
    base_vars_model_2 = independent_vars_model_1.copy()
    initial_aic = np.inf
    
    for var in additional_vars:
        current_vars = base_vars_model_2 + [var]
        
        X = df_log[current_vars]
        X = sm.add_constant(X)
        y = df_log[dependent_var]
        
        model = sm.OLS(y, X).fit()
        
        if model.aic < initial_aic:
            base_vars_model_2 = current_vars
            initial_aic = model.aic
            log_multivariate_results_stepwise_model_2[f'{dependent_var} with {var}'] = pd.DataFrame({
                "Coefficients": model.params,
                "Standard Errors": model.bse,
                "t-values": model.tvalues,
                "p-values": model.pvalues,
                "Confidence Interval Lower": model.conf_int()[0],
                "Confidence Interval Upper": model.conf_int()[1]
            })
            log_fit_stats_stepwise_model_2[f'{dependent_var} with {var}'] = extract_fit_statistics(model)
    
    # Final model
    final_model = sm.OLS(df_log[dependent_var], sm.add_constant(df_log[base_vars_model_2])).fit()
    log_multivariate_results_stepwise_model_2[f'{dependent_var} Final Model 2'] = pd.DataFrame({
        "Coefficients": final_model.params,
        "Standard Errors": final_model.bse,
        "t-values": final_model.tvalues,
        "p-values": final_model.pvalues,
        "Confidence Interval Lower": final_model.conf_int()[0],
        "Confidence Interval Upper": final_model.conf_int()[1]
    })
    log_fit_stats_stepwise_model_2[f'{dependent_var} Final Model 2'] = extract_fit_statistics(final_model)

# Save all results to Excel file
lognorm_results_path = "output/lognorm_results.xlsx"
with pd.ExcelWriter(lognorm_results_path) as writer:
    # Write univariate results
    univariate_df = pd.concat(log_univariate_results)
    univariate_df.to_excel(writer, sheet_name='Univariate', float_format="%.3f")
    
    # Write multivariate results for Model 1
    model_1_df = pd.concat(log_multivariate_results_model_1)
    model_1_df.to_excel(writer, sheet_name='Model 1', float_format="%.3f")
    
    # Write stepwise multivariate results for Model 2
    model_2_df = pd.concat(log_multivariate_results_stepwise_model_2)
    model_2_df.to_excel(writer, sheet_name='Stepwise Model 2', float_format="%.3f")
    
    # Write fit statistics for all models
    fit_stats_df_univariate = pd.DataFrame(log_fit_stats_univariate).T
    fit_stats_df_univariate.to_excel(writer, sheet_name='Univariate Fit Stats', float_format="%.3f")
    
    fit_stats_df_model_1 = pd.DataFrame(log_fit_stats_model_1).T
    fit_stats_df_model_1.to_excel(writer, sheet_name='Model 1 Fit Stats', float_format="%.3f")
    
    fit_stats_df_stepwise_model_2 = pd.DataFrame(log_fit_stats_stepwise_model_2).T
    fit_stats_df_stepwise_model_2.to_excel(writer, sheet_name='Stepwise Model 2 Fit Stats', float_format="%.3f")

print(f"Log-normalized regression (without interaction) results saved to {lognorm_results_path}")

# =============================================================================
# LOG-NORMALIZED REGRESSION ANALYSES (WITH INTERACTION TERMS)
# =============================================================================

print(f"\n{'='*60}")
print("LOG-NORMALIZED REGRESSION ANALYSES WITH INTERACTION TERMS")
print(f"{'='*60}")

# Define interaction terms
df_clean['Wandel_UrenWeek_SSRQ'] = df_clean['Wandel_UrenWeek'] * df_clean['SSRQ_Totaal']
df_clean['Moderate_UrenWeek_SSRQ'] = df_clean['Moderate_UrenWeek'] * df_clean['SSRQ_Totaal']
df_clean['Vigorous_UrenWeek_SSRQ'] = df_clean['Vigorous_UrenWeek'] * df_clean['SSRQ_Totaal']

# Update independent variables to include interaction terms
interaction_terms = ['Wandel_UrenWeek_SSRQ', 'Moderate_UrenWeek_SSRQ', 'Vigorous_UrenWeek_SSRQ']
independent_vars_model_1_interaction = independent_vars_model_1 + interaction_terms

# Initialize dictionaries for interaction results
interaction_log_multivariate_results_model_1 = {}
interaction_log_multivariate_results_stepwise_model_2 = {}
interaction_log_fit_stats_model_1 = {}
interaction_log_fit_stats_stepwise_model_2 = {}

# Apply log-normalization to interaction terms
df_log_interaction = df_clean.copy()
variables_to_transform_interaction = dependent_vars + independent_vars_univariate + interaction_terms
for var in variables_to_transform_interaction:
    df_log_interaction[var] = np.log1p(df_log_interaction[var])

print("Log-normalization completed for variables with interaction terms.")

# Multivariate regressions for Model 1 with interaction terms
print("Running multivariate regression analyses with interaction terms (Model 1)...")
for dependent_var in dependent_vars:
    X = df_log_interaction[independent_vars_model_1_interaction]
    X = sm.add_constant(X)
    y = df_log_interaction[dependent_var]
    
    model = sm.OLS(y, X).fit()
    
    result_df = pd.DataFrame({
        "Coefficients": model.params,
        "Standard Errors": model.bse,
        "t-values": model.tvalues,
        "p-values": model.pvalues,
        "Confidence Interval Lower": model.conf_int()[0],
        "Confidence Interval Upper": model.conf_int()[1]
    })
    
    interaction_log_multivariate_results_model_1[f'{dependent_var} Model 1'] = result_df
    interaction_log_fit_stats_model_1[f'{dependent_var} Model 1'] = extract_fit_statistics(model)

# Stepwise Model 2 with interaction terms
print("Running stepwise regression analyses with interaction terms (Model 2)...")
for dependent_var in dependent_vars:
    base_vars_model_2 = independent_vars_model_1_interaction.copy()
    initial_aic = np.inf
    
    for var in additional_vars:
        current_vars = base_vars_model_2 + [var]
        
        X = df_log_interaction[current_vars]
        X = sm.add_constant(X)
        y = df_log_interaction[dependent_var]
        
        model = sm.OLS(y, X).fit()
        
        if model.aic < initial_aic:
            base_vars_model_2 = current_vars
            initial_aic = model.aic
            interaction_log_multivariate_results_stepwise_model_2[f'{dependent_var} with {var}'] = pd.DataFrame({
                "Coefficients": model.params,
                "Standard Errors": model.bse,
                "t-values": model.tvalues,
                "p-values": model.pvalues,
                "Confidence Interval Lower": model.conf_int()[0],
                "Confidence Interval Upper": model.conf_int()[1]
            })
            interaction_log_fit_stats_stepwise_model_2[f'{dependent_var} with {var}'] = extract_fit_statistics(model)
    
    # Final model with interaction terms
    final_model = sm.OLS(df_log_interaction[dependent_var], sm.add_constant(df_log_interaction[base_vars_model_2])).fit()
    interaction_log_multivariate_results_stepwise_model_2[f'{dependent_var} Final Model 2'] = pd.DataFrame({
        "Coefficients": final_model.params,
        "Standard Errors": final_model.bse,
        "t-values": final_model.tvalues,
        "p-values": final_model.pvalues,
        "Confidence Interval Lower": final_model.conf_int()[0],
        "Confidence Interval Upper": final_model.conf_int()[1]
    })
    interaction_log_fit_stats_stepwise_model_2[f'{dependent_var} Final Model 2'] = extract_fit_statistics(final_model)

# Save interaction results to Excel file
lognorm_interaction_results_path = "output/lognorm_interaction_results.xlsx"
with pd.ExcelWriter(lognorm_interaction_results_path) as writer:
    # Write multivariate results for Model 1 with interactions
    model_1_interaction_df = pd.concat(interaction_log_multivariate_results_model_1)
    model_1_interaction_df.to_excel(writer, sheet_name='Model 1 Interactions', float_format="%.3f")
    
    # Write stepwise multivariate results for Model 2 with interactions
    model_2_interaction_df = pd.concat(interaction_log_multivariate_results_stepwise_model_2)
    model_2_interaction_df.to_excel(writer, sheet_name='Stepwise Model 2 Interactions', float_format="%.3f")
    
    # Write fit statistics
    fit_stats_model_1_interaction = pd.DataFrame(interaction_log_fit_stats_model_1).T
    fit_stats_model_1_interaction.to_excel(writer, sheet_name='Model 1 Interaction Fit Stats', float_format="%.3f")
    
    fit_stats_stepwise_model_2_interaction = pd.DataFrame(interaction_log_fit_stats_stepwise_model_2).T
    fit_stats_stepwise_model_2_interaction.to_excel(writer, sheet_name='Stepwise Model 2 Interaction Fit Stats', float_format="%.3f")

print(f"Log-normalized regression (with interaction) results saved to {lognorm_interaction_results_path}")

# =============================================================================
# SENSITIVITY ANALYSES BASED ON SSRQ_TOTAAL MEDIAN
# =============================================================================

print(f"\n{'='*60}")
print("SENSITIVITY ANALYSES BASED ON SSRQ_TOTAAL MEDIAN")
print(f"{'='*60}")

# Split the dataset into two groups: below and above the median of SSRQ_Totaal
median_ssrq = df_clean['SSRQ_Totaal'].median()
df_group_1 = df_clean[df_clean['SSRQ_Totaal'] <= median_ssrq]
df_group_2 = df_clean[df_clean['SSRQ_Totaal'] > median_ssrq]

print(f"SSRQ median split: {median_ssrq:.2f}")
print(f"Group 1 (≤ median): {df_group_1.shape[0]} participants")
print(f"Group 2 (> median): {df_group_2.shape[0]} participants")

# Apply log-normalization to relevant variables for both groups
df_group_1_log = df_group_1.copy()
df_group_2_log = df_group_2.copy()

for var in variables_to_transform:
    df_group_1_log[var] = np.log1p(df_group_1_log[var])
    df_group_2_log[var] = np.log1p(df_group_2_log[var])

# Function to perform regressions for each group
def perform_regressions_for_group(df_group_log, group_name):
    """Perform complete regression analyses for a specific group"""
    group_log_univariate_results = {}
    group_log_multivariate_results_model_1 = {}
    group_log_multivariate_results_stepwise_model_2 = {}
    group_log_fit_stats_univariate = {}
    group_log_fit_stats_model_1 = {}
    group_log_fit_stats_stepwise_model_2 = {}

    print(f"\nAnalyzing {group_name}...")
    
    # Univariate regressions for the group
    for dependent_var in dependent_vars:
        for var in independent_vars_univariate:
            X = df_group_log[[var]]
            X = sm.add_constant(X)
            y = df_group_log[dependent_var]

            model = sm.OLS(y, X).fit()

            result_df = pd.DataFrame({
                "Coefficient": model.params,
                "Standard Error": model.bse,
                "t-value": model.tvalues,
                "p-value": model.pvalues,
                "Confidence Interval Lower": model.conf_int()[0],
                "Confidence Interval Upper": model.conf_int()[1]
            })

            sheet_name = f'{dependent_var} x {var}'
            group_log_univariate_results[sheet_name] = result_df
            group_log_fit_stats_univariate[sheet_name] = extract_fit_statistics(model)

    # Multivariate regressions for Model 1 for the group
    for dependent_var in dependent_vars:
        X = df_group_log[independent_vars_model_1]
        X = sm.add_constant(X)
        y = df_group_log[dependent_var]

        model = sm.OLS(y, X).fit()

        result_df = pd.DataFrame({
            "Coefficients": model.params,
            "Standard Errors": model.bse,
            "t-values": model.tvalues,
            "p-values": model.pvalues,
            "Confidence Interval Lower": model.conf_int()[0],
            "Confidence Interval Upper": model.conf_int()[1]
        })

        group_log_multivariate_results_model_1[f'{dependent_var} Model 1'] = result_df
        group_log_fit_stats_model_1[f'{dependent_var} Model 1'] = extract_fit_statistics(model)

    # Stepwise Model 2 for the group
    for dependent_var in dependent_vars:
        base_vars_model_2 = independent_vars_model_1.copy()
        initial_aic = np.inf
        
        for var in additional_vars:
            current_vars = base_vars_model_2 + [var]

            X = df_group_log[current_vars]
            X = sm.add_constant(X)
            y = df_group_log[dependent_var]

            model = sm.OLS(y, X).fit()

            if model.aic < initial_aic:
                base_vars_model_2 = current_vars
                initial_aic = model.aic
                group_log_multivariate_results_stepwise_model_2[f'{dependent_var} with {var}'] = pd.DataFrame({
                    "Coefficients": model.params,
                    "Standard Errors": model.bse,
                    "t-values": model.tvalues,
                    "p-values": model.pvalues,
                    "Confidence Interval Lower": model.conf_int()[0],
                    "Confidence Interval Upper": model.conf_int()[1]
                })
                group_log_fit_stats_stepwise_model_2[f'{dependent_var} with {var}'] = extract_fit_statistics(model)

        final_model = sm.OLS(df_group_log[dependent_var], sm.add_constant(df_group_log[base_vars_model_2])).fit()
        group_log_multivariate_results_stepwise_model_2[f'{dependent_var} Final Model 2'] = pd.DataFrame({
            "Coefficients": final_model.params,
            "Standard Errors": final_model.bse,
            "t-values": final_model.tvalues,
            "p-values": final_model.pvalues,
            "Confidence Interval Lower": final_model.conf_int()[0],
            "Confidence Interval Upper": final_model.conf_int()[1]
        })
        group_log_fit_stats_stepwise_model_2[f'{dependent_var} Final Model 2'] = extract_fit_statistics(final_model)

    return (group_log_univariate_results, group_log_multivariate_results_model_1, 
            group_log_multivariate_results_stepwise_model_2, 
            group_log_fit_stats_univariate, group_log_fit_stats_model_1, group_log_fit_stats_stepwise_model_2)

# Perform regressions for both groups
group_1_results = perform_regressions_for_group(df_group_1_log, 'Group 1 (Low SSRQ)')
group_2_results = perform_regressions_for_group(df_group_2_log, 'Group 2 (High SSRQ)')

# Save sensitivity analysis results
lognorm_sensitivity_results_path = "output/lognorm_results_by_SSRQ.xlsx"
with pd.ExcelWriter(lognorm_sensitivity_results_path) as writer:
    # Group 1 results
    univariate_df_group_1 = pd.concat(group_1_results[0])
    univariate_df_group_1.to_excel(writer, sheet_name='Group 1 Univariate', float_format="%.3f")
    model_1_df_group_1 = pd.concat(group_1_results[1])
    model_1_df_group_1.to_excel(writer, sheet_name='Group 1 Model 1', float_format="%.3f")
    model_2_df_group_1 = pd.concat(group_1_results[2])
    model_2_df_group_1.to_excel(writer, sheet_name='Group 1 Stepwise Model 2', float_format="%.3f")
    fit_stats_df_group_1_univariate = pd.DataFrame(group_1_results[3]).T
    fit_stats_df_group_1_univariate.to_excel(writer, sheet_name='Group 1 Univariate Fit Stats', float_format="%.3f")
    fit_stats_df_group_1_model_1 = pd.DataFrame(group_1_results[4]).T
    fit_stats_df_group_1_model_1.to_excel(writer, sheet_name='Group 1 Model 1 Fit Stats', float_format="%.3f")
    fit_stats_df_group_1_stepwise_model_2 = pd.DataFrame(group_1_results[5]).T
    fit_stats_df_group_1_stepwise_model_2.to_excel(writer, sheet_name='Group 1 Stepwise Model 2 Fit Stats', float_format="%.3f")

    # Group 2 results
    univariate_df_group_2 = pd.concat(group_2_results[0])
    univariate_df_group_2.to_excel(writer, sheet_name='Group 2 Univariate', float_format="%.3f")
    model_1_df_group_2 = pd.concat(group_2_results[1])
    model_1_df_group_2.to_excel(writer, sheet_name='Group 2 Model 1', float_format="%.3f")
    model_2_df_group_2 = pd.concat(group_2_results[2])
    model_2_df_group_2.to_excel(writer, sheet_name='Group 2 Stepwise Model 2', float_format="%.3f")
    fit_stats_df_group_2_univariate = pd.DataFrame(group_2_results[3]).T
    fit_stats_df_group_2_univariate.to_excel(writer, sheet_name='Group 2 Univariate Fit Stats', float_format="%.3f")
    fit_stats_df_group_2_model_1 = pd.DataFrame(group_2_results[4]).T
    fit_stats_df_group_2_model_1.to_excel(writer, sheet_name='Group 2 Model 1 Fit Stats', float_format="%.3f")
    fit_stats_df_group_2_stepwise_model_2 = pd.DataFrame(group_2_results[5]).T
    fit_stats_df_group_2_stepwise_model_2.to_excel(writer, sheet_name='Group 2 Stepwise Model 2 Fit Stats', float_format="%.3f")

print(f"Sensitivity analysis results saved to {lognorm_sensitivity_results_path}")

# =============================================================================
# DESCRIPTIVE SUMMARY TABLE
# =============================================================================

print(f"\n{'='*60}")
print("CREATING DESCRIPTIVE SUMMARY TABLE")
print(f"{'='*60}")

def mean_sd_str(series):
    """Format mean and standard deviation as string"""
    return f"{series.mean():.2f} ({series.std():.2f})"

# Total stats for all data
total_stats = df_clean[cont_vars].agg(['mean', 'std']).T
total_stats['total'] = total_stats.apply(lambda row: f"{row['mean']:.2f} ({row['std']:.2f})", axis=1)

# Save descriptive table
summary_table = total_stats[['total']].copy()
summary_table.columns = ['Mean (SD)']

# Save to Excel
descriptive_output_path = "output/descriptive_table.xlsx"
with pd.ExcelWriter(descriptive_output_path) as writer:
    summary_table.to_excel(writer, sheet_name='Descriptive Statistics')
    
    # Also save categorical variables summary
    categorical_summary = {}
    for var in cat_vars:
        counts = df_clean[var].value_counts().sort_index()
        percentages = (counts / counts.sum() * 100).round(1)
        categorical_summary[var] = pd.DataFrame({
            'Count': counts,
            'Percentage': percentages
        })
    
    # Write categorical summaries to separate sheets
    for var, summary in categorical_summary.items():
        summary.to_excel(writer, sheet_name=f'{var}_Summary')

print(f"Descriptive summary table saved to {descriptive_output_path}")

# =============================================================================
# ANALYSIS COMPLETION SUMMARY
# =============================================================================

print(f"\n{'='*60}")
print("ANALYSIS COMPLETED SUCCESSFULLY!")
print(f"{'='*60}")
print(f"Final sample size: {df_clean.shape[0]} participants")
print(f"Variables analyzed: {len(cont_vars)} continuous, {len(cat_vars)} categorical")
print(f"\nOutput files generated:")
print(f"1. output/reliability_results.csv - Internal consistency results")
print(f"2. output/lognorm_results.xlsx - Main regression analyses")
print(f"3. output/lognorm_interaction_results.xlsx - Interaction term analyses")
print(f"4. output/lognorm_results_by_SSRQ.xlsx - Sensitivity analyses")
print(f"5. output/descriptive_table.xlsx - Descriptive statistics")
print(f"6. output/continuous_variables_histograms.png - Continuous variable distributions")
print(f"7. output/categorical_variables_histograms.png - Categorical variable distributions")
print(f"8. output/correlation_matrix.png - Correlation matrix heatmap")
print(f"\nAll analyses completed according to the published methodology.")
print(f"Results are ready for manuscript preparation and journal submission.")