# Sephora Marketing Analyzer

## 1. Problem & User
This project aims to provide data-driven decision support for the beauty e-commerce industry, assisting with product selection and targeted marketing strategy development through the analysis of customer review feedback and product ingredient information. Designed for sales and marketing teams in beauty e-commerce, the tool helps users extract actionable business insights from large volumes of product data and customer reviews.

## Data

**Source**: [Sephora Products and Skincare Reviews Dataset](https://www.kaggle.com/datasets/nadyinky/sephora-products-and-skincare-reviews) (Kaggle)

**Access Date**: April 2026

**Dataset Files**:
- `product_info.csv` — Product metadata (brand, price, category, ingredients)
- `reviews_0-250.csv` — Reviews for products ranked 0–250
- `reviews_250-500.csv` — Reviews for products ranked 250–500
- `reviews_500-750.csv` — Reviews for products ranked 500–750
- `reviews_750-1250.csv` — Reviews for products ranked 750–1250
- `reviews_1250-end.csv` — Reviews for products ranked 1250+

**Note**: The complete dataset is sourced from Kaggle. Due to file size limitations, raw data is not uploaded to this repository. Download the files from Kaggle and run `data-prep-new.py` to generate the cleaned dataset required by the application.

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

- **Data recency**: The dataset was accessed in April 2026 and reflects product listings and reviews available at that time. Product formulations, pricing, and customer preferences may have changed since then, which could affect the relevance of insights for current market conditions.

- **Sentiment analysis**: The current version relies on rule-based keyword matching, which may not capture nuanced or context-dependent opinions. This method could be upgraded with pre-trained machine learning models to improve classification accuracy.

- **Skin type inference**: Skin type labels are inferred from review text rather than verified user profiles, which may introduce classification errors. A more robust approach would integrate structured user demographic data or dermatological assessments.

- **Future enhancements**:
  - Implement scheduled data updates to reflect real-time changes in product listings, pricing, and customer feedback.
  - Add personalized marketing recommendation features based on user behavior and preference data.
  - Expand ingredient analysis to include allergen warnings and cross-reference with dermatological safety databases.

