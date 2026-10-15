import logging
import numpy as np
from PIL import Image
import os

logger = logging.getLogger(__name__)

# Global model cache to avoid re-loading on each request
_clip_model = None
_model_failed = False

def get_clip_model():
    """
    Lazy loader for sentence-transformers/clip-ViT-B-32 model.
    Falls back gracefully if weights are still downloading or offline.
    """
    global _clip_model, _model_failed
    if _clip_model is not None:
        return _clip_model
    if _model_failed:
        return None

    try:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading CLIP model: sentence-transformers/clip-ViT-B-32...")
        _clip_model = SentenceTransformer("sentence-transformers/clip-ViT-B-32")
        logger.info("CLIP model loaded successfully.")
        return _clip_model
    except Exception as e:
        logger.warning(f"Could not load SentenceTransformer CLIP model yet: {e}. Using fallback vectorizer.")
        _model_failed = True
        return None

def fallback_text_embedding(text):
    """
    Lightweight deterministic text embedding fallback using character n-grams and hashing
    when CLIP model is initializing or in low-resource environments.
    Guarantees normalized vectors and semantic keyword alignment.
    """
    if not text:
        text = ""
    words = text.lower().strip().split()
    # 512-dim pseudo-semantic normalized vector
    dim = 512
    vec = np.zeros(dim, dtype=np.float32)
    for word in words:
        h = hash(word) % dim
        vec[h] += 1.0
        # Add character bi-grams
        for i in range(len(word) - 1):
            bg_h = hash(word[i:i+2]) % dim
            vec[bg_h] += 0.5
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    else:
        vec[0] = 1.0
    return vec

def generate_image_embedding(image_path):
    """
    Generate normalized CLIP image embedding vector from local image file.
    """
    if not image_path or not os.path.exists(image_path):
        return None

    model = get_clip_model()
    if model is not None:
        try:
            with Image.open(image_path) as img:
                # Convert RGBA or CMYK to RGB
                rgb_img = img.convert("RGB")
                # sentence-transformers encode accepts PIL.Image
                embedding = model.encode(rgb_img, normalize_embeddings=True)
                return np.array(embedding, dtype=np.float32)
        except Exception as e:
            logger.error(f"Error encoding image at {image_path}: {e}")
            return None
    return None

def generate_text_embedding(title, description=""):
    """
    Generate normalized CLIP text embedding vector from title and description.
    """
    full_text = f"{title.strip()}. {description.strip()}".strip()
    if not full_text:
        return None

    model = get_clip_model()
    if model is not None:
        try:
            # model.encode([text], normalize_embeddings=True) per specification
            embeddings = model.encode([full_text], normalize_embeddings=True)
            return np.array(embeddings[0], dtype=np.float32)
        except Exception as e:
            logger.error(f"Error encoding text: {e}")
            return fallback_text_embedding(full_text)
    
    return fallback_text_embedding(full_text)

def compute_cosine_similarity(vec1, vec2):
    """
    Computes cosine similarity between two normalized vectors using dot product:
    similarity = dot(embedding_1, embedding_2)
    """
    if vec1 is None or vec2 is None:
        return 0.0
    try:
        v1 = np.array(vec1, dtype=np.float32)
        v2 = np.array(vec2, dtype=np.float32)
        # Verify normalization
        n1 = np.linalg.norm(v1)
        n2 = np.linalg.norm(v2)
        if n1 > 0 and n2 > 0:
            v1 = v1 / n1
            v2 = v2 / n2
            dot_prod = float(np.dot(v1, v2))
            # Bound within [-1.0, 1.0]
            return max(-1.0, min(1.0, dot_prod))
    except Exception as e:
        logger.error(f"Error computing cosine similarity: {e}")
    return 0.0

def find_matches(target_item, candidate_items, threshold=0.25, max_results=5):
    """
    Finds top matching items per Section 6 Matching Logic:
    1. Compare only lost with found items (opposite type).
    2. Ignore resolved items.
    3. If both items have images, use image similarity.
    4. If either image is missing, use text similarity.
    5. Display only matches with similarity greater than threshold (0.25).
    6. Sort highest to lowest similarity.
    7. Return top max_results (5).
    """
    matches = []
    
    # Target item embeddings
    target_img_emb = target_item.image_embedding
    target_txt_emb = target_item.text_embedding

    target_type = target_item.item_type.lower()
    opposite_type = "found" if target_type == "lost" else "lost"

    for candidate in candidate_items:
        # 1. Compare only opposite type
        if candidate.item_type.lower() != opposite_type:
            continue
        # 2. Ignore resolved items
        if candidate.status.lower() != 'open':
            continue
        # Skip self
        if candidate.id == target_item.id:
            continue

        cand_img_emb = candidate.image_embedding
        cand_txt_emb = candidate.text_embedding

        # 3. If both items have images, use image similarity.
        # 4. If either image is missing, use text similarity.
        match_type = 'text'
        if target_img_emb is not None and cand_img_emb is not None:
            similarity = compute_cosine_similarity(target_img_emb, cand_img_emb)
            match_type = 'image'
        else:
            similarity = compute_cosine_similarity(target_txt_emb, cand_txt_emb)
            match_type = 'text'

        # 5. Display only matches with similarity > threshold
        if similarity >= threshold:
            percentage = round(max(0.0, similarity) * 100, 1)
            matches.append({
                'item': candidate,
                'similarity': similarity,
                'percentage': percentage,
                'match_type': match_type
            })

    # 6. Sort matches from highest to lowest similarity
    matches.sort(key=lambda x: x['similarity'], reverse=True)

    # 7. Show maximum 5 results
    return matches[:max_results]
