# Medicare Patient Risk Analysis
## Can we predict which Medicare patients will be readmitted?

**Author:** Jeffrey Lee  
**Data:** CMS 2008-2010 DE-SynPUF, Beneficiary and Inpatient Claims, Samples 1-5  
**Notebook:** [notebooks/medicare_readmission_analysis.ipynb](notebooks/medicare_readmission_analysis.ipynb)

---

## Why I built this

Several years working in Medicare Advantage finance at Kaiser Permanente 
brought the same two questions up repeatedly: which members are likely to 
be readmitted, and which ones will generate disproportionate cost? Health 
plans use the answers to design care management programs and allocate 
resources, but answering them well requires more than spreadsheet analysis.

This project is an attempt to explore those questions using machine 
learning on publicly available Medicare claims data. The goal was not to 
build a production model but to understand which patient characteristics 
carry the most predictive signal and what that might mean for how a health 
plan thinks about member risk stratification.

---

## The data

CMS publishes a synthetic Medicare dataset called DE-SynPUF that mirrors 
the structure of real claims data without exposing patient information. 
This project uses five of the twenty available samples, covering 581,780 
patients and 332,606 hospital admissions. After filtering to patients with 
at least one hospitalization the final analysis dataset contains 188,559 
patients.

| File | What it contains |
|---|---|
| Beneficiary Samples 1-5 | Demographics and chronic conditions |
| Inpatient Claims Samples 1-5 | Hospital admissions and costs |

---

## What I found

The most striking finding was how consistently chronic condition count 
predicts readmission risk. Patients with no chronic conditions have an 
11.5% readmission rate. Patients with 11 conditions have a 94% rate. The 
relationship climbs almost perfectly linearly across 188,559 patients with 
very little deviation, which suggests that simply counting documented 
conditions gives a health plan most of the predictive signal a more 
complex model would provide.

Not all conditions carry equal weight once the total count is controlled 
for. Kidney disease and COPD showed stronger independent associations with 
readmission than diabetes or ischemic heart disease, despite those two 
being far more prevalent. This has real implications for how care 
management programs prioritize outreach.

Predicting cost turned out to be a different problem than predicting 
readmission. The same features that achieved a ROC-AUC of 0.763 for 
readmission basically failed at predicting exact inpatient cost, producing 
an R-squared of -0.019. The likely reason is that cost depends heavily on 
visit frequency, which had to be excluded from the model to avoid data 
leakage. This points to an important distinction for health plans: 
condition flags are a useful starting point for readmission risk programs, 
but accurate cost prediction likely requires prior utilization history.

The clustering analysis found four patient segments. The most significant 
is a group of 18,371 patients with a 100% readmission rate and average 
costs exceeding 53,000 dollars over the 2008 to 2010 study period. 
Despite representing only 10% of the hospitalized population, this group 
would account for a disproportionate share of total inpatient spend.

![Patient Segments](docs/charts/patient_clusters.png)

---

## Model results

| Model | Task | ROC-AUC |
|---|---|---|
| Logistic Regression | Readmission prediction | 0.763 |
| Random Forest | Readmission prediction | 0.698 |
| Logistic Regression | High-cost classification | 0.699 |
| Random Forest | High-cost classification | 0.632 |

One issue worth documenting: an early version of the model included 
inpatient visit count as a feature and returned a perfect ROC-AUC of 1.0. 
Since readmission is defined as having more than one inpatient visit, that 
feature was directly encoding the target variable. Removing it produced 
realistic scores and a more honest picture of what the model actually 
learned.

---

## Tools used

Python, pandas, numpy, scikit-learn, matplotlib, seaborn, Jupyter

---

## Limitations

The data is synthetic and CMS explicitly cautions against using it for 
inferential research conclusions. The readmission definition used here is 
also simplified since real readmission measures typically require a 
specific time window between discharge and return that this analysis does 
not apply.

> Race and ethnicity categories follow CMS standard coding from the 
> original SynPUF data.