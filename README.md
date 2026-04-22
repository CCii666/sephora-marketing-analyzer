# Sephora Marketing Analyzer

## 1. Problem & User
This project aims to provide data-driven decision support for the beauty e-commerce industry, assisting with product selection and targeted marketing strategy development through the analysis of customer review feedback and product ingredient information. Designed for sales and marketing teams in beauty e-commerce, the tool helps users extract actionable business insights from large volumes of product data and customer reviews.

## 2. Data
- **Source**: [Sephora Products and Skincare Reviews Dataset](https://www.kaggle.com/datasets/nadyinky/sephora-products-and-skincare-reviews) (Kaggle)
- **Access Date**: April 2026
- **Key Fields**: product name, brand, price, rating, review text, ingredients, skin type, review date
- **Size**: 10,000+ product reviews (full dataset); 1,000 rows (sample)
> **Warning:** The complete cleaned dataset exceeds GitHub's 25MB file limit. The sample file provided is `sephora_ecommerce_cleaned_sample.csv`; to run with full data, download the full dataset from the Kaggle link and replace the sample file with `sephora_ecommerce_cleaned.csv`.

## 3. Methods
- Data cleaning and preprocessing using pandas to merge product metadata and review datasets
- Text processing for sentiment analysis and keyword extraction from review text
- Feature engineering for ingredient analysis, skin type classification, and price strategy detection
- Interactive visualization using Plotly to create multi-filter search, market comparison, and trend analysis features
- Streamlit-based deployment to build an interactive user interface for data exploration and marketing recommendation generation

## 4. Key Findings
- Skincare products with moisturizing and anti-aging ingredients receive the highest positive customer feedback.
- Price is the most common complaint for high-end beauty products, indicating potential for promotional strategy optimization.
- Combination and dry skin types represent the largest user groups in the dataset, guiding targeted product recommendations.
- Products with transparent ingredient information tend to have higher customer ratings and repurchase intentions.

## 5. How to run
```bash
# 1. Clone repo
git clone https://github.com/CCii666/sephora-marketing-analyzer.git
cd sephora-marketing-analyzer

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run app
streamlit run sephora-marketing-analyzer.py
``````
Then open http://localhost:8501 in your browser.


## 6. Product link / Demo
https://github.com/CCii666/sephora-marketing-analyzer


## 7. Limitations & next steps
- The project uses a 1,000-row sample dataset due to GitHub file size limits; full dataset analysis would enhance the robustness of insights.
- Sentiment analysis relies on basic keyword matching, which can be upgraded with machine learning models for higher accuracy.
- Future versions can add real-time data update functionality, competitor benchmarking integration, and personalized marketing recommendation features.
