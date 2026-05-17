"""
Memory storage and retrieval service using pgvector cosine similarity.
Uses a lightweight local sentence-transformer for embeddings in Phase 2.
Swapped for OpenAI embeddings in Phase 6.
"""
import logging
import numpy as np
from django.db import connection

logger = logging.getLogger(__name__)

# Lazy-load the embedding model so it doesn't block startup
_embedder = None


def get_embedder():
    global _embedder
    if _embedder is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedder = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info('SentenceTransformer loaded: all-MiniLM-L6-v2')
        except Exception as e:
            logger.warning(f'Could not load SentenceTransformer: {e}. Embeddings will be null.')
            _embedder = None
    return _embedder


def embed_text(text: str):
    """Return a list of 384 floats or None if embedder unavailable."""
    embedder = get_embedder()
    if embedder is None:
        return None
    try:
        vector = embedder.encode(text, normalize_embeddings=True)
        return vector.tolist()
    except Exception as e:
        logger.error(f'Embedding failed: {e}')
        return None


def store_memory(agent_id: int, text: str, importance: float = 0.5,
                 memory_type: str = 'experience', tick: int = 0,
                 sim_day: int = 1, sim_year: int = 1):
    """
    Store a memory for an agent with an optional embedding.
    Returns the created AgentMemory instance.
    """
    from apps.memory.models import AgentMemory

    embedding = embed_text(text)

    memory = AgentMemory.objects.create(
        agent_id=agent_id,
        memory_text=text,
        embedding=embedding,
        importance=importance,
        memory_type=memory_type,
        tick_number=tick,
        simulation_day=sim_day,
        simulation_year=sim_year,
    )
    return memory


def retrieve_similar_memories(agent_id: int, query_text: str, top_k: int = 5):
    """
    Retrieve the top_k most relevant memories for an agent
    using cosine similarity on embeddings.
    Falls back to importance-ordered retrieval if no embeddings available.
    """
    from apps.memory.models import AgentMemory

    query_embedding = embed_text(query_text)

    if query_embedding is None:
        # Fallback: return most important memories
        return AgentMemory.objects.filter(
            agent_id=agent_id
        ).order_by('-importance', '-tick_number')[:top_k]

    # Use pgvector cosine similarity operator <=>
    # Lower value = more similar (cosine distance)
    memories = AgentMemory.objects.filter(
        agent_id=agent_id,
        embedding__isnull=False,
    ).order_by(
        models_cosine_distance('embedding', query_embedding)
    )[:top_k]

    return memories


def models_cosine_distance(field_name: str, vector: list):
    """
    Returns an OrderBy expression for pgvector cosine distance.
    Uses raw SQL via RawSQL for compatibility.
    """
    from django.db.models.expressions import RawSQL
    vector_str = '[' + ','.join(str(v) for v in vector) + ']'
    return RawSQL(f'"{field_name}" <=> %s::vector', (vector_str,))


def retrieve_memories_by_importance(agent_id: int, top_k: int = 10):
    """Simple importance-ranked retrieval without embedding search."""
    from apps.memory.models import AgentMemory
    return AgentMemory.objects.filter(
        agent_id=agent_id
    ).order_by('-importance', '-tick_number')[:top_k]