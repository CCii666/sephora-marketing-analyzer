import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from collections import Counter
import re
import plotly.graph_objects as go

st.set_page_config(page_title="Sephora Marketing Analyzer", layout="wide")

# Custom CSS for modern, premium styling
st.markdown("""
<style>
    .filter-card {
        background: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid rgba(255,255,255,0.8);
        margin-bottom: 20px;
    }
    .result-counter {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 24px;
        border-radius: 25px;
        font-weight: 600;
        font-size: 0.95rem;
        display: inline-block;
        margin-top: 20px;
    }
    .tag-new {
        background: linear-gradient(135deg, #FFD700, #FFA500);
        color: #000;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 700;
        margin-left: 6px;
    }
    .tag-limited {
        background: linear-gradient(135deg, #FF6B6B, #FF8E53);
        color: #fff;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 700;
        margin-left: 6px;
    }
    .tag-sale {
        background: linear-gradient(135deg, #e74c3c, #c0392b);
        color: #fff;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 700;
        margin-left: 6px;
    }
    .strategy-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 12px;
        padding: 20px;
        border-left: 4px solid #28a745;
        margin-bottom: 12px;
    }
    .warning-box {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 16px;
        border-radius: 8px;
        margin: 12px 0;
    }
    .price-tag-budget { color: #28a745; font-weight: 600; }
    .price-tag-mid { color: #667eea; font-weight: 600; }
    .price-tag-luxury { color: #8B0000; font-weight: 600; }
    .section-header {
        font-size: 1.1rem;
        font-weight: 700;
        margin-top: 16px;
        margin-bottom: 8px;
        color: #333;
    }
    .highlight-yellow {
        background-color: #fff3cd;
        padding: 2px 4px;
        border-radius: 3px;
        font-weight: 500;
    }
    .function-tag {
        display: inline-block;
        background-color: #E3F2FD;
        color: #1565C0;
        border: 1px solid #90CAF9;
        border-radius: 20px;
        padding: 4px 12px;
        margin: 2px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .floating-button {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 999;
    }
    .stock-hint {
        color: #6c757d;
        font-size: 0.85rem;
        margin-left: 8px;
    }
    .ingredient-item {
        color: #333;
        margin: 4px 0;
        line-height: 1.6;
    }
    .ingredient-name {
        font-weight: 700;
        color: #000;
    }
    .marketing-copy-box {
        background: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 20px 24px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        font-size: 1rem;
        line-height: 1.5;
        color: #2c3e50;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_csv('sephora_ecommerce_cleaned.csv')
    df['review_date'] = pd.to_datetime(df['review_date'])
    
    if 'price_usd_y' in df.columns:
        df['price'] = df['price_usd_y']
    elif 'price_usd_x' in df.columns:
        df['price'] = df['price_usd_x']
    elif 'price_usd' in df.columns:
        df['price'] = df['price_usd']
    else:
        df['price'] = 0
    
    if 'sale_price_usd' in df.columns:
        df['sale_price_usd'] = pd.to_numeric(df['sale_price_usd'], errors='coerce')
    
    bool_cols = ['limited_edition', 'new', 'sephora_exclusive']
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].fillna(False).astype(bool)
    
    if 'ingredients' not in df.columns:
        df['ingredients'] = ''
    df['ingredients'] = df['ingredients'].fillna('').astype(str)
    
    if 'skin_type' not in df.columns:
        df['skin_type'] = 'Unknown'
    df['skin_type'] = df['skin_type'].fillna('Unknown')
    
    if 'primary_category' in df.columns:
        df['primary_category'] = df['primary_category'].fillna('Unknown')
    if 'secondary_category' in df.columns:
        df['secondary_category'] = df['secondary_category'].fillna('Unknown')
    if 'tertiary_category' in df.columns:
        df['tertiary_category'] = df['tertiary_category'].fillna('Unknown')
    
    return df

def extract_keywords(texts, keyword_list):
    word_counts = Counter()
    for text in texts:
        if pd.notna(text):
            words = str(text).lower().split()
            for word in words:
                cleaned = word.strip('.,!?;:"()[]')
                if cleaned in keyword_list:
                    word_counts[cleaned] += 1
    return dict(word_counts.most_common(10))

# Valid function categories only
VALID_FUNCTION_CATEGORIES = [
    'Moisturizers', 'Treatments', 'Cleansers', 'Eye Care', 
    'Face Masks', 'Face Sunscreen', 'Mists & Essences', 
    'Toners', 'Face Oils', 'Makeup Removers'
]

# Ingredient to function mapping
FUNCTION_MAPPING = {
    'whitening': ['niacinamide', 'vitamin c', 'ascorbic acid', 'arbutin', 'tranexamic acid', 'kojic acid', 'licorice root'],
    'anti-aging': ['retinol', 'retinyl', 'peptide', 'peptides', 'adenosine', 'coenzyme q10', 'resveratrol', 'bakuchiol', 'collagen', 'elastin'],
    'hydration': ['hyaluronic acid', 'sodium hyaluronate', 'ceramide', 'squalane', 'panthenol', 'glycerin', 'urea', 'sodium pca'],
    'antioxidant': ['vitamin c', 'vitamin e', 'tocopherol', 'resveratrol', 'green tea', 'white tea', 'astaxanthin', 'lycopene', 'coenzyme q10'],
    'oil-control': ['salicylic acid', 'azelaic acid', 'zinc pca', 'niacinamide', 'tea tree', 'witch hazel'],
    'repairing': ['centella asiatica', 'cica', 'madecassoside', 'panthenol', 'allantoin', 'beta-glucan', 'bisabolol']
}

# Complete ingredient database - descriptions with yellow highlights for keywords
INGREDIENT_DATABASE = {
    # Caution/Sensitizing Ingredients
    'alcohol': ('Alcohol', 'Oil-control and refreshing, caution for <span class="highlight-yellow">sensitive skin</span>', 'danger'),
    'alcohol denat': ('Alcohol Denat', 'Strong oil-control, very irritating, dry and <span class="highlight-yellow">sensitive skin</span> avoid', 'danger'),
    'denatured alcohol': ('Denatured Alcohol', 'Strong oil-control, very irritating, dry and <span class="highlight-yellow">sensitive skin</span> avoid', 'danger'),
    'sd alcohol': ('SD Alcohol', 'Oil-control and refreshing, caution for <span class="highlight-yellow">sensitive skin</span>', 'danger'),
    'fragrance': ('Fragrance', 'Adds scent, may cause <span class="highlight-yellow">allergies</span>', 'danger'),
    'parfum': ('Parfum', 'Adds scent, may cause <span class="highlight-yellow">allergies</span>', 'danger'),
    'parabens': ('Parabens', 'Preservative, some users prefer to avoid', 'danger'),
    'methylparaben': ('Methylparaben', 'Preservative, <span class="highlight-yellow">sensitive skin</span> caution', 'danger'),
    'propylparaben': ('Propylparaben', 'Preservative, <span class="highlight-yellow">sensitive skin</span> caution', 'danger'),
    'phenoxyethanol': ('Phenoxyethanol', 'Preservative, may sting for some', 'danger'),
    'linalool': ('Linalool', 'Fragrance component, prone to <span class="highlight-yellow">sensitization</span>', 'danger'),
    'limonene': ('Limonene', 'Fragrance component, prone to <span class="highlight-yellow">sensitization</span>', 'danger'),
    'essential oils': ('Essential Oils', 'May irritate, <span class="highlight-yellow">sensitive skin</span> caution', 'danger'),
    'benzyl alcohol': ('Benzyl Alcohol', 'Preservative or fragrance, may cause <span class="highlight-yellow">allergies</span>', 'danger'),
    'bha': ('BHA', 'Preservative, potential <span class="highlight-yellow">allergen</span>', 'danger'),
    'bht': ('BHT', 'Preservative, potential <span class="highlight-yellow">allergen</span>', 'danger'),
    'propylene glycol': ('Propylene Glycol', 'Penetration enhancer, may sting <span class="highlight-yellow">sensitive skin</span>', 'danger'),
    'isopropyl myristate': ('Isopropyl Myristate', 'High comedogenicity, acne-prone skin caution', 'danger'),
    'isopropyl palmitate': ('Isopropyl Palmitate', 'High comedogenicity, acne-prone skin caution', 'danger'),
    'sodium lauryl sulfate': ('Sodium Lauryl Sulfate (SLS)', 'Strong cleansing, highly irritating, <span class="highlight-yellow">sensitive skin</span> avoid', 'danger'),
    'sls': ('SLS', 'Strong cleansing, highly irritating, <span class="highlight-yellow">sensitive skin</span> avoid', 'danger'),
    'mineral oil': ('Mineral Oil', 'May clog pores for some skin types', 'danger'),
    'petrolatum': ('Petrolatum', 'May clog pores for some skin types', 'danger'),
    
    # Star Performance Ingredients
    'hyaluronic acid': ('Hyaluronic Acid', 'Deep <span class="highlight-yellow">hydration</span>, ideal for dry and mature skin', 'star'),
    'sodium hyaluronate': ('Sodium Hyaluronate', 'Deep <span class="highlight-yellow">hydration</span>, ideal for dry and mature skin', 'star'),
    'niacinamide': ('Niacinamide', 'Oil-control and repair, <span class="highlight-yellow">brightens</span> skin tone', 'star'),
    'retinol': ('Retinol', '<span class="highlight-yellow">Anti-aging</span> and wrinkle reduction, build tolerance gradually', 'star'),
    'retinyl': ('Retinyl', '<span class="highlight-yellow">Anti-aging</span> and skin renewal, use with care', 'star'),
    'vitamin c': ('Vitamin C', '<span class="highlight-yellow">Antioxidant</span> and brightening, recommended for morning use', 'star'),
    'ascorbic acid': ('Ascorbic Acid', '<span class="highlight-yellow">Antioxidant</span> and brightening, boosts radiance', 'star'),
    'ceramide': ('Ceramide', 'Repairs barrier, enhances <span class="highlight-yellow">moisture</span> retention', 'star'),
    'squalane': ('Squalane', 'Skin-friendly <span class="highlight-yellow">hydration</span>, antioxidant', 'star'),
    'peptide': ('Peptides', '<span class="highlight-yellow">Anti-aging</span> and firming, promotes collagen', 'star'),
    'peptides': ('Peptides', '<span class="highlight-yellow">Anti-aging</span> and firming, promotes collagen', 'star'),
    'salicylic acid': ('Salicylic Acid', 'Unclogs pores, ideal for oily and acne skin', 'star'),
    'glycolic acid': ('Glycolic Acid', 'Exfoliates and brightens, use sun protection', 'star'),
    'lactic acid': ('Lactic Acid', 'Gentle exfoliation and <span class="highlight-yellow">hydration</span>, sensitive-friendly', 'star'),
    'azelaic acid': ('Azelaic Acid', 'Anti-inflammatory and anti-acne, improves redness', 'star'),
    'adenosine': ('Adenosine', '<span class="highlight-yellow">Anti-wrinkle</span> and soothing', 'star'),
    'arbutin': ('Arbutin', 'Fades dark spots, <span class="highlight-yellow">whitening</span>', 'star'),
    'tranexamic acid': ('Tranexamic Acid', 'Fades acne marks, improves dullness', 'star'),
    'centella asiatica': ('Centella Asiatica', 'Soothes and repairs, <span class="highlight-yellow">sensitive skin</span> friendly', 'star'),
    'panthenol': ('Panthenol', '<span class="highlight-yellow">Hydration</span> and repair, soothing', 'star'),
    'allantoin': ('Allantoin', 'Soothes inflammation, promotes healing', 'star'),
    'zinc pca': ('Zinc PCA', 'Oil-control and antibacterial, ideal for oily skin', 'star'),
    'caffeine': ('Caffeine', 'De-puffing and firming, fades dark circles', 'star'),
    'coenzyme q10': ('Coenzyme Q10', '<span class="highlight-yellow">Antioxidant</span>, anti-aging', 'star'),
    'resveratrol': ('Resveratrol', 'Strong <span class="highlight-yellow">antioxidant</span>, anti-aging', 'star'),
    'green tea': ('Green Tea', '<span class="highlight-yellow">Antioxidant</span> and soothing', 'star'),
    'aloe vera': ('Aloe Vera', 'Soothes and hydrates', 'star'),
    'jojoba oil': ('Jojoba Oil', 'Balances oil, lightweight <span class="highlight-yellow">moisture</span>', 'star'),
    'rosehip oil': ('Rosehip Oil', 'Repairs and brightens', 'star'),
    'bakuchiol': ('Bakuchiol', 'Gentle retinol alternative, <span class="highlight-yellow">anti-aging</span>', 'star'),
    'collagen': ('Collagen', 'Supports skin elasticity', 'star'),
    'elastin': ('Elastin', 'Supports skin firmness', 'star'),
    'urea': ('Urea', '<span class="highlight-yellow">Hydrates</span> and softens skin', 'star'),
    'licorice root': ('Licorice Root', '<span class="highlight-yellow">Brightens</span> and soothes', 'star'),
    'kojic acid': ('Kojic Acid', '<span class="highlight-yellow">Brightens</span> and evens skin tone', 'star'),
    'mandelic acid': ('Mandelic Acid', 'Gentle exfoliation, sensitive-friendly', 'star'),
    'polyhydroxy acid': ('PHA', 'Gentle exfoliation, <span class="highlight-yellow">hydrating</span>', 'star'),
    'gluconolactone': ('Gluconolactone', 'Gentle exfoliation, <span class="highlight-yellow">hydrating</span>', 'star'),
    'lactobionic acid': ('Lactobionic Acid', 'Gentle exfoliation, <span class="highlight-yellow">antioxidant</span>', 'star'),
    'bisabolol': ('Bisabolol', 'Soothes and calms irritation', 'star'),
    'cica': ('Cica', 'Repairs and soothes <span class="highlight-yellow">sensitive skin</span>', 'star'),
    'madecassoside': ('Madecassoside', 'Repairs and strengthens barrier', 'star'),
    'beta-glucan': ('Beta-Glucan', '<span class="highlight-yellow">Hydrates</span> and soothes', 'star'),
    'pantothenic acid': ('Pantothenic Acid', 'Supports skin barrier', 'star'),
    'vitamin e': ('Vitamin E', '<span class="highlight-yellow">Antioxidant</span>, nourishes skin', 'star'),
    'tocopherol': ('Tocopherol', '<span class="highlight-yellow">Antioxidant</span>, nourishes skin', 'star'),
    'vitamin b5': ('Vitamin B5', '<span class="highlight-yellow">Hydrates</span> and repairs', 'star'),
    'pro-vitamin b5': ('Pro-Vitamin B5', '<span class="highlight-yellow">Hydrates</span> and repairs', 'star'),
    'squalene': ('Squalene', 'Natural <span class="highlight-yellow">moisture</span>, lightweight', 'star'),
    'shea butter': ('Shea Butter', 'Deep nourishment, dry skin friendly', 'star'),
    'cocoa butter': ('Cocoa Butter', 'Rich <span class="highlight-yellow">moisture</span>, very dry skin', 'star'),
    'mango butter': ('Mango Butter', 'Softens and nourishes skin', 'star'),
    'cupuacu butter': ('Cupuacu Butter', 'Intense <span class="highlight-yellow">hydration</span>, dry skin', 'star'),
    'murumuru butter': ('Murumuru Butter', 'Locks in <span class="highlight-yellow">moisture</span>', 'star'),
    'tamanu oil': ('Tamanu Oil', 'Repairs and soothes', 'star'),
    'marula oil': ('Marula Oil', 'Rich in <span class="highlight-yellow">antioxidants</span>, nourishes', 'star'),
    'argan oil': ('Argan Oil', 'Nourishes and adds radiance', 'star'),
    'camellia oil': ('Camellia Oil', 'Lightweight <span class="highlight-yellow">moisture</span>, <span class="highlight-yellow">antioxidant</span>', 'star'),
    'sunflower seed oil': ('Sunflower Seed Oil', 'Nourishes and protects barrier', 'star'),
    'grapeseed oil': ('Grapeseed Oil', 'Lightweight, <span class="highlight-yellow">antioxidant</span>', 'star'),
    'evening primrose oil': ('Evening Primrose Oil', 'Soothes and balances', 'star'),
    'borage oil': ('Borage Oil', 'Rich in GLA, soothes', 'star'),
    'black currant seed oil': ('Black Currant Seed Oil', 'Nourishes and repairs', 'star'),
    'sea buckthorn oil': ('Sea Buckthorn Oil', 'Rich in nutrients, repairs', 'star'),
    'hemp seed oil': ('Hemp Seed Oil', 'Balances oil, nourishes', 'star'),
    'chia seed oil': ('Chia Seed Oil', 'Omega-rich, <span class="highlight-yellow">hydrates</span>', 'star'),
    'flaxseed oil': ('Flaxseed Oil', 'Omega-rich, nourishes', 'star'),
    'pomegranate seed oil': ('Pomegranate Seed Oil', '<span class="highlight-yellow">Antioxidant</span>, anti-aging', 'star'),
    'raspberry seed oil': ('Raspberry Seed Oil', 'Protects and nourishes', 'star'),
    'cranberry seed oil': ('Cranberry Seed Oil', 'Rich in <span class="highlight-yellow">antioxidants</span>', 'star'),
    'blueberry seed oil': ('Blueberry Seed Oil', '<span class="highlight-yellow">Antioxidant</span>, nourishes', 'star'),
    'acai berry': ('Acai Berry', '<span class="highlight-yellow">Antioxidant</span> powerhouse', 'star'),
    'goji berry': ('Goji Berry', '<span class="highlight-yellow">Antioxidant</span>, energizes skin', 'star'),
    'pomegranate extract': ('Pomegranate Extract', '<span class="highlight-yellow">Antioxidant</span>, anti-aging', 'star'),
    'green tea extract': ('Green Tea Extract', '<span class="highlight-yellow">Antioxidant</span> and soothing', 'star'),
    'white tea extract': ('White Tea Extract', 'Gentle <span class="highlight-yellow">antioxidant</span>', 'star'),
    'black tea extract': ('Black Tea Extract', '<span class="highlight-yellow">Antioxidant</span>, firms skin', 'star'),
    'fermented ingredients': ('Fermented Ingredients', 'Enhances absorption, nourishes', 'star'),
    'galactomyces': ('Galactomyces', '<span class="highlight-yellow">Brightens</span> and refines texture', 'star'),
    'saccharomyces': ('Saccharomyces', 'Nourishes and <span class="highlight-yellow">brightens</span>', 'star'),
    'bifida ferment': ('Bifida Ferment', 'Strengthens and repairs', 'star'),
    'lactobacillus': ('Lactobacillus', 'Balances skin microbiome', 'star'),
    'rice ferment': ('Rice Ferment', '<span class="highlight-yellow">Brightens</span> and softens skin', 'star'),
    'soybean ferment': ('Soybean Ferment', 'Nourishes and firms', 'star'),
    'mugwort': ('Mugwort', 'Soothes and calms irritation', 'star'),
    'artemisia': ('Artemisia', 'Soothes and repairs', 'star'),
    'houttuynia cordata': ('Houttuynia Cordata', 'Soothes and purifies', 'star'),
    'tea tree': ('Tea Tree', 'Antibacterial, ideal for acne', 'star'),
    'witch hazel': ('Witch Hazel', 'Astringent, oil-control', 'star'),
    'willow bark': ('Willow Bark', 'Natural BHA, unclogs pores', 'star'),
    'papaya extract': ('Papaya Extract', 'Gentle exfoliation', 'star'),
    'pineapple extract': ('Pineapple Extract', 'Gentle exfoliation', 'star'),
    'pumpkin enzyme': ('Pumpkin Enzyme', 'Gentle exfoliation', 'star'),
    'pomegranate enzyme': ('Pomegranate Enzyme', 'Gentle exfoliation', 'star'),
    'fig extract': ('Fig Extract', '<span class="highlight-yellow">Hydrates</span> and softens', 'star'),
    'mulberry extract': ('Mulberry Extract', '<span class="highlight-yellow">Brightens</span> and evens tone', 'star'),
    'bearberry extract': ('Bearberry Extract', 'Natural <span class="highlight-yellow">brightening</span>', 'star'),
    'grape extract': ('Grape Extract', '<span class="highlight-yellow">Antioxidant</span>, resveratrol source', 'star'),
    'apple extract': ('Apple Extract', '<span class="highlight-yellow">Antioxidant</span>, gentle exfoliation', 'star'),
    'citrus extract': ('Citrus Extract', '<span class="highlight-yellow">Brightens</span> and refreshes', 'star'),
    'lemon extract': ('Lemon Extract', '<span class="highlight-yellow">Brightens</span> and clarifies', 'star'),
    'orange extract': ('Orange Extract', '<span class="highlight-yellow">Brightens</span> and energizes', 'star'),
    'grapefruit extract': ('Grapefruit Extract', 'Refreshes and clarifies', 'star'),
    'lime extract': ('Lime Extract', '<span class="highlight-yellow">Brightens</span> and refreshes', 'star'),
    'bergamot': ('Bergamot', 'Uplifting, clarifies skin', 'star'),
    'ylang ylang': ('Ylang Ylang', 'Balances oil production', 'star'),
    'lavender': ('Lavender', 'Soothes and calms', 'star'),
    'chamomile': ('Chamomile', 'Soothes <span class="highlight-yellow">sensitive skin</span>', 'star'),
    'calendula': ('Calendula', 'Soothes and repairs', 'star'),
    'rose': ('Rose', '<span class="highlight-yellow">Hydrates</span> and soothes', 'star'),
    'rose extract': ('Rose Extract', '<span class="highlight-yellow">Hydrates</span> and soothes', 'star'),
    'rose water': ('Rose Water', '<span class="highlight-yellow">Hydrates</span> and refreshes', 'star'),
    'orange blossom': ('Orange Blossom', 'Soothes and <span class="highlight-yellow">brightens</span>', 'star'),
    'neroli': ('Neroli', 'Rejuvenates and soothes', 'star'),
    'jasmine': ('Jasmine', '<span class="highlight-yellow">Hydrates</span> and uplifts', 'star'),
    'lotus extract': ('Lotus Extract', 'Purifies and <span class="highlight-yellow">hydrates</span>', 'star'),
    'water lily': ('Water Lily', 'Soothes and <span class="highlight-yellow">hydrates</span>', 'star'),
    'bamboo extract': ('Bamboo Extract', 'Strengthens and <span class="highlight-yellow">hydrates</span>', 'star'),
    'lotus leaf extract': ('Lotus Leaf Extract', 'Purifies and soothes', 'star'),
    'ginkgo biloba': ('Ginkgo Biloba', '<span class="highlight-yellow">Antioxidant</span>, improves circulation', 'star'),
    'ginseng': ('Ginseng', 'Energizes and <span class="highlight-yellow">anti-aging</span>', 'star'),
    'ginger root': ('Ginger Root', '<span class="highlight-yellow">Antioxidant</span>, energizes', 'star'),
    'turmeric': ('Turmeric', 'Anti-inflammatory and <span class="highlight-yellow">brightens</span>', 'star'),
    'honey': ('Honey', 'Nourishes and antibacterial', 'star'),
    'propolis': ('Propolis', 'Repairs and antibacterial', 'star'),
    'royal jelly': ('Royal Jelly', 'Nourishes and <span class="highlight-yellow">anti-aging</span>', 'star'),
    'bee venom': ('Bee Venom', 'Firms and plumps skin', 'star'),
    'snail mucin': ('Snail Mucin', 'Repairs and <span class="highlight-yellow">hydrates</span>', 'star'),
    'snail secretion': ('Snail Secretion', 'Repairs and <span class="highlight-yellow">hydrates</span>', 'star'),
    'egf': ('EGF', 'Promotes skin renewal', 'star'),
    'fgf': ('FGF', 'Supports skin repair', 'star'),
    'copper peptide': ('Copper Peptide', 'Repairs and <span class="highlight-yellow">anti-aging</span>', 'star'),
    'matrixyl': ('Matrixyl', '<span class="highlight-yellow">Anti-wrinkle</span> peptide', 'star'),
    'argireline': ('Argireline', 'Reduces expression lines', 'star'),
    'syn-ake': ('Syn-Ake', 'Botox-like peptide', 'star'),
    'snap-8': ('Snap-8', 'Reduces fine lines', 'star'),
    'leuphasyl': ('Leuphasyl', 'Relaxes facial muscles', 'star'),
    'inoveol': ('Inoveol', '<span class="highlight-yellow">Antioxidant</span>, anti-aging', 'star'),
    'astaxanthin': ('Astaxanthin', 'Super <span class="highlight-yellow">antioxidant</span>', 'star'),
    'astaxanthin extract': ('Astaxanthin Extract', 'Super <span class="highlight-yellow">antioxidant</span>', 'star'),
    'lycopene': ('Lycopene', '<span class="highlight-yellow">Antioxidant</span>, protects skin', 'star'),
    'beta-carotene': ('Beta-Carotene', 'Provitamin A, <span class="highlight-yellow">antioxidant</span>', 'star'),
    'lutein': ('Lutein', 'Protects from blue light', 'star'),
    'zeaxanthin': ('Zeaxanthin', '<span class="highlight-yellow">Antioxidant</span>, protects', 'star'),
    'fucoxanthin': ('Fucoxanthin', '<span class="highlight-yellow">Antioxidant</span> from seaweed', 'star'),
    'spirulina': ('Spirulina', 'Nourishes and detoxifies', 'star'),
    'chlorella': ('Chlorella', 'Detoxifies and nourishes', 'star'),
    'seaweed': ('Seaweed', '<span class="highlight-yellow">Hydrates</span> and mineral-rich', 'star'),
    'kelp': ('Kelp', 'Mineral-rich, <span class="highlight-yellow">hydrates</span>', 'star'),
    'wakame': ('Wakame', '<span class="highlight-yellow">Hydrates</span> and firms', 'star'),
    'nori': ('Nori', 'Nourishes and <span class="highlight-yellow">hydrates</span>', 'star'),
    'sea kelp': ('Sea Kelp', 'Mineral-rich, <span class="highlight-yellow">hydrates</span>', 'star'),
    'sea lettuce': ('Sea Lettuce', '<span class="highlight-yellow">Hydrates</span> and nourishes', 'star'),
    'sea fennel': ('Sea Fennel', 'Firms and renews skin', 'star'),
    'sea salt': ('Sea Salt', 'Mineral-rich, purifies', 'star'),
    'marine collagen': ('Marine Collagen', 'Supports elasticity', 'star'),
    'fish collagen': ('Fish Collagen', 'Supports elasticity', 'star'),
    'plant collagen': ('Plant Collagen', 'Vegan alternative, <span class="highlight-yellow">hydrates</span>', 'star'),
    'vegan collagen': ('Vegan Collagen', 'Plant-based support', 'star'),
    'snow mushroom': ('Snow Mushroom', '<span class="highlight-yellow">Hydrates</span> like hyaluronic acid', 'star'),
    'tremella': ('Tremella', '<span class="highlight-yellow">Hydrates</span> and plumps', 'star'),
    'reishi mushroom': ('Reishi Mushroom', '<span class="highlight-yellow">Antioxidant</span>, soothes', 'star'),
    'shiitake mushroom': ('Shiitake Mushroom', '<span class="highlight-yellow">Brightens</span> and nourishes', 'star'),
    'maitake mushroom': ('Maitake Mushroom', 'Supports skin immunity', 'star'),
    'cordyceps': ('Cordyceps', 'Energizes and <span class="highlight-yellow">anti-aging</span>', 'star'),
    'chaga mushroom': ('Chaga Mushroom', '<span class="highlight-yellow">Antioxidant</span> powerhouse', 'star'),
    'lion mane': ('Lion\'s Mane', 'Supports skin health', 'star'),
    'turkey tail': ('Turkey Tail', 'Supports skin immunity', 'star'),
    'meshima': ('Meshima', 'Soothes and repairs', 'star'),
    'phellinus linteus': ('Phellinus Linteus', '<span class="highlight-yellow">Antioxidant</span>, anti-aging', 'star'),
    'ganoderma': ('Ganoderma', 'Reishi, <span class="highlight-yellow">antioxidant</span> and soothes', 'star'),
    'lingzhi': ('Lingzhi', 'Reishi, <span class="highlight-yellow">antioxidant</span> and soothes', 'star'),
    'truffle extract': ('Truffle Extract', 'Luxurious, nourishes', 'star'),
    'white truffle': ('White Truffle', '<span class="highlight-yellow">Brightens</span> and nourishes', 'star'),
    'black truffle': ('Black Truffle', '<span class="highlight-yellow">Anti-aging</span>, nourishes', 'star'),
    'caviar extract': ('Caviar Extract', 'Luxury <span class="highlight-yellow">anti-aging</span>', 'star'),
    'gold': ('Gold', 'Luxury, <span class="highlight-yellow">brightens</span>', 'star'),
    'colloidal gold': ('Colloidal Gold', 'Luxury, <span class="highlight-yellow">anti-aging</span>', 'star'),
    'silver': ('Silver', 'Antibacterial, soothes', 'star'),
    'colloidal silver': ('Colloidal Silver', 'Antibacterial, soothes', 'star'),
    'platinum': ('Platinum', 'Luxury <span class="highlight-yellow">anti-aging</span>', 'star'),
    'pearl extract': ('Pearl Extract', '<span class="highlight-yellow">Brightens</span> and illuminates', 'star'),
    'mother of pearl': ('Mother of Pearl', 'Illuminates skin', 'star'),
    'diamond powder': ('Diamond Powder', 'Exfoliates and illuminates', 'star'),
    'ruby powder': ('Ruby Powder', 'Energizes and <span class="highlight-yellow">brightens</span>', 'star'),
    'sapphire powder': ('Sapphire Powder', 'Calms and illuminates', 'star'),
    'amethyst powder': ('Amethyst Powder', 'Purifies and balances', 'star'),
    'tourmaline': ('Tourmaline', 'Energizes skin', 'star'),
    'jade powder': ('Jade Powder', 'Calms and cools', 'star'),
    'malachite': ('Malachite', 'Protects and energizes', 'star'),
    'azurite': ('Azurite', 'Calms and soothes', 'star'),
    'rose quartz': ('Rose Quartz', 'Promotes self-love, soothes', 'star'),
    'clear quartz': ('Clear Quartz', 'Amplifies other ingredients', 'star'),
    'smoky quartz': ('Smoky Quartz', 'Detoxifies and protects', 'star'),
    'amber': ('Amber', 'Warming, <span class="highlight-yellow">anti-aging</span>', 'star'),
    'amber extract': ('Amber Extract', '<span class="highlight-yellow">Anti-aging</span>, nourishes', 'star'),
    'propolis extract': ('Propolis Extract', 'Repairs and protects', 'star'),
    'bee pollen': ('Bee Pollen', 'Nourishes and energizes', 'star'),
    'honey extract': ('Honey Extract', '<span class="highlight-yellow">Hydrates</span> and nourishes', 'star'),
    'royal jelly extract': ('Royal Jelly Extract', '<span class="highlight-yellow">Anti-aging</span>, nourishes', 'star'),
    'bee venom extract': ('Bee Venom Extract', 'Firms and plumps', 'star'),
    'lanolin': ('Lanolin', 'Deep <span class="highlight-yellow">moisture</span>, dry skin', 'star'),
    'lanolin oil': ('Lanolin Oil', 'Nourishes and protects', 'star'),
    'shea oil': ('Shea Oil', 'Lightweight nourishment', 'star'),
    'cocoa oil': ('Cocoa Oil', 'Rich <span class="highlight-yellow">moisture</span>', 'star'),
    'mango oil': ('Mango Oil', 'Softens and nourishes', 'star'),
    'avocado oil': ('Avocado Oil', 'Rich nourishment, dry skin', 'star'),
    'avocado butter': ('Avocado Butter', 'Deep <span class="highlight-yellow">moisture</span>', 'star'),
    'olive oil': ('Olive Oil', 'Nourishes and protects', 'star'),
    'olive squalane': ('Olive Squalane', 'Lightweight <span class="highlight-yellow">moisture</span>', 'star'),
    'olive extract': ('Olive Extract', '<span class="highlight-yellow">Antioxidant</span>, nourishes', 'star'),
    'olive leaf extract': ('Olive Leaf Extract', '<span class="highlight-yellow">Antioxidant</span>, protects', 'star'),
    'grape seed extract': ('Grape Seed Extract', '<span class="highlight-yellow">Antioxidant</span> powerhouse', 'star'),
    'grape seed oil': ('Grape Seed Oil', 'Lightweight, <span class="highlight-yellow">antioxidant</span>', 'star'),
    'wine extract': ('Wine Extract', 'Resveratrol source', 'star'),
    'resveratrol extract': ('Resveratrol Extract', 'Strong <span class="highlight-yellow">antioxidant</span>', 'star'),
    'pomegranate seed extract': ('Pomegranate Seed Extract', '<span class="highlight-yellow">Antioxidant</span>, nourishes', 'star'),
    'pomegranate juice': ('Pomegranate Juice', '<span class="highlight-yellow">Brightens</span> and energizes', 'star'),
    'pomegranate peel extract': ('Pomegranate Peel Extract', '<span class="highlight-yellow">Antioxidant</span> rich', 'star'),
    'cranberry extract': ('Cranberry Extract', '<span class="highlight-yellow">Antioxidant</span>, protects', 'star'),
    'blueberry extract': ('Blueberry Extract', '<span class="highlight-yellow">Antioxidant</span>, nourishes', 'star'),
    'raspberry extract': ('Raspberry Extract', '<span class="highlight-yellow">Antioxidant</span>, protects', 'star'),
    'strawberry extract': ('Strawberry Extract', '<span class="highlight-yellow">Brightens</span> and refreshes', 'star'),
    'blackberry extract': ('Blackberry Extract', '<span class="highlight-yellow">Antioxidant</span> rich', 'star'),
    'acai extract': ('Acai Extract', 'Superfood for skin', 'star'),
    'goji extract': ('Goji Extract', 'Energizes and <span class="highlight-yellow">antioxidant</span>', 'star'),
    'maqui berry': ('Maqui Berry', 'Super <span class="highlight-yellow">antioxidant</span>', 'star'),
    'acerola cherry': ('Acerola Cherry', 'Vitamin C rich', 'star'),
    'camu camu': ('Camu Camu', 'Highest vitamin C content', 'star'),
    'amla': ('Amla', 'Vitamin C and <span class="highlight-yellow">antioxidant</span>', 'star'),
    'sea buckthorn': ('Sea Buckthorn', 'Omega-rich, repairs', 'star'),
    'sea buckthorn berry': ('Sea Buckthorn Berry', 'Nutrient dense', 'star'),
    'sea buckthorn oil': ('Sea Buckthorn Oil', 'Repairs and nourishes', 'star'),
    'cloudberry': ('Cloudberry', 'Vitamin C rich, <span class="highlight-yellow">brightens</span>', 'star'),
    'lingonberry': ('Lingonberry', '<span class="highlight-yellow">Antioxidant</span>, protects', 'star'),
    'bilberry': ('Bilberry', '<span class="highlight-yellow">Antioxidant</span>, strengthens', 'star'),
    'elderberry': ('Elderberry', '<span class="highlight-yellow">Antioxidant</span>, protects', 'star'),
    'aronia berry': ('Aronia Berry', 'Super <span class="highlight-yellow">antioxidant</span>', 'star'),
    'chokeberry': ('Chokeberry', '<span class="highlight-yellow">Antioxidant</span> rich', 'star'),
    'hawthorn berry': ('Hawthorn Berry', 'Circulation and <span class="highlight-yellow">antioxidant</span>', 'star'),
    'rosehip': ('Rosehip', 'Vitamin C and repairs', 'star'),
    'rosehip seed oil': ('Rosehip Seed Oil', 'Regenerates and <span class="highlight-yellow">brightens</span>', 'star'),
    'rosehip extract': ('Rosehip Extract', 'Vitamin C rich', 'star'),
    'hibiscus': ('Hibiscus', 'Natural AHA, firms', 'star'),
    'hibiscus extract': ('Hibiscus Extract', 'Botox plant, firms', 'star'),
    'okra extract': ('Okra Extract', '<span class="highlight-yellow">Hydrates</span> and soothes', 'star'),
    'mallow extract': ('Mallow Extract', 'Soothes and softens', 'star'),
    'marshmallow root': ('Marshmallow Root', 'Soothes and <span class="highlight-yellow">hydrates</span>', 'star'),
    'althea root': ('Althea Root', 'Soothes and protects', 'star'),
    'slippery elm': ('Slippery Elm', 'Soothes and protects', 'star'),
    'comfrey': ('Comfrey', 'Repairs and soothes', 'star'),
    'comfrey extract': ('Comfrey Extract', 'Allantoin source', 'star'),
    'plantain': ('Plantain', 'Soothes and heals', 'star'),
    'plantain extract': ('Plantain Extract', 'Repairs skin', 'star'),
    'yarrow': ('Yarrow', 'Heals and soothes', 'star'),
    'yarrow extract': ('Yarrow Extract', 'Repairs and calms', 'star'),
    'echinacea': ('Echinacea', 'Strengthens and protects', 'star'),
    'echinacea extract': ('Echinacea Extract', 'Immunity for skin', 'star'),
    'goldenseal': ('Goldenseal', 'Antibacterial, heals', 'star'),
    'myrrh': ('Myrrh', 'Heals and <span class="highlight-yellow">anti-aging</span>', 'star'),
    'myrrh extract': ('Myrrh Extract', 'Ancient healing', 'star'),
    'frankincense': ('Frankincense', '<span class="highlight-yellow">Anti-aging</span>, sacred', 'star'),
    'frankincense oil': ('Frankincense Oil', 'Rejuvenates and firms', 'star'),
    'boswellia': ('Boswellia', 'Soothes and <span class="highlight-yellow">anti-aging</span>', 'star'),
    'boswellia extract': ('Boswellia Extract', 'Calms inflammation', 'star'),
    'neem': ('Neem', 'Purifies and heals', 'star'),
    'neem oil': ('Neem Oil', 'Clears and balances', 'star'),
    'neem extract': ('Neem Extract', 'Purifies skin', 'star'),
    'tamanu': ('Tamanu', 'Heals and regenerates', 'star'),
    'tamanu oil': ('Tamanu Oil', 'Miracle healing oil', 'star'),
    'andiroba oil': ('Andiroba Oil', 'Soothes and heals', 'star'),
    'pracaxi oil': ('Pracaxi Oil', 'Conditions and repairs', 'star'),
    'buriti oil': ('Buriti Oil', 'Beta-carotene rich', 'star'),
    'brazil nut oil': ('Brazil Nut Oil', 'Selenium rich', 'star'),
    'passion fruit oil': ('Passion Fruit Oil', 'Lightweight, vitamin rich', 'star'),
    'maracuja oil': ('Maracuja Oil', '<span class="highlight-yellow">Brightens</span> and balances', 'star'),
    'acai oil': ('Acai Oil', '<span class="highlight-yellow">Antioxidant</span> powerhouse', 'star'),
    'babassu oil': ('Babassu Oil', 'Lightweight <span class="highlight-yellow">moisture</span>', 'star'),
    'cupuacu butter': ('Cupuacu Butter', 'Super <span class="highlight-yellow">hydration</span>', 'star'),
    'murumuru butter': ('Murumuru Butter', 'Locks <span class="highlight-yellow">moisture</span>', 'star'),
    'tucuma butter': ('Tucuma Butter', 'Rich nourishment', 'star'),
    'ucuuba butter': ('Ucuuba Butter', 'Heals and soothes', 'star'),
    'palm oil': ('Palm Oil', 'Rich in vitamin E', 'star'),
    'palm kernel oil': ('Palm Kernel Oil', 'Lauric acid rich', 'star'),
    'coconut oil': ('Coconut Oil', 'Nourishes and protects', 'star'),
    'coconut butter': ('Coconut Butter', 'Deep <span class="highlight-yellow">moisture</span>', 'star'),
    'coconut extract': ('Coconut Extract', '<span class="highlight-yellow">Hydrates</span> and nourishes', 'star'),
    'coconut water': ('Coconut Water', '<span class="highlight-yellow">Hydrates</span> and mineral rich', 'star'),
    'coconut milk': ('Coconut Milk', 'Nourishes and softens', 'star'),
    'monoi oil': ('Monoi Oil', 'Luxury <span class="highlight-yellow">hydration</span>', 'star'),
    'tiare flower': ('Tiare Flower', 'Exotic, nourishes', 'star'),
    'gardenia': ('Gardenia', 'Soothes and fragrances', 'star'),
    'gardenia extract': ('Gardenia Extract', 'Calms and <span class="highlight-yellow">brightens</span>', 'star'),
    'plumeria': ('Plumeria', 'Exotic, softens', 'star'),
    'plumeria extract': ('Plumeria Extract', 'Luxury ingredient', 'star'),
    'pikake': ('Pikake', 'Hawaiian jasmine, soothes', 'star'),
    'pikake extract': ('Pikake Extract', 'Exotic <span class="highlight-yellow">hydration</span>', 'star'),
    'orchid': ('Orchid', 'Luxury, <span class="highlight-yellow">anti-aging</span>', 'star'),
    'orchid extract': ('Orchid Extract', 'Firms and rejuvenates', 'star'),
    'vanilla': ('Vanilla', '<span class="highlight-yellow">Antioxidant</span>, comforts', 'star'),
    'vanilla extract': ('Vanilla Extract', 'Soothes and scents', 'star'),
    'vanilla bean': ('Vanilla Bean', 'Rich <span class="highlight-yellow">antioxidant</span>', 'star'),
    'cocoa extract': ('Cocoa Extract', '<span class="highlight-yellow">Antioxidant</span>, comforts', 'star'),
    'cocoa powder': ('Cocoa Powder', 'Rich in flavonoids', 'star'),
    'chocolate extract': ('Chocolate Extract', '<span class="highlight-yellow">Antioxidant</span> luxury', 'star'),
    'coffee extract': ('Coffee Extract', 'De-puffs and energizes', 'star'),
    'coffee seed oil': ('Coffee Seed Oil', '<span class="highlight-yellow">Antioxidant</span>, firms', 'star'),
    'green coffee': ('Green Coffee', 'Chlorogenic acid rich', 'star'),
    'guarana': ('Guarana', 'Energizes and firms', 'star'),
    'guarana extract': ('Guarana Extract', 'Caffeine alternative', 'star'),
    'yerba mate': ('Yerba Mate', '<span class="highlight-yellow">Antioxidant</span>, energizes', 'star'),
    'yerba mate extract': ('Yerba Mate Extract', 'Polyphenol rich', 'star'),
    'matcha': ('Matcha', 'Super green tea, <span class="highlight-yellow">antioxidant</span>', 'star'),
    'matcha extract': ('Matcha Extract', 'Chlorophyll and <span class="highlight-yellow">antioxidant</span>', 'star'),
    'white tea': ('White Tea', 'Gentlest <span class="highlight-yellow">antioxidant</span>', 'star'),
    'white tea extract': ('White Tea Extract', 'Delicate <span class="highlight-yellow">antioxidant</span>', 'star'),
    'oolong tea': ('Oolong Tea', 'Balances and <span class="highlight-yellow">antioxidant</span>', 'star'),
    'pu-erh tea': ('Pu-erh Tea', 'Fermented, detoxifies', 'star'),
    'kombucha': ('Kombucha', 'Probiotic, balances', 'star'),
    'kombucha extract': ('Kombucha Extract', 'Fermented benefits', 'star'),
    'apple cider vinegar': ('Apple Cider Vinegar', 'Balances pH, clarifies', 'star'),
    'vinegar': ('Vinegar', 'Gentle exfoliation', 'star'),
    'rice vinegar': ('Rice Vinegar', '<span class="highlight-yellow">Brightens</span> and softens', 'star'),
    'sake': ('Sake', 'Fermented, <span class="highlight-yellow">brightens</span>', 'star'),
    'sake extract': ('Sake Extract', 'Kojic acid source', 'star'),
    'sake lees': ('Sake Lees', '<span class="highlight-yellow">Brightens</span> and nourishes', 'star'),
    'rice': ('Rice', '<span class="highlight-yellow">Brightens</span> and softens', 'star'),
    'rice extract': ('Rice Extract', 'Traditional <span class="highlight-yellow">brightening</span>', 'star'),
    'rice bran': ('Rice Bran', 'Vitamin E rich', 'star'),
    'rice bran oil': ('Rice Bran Oil', 'Lightweight <span class="highlight-yellow">antioxidant</span>', 'star'),
    'rice water': ('Rice Water', '<span class="highlight-yellow">Brightens</span> and strengthens', 'star'),
    'rice ferment filtrate': ('Rice Ferment Filtrate', 'Pitera alternative', 'star'),
    'pitera': ('Pitera', 'Galactomyces ferment', 'star'),
    'galactomyces ferment filtrate': ('Galactomyces Ferment Filtrate', '<span class="highlight-yellow">Brightens</span> and refines', 'star'),
    'bifida ferment lysate': ('Bifida Ferment Lysate', 'Strengthens barrier', 'star'),
    'lactococcus ferment': ('Lactococcus Ferment', 'Balances microbiome', 'star'),
    'streptococcus thermophilus': ('Streptococcus Thermophilus', 'Supports skin health', 'star'),
    'leuconostoc': ('Leuconostoc', 'Natural preservative, probiotic', 'star'),
    'radish root ferment': ('Radish Root Ferment', 'Natural antimicrobial', 'star'),
    'kimchi extract': ('Kimchi Extract', 'Probiotic, energizes', 'star'),
    'miso extract': ('Miso Extract', 'Fermented, nourishes', 'star'),
    'natto extract': ('Natto Extract', 'Polyglutamic acid source', 'star'),
    'polyglutamic acid': ('Polyglutamic Acid', 'Super <span class="highlight-yellow">hydrator</span>', 'star'),
    'sodium pca': ('Sodium PCA', 'Natural <span class="highlight-yellow">moisturizing</span> factor', 'star'),
    'pca': ('PCA', 'Skin-identical <span class="highlight-yellow">hydrator</span>', 'star'),
    'sodium lactate': ('Sodium Lactate', '<span class="highlight-yellow">Hydrates</span> and pH balances', 'star'),
    'lactic acid': ('Lactic Acid', 'Gentle exfoliation and <span class="highlight-yellow">hydration</span>', 'star'),
    'sodium hyaluronate': ('Sodium Hyaluronate', 'Deep <span class="highlight-yellow">hydration</span>', 'star'),
    'hyaluronic acid': ('Hyaluronic Acid', 'Deep <span class="highlight-yellow">hydration</span>, ideal for dry and mature skin', 'star'),
    'hydrolyzed hyaluronic acid': ('Hydrolyzed Hyaluronic Acid', 'Penetrates deeper', 'star'),
    'hyaluronic acid crosspolymer': ('Hyaluronic Acid Crosspolymer', 'Long-lasting <span class="highlight-yellow">hydration</span>', 'star'),
    'potassium hyaluronate': ('Potassium Hyaluronate', '<span class="highlight-yellow">Hydrates</span> and soothes', 'star'),
    'hydroxypropyltrimonium hyaluronate': ('Hydroxypropyltrimonium Hyaluronate', 'Cationic <span class="highlight-yellow">hydrator</span>', 'star'),
    'sodium acetylated hyaluronate': ('Sodium Acetylated Hyaluronate', 'Super <span class="highlight-yellow">hydrator</span>', 'star'),
    'cetyl hyaluronate': ('Cetyl Hyaluronate', 'Oil-soluble <span class="highlight-yellow">hydrator</span>', 'star'),
    'dimethyl hyaluronate': ('Dimethyl Hyaluronate', 'Unique <span class="highlight-yellow">hydrator</span>', 'star'),
    'hyaluronate': ('Hyaluronate', '<span class="highlight-yellow">Hydrates</span> and plumps', 'star'),
    'hyaluronan': ('Hyaluronan', '<span class="highlight-yellow">Hydrates</span> and plumps', 'star'),
}

def check_ingredients(ingredients_text):
    """Check ingredients against database and return categorized results"""
    text = str(ingredients_text).lower()
    results = {'danger': [], 'star': []}
    
    # Check for multi-word ingredients first
    for keyword, (name, desc, category) in INGREDIENT_DATABASE.items():
        if ' ' in keyword:
            if keyword in text:
                if category == 'danger':
                    results['danger'].append((name, desc))
                else:
                    results['star'].append((name, desc))
    
    # Then check single words
    words = set(text.replace(',', ' ').replace(';', ' ').split())
    for keyword, (name, desc, category) in INGREDIENT_DATABASE.items():
        if ' ' not in keyword and keyword in words:
            # Avoid duplicates
            already_found = any(n == name for n, _ in results[category])
            if not already_found:
                if category == 'danger':
                    results['danger'].append((name, desc))
                else:
                    results['star'].append((name, desc))
    
    return results

def get_function_tags(ingredients_text):
    """Extract function tags from ingredients"""
    text = str(ingredients_text).lower()
    tags = []
    
    for function, keywords in FUNCTION_MAPPING.items():
        for keyword in keywords:
            if keyword in text:
                tags.append(function)
                break
    
    return list(set(tags))

def get_price_tier(price):
    # Absolute price tiers as specified
    if price <= 50:
        return 'Budget-Friendly', 'price-tag-budget'
    elif price <= 100:
        return 'Affordable Luxury', 'price-tag-mid'
    else:
        return 'Premium', 'price-tag-luxury'

def analyze_price_complaints(reviews_df):
    price_keywords = ['expensive', 'pricey', 'overpriced', 'not worth', 'overpriced', 'too expensive']
    price_complaints = 0
    
    for text in reviews_df['review_text'].fillna('').astype(str):
        text_lower = text.lower()
        if any(kw in text_lower for kw in price_keywords):
            price_complaints += 1
    
    total_reviews = len(reviews_df)
    complaint_rate = price_complaints / total_reviews if total_reviews > 0 else 0
    
    return price_complaints, complaint_rate

def generate_price_strategy(price_tier, price_complaints, complaint_rate, total_reviews, price):
    if price_tier == 'Budget-Friendly':
        if complaint_rate < 0.01:
            return f"Budget-friendly (${price:.0f}), few price complaints. Suitable for limited-time discounts and volume promotions."
        else:
            return f"Budget pricing but {price_complaints} complaints about expensive or poor value. Check if pricing is higher than competitors or if efficacy meets expectations. Consider short-term price testing."
    elif price_tier == 'Affordable Luxury':
        if complaint_rate < 0.01:
            return f"Affordable luxury positioning (${price:.0f}), few price complaints. Maintain pricing, use gift sets and loyalty points instead of direct discounts."
        else:
            return f"Mid-range product with {price_complaints} complaints about too expensive. Consider increasing gift value or introducing smaller sizes. Avoid direct price cuts."
    else:
        if complaint_rate < 0.01:
            return f"Premium line (${price:.0f}), few price complaints. Maintain premium pricing strategy."
        else:
            return f"Premium product with {price_complaints} complaints about too expensive or poor value. Consider gift bundles, smaller sizes, or strengthening ingredient claims to justify premium."

def calculate_comprehensive_score(rating, review_count, price, peer_avg_price, positive_rate):
    rating_score = (rating / 5) * 5 * 0.40
    
    max_reviews = 1000
    popularity_score = min(review_count / max_reviews * 5, 5) * 0.25
    
    if price > 0 and peer_avg_price > 0:
        price_ratio = peer_avg_price / price
        value_score = min(price_ratio * 5, 5) * 0.20
    else:
        value_score = 2.5
    
    reputation_score = positive_rate * 5 * 0.15
    
    total_score = rating_score + popularity_score + value_score + reputation_score
    
    return {
        'total': round(total_score, 1),
        'rating_component': round(rating_score, 2),
        'popularity_component': round(popularity_score, 2),
        'value_component': round(value_score, 2),
        'reputation_component': round(reputation_score, 2)
    }

def analyze_skin_types(product_reviews):
    # Extract skin type mentions from review text
    skin_keywords = {
        'oily': ['oily skin', 'oily', 'greasy', 'shine', 'shiny', 'sebum'],
        'dry': ['dry skin', 'dry', 'flaky', 'tight', 'dehydrated', 'rough'],
        'combination': ['combination skin', 'combination', 'mixed skin', 'oily t-zone'],
        'sensitive': ['sensitive skin', 'sensitive', 'reactive', 'irritated', 'redness'],
        'normal': ['normal skin', 'normal', 'balanced skin']
    }
    
    skin_mentions = {key: 0 for key in skin_keywords.keys()}
    skin_mentions['other'] = 0
    
    for idx, row in product_reviews.iterrows():
        review_text = str(row.get('review_text', '')).lower()
        matched = False
        
        for skin_type, keywords in skin_keywords.items():
            for keyword in keywords:
                if keyword in review_text:
                    skin_mentions[skin_type] += 1
                    matched = True
                    break
            if matched:
                break
        
        if not matched:
            skin_mentions['other'] += 1
    
    standardized = {k.capitalize(): v for k, v in skin_mentions.items() if v > 0}
    
    if not standardized or (len(standardized) == 1 and 'Other' in standardized):
        return None
    
    if 'Other' in standardized and len(standardized) > 1:
        del standardized['Other']
    
    dominant_skin = max(standardized, key=standardized.get)
    dominant_count = standardized[dominant_skin]
    total = sum(standardized.values())
    
    negative_keywords = ['irritating', 'sticky', 'breakout', 'allergic', 'harsh', 
                        'burning', 'drying', 'tight', 'redness', 'itchy', 'greasy']
    
    neg_reviews = product_reviews[product_reviews['rating'].isin([1, 2])]
    neg_texts = neg_reviews['review_text'].tolist()
    
    neg_words = extract_keywords(neg_texts, negative_keywords)
    top_concern = list(neg_words.keys())[0] if neg_words else None
    
    return {
        'distribution': standardized,
        'dominant': dominant_skin,
        'dominant_count': dominant_count,
        'dominant_pct': dominant_count / total if total > 0 else 0,
        'top_concern': top_concern,
        'is_balanced': max(standardized.values()) / total < 0.8 if total > 0 else True
    }



def generate_marketing_copy(product, product_reviews, score_details, price_tier,
                           ingredients_info, skin_analysis, pos_words, neg_words,
                           peer_avg, actual_review_count):
    """Generate marketing copy based on product data using template filling"""

    product_name = product['product_name']
    rating = product['rating']
    price = product['price']
    score = score_details['total']

    positive_rate = (product_reviews['rating'] >= 4).mean() if len(product_reviews) > 0 else 0.5
    rec_rate_text = f"{positive_rate:.0%}" if positive_rate > 0 else "high"

    star_ingredients = ingredients_info['star'][:3] if ingredients_info['star'] else []
    ingredient_texts = []
    for name, desc in star_ingredients:
        benefit = desc.replace('<span class="highlight-yellow">', '').replace('</span>', '')
        ingredient_texts.append(f"{name} {benefit.lower()}")

    if skin_analysis:
        dominant_skin = skin_analysis['dominant']
        skin_pct = skin_analysis['dominant_pct'] * 100
        skin_text = f"particularly suitable for {dominant_skin.lower()} skin"
        if skin_analysis['is_balanced']:
            skin_text += f" with {skin_pct:.0f}% of reviewers belonging to this group"
    else:
        skin_text = "suitable for all skin types"

    if price <= 50:
        price_text = f"priced accessibly at ${price:.0f}"
        promo_text = "consider bundling with travel-size samples or offering a buy-one-get-one deal to drive volume"
    elif price <= 100:
        price_text = f"positioned as affordable luxury at ${price:.0f}"
        promo_text = "enhance perceived value through gift-with-purchase sets or loyalty point multipliers rather than direct discounts"
    else:
        price_text = f"positioned in the premium segment at ${price:.0f}"
        promo_text = "maintain premium positioning while offering exclusive gift bundles or limited-edition packaging to justify the investment"

    top_pos = list(pos_words.keys())[:2] if pos_words else ["effective", "gentle"]
    pos_keywords_text = " and ".join(top_pos)

    paragraphs = []

    opening = f"This {product_name} earns a comprehensive score of {score:.1f} out of 5.0, backed by a {rec_rate_text} positive recommendation rate from {actual_review_count} verified reviewers who praise its consistent performance."
    paragraphs.append(opening)

    if ingredient_texts:
        if len(ingredient_texts) > 1:
            ingredients_sentence = "The formula features " + ", ".join(ingredient_texts[:-1]) + " and " + ingredient_texts[-1] + "."
        else:
            ingredients_sentence = "The formula features " + ingredient_texts[0] + "."
        paragraphs.append(ingredients_sentence)

    feedback_sentence = f"Users consistently describe the experience as {pos_keywords_text}, making it {skin_text}."
    if skin_analysis and skin_analysis.get('top_concern'):
        feedback_sentence += " Even those with sensitivity concerns note minimal irritation."
    paragraphs.append(feedback_sentence)

    price_sentence = f"{price_text.capitalize()}, this product delivers exceptional value. For merchants, {promo_text}."
    paragraphs.append(price_sentence)

    closing = f"Whether you are building a curated skincare selection or expanding your bestseller lineup, this product offers proven market appeal with strong customer retention potential."
    paragraphs.append(closing)

    copy = " ".join(paragraphs)

    return copy

df = load_data()

agg_dict = {
    'rating': 'first',
    'price': 'first',
    'loves_count': 'first',
    'skin_type': 'first',
    'review_date': 'count',
    'sale_price_usd': 'first',
    'limited_edition': 'first',
    'new': 'first',
    'sephora_exclusive': 'first',
    'ingredients': 'first'
}

if 'primary_category' in df.columns:
    agg_dict['primary_category'] = 'first'
if 'secondary_category' in df.columns:
    agg_dict['secondary_category'] = 'first'
if 'tertiary_category' in df.columns:
    agg_dict['tertiary_category'] = 'first'
if 'is_recommended' in df.columns:
    agg_dict['is_recommended'] = 'mean'

product_stats = df.groupby(['product_name', 'brand_name']).agg(agg_dict).reset_index()
product_stats.rename(columns={'review_date': 'review_count'}, inplace=True)

# Filter to valid function categories only
if 'secondary_category' in product_stats.columns:
    product_stats['secondary_category'] = product_stats['secondary_category'].apply(
        lambda x: x if x in VALID_FUNCTION_CATEGORIES else 'Other'
    )

# Sort by rating desc, then review_count desc
product_stats = product_stats.sort_values(['rating', 'review_count'], ascending=[False, False])

st.title("SEPHORA MARKETING ANALYZER")
st.caption("Beauty E-commerce Marketing Intelligence Tool")
st.divider()

st.markdown("<h2 style='font-weight: 600; margin-bottom: 24px;'>Product Filter</h2>", unsafe_allow_html=True)

if 'selected_price_tier' not in st.session_state:
    st.session_state.selected_price_tier = 'All Prices'
    st.session_state.price_min = float(product_stats['price'].min())
    st.session_state.price_max = float(product_stats['price'].max())

if 'show_copy' not in st.session_state:
    st.session_state.show_copy = False
if 'generated_copy' not in st.session_state:
    st.session_state.generated_copy = ""

has_secondary = 'secondary_category' in product_stats.columns and product_stats['secondary_category'].nunique() > 1

# Row 1: Brand + Secondary Category (Function Category)
if has_secondary:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Brand**")
        brands = ['All Brands'] + sorted(product_stats['brand_name'].unique().tolist())
        selected_brand = st.selectbox("Select Brand", brands, label_visibility="collapsed")
    with col2:
        st.markdown("**Product Function Category**")
        # Only show valid function categories
        valid_cats = [c for c in product_stats['secondary_category'].unique() if c in VALID_FUNCTION_CATEGORIES or c == 'Other']
        function_categories = ['All Categories'] + sorted(valid_cats)
        selected_secondary = st.selectbox("Select Function", function_categories, label_visibility="collapsed")
else:
    st.markdown("**Brand**")
    brands = ['All Brands'] + sorted(product_stats['brand_name'].unique().tolist())
    selected_brand = st.selectbox("Select Brand", brands, label_visibility="collapsed")
    selected_secondary = 'All Categories'

# Row 2: Function Tags Filter
st.markdown("**Function Tags**")
tag_cols = st.columns(6)
function_tags = ['Whitening', 'Anti-aging', 'Hydration', 'Antioxidant', 'Oil-control', 'Repairing']
selected_tags = []

for idx, tag in enumerate(function_tags):
    with tag_cols[idx]:
        if st.checkbox(tag, key=f"tag_{tag}", value=False):
            selected_tags.append(tag.lower())

if selected_tags:
    col_reset, _ = st.columns([1, 5])
    with col_reset:
        if st.button("Reset Tags", key="reset_tags"):
            selected_tags = []
            st.session_state.need_rerun = True

# Row 3: Price Range
with st.container():
    st.markdown("**Price Range**")
    
    tier_cols = st.columns(4)
    price_tiers = {
        'All Prices': (float(product_stats['price'].min()), float(product_stats['price'].max())),
        'Budget Friendly ($3-50)': (3.0, 50.0),
        'Affordable Luxury ($50-100)': (50.0, 100.0),
        'Premium ($100+)': (100.0, float(product_stats['price'].max()))
    }
    
    for idx, (tier_name, (tier_min, tier_max)) in enumerate(price_tiers.items()):
        with tier_cols[idx]:
            is_active = st.session_state.selected_price_tier == tier_name
            btn_type = "primary" if is_active else "secondary"
            if st.button(tier_name, key=f"tier_{tier_name}", use_container_width=True, type=btn_type):
                st.session_state.selected_price_tier = tier_name
                st.session_state.price_min = tier_min
                st.session_state.price_max = tier_max
                st.session_state.need_rerun = True
    
    price_range = st.slider(
        "Fine-tune Price",
        min_value=float(product_stats['price'].min()),
        max_value=float(product_stats['price'].max()),
        value=(st.session_state.price_min, st.session_state.price_max),
        step=5.0,
        label_visibility="collapsed"
    )
    st.session_state.price_min = price_range[0]
    st.session_state.price_max = price_range[1]
    st.markdown(f"<div style='text-align: center; color: #666;'>${price_range[0]:.0f} - ${price_range[1]:.0f}</div>", unsafe_allow_html=True)

# Row 4: Special Attributes
st.markdown("**Special Attributes**")
attr_cols = st.columns(4)
with attr_cols[0]:
    filter_new = st.checkbox("New Arrivals Only", value=False)
with attr_cols[1]:
    filter_limited = st.checkbox("Limited Edition Only", value=False)
with attr_cols[2]:
    filter_exclusive = st.checkbox("Sephora Exclusive Only", value=False)
with attr_cols[3]:
    filter_stock = st.checkbox("Hide Out of Stock", value=True)
    st.markdown('<span class="stock-hint">When checked, only shows products with available stock</span>', unsafe_allow_html=True)

# Row 5: Rating + Reviews
col3, col4 = st.columns(2)

with col3:
    st.markdown("**Minimum Rating**")
    min_rating = st.slider("Rating", 1.0, 5.0, 3.0, 0.1, label_visibility="collapsed")
    st.markdown(f"<div style='text-align: center; color: #8B0000; font-weight: 600;'>{min_rating:.1f}+ Stars</div>", unsafe_allow_html=True)

with col4:
    st.markdown("**Minimum Reviews**")
    min_reviews = st.slider("Reviews", 0, int(product_stats['review_count'].max()), 50, step=10, label_visibility="collapsed")
    st.markdown(f"<div style='text-align: center; color: #8B0000; font-weight: 600;'>{min_reviews}+ Reviews</div>", unsafe_allow_html=True)

# Apply filters
filtered_df = product_stats.copy()

if selected_brand != 'All Brands':
    filtered_df = filtered_df[filtered_df['brand_name'] == selected_brand]

if has_secondary and selected_secondary != 'All Categories':
    filtered_df = filtered_df[filtered_df['secondary_category'] == selected_secondary]

# Filter by function tags (ingredient-based)
if selected_tags and 'ingredients' in filtered_df.columns:
    mask = False
    for tag in selected_tags:
        keywords = FUNCTION_MAPPING.get(tag, [])
        for keyword in keywords:
            mask = mask | filtered_df['ingredients'].str.lower().str.contains(keyword, na=False)
    filtered_df = filtered_df[mask]

if filter_new and 'new' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['new'] == True]
if filter_limited and 'limited_edition' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['limited_edition'] == True]
if filter_exclusive and 'sephora_exclusive' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['sephora_exclusive'] == True]

if len(filtered_df) > 0:
    available_min = float(filtered_df['price'].min())
    available_max = float(filtered_df['price'].max())
    actual_min = max(price_range[0], available_min)
    actual_max = min(price_range[1], available_max)
    if actual_min <= actual_max:
        filtered_df = filtered_df[(filtered_df['price'] >= actual_min) & (filtered_df['price'] <= actual_max)]

filtered_df = filtered_df[filtered_df['rating'] >= min_rating]
filtered_df = filtered_df[filtered_df['review_count'] >= min_reviews]

result_count = len(filtered_df)
st.markdown(f'<div class="result-counter">Found {result_count} Products</div>', unsafe_allow_html=True)

# Check for missing secondary categories
if has_secondary:
    missing_count = product_stats[product_stats['secondary_category'] == 'Other'].shape[0]
    if missing_count > 0:
        st.warning(f"Note: {missing_count} products are not assigned to a function category")

st.divider()

# Product List Section
st.header("Recommended Products")
st.caption("Higher-rated products appear first; same ratings sorted by review count")

st.info("Select a product from the filtered list below to view detailed market analysis and promotion recommendations.")

if len(filtered_df) == 0:
    st.warning("No products match the selected criteria. Please adjust filters.")
else:
    # Table columns: Product, Price, Rating, Reviews, Action
    h1, h2, h3, h4, h5 = st.columns([4, 1, 1, 1, 1.5])
    h1.markdown("**Product**")
    h2.markdown("**Price**")
    h3.markdown("**Rating**")
    h4.markdown("**Reviews**")
    h5.markdown("**Action**")
    
    for idx, row in filtered_df.head(20).iterrows():
        product_data = df[df['product_name'] == row['product_name']]
        actual_review_count = len(product_data)
        
        c1, c2, c3, c4, c5 = st.columns([4, 1, 1, 1, 1.5])
        
        with c1:
            name_html = f"**{row['product_name']}**"
            
            tags_html = ""
            if row.get('new', False):
                tags_html += '<span class="tag-new">NEW</span>'
            if row.get('limited_edition', False):
                tags_html += '<span class="tag-limited">LIMITED</span>'
            
            # Show secondary category if available
            if has_secondary and row.get('secondary_category') and row['secondary_category'] != 'Unknown' and row['secondary_category'] != 'Other':
                st.caption(f"{row['brand_name']} | {row['secondary_category']}")
            else:
                st.caption(f"{row['brand_name']}")
            
            st.markdown(f"{name_html} {tags_html}", unsafe_allow_html=True)
            
        with c2:
            price_html = f"${row['price']:.2f}"
            
            has_sale = (pd.notna(row.get('sale_price_usd')) and 
                       row['sale_price_usd'] > 0 and 
                       row['sale_price_usd'] < row['price'])
            if has_sale:
                price_html += '<span class="tag-sale">SALE</span>'
            
            st.markdown(price_html, unsafe_allow_html=True)
            
        with c3:
            st.write(f"★ {row['rating']:.1f}")
            
        with c4:
            st.write(f"{int(row['review_count'])}")
            
        with c5:
            if st.button("Select Product", key=f"btn_{idx}", type="primary", use_container_width=True):
                st.session_state.selected_product = row.to_dict()
                st.session_state.show_analysis = False
                st.session_state.need_rerun = True
        
        st.divider()

if st.session_state.get('need_rerun'):
    st.session_state.need_rerun = False
    st.rerun()

if 'selected_product' in st.session_state and st.session_state.selected_product:
    
    product = st.session_state.selected_product
    product_name = product['product_name']
    product_reviews = df[df['product_name'] == product_name]
    actual_review_count = len(product_reviews)
    product_full = product_reviews.iloc[0] if len(product_reviews) > 0 else None
    
    st.header(product_name)
    
    b1, b2, b3, b4 = st.columns([1, 1, 1, 2])
    
    with b1:
        if product.get('new', False):
            st.markdown('<div style="background: linear-gradient(135deg, #FFD700, #FFA500); color: #000; padding: 8px 16px; border-radius: 8px; text-align: center; font-weight: 700;">NEW ARRIVAL</div>', unsafe_allow_html=True)
    
    with b2:
        if product.get('limited_edition', False):
            st.markdown('<div style="background: linear-gradient(135deg, #FFD700, #FF6347); color: #000; padding: 8px 16px; border-radius: 8px; text-align: center; font-weight: 700;">LIMITED EDITION</div>', unsafe_allow_html=True)
    
    with b3:
        loves = int(product.get('loves_count', 0))
        st.markdown(f'<div style="background: linear-gradient(135deg, #FF69B4, #FF1493); color: #fff; padding: 8px 16px; border-radius: 8px; text-align: center; font-weight: 700;">♥ {loves:,} LOVES</div>', unsafe_allow_html=True)
    
    st.divider()
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Price", f"${product['price']:.2f}")
    m2.metric("Rating", f"{product['rating']:.2f}/5.0")
    m3.metric("Reviews", f"{actual_review_count}")
    m4.metric("Heat Score", f"{int(product['review_count'])}")
    
    # Show secondary category
    if has_secondary and product.get('secondary_category') and product['secondary_category'] not in ['Unknown', 'Other']:
        st.markdown(f"**Function Category:** {product['secondary_category']}")
    
    price_tier, price_class = get_price_tier(product['price'])
    st.markdown(f"**Price Positioning:** <span class='{price_class}'>{price_tier} (${product['price']:.0f})</span>", unsafe_allow_html=True)
    
    if pd.notna(product.get('skin_type')) and product.get('skin_type') != 'Unknown':
        st.info(f"**Suitable For:** {product['skin_type']} skin types")
    
    st.divider()
    
    # Market Position Comparison - Same Function Category Average
    st.subheader("Market Position Comparison")
    
    # Use secondary_category for peer comparison
    if has_secondary and product.get('secondary_category') and product['secondary_category'] not in ['Unknown', 'Other']:
        peer_data = product_stats[product_stats['secondary_category'] == product['secondary_category']]
        comparison_label = 'Same Category Average'
    else:
        peer_data = product_stats[product_stats['brand_name'] == product['brand_name']]
        comparison_label = 'Brand Average'
    
    # Exclude current product from peer data
    peer_data = peer_data[peer_data['product_name'] != product_name]
    
    peer_avg = {
        'rating': peer_data['rating'].mean() if len(peer_data) > 0 else product['rating'],
        'price': peer_data['price'].mean() if len(peer_data) > 0 else product['price'],
        'review_count': peer_data['review_count'].mean() if len(peer_data) > 0 else product['review_count'],
        'loves_count': peer_data['loves_count'].mean() if len(peer_data) > 0 else product['loves_count']
    }
    
    # Three separate bar charts with detailed percentage difference
    chart_cols = st.columns(3)
    
    metrics_data = [
        ('Rating', product['rating'], peer_avg['rating'], 0, 5),
        ('Review Count', actual_review_count, peer_avg['review_count'], 0, max(product_stats['review_count'].max(), actual_review_count)),
        ('Price Comparison ($)', product['price'], peer_avg['price'], 0, max(product['price'], peer_avg['price']) * 1.2)
    ]
    
    for idx, (metric_name, current_val, peer_val, min_val, max_val) in enumerate(metrics_data):
        with chart_cols[idx]:
            fig = go.Figure()
            
            colors = ['#2E5C8A' if current_val >= peer_val else '#5B9BD5', '#A5A5A5']
            
            fig.add_trace(go.Bar(
                x=['Current Product', comparison_label],
                y=[current_val, peer_val],
                marker_color=colors,
                text=[f'{current_val:.1f}', f'{peer_val:.1f}'],
                textposition='outside',
                textfont=dict(size=14, family='Arial Black')
            ))
            
            fig.update_layout(
                showlegend=False,
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(l=20, r=20, t=40, b=20),
                height=250,
                yaxis=dict(range=[min_val, max_val], showgrid=True, gridcolor='lightgray'),
                xaxis=dict(tickfont=dict(size=11)),
                title=dict(text=metric_name, font=dict(size=13, family='Arial Black')),
                bargap=0.4
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Detailed percentage difference with comparison object
            if peer_val > 0:
                pct_diff = ((current_val - peer_val) / peer_val) * 100
                if pct_diff > 0:
                    diff_text = f"{abs(pct_diff):.0f}% more expensive than {comparison_label.lower()}"
                    st.markdown(f'<div style="color: #28a745; text-align: center; font-weight: 600;">{diff_text}</div>', unsafe_allow_html=True)
                elif pct_diff < 0:
                    diff_text = f"{abs(pct_diff):.0f}% cheaper than {comparison_label.lower()}"
                    st.markdown(f'<div style="color: #dc3545; text-align: center; font-weight: 600;">{diff_text}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div style="color: #6c757d; text-align: center; font-weight: 600;">Same price as {comparison_label.lower()}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="color: #6c757d; text-align: center; font-weight: 600;">N/A</div>', unsafe_allow_html=True)
    
    st.divider()
    
    # Review Volume Trend - Same Category Average with axis labels and legend
    st.subheader("Review Volume Trend")
    st.caption("Monthly review count comparison: This Product vs Same Category Average")

    product_reviews['month'] = product_reviews['review_date'].dt.to_period('M')
    monthly_product = product_reviews.groupby('month').size()

    # Use same secondary_category for trend comparison
    if has_secondary and product.get('secondary_category') and product['secondary_category'] not in ['Unknown', 'Other']:
        category_peers = df[df['secondary_category'] == product['secondary_category']]
    else:
        category_peers = df[df['brand_name'] == product['brand_name']]

    category_peers['month'] = category_peers['review_date'].dt.to_period('M')
    monthly_category = category_peers.groupby('month').size()

    # Determine start date based on product data span
    from datetime import datetime
    current_year = datetime.now().year
    five_years_ago = pd.Period(f'{current_year-5}-01', freq='M')

    if len(monthly_product) > 0:
        first_review_date = monthly_product.index.min()
        last_review_date = monthly_product.index.max()
        data_span_months = (last_review_date - first_review_date).n

        if data_span_months < 6:
            # Short data span: show product's own timeline with small padding
            start_date = first_review_date - 1
        else:
            # Long data span: show last 5 years
            start_date = min(first_review_date, five_years_ago)
    else:
        # Default to last 5 years
        start_date = five_years_ago

    # Filter data from start_date onwards
    monthly_product = monthly_product[monthly_product.index >= start_date]
    monthly_category = monthly_category[monthly_category.index >= start_date]

    all_months = monthly_product.index.union(monthly_category.index)

    # Create DataFrame with filtered data
    trend_df = pd.DataFrame({
        'This Product': [monthly_product.get(m, 0) for m in all_months],
        'Category Average': [monthly_category.get(m, 0) for m in all_months]
    }, index=[str(m) for m in all_months])

    # Calculate Y-axis max for better tick display
    y_max = max(trend_df['This Product'].max(), trend_df['Category Average'].max())
    y_max_rounded = int((y_max // 500 + 1) * 500) if y_max > 0 else 500

    # Create line chart with improved styling
    fig_trend = go.Figure()

    # This Product - Blue bold line
    fig_trend.add_trace(go.Scatter(
        x=trend_df.index,
        y=trend_df["This Product"],
        mode='lines+markers',
        name='This Product',
        line=dict(color='#2E5C8A', width=3),
        marker=dict(size=8, color='#2E5C8A', symbol='circle'),
        hovertemplate="<b>This Product</b><br>Month: %{x}<br>Reviews: %{y}<extra></extra>"
    ))

    # Category Average - Gray normal line
    fig_trend.add_trace(go.Scatter(
        x=trend_df.index,
        y=trend_df["Category Average"],
        mode='lines+markers',
        name='Same Category Average',
        line=dict(color='#A5A5A5', width=1.5),
        marker=dict(size=6, color='#A5A5A5', symbol='diamond'),
        hovertemplate="<b>Category Average</b><br>Month: %{x}<br>Reviews: %{y}<extra></extra>"
    ))

    fig_trend.update_layout(
        xaxis_title='Time (Month)',
        yaxis_title='Number of Reviews',
        yaxis=dict(
            range=[0, y_max_rounded],
            dtick=500 if y_max_rounded <= 3000 else 1000,
            showgrid=True,
            gridcolor='rgba(211, 211, 211, 0.5)'
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(211, 211, 211, 0.3)',
            tickangle=45
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=12)
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=60, r=40, t=100, b=80),
        height=450,
        hovermode='x unified'
    )

    st.plotly_chart(fig_trend, use_container_width=True)
    st.divider()
    
    # Deep Analysis Section
    st.subheader("Deep Analysis")
    
    if not st.session_state.get('show_analysis', False):
        st.write("Analyze reviews and generate promotion recommendations.")
        if st.button("Select This Product to Continue Analysis", type="primary", use_container_width=True):
            st.session_state.show_analysis = True
            st.session_state.need_rerun = True
    else:
        pos_reviews = product_reviews[product_reviews['rating'].isin([4, 5])]['review_text'].tolist()
        neg_reviews = product_reviews[product_reviews['rating'].isin([1, 2])]['review_text'].tolist()
        
        positive_keywords = ['hydrating', 'moisturizing', 'smooth', 'brightening', 'effective', 
                           'gentle', 'love', 'perfect', 'excellent', 'amazing', 'soft', 'glowing', 'repurchase']
        negative_keywords = ['irritating', 'oily', 'sticky', 'expensive', 'waste', 'disappointed', 
                           'breakout', 'allergic', 'dry', 'harsh', 'greasy', 'burning', 'useless']
        
        pos_words = extract_keywords(pos_reviews, positive_keywords)
        neg_words = extract_keywords(neg_reviews, negative_keywords)
        
        # Comprehensive Score Display
        st.subheader("Comprehensive Score")
        
        positive_rate = (product_reviews['rating'] >= 4).mean() if len(product_reviews) > 0 else 0.5
        
        score_details = calculate_comprehensive_score(
            product['rating'], actual_review_count, product['price'], peer_avg['price'], positive_rate
        )
        
        score_col1, score_col2 = st.columns([1, 2])
        with score_col1:
            st.markdown(f'<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 16px; text-align: center;"><div style="font-size: 3rem; font-weight: 800;">{score_details["total"]}</div><div style="font-size: 1.2rem;">/ 5.0</div></div>', unsafe_allow_html=True)
        
        with score_col2:
            st.write("**Formula:** Rating x 40% + Popularity x 25% + Value x 20% + Reputation x 15%")
            st.write(f"• Rating: {product['rating']:.1f} x 0.40 = {score_details['rating_component']:.2f}")
            st.write(f"• Popularity: {actual_review_count} reviews → {score_details['popularity_component']:.2f}")
            st.write(f"• Value: ${product['price']:.2f} vs avg ${peer_avg['price']:.2f} = {score_details['value_component']:.2f}")
            st.write(f"• Reputation: {positive_rate:.1%} positive = {score_details['reputation_component']:.2f}")
        
        st.divider()
        
        # Price Strategy Alert with warning icon
        st.subheader("⚠️ Price Strategy Alert")
        
        price_complaints, complaint_rate = analyze_price_complaints(product_reviews)
        price_strategy = generate_price_strategy(price_tier, price_complaints, complaint_rate, actual_review_count, product['price'])
        
        st.markdown(f'<div class="warning-box">{price_strategy}</div>', unsafe_allow_html=True)
        
        st.divider()
        
        # Ingredients Overview - Updated Visual Design
        st.subheader("Ingredients Overview")
        
        ingredients_text = product.get('ingredients', '')
        ingredients_info = check_ingredients(ingredients_text)
        function_tags = get_function_tags(ingredients_text)
        
        # Display function tags above ingredients - light gray style
        if function_tags:
            st.markdown("**Function Tags**")
            tags_html = ""
            for tag in function_tags:
                tags_html += f'<span class="function-tag">{tag.capitalize()}</span>'
            st.markdown(tags_html, unsafe_allow_html=True)
            st.write("")
        
        has_danger = len(ingredients_info['danger']) > 0
        has_star = len(ingredients_info['star']) > 0
        
        if has_danger:
            st.markdown('<div style="background-color: #FFEBEE; color: #C62828; padding: 10px 16px; border-radius: 8px; font-weight: 700; font-size: 1.1rem; margin-bottom: 12px; border-left: 4px solid #EF5350;">Caution: Sensitizing Ingredients</div>', unsafe_allow_html=True)
            for name, desc in ingredients_info['danger']:
                # All text in black/dark gray, ingredient name bold
                st.markdown(f'<div class="ingredient-item"><span class="ingredient-name">{name}</span>: {desc}</div>', unsafe_allow_html=True)
        
        if has_star:
            st.markdown('<div style="background-color: #E8F5E9; color: #2E7D32; padding: 10px 16px; border-radius: 8px; font-weight: 700; font-size: 1.1rem; margin-bottom: 12px; border-left: 4px solid #66BB6A;">Star Performance Ingredients</div>', unsafe_allow_html=True)
            for name, desc in ingredients_info['star']:
                # All text in black/dark gray, ingredient name bold
                st.markdown(f'<div class="ingredient-item"><span class="ingredient-name">{name}</span>: {desc}</div>', unsafe_allow_html=True)
        
        if not has_danger and not has_star:
            st.info("No specific key ingredients detected in the formula.")
        
        st.divider()
        
        # Marketing Strategy
        st.subheader("Marketing Strategy")
        
        recommendation_rate = product.get('is_recommended', np.nan)
        if pd.isna(recommendation_rate) and 'is_recommended' in product_reviews.columns:
            recommendation_rate = product_reviews['is_recommended'].mean()
        
        strategies = []
        
        has_sale = (pd.notna(product.get('sale_price_usd')) and 
                   product['sale_price_usd'] > 0 and 
                   product['sale_price_usd'] < product['price'])
        
        if has_sale:
            original = product['price']
            sale = product['sale_price_usd']
            savings = original - sale
            strategies.append(f"Current Discount: Original ${original:.2f}, Now ${sale:.2f}, Save ${savings:.2f}")
            
            if product['rating'] < peer_avg['rating']:
                strategies.append("Discount Trap: Lower rating than average, promote with caution")
        
        if pd.notna(recommendation_rate):
            if recommendation_rate > 0.7:
                strategies.append(f"User Recommendation Rate: {recommendation_rate:.1%} - Strong Word of Mouth")
            elif recommendation_rate < 0.5:
                strategies.append(f"Low Recommendation Rate: {recommendation_rate:.1%} - Investigate Negative Reviews")
        
        # Check for specific ingredients in strategies
        text_lower = str(ingredients_text).lower()
        if any(kw in text_lower for kw in ['alcohol', 'denat', 'sd alcohol']):
            strategies.append("Marketing Tip: Highlight oil-control and refreshing feel. Avoid gentle or sensitive skin claims")
        
        if any(kw in text_lower for kw in ['hyaluronic', 'hyaluronan', 'sodium hyaluronate']):
            strategies.append("Marketing Tip: Emphasize deep hydration, perfect for dry seasons and mature skin")
        
        for strategy in strategies[:2]:
            st.markdown(f'<div class="strategy-card">{strategy}</div>', unsafe_allow_html=True)
        
        st.divider()
        
        # Skin Type Insights
        st.subheader("Skin Type Insights")
        
        skin_analysis = analyze_skin_types(product_reviews)
        
        if skin_analysis:
            dist_cols = st.columns(len(skin_analysis['distribution']))
            for idx, (skin_type, count) in enumerate(skin_analysis['distribution'].items()):
                with dist_cols[idx]:
                    pct = count / sum(skin_analysis['distribution'].values()) * 100
                    st.metric(skin_type, f"{count}", f"{pct:.1f}%")
            
            st.write("")
            
            dominant = skin_analysis['dominant']
            dominant_pct = skin_analysis['dominant_pct'] * 100
            
            insight_text = f"**Primary User Group:** {dominant} Skin ({dominant_pct:.1f}% of reviewers)"
            
            if skin_analysis['top_concern']:
                insight_text += f"\n\n**Common Concern:** {dominant} skin users frequently mention '{skin_analysis['top_concern']}'"
            
            if not skin_analysis['is_balanced']:
                insight_text += "\n\n*Note: Sample skin type distribution is imbalanced, for reference only.*"
            
            st.info(insight_text)
        else:
            st.caption("Skin type data not available for this product.")
        
        st.divider()
        
        # Sentiment Analysis
        st.write("**Positive Feedback Themes**")
        if pos_words:
            word_count = len(pos_words)
            cols = st.columns(min(word_count, 6))
            
            for idx, (word, count) in enumerate(pos_words.items()):
                col_idx = idx % len(cols)
                with cols[col_idx]:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #d4edda, #c3e6cb); padding: 20px 15px; border-radius: 12px; text-align: center; border-left: 5px solid #28a745; min-height: 80px; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                        <div style="font-size: 1.3rem; font-weight: 700; color: #155724; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width: 100%;">{word.capitalize()}</div>
                        <div style="font-size: 1rem; color: #155724; margin-top: 8px; font-weight: 500;">{count} mentions</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.caption("No dominant positive keywords detected")
        
        st.write("")
        
        st.write("**Negative Feedback Themes**")
        if neg_words:
            neg_cols = st.columns(min(len(neg_words), 6))
            
            for idx, (word, count) in enumerate(neg_words.items()):
                col_idx = idx % len(neg_cols)
                with neg_cols[col_idx]:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #f8d7da, #f5c6cb); padding: 20px 15px; border-radius: 12px; text-align: center; border-left: 5px solid #dc3545; min-height: 80px; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                        <div style="font-size: 1.3rem; font-weight: 700; color: #721c24; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width: 100%;">{word.capitalize()}</div>
                        <div style="font-size: 1rem; color: #721c24; margin-top: 8px; font-weight: 500;">{count} mentions</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.caption("No significant negative keywords detected")
        
        
        # Marketing Copy Generator
        st.markdown('<hr style="margin: 32px 0 24px 0; border: none; border-top: 1px solid #e0e0e0;">', unsafe_allow_html=True)
        st.subheader("Final Marketing Recommendation")
        st.caption("Generate final marketing recommendation based on product analysis data")

        if st.button("Generate Final Recommendation", key="generate_copy_btn", type="primary", use_container_width=True):
            with st.spinner("Generating final recommendation..."):
                marketing_copy = generate_marketing_copy(
                    product, product_reviews, score_details, price_tier,
                    ingredients_info, skin_analysis, pos_words, neg_words,
                    peer_avg, actual_review_count
                )
                st.session_state.generated_copy = marketing_copy
                st.session_state.show_copy = True

        if st.session_state.get('show_copy', False) and 'generated_copy' in st.session_state:
            st.markdown(f'<div class="marketing-copy-box">{st.session_state.generated_copy}</div>', unsafe_allow_html=True)

        st.divider()

        # Floating Return Button
        st.markdown('<div class="floating-button">', unsafe_allow_html=True)
        if st.button("Return to Product List", type="secondary"):
            st.session_state.show_analysis = False
            st.session_state.selected_product = None
            st.session_state.need_rerun = True
        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.info("Select a product from the filtered list above to view detailed market analysis and promotion recommendations.")