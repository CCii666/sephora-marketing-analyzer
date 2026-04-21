# Sephora Marketing Analyzer

A data-driven product selection and marketing intelligence tool for beauty e-commerce sellers and marketers. It helps users select target products from massive SKUs by relying on data indicators, mine customer pain points and emotional attitudes from product review text, and generate professional, data-backed marketing recommendations.

## Target User

Beauty e-commerce sellers, resellers, and marketing teams who need to:
- Select target products from massive SKUs using data indicators
- Mine customer pain points and emotional attitudes from product review text
- Optimize pricing and promotion strategies with competitive benchmarks
- Generate professional, data-backed marketing recommendations

## Dataset

- **Source**: [Sephora Products and Skincare Reviews Dataset](https://www.kaggle.com/datasets) (Kaggle)
- **Access Date**: April 2026
- **Files**: Product metadata + 5 review CSV files merged into `sephora_ecommerce_cleaned.csv`
- **Size**: 10,000+ product reviews
- **Key Fields**: product name, brand, price, rating, review text, ingredients, skin type, review date

## How to Run

```bash
# 1. Clone repo
git clone https://github.com/CCii666/sephora-marketing-analyzer.git
cd sephora-marketing-analyzer

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run app
streamlit run sephora-marketing-analyzer.py
```
Then open http://localhost:8501 in your browser.
## Project Structure
 ```
sephora-marketing-analyzer/
├── data-prep-new.py                    # Data cleaning script
├── product_summary_ecommerce.csv       # Product summary dataset
├── sephora_ecommerce_cleaned.csv     # Cleaned dataset
├── sephora-marketing-analyzer.py     # Main Streamlit app
├── requirements.txt                    # Python dependencies
└── README.md                           # This file
```
## Key Features

| Feature | Description |
|---------|-------------|
| **Multi-filter Search** | Filter by brand, category, price, rating, review count, special attributes |
| **Market Comparison** | Side-by-side bar charts vs. category average (rating, price, reviews) |
| **Trend Analysis** | Monthly review volume trend line chart |
| **Comprehensive Score** | Weighted score (Rating 40% + Popularity 25% + Value 20% + Reputation 15%) |
| **Price Strategy** | Auto-detect price complaints and suggest promotion tactics |
| **Ingredient Analysis** | Identify star ingredients vs. caution ingredients |
| **Skin Type Insights** | Extract skin type distribution from review text |
| **Sentiment Analysis** | Extract positive/negative keyword themes |
| **Marketing Copy** | Auto-generate final marketing recommendation |

## Tech Stack

- **Streamlit** - Interactive UI
- **Pandas / NumPy** - Data processing
- **Plotly** - Data visualization
- **Python Counter** - Text keyword extraction

## Requirements
streamlit
pandas
numpy
plotly

## License

This project is for educational purposes (ACC102 Mini Assignment).
