"""
Skills Module: Pre-defined skill templates for complex data science tasks.
Each skill contains a sequence of tasks that the planner can execute.
"""

from typing import List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class TaskTemplate:
    """A single task template within a skill."""
    id: str
    name: str
    description: str
    prompt_template: str
    expected_output_type: str  # "code", "text", "chart", "data"
    dependencies: List[str] = field(default_factory=list)  # IDs of tasks this depends on


@dataclass
class Skill:
    """A skill is a collection of task templates for a specific domain."""
    id: str
    name: str
    description: str
    tasks: List[TaskTemplate]
    trigger_keywords: List[str]


# ── EDA Skill ───────────────────────────────────────────────

EDA_SKILL = Skill(
    id="eda",
    name="Exploratory Data Analysis",
    description="Comprehensive data exploration including profiling, quality checks, correlations, and insights",
    trigger_keywords=["eda", "exploratory data analysis", "analyze data", "data profile", "understand data"],
    tasks=[
        TaskTemplate(
            id="eda_1",
            name="Data Profiling",
            description="Generate basic statistics and structure information",
            prompt_template="""Generate Python code to profile the dataset:
- Shape (rows, columns)
- Column names and data types
- Missing value counts and percentages
- Basic statistics for numeric columns (mean, std, min, max, quartiles)
- Unique value counts for categorical columns
- Sample first 5 rows

Return the results as a structured dictionary.""",
            expected_output_type="data"
        ),
        TaskTemplate(
            id="eda_2",
            name="Data Quality Assessment",
            description="Identify data quality issues",
            prompt_template="""Analyze data quality issues:
- Columns with >30% missing values
- Duplicate rows count
- Columns with constant or near-constant values (>95% same value)
- Potential data type mismatches (numbers stored as strings)
- Outliers using IQR method (values < Q1-1.5*IQR or > Q3+1.5*IQR)

Return a quality report with specific findings.""",
            expected_output_type="text",
            dependencies=["eda_1"]
        ),
        TaskTemplate(
            id="eda_3",
            name="Correlation Analysis",
            description="Find relationships between numeric variables",
            prompt_template="""Generate code to:
- Calculate correlation matrix for all numeric columns
- Identify strong correlations (|r| > 0.5)
- Create a heatmap visualization if more than 3 numeric columns exist
- List top 5 positive and negative correlations

Return correlation matrix and key findings.""",
            expected_output_type="chart",
            dependencies=["eda_1"]
        ),
        TaskTemplate(
            id="eda_4",
            name="Distribution Analysis",
            description="Analyze distributions of key variables",
            prompt_template="""Generate code to visualize distributions:
- Histograms for numeric columns with significant variance
- Bar charts for top 10 categories in categorical columns
- Box plots to identify outliers
- Skewness and kurtosis calculations

Create appropriate visualizations and summarize distribution characteristics.""",
            expected_output_type="chart",
            dependencies=["eda_1"]
        ),
        TaskTemplate(
            id="eda_5",
            name="Insights Summary",
            description="Compile actionable insights from all analysis",
            prompt_template="""Based on all previous analysis, generate a comprehensive summary:
1. Data Overview: Shape, types, quality score (0-100)
2. Key Findings: Top 3-5 important patterns discovered
3. Data Quality Issues: Critical problems to address
4. Relationships: Notable correlations or patterns
5. Recommendations: 3-5 actionable next steps for analysis

Write a clear, professional report suitable for stakeholders.""",
            expected_output_type="text",
            dependencies=["eda_2", "eda_3", "eda_4"]
        )
    ]
)


# ── Data Science Skill ───────────────────────────────────────

DATA_SCIENCE_SKILL = Skill(
    id="data_science",
    name="Data Science & Modeling",
    description="End-to-end machine learning workflow from preprocessing to model evaluation",
    trigger_keywords=["model", "prediction", "machine learning", "ml", "train", "classify", "regression", "forecast"],
    tasks=[
        TaskTemplate(
            id="ds_1",
            name="Target & Feature Identification",
            description="Identify target variable and feature columns",
            prompt_template="""Analyze the dataset to identify:
- Likely target variable(s) based on column names and data types
- Feature columns suitable for modeling
- Columns to exclude (IDs, dates if not useful, high-cardinality categoricals)
- Required preprocessing for each feature type

Return a modeling plan with target, features, and preprocessing steps.""",
            expected_output_type="text",
            dependencies=[]
        ),
        TaskTemplate(
            id="ds_2",
            name="Data Preprocessing",
            description="Prepare data for modeling",
            prompt_template="""Generate code to preprocess the data:
- Handle missing values (imputation or removal)
- Encode categorical variables (one-hot or label encoding)
- Scale numeric features if needed
- Split into train/test sets (80/20)
- Address class imbalance if present (SMOTE or sampling)

Return preprocessed X_train, X_test, y_train, y_test.""",
            expected_output_type="code",
            dependencies=["ds_1"]
        ),
        TaskTemplate(
            id="ds_3",
            name="Model Training",
            description="Train multiple models and compare",
            prompt_template="""Generate code to train and compare models:
- For classification: Logistic Regression, Random Forest, Gradient Boosting, XGBoost
- For regression: Linear Regression, Random Forest, Gradient Boosting, XGBoost
- Use cross-validation (5-fold)
- Track metrics: Accuracy/Precision/Recall/F1 for classification, RMSE/R² for regression

Train all models and return comparison results.""",
            expected_output_type="code",
            dependencies=["ds_2"]
        ),
        TaskTemplate(
            id="ds_4",
            name="Model Evaluation",
            description="Evaluate best model performance",
            prompt_template="""Generate code to evaluate the best performing model:
- Confusion matrix and classification report (for classification)
- Residual analysis (for regression)
- Feature importance ranking
- ROC-AUC curve if applicable
- Compare predicted vs actual values

Create visualizations and detailed evaluation metrics.""",
            expected_output_type="chart",
            dependencies=["ds_3"]
        ),
        TaskTemplate(
            id="ds_5",
            name="Model Summary & Recommendations",
            description="Summarize findings and recommend next steps",
            prompt_template="""Generate a comprehensive model summary:
1. Best Model: Name and key metrics
2. Performance: How well does it perform? Is it good enough?
3. Key Features: Top 5 most important features
4. Limitations: What could improve the model?
5. Next Steps: Recommendations for deployment or further analysis

Write a clear summary for technical and non-technical stakeholders.""",
            expected_output_type="text",
            dependencies=["ds_4"]
        )
    ]
)


# ── Visualization Skill ───────────────────────────────────────

VISUALIZATION_SKILL = Skill(
    id="visualization",
    name="Advanced Visualization",
    description="Create comprehensive visual analysis with multiple chart types",
    trigger_keywords=["visualize", "plot", "chart", "graph", "dashboard", "show me visually"],
    tasks=[
        TaskTemplate(
            id="viz_1",
            name="Chart Planning",
            description="Determine best chart types for the data and question",
            prompt_template="""Based on the user's question and data characteristics:
- Identify key variables to visualize
- Determine the best chart type(s) for the analysis
- Plan 3-5 complementary visualizations that tell a complete story
- Consider: comparisons, distributions, relationships, trends over time

Return a visualization plan with chart types and rationale.""",
            expected_output_type="text",
            dependencies=[]
        ),
        TaskTemplate(
            id="viz_2",
            name="Generate Visualizations",
            description="Create the planned visualizations",
            prompt_template="""Generate Python code using plotly to create the planned visualizations:
- Use appropriate chart types (bar, line, scatter, histogram, box, heatmap, etc.)
- Include proper titles, labels, and legends
- Add interactive features where helpful
- Ensure color schemes are accessible
- Create subplots if multiple related charts

Return executable plotly code.""",
            expected_output_type="chart",
            dependencies=["viz_1"]
        ),
        TaskTemplate(
            id="viz_3",
            name="Visual Insights",
            description="Interpret the visualizations",
            prompt_template="""Analyze the generated visualizations and provide:
- Key patterns visible in the charts
- Surprising or notable findings
- Answers to the user's original question
- Recommendations based on visual evidence

Write a concise interpretation of what the visuals reveal.""",
            expected_output_type="text",
            dependencies=["viz_2"]
        )
    ]
)


# ── Data Cleaning Skill ───────────────────────────────────────

DATA_CLEANING_SKILL = Skill(
    id="data_cleaning",
    name="Data Cleaning & Preparation",
    description="Comprehensive data cleaning and transformation workflow",
    trigger_keywords=["clean", "prepare", "transform", "fix data", "handle missing", "data preparation"],
    tasks=[
        TaskTemplate(
            id="dc_1",
            name="Issue Detection",
            description="Identify all data quality issues",
            prompt_template="""Scan the dataset for issues:
- Missing values pattern and severity
- Duplicate records
- Inconsistent formatting (dates, text case, etc.)
- Invalid values (negative ages, impossible dates)
- Outliers and anomalies
- Data type issues

Return a detailed issue report with severity ratings.""",
            expected_output_type="text",
            dependencies=[]
        ),
        TaskTemplate(
            id="dc_2",
            name="Cleaning Code Generation",
            description="Generate code to fix identified issues",
            prompt_template="""Generate comprehensive cleaning code:
- Remove or impute missing values appropriately
- Remove duplicates
- Standardize formats (dates, text, numbers)
- Fix or flag invalid values
- Handle outliers (cap, transform, or flag)
- Convert to correct data types

Return executable cleaning code with comments.""",
            expected_output_type="code",
            dependencies=["dc_1"]
        ),
        TaskTemplate(
            id="dc_3",
            name="Before/After Comparison",
            description="Show impact of cleaning",
            prompt_template="""Generate code to compare data before and after cleaning:
- Side-by-side statistics
- Missing value reduction
- Distribution changes
- Record count changes
- Quality score improvement

Create a summary table showing the impact of cleaning.""",
            expected_output_type="data",
            dependencies=["dc_2"]
        )
    ]
)


# Registry of all skills
SKILLS_REGISTRY: Dict[str, Skill] = {
    "eda": EDA_SKILL,
    "data_science": DATA_SCIENCE_SKILL,
    "visualization": VISUALIZATION_SKILL,
    "data_cleaning": DATA_CLEANING_SKILL,
}


def get_skill_by_keywords(keywords: List[str]) -> Skill | None:
    """Find the best matching skill based on keywords."""
    keyword_str = " ".join(keywords).lower()
    
    best_match = None
    best_score = 0
    
    for skill in SKILLS_REGISTRY.values():
        score = sum(1 for kw in skill.trigger_keywords if kw in keyword_str)
        if score > best_score:
            best_score = score
            best_match = skill
    
    return best_match if best_score > 0 else None


def get_skill_by_id(skill_id: str) -> Skill | None:
    """Get a skill by its ID."""
    return SKILLS_REGISTRY.get(skill_id)
