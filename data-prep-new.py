import pandas as pd
import numpy as np
from datetime import datetime
import re

def clean_sephora_data_lightweight():
    """
    Lightweight data cleaning for Sephora e-commerce marketing analysis.
    Only keeps high-representative products (review_count >= 50, mainstream brands).
    Target users: Beauty e-commerce marketing teams.
    """
    
    print("="*60)
    print("SEPHORA E-COMMERCE DATA PREPARATION [LIGHTWEIGHT MODE]")
    print("="*60)
    print("Strategy: Keep only high-quality, representative data")
    print("Filters: Review count >= 50, mainstream brands only")
    print("="*60)
    
    # Define file paths
    review_files = [
        'reviews_0-250.csv',
        'reviews_250-500.csv', 
        'reviews_500-750.csv',
        'reviews_750-1250.csv',
        'reviews_1250-end.csv'
    ]
    
    product_file = 'product_info.csv'
    
    # Step 1: Load product info FIRST (to filter reviews)
    print("\n[Step 1] Loading product information for filtering...")
    try:
        products_df = pd.read_csv(product_file)
        print(f"  Total products in catalog: {len(products_df):,}")
        print(f"  Available columns: {list(products_df.columns)}")
    except FileNotFoundError:
        print(f"  Error: {product_file} not found!")
        return None, None
    
    # Step 2: Identify mainstream brands & high-volume products
    print("\n[Step 2] Filtering for representative products only...")
    
    # Keep only products with review_count >= 50
    if 'review_count' in products_df.columns:
        initial_products = len(products_df)
        products_df = products_df[products_df['review_count'] >= 50].copy()
        print(f"  Filtered by review_count >= 50: {initial_products:,} -> {len(products_df):,} products")
    else:
        print("  Warning: review_count column not found, skipping filter")
    
    # Define mainstream brands (top beauty brands with market presence)
    mainstream_brands = [
        'SEPHORA COLLECTION', 'The Ordinary', 'CeraVe', 'Neutrogena', "Kiehl's Since 1851",
        'La Mer', 'Drunk Elephant', 'Tatcha', 'Youth To The People', 'Fenty Beauty by Rihanna',
        'Rare Beauty by Selena Gomez', 'Charlotte Tilbury', "NARS", 'Dior', 'Chanel',
        'Tarte', 'Too Faced', 'Urban Decay', 'Anastasia Beverly Hills', 'Benefit Cosmetics',
        'Laura Mercier', 'Make Up For Ever', 'Bobbi Brown', 'Estée Lauder', 'Clinique',
        'Shiseido', 'SK-II', 'Sunday Riley', 'Paulas Choice', 'The INKEY List',
        'Glow Recipe', 'Summer Fridays', 'Farmacy', 'Tower 28 Beauty', 'Saie',
        'LANEIGE', 'Dr. Jart+', 'belif', 'First Aid Beauty', 'Skinfix',
        'Supergoop!', 'Anessa', "Kiehls", 'Origins', 'Lancôme', 'Guerlain',
        'Gisou', 'Olaplex', 'Bumble and bumble', 'Drybar', 'Moroccanoil',
        'Osea', 'Sol de Janeiro', 'Rahua', 'Virtue', 'Living Proof'
    ]
    
    # Filter by mainstream brands
    if 'brand_name' in products_df.columns:
        initial_count = len(products_df)
        products_df = products_df[products_df['brand_name'].isin(mainstream_brands)]
        print(f"  Filtered by mainstream brands: {initial_count:,} -> {len(products_df):,} products")
        print(f"  Kept brands: {products_df['brand_name'].nunique()}")
    else:
        print("  Warning: brand_name column not found, skipping brand filter")
    
    # Get list of product IDs to keep
    if 'product_id' in products_df.columns:
        valid_product_ids = set(products_df['product_id'].astype(str))
        print(f"  Valid product IDs to process: {len(valid_product_ids):,}")
    else:
        print("  Error: product_id column not found in product_info.csv")
        return None, None
    
    # Step 3: Load and filter reviews (only for valid products)
    print("\n[Step 3] Loading and filtering reviews (this may take 1-2 minutes)...")
    review_dfs = []
    total_loaded = 0
    
    for i, file in enumerate(review_files, 1):
        try:
            print(f"  Loading {file}...")
            df = pd.read_csv(file)
            total_loaded += len(df)
            
            # Filter: Only keep reviews for valid products
            if 'product_id' in df.columns:
                df['product_id'] = df['product_id'].astype(str)
                df_filtered = df[df['product_id'].isin(valid_product_ids)].copy()
                review_dfs.append(df_filtered)
                print(f"    Total: {len(df):,} | Kept: {len(df_filtered):,}")
            else:
                print(f"    Warning: No product_id column in {file}")
                
        except FileNotFoundError:
            print(f"    Warning: {file} not found, skipping...")
            continue
    
    if not review_dfs:
        print("Error: No review files loaded!")
        return None, None
    
    # Merge filtered reviews
    print(f"\n  Merging {len(review_dfs)} files...")
    reviews_df = pd.concat(review_dfs, ignore_index=True)
    print(f"  Reviews after filtering: {len(reviews_df):,} (from {total_loaded:,} total)")
    
    # Check available columns
    print(f"\n  Available review columns: {list(reviews_df.columns)}")
    
    # Step 4: Select ONLY essential columns (delete unnecessary fields)
    print("\n[Step 4] Keeping only essential columns...")
    
    # Define possible date column names (submission_time is the actual column name)
    possible_date_cols = ['submission_time', 'review_date', 'posted_at', 'date', 'created_at']
    date_col = None
    for col in possible_date_cols:
        if col in reviews_df.columns:
            date_col = col
            print(f"  Found date column: '{date_col}'")
            break
    
    # Essential columns that must exist
    essential_cols = ['product_id', 'product_name', 'brand_name', 'review_text']
    optional_cols = ['review_title', 'rating', 'is_recommended', 'helpfulness', 'total_feedback_count']
    
    # Keep only columns that exist
    existing_cols = [col for col in essential_cols if col in reviews_df.columns]
    existing_cols += [col for col in optional_cols if col in reviews_df.columns]
    
    # Add date column if found
    if date_col:
        existing_cols.append(date_col)
    
    reviews_df = reviews_df[existing_cols].copy()
    print(f"  Kept columns: {existing_cols}")
    
    # Step 5: Data cleaning
    print("\n[Step 5] Cleaning data...")
    
    # Remove duplicates: Same review text = same person, keep one
    initial_count = len(reviews_df)
    reviews_df = reviews_df.drop_duplicates(subset=['review_text'], keep='first')
    print(f"  Duplicate reviews removed: {initial_count - len(reviews_df):,}")
    
    # Remove rows with missing critical fields
    critical_cols = ['product_name', 'brand_name']
    if 'rating' in reviews_df.columns:
        critical_cols.append('rating')
    
    for col in critical_cols:
        if col in reviews_df.columns:
            missing_count = reviews_df[col].isna().sum()
            reviews_df = reviews_df.dropna(subset=[col])
            if missing_count > 0:
                print(f"  Removed {missing_count:,} rows with missing {col}")
    
    # Clean review text
    reviews_df['review_text'] = reviews_df['review_text'].fillna('').astype(str)
    if 'review_title' in reviews_df.columns:
        reviews_df['review_title'] = reviews_df['review_title'].fillna('').astype(str)
    
    # Convert dates if date column exists
    if date_col:
        reviews_df[date_col] = pd.to_datetime(reviews_df[date_col], errors='coerce')
        # Rename to standard 'review_date' for consistency
        reviews_df = reviews_df.rename(columns={date_col: 'review_date'})
        # Remove invalid dates
        invalid_dates = reviews_df['review_date'].isna().sum()
        if invalid_dates > 0:
            print(f"  Removed {invalid_dates:,} rows with invalid dates")
            reviews_df = reviews_df.dropna(subset=['review_date'])
        print(f"  Date range: {reviews_df['review_date'].min()} to {reviews_df['review_date'].max()}")
    
    # Convert numeric fields
    numeric_cols = ['rating', 'helpfulness', 'total_feedback_count']
    for col in numeric_cols:
        if col in reviews_df.columns:
            reviews_df[col] = pd.to_numeric(reviews_df[col], errors='coerce')
    
    # Step 6: Create features
    print("\n[Step 6] Creating marketing features...")
    
    # Sentiment from rating
    def get_sentiment(rating):
        if pd.isna(rating):
            return 'neutral'
        elif rating >= 4:
            return 'positive'
        elif rating <= 2:
            return 'negative'
        else:
            return 'neutral'
    
    if 'rating' in reviews_df.columns:
        reviews_df['sentiment'] = reviews_df['rating'].apply(get_sentiment)
    else:
        reviews_df['sentiment'] = 'neutral'
    
    # Review metrics
    reviews_df['review_length'] = reviews_df['review_text'].str.len()
    reviews_df['word_count'] = reviews_df['review_text'].str.split().str.len()
    
    # Calculate days since review only if review_date exists
    if 'review_date' in reviews_df.columns:
        reviews_df['days_since_review'] = (datetime.now() - reviews_df['review_date']).dt.days
    
    # Step 7: Merge with product info (get loves_count, price, etc.)
    print("\n[Step 7] Merging with product data...")
    
    # Dynamically find available product columns
    available_product_cols = ['product_id']
    desired_cols = ['loves_count', 'price_usd', 'sale_price_usd', 'review_count', 'rating', 'primary_category', 'secondary_category', 'tertiary_category', 'ingredients', 'limited_edition', 'new', 'sephora_exclusive']
    for col in desired_cols:
        if col in products_df.columns:
            available_product_cols.append(col)
    
    print(f"  Merging with columns: {available_product_cols}")
    
    if len(available_product_cols) > 1:
        merged_df = reviews_df.merge(
            products_df[available_product_cols],
            on='product_id',
            how='left',
            suffixes=('', '_product')
        )
        print(f"  Successfully merged: {len(merged_df):,} records")
    else:
        merged_df = reviews_df.copy()
        print("  Warning: No additional product columns to merge")
    
    # Step 8: Create product summary
    print("\n[Step 8] Creating product summary...")
    
    # Build aggregation dict dynamically based on available columns
    agg_dict = {
        'rating': ['mean', 'count', 'std'],
        'sentiment': lambda x: (x == 'positive').mean() * 100,
        'review_length': 'mean',
    }
    
    # Add optional aggregations
    if 'is_recommended' in merged_df.columns:
        agg_dict['is_recommended'] = 'mean'
    if 'helpfulness' in merged_df.columns:
        agg_dict['helpfulness'] = 'mean'
    if 'days_since_review' in merged_df.columns:
        agg_dict['days_since_review'] = 'mean'
    
    # Add product info columns
    if 'loves_count' in merged_df.columns:
        agg_dict['loves_count'] = 'first'
    if 'price_usd' in merged_df.columns:
        agg_dict['price_usd'] = 'first'
    if 'brand_name' in merged_df.columns:
        agg_dict['brand_name'] = 'first'
    if 'category' in merged_df.columns:
        agg_dict['category'] = 'first'
    if 'primary_category' in merged_df.columns:
        agg_dict['primary_category'] = 'first'
    if 'secondary_category' in merged_df.columns:
        agg_dict['secondary_category'] = 'first'
    if 'tertiary_category' in merged_df.columns:
        agg_dict['tertiary_category'] = 'first'
    
    summary = merged_df.groupby('product_name').agg(agg_dict).reset_index()
    
    # Flatten multi-level column names
    summary.columns = [' '.join(col).strip() if isinstance(col, tuple) else col for col in summary.columns.values]
    
    # Rename columns for clarity
    col_mapping = {
        'rating mean': 'avg_rating',
        'rating count': 'review_count',
        'rating std': 'rating_std',
        'sentiment <lambda>': 'positive_pct',
        'is_recommended mean': 'recommendation_rate',
        'review_length mean': 'avg_review_length',
        'helpfulness mean': 'avg_helpfulness',
        'loves_count first': 'loves_count',
        'price_usd first': 'price_usd',
        'brand_name first': 'brand_name',
        'category first': 'category',
        'primary_category first': 'primary_category',
        'secondary_category first': 'secondary_category',
        'tertiary_category first': 'tertiary_category',
        'days_since_review mean': 'avg_recency_days'
    }
    
    summary = summary.rename(columns=col_mapping)
    
    # Calculate engagement score
    if 'loves_count' in summary.columns and 'review_count' in summary.columns:
        summary['engagement_score'] = (
            summary['review_count'] * 0.4 + 
            summary['loves_count'].fillna(0) * 0.6
        )
        summary = summary.sort_values('engagement_score', ascending=False)
    
    # Step 9: Final quality check
    print("\n[Step 9] Final quality check...")
    print(f"  Final review records: {len(merged_df):,}")
    print(f"  Final product count: {len(summary):,}")
    if 'review_date' in merged_df.columns:
        print(f"  Date range: {merged_df['review_date'].min().date()} to {merged_df['review_date'].max().date()}")
    print(f"  Brands covered: {merged_df['brand_name'].nunique()}")
    if 'category' in summary.columns:
        print(f"  Categories: {summary['category'].nunique()}")
    elif 'primary_category' in summary.columns:
        print(f"  Categories: {summary['primary_category'].nunique()}")
    
    # Step 10: Save
    print("\n[Step 10] Saving cleaned data...")
    
    output_file = 'sephora_ecommerce_cleaned.csv'
    merged_df.to_csv(output_file, index=False)
    print(f"  Saved: {output_file}")
    
    summary_file = 'product_summary_ecommerce.csv'
    summary.to_csv(summary_file, index=False)
    print(f"  Saved: {summary_file}")
    
    # Print top products
    print("\n" + "="*60)
    print("TOP 10 HIGH-REPRESENTATIVE PRODUCTS (by engagement)")
    print("="*60)
    for idx, row in summary.head(10).iterrows():
        print(f"{idx+1}. {row['product_name'][:50]}...")
        brand = row.get('brand_name', 'N/A')
        rating = row.get('avg_rating', 0)
        reviews = row.get('review_count', 0)
        price = row.get('price_usd', 0)
        loves = row.get('loves_count', 0)
        print(f"   Brand: {brand} | Rating: {rating:.2f} | Reviews: {reviews}")
        print(f"   Price: ${price:.2f} | Loves: {loves}")
        print()
    
    print("="*60)
    print("Data cleaning COMPLETE!")
    print("Features ready for Streamlit:")
    if 'loves_count' in merged_df.columns:
        print("  - loves_count: Popularity indicator")
    if 'review_date' in merged_df.columns:
        print("  - review_date: Timeliness analysis")
    print("  - sentiment: Positive/negative ratio")
    if 'engagement_score' in summary.columns:
        print("  - engagement_score: Overall product appeal")
    print("="*60)
    
    return merged_df, summary

if __name__ == "__main__":
    clean_sephora_data_lightweight()