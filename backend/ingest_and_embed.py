import pandas as pd
import re
import time
import os
from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel

# --- Configuration ---
# It's best practice to get these from environment variables
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOCATION = os.getenv("GCP_LOCATION", "us-central1")
MODEL_NAME = "text-embedding-004"

# --- Input/Output Paths ---
CSV_PATH = "resources/SB_publication_PMC.csv" # The CSV file with publication titles and links
OUTPUT_PATH = "processed_data/nasa_publications_with_embeddings.jsonl" # The output file

def preprocess_text(text: str) -> str:
    """
    A simple function to clean text data for embedding.
    - Lowercases text
    - Removes bracketed text (like citations)
    - Normalizes whitespace
    """
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'\[.*?\]', '', text)  # Remove text in brackets [like this]
    text = re.sub(r'\s+', ' ', text).strip()  # Remove extra whitespace
    return text

def generate_embeddings_in_batches(texts: list[str], model: TextEmbeddingModel, batch_size: int = 5) -> list:
    """
    Generates embeddings for a list of texts in batches to respect API limits.

    Args:
        texts: A list of strings to embed.
        model: An initialized TextEmbeddingModel instance.
        batch_size: The number of texts to process in each API call.

    Returns:
        A list of embedding vectors. Returns an empty list for failed texts.
    """
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        try:
            # The API returns a list of TextEmbedding objects
            embeddings_batch = model.get_embeddings(batch)
            # We extract the 'values' attribute from each object
            all_embeddings.extend([e.values for e in embeddings_batch])
            print(f"Embedded batch {i//batch_size + 1}...")
            # A small delay can help with rate limiting in large-scale jobs
            time.sleep(1)
        except Exception as e:
            print(f"An error occurred in batch {i//batch_size + 1}: {e}")
            # Add empty embeddings for the failed batch to maintain index alignment
            all_embeddings.extend([[] for _ in batch])
    return all_embeddings

def main():
    """Main function to run the data ingestion and embedding pipeline."""
    # Check for environment variables
    if not PROJECT_ID:
        print("Error: GCP_PROJECT_ID environment variable not set.")
        return

    # Check for Google credentials
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print("Error: GOOGLE_APPLICATION_CREDENTIALS environment variable not set.")
        return

    # 1. Initialize Vertex AI
    try:
        print(f"Initializing Vertex AI for project '{PROJECT_ID}' in location '{LOCATION}'...")
        aiplatform.init(project=PROJECT_ID, location=LOCATION)
        embedding_model = TextEmbeddingModel.from_pretrained(MODEL_NAME)
        print(f"Loaded embedding model '{MODEL_NAME}'.")
    except Exception as e:
        print(f"Error initializing Vertex AI or loading model: {e}")
        return

    # 2. Load and Preprocess Data
    print(f"Loading data from '{CSV_PATH}'...")
    try:
        df = pd.read_csv(CSV_PATH)
        print("First few rows of loaded data:")
        print(df.head())
        # Standardize column names for consistency
        df.rename(columns={'Title': 'title', 'Link': 'link'}, inplace=True)
        if 'title' not in df.columns:
            print("Error: CSV must contain a 'Title' column.")
            return
    except FileNotFoundError:
        print(f"Error: The file '{CSV_PATH}' was not found.")
        return
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return

    print("Preprocessing titles and creating embedding input...")
    df['embedding_input'] = df['title'].fillna('').apply(preprocess_text)

    # 3. Generate Embeddings
    print(f"\nGenerating embeddings for {len(df)} documents using '{MODEL_NAME}'...")
    texts_to_embed = df['embedding_input'].tolist()
    embeddings = generate_embeddings_in_batches(texts_to_embed, embedding_model)
    df['embedding'] = embeddings

    # 4. Save Results
    df_successful = df[df['embedding'].apply(lambda x: len(x) > 0)].copy()
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df_successful.drop(columns=['embedding_input'], inplace=True)
    df_successful.to_json(OUTPUT_PATH, orient='records', lines=True)
    print(f"\nSuccessfully generated embeddings for {len(df_successful)} documents.")
    print(f"Processed data with embeddings saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()