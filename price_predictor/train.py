
import os
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers
import re

# File paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'app', 'utils', 'marketing_sample_for_ebay_com-ebay_com_product__20210101_20210331__30k_data.csv')
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'saved_model.keras')

def clean_price(price_str):
    if pd.isna(price_str):
        return None
    # Remove '$', ',', and potential other chars
    price_str = str(price_str)
    # Extract the first valid number found (handling potential ranges like "$10 - $20")
    # We take the first one as a simplification.
    match = re.search(r'(\d+\.?\d*)', price_str.replace(',', ''))
    if match:
        return float(match.group(1))
    return None

def load_and_preprocess():
    print(f"Loading data from {DATA_PATH}...")
    try:
        df = pd.read_csv(DATA_PATH, on_bad_lines='skip')
    except Exception as e:
        print(f"Error reading CSV: {e}")
        # Try with a different engine or delimiter if needed
        df = pd.read_csv(DATA_PATH, on_bad_lines='skip', engine='python') # Fallback

    
    # Keep only relevant columns
    df = df[['Title', 'Price']]
    
    # Drop missing values
    df = df.dropna()

    # Clean Title (remove non-ascii to avoid save errors on Windows)
    df['Title'] = df['Title'].apply(lambda x: re.sub(r'[^\x00-\x7F]+', '', str(x)))
    
    # Clean Price
    df['Price'] = df['Price'].apply(clean_price)
    df = df.dropna(subset=['Price'])
    
    print(f"Data loaded. Shape: {df.shape}")
    return df

def train_model():
    df = load_and_preprocess()
    
    titles = df['Title'].values
    prices = df['Price'].values
    
    # Vectorize text
    max_tokens = 10000
    output_sequence_length = 20
    
    vectorizer = layers.TextVectorization(
        max_tokens=max_tokens,
        output_mode='int',
        output_sequence_length=output_sequence_length
    )
    
    # Adapt vectorizer to the data
    vectorizer.adapt(titles)
    
    # Build Model
    # Embedding -> GlobalAverageBPooling -> Dense -> Dense
    
    model = tf.keras.Sequential([
        vectorizer,
        layers.Embedding(input_dim=max_tokens, output_dim=64, mask_zero=True),
        layers.GlobalAveragePooling1D(),
        layers.Dense(64, activation='relu'),
        layers.Dense(32, activation='relu'),
        layers.Dense(1) # Linear activation for regression
    ])
    
    model.compile(loss='mean_absolute_error',
                  optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
                  metrics=['mae'])
    
    # Train
    print("Starting training...")
    history = model.fit(
        titles, 
        prices,
        epochs=15, 
        batch_size=32,
        validation_split=0.2,
        verbose=1
    )
    
    # Save model
    model.save(MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")
    
    return model

if __name__ == "__main__":
    train_model()
