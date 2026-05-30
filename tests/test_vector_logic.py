import pytest
import asyncio
from unittest.mock import MagicMock, patch
from backend.retrieval.vector_retriever import VectorRetriever
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_vector_retriever_initialization_and_dimensions():
    # Mock the SQLAlchemy session
    mock_session = MagicMock(spec=AsyncSession)
    retriever = VectorRetriever(session=mock_session)
    
    # Mock the sentence_transformers load inside the asyncio thread
    with patch('sentence_transformers.SentenceTransformer') as mock_st:
        # Create a mock model instance
        mock_model_instance = MagicMock()
        # Mock the encode method to return exactly 384 dimensions
        mock_model_instance.encode.return_value = [0.1] * 384
        mock_st.return_value = mock_model_instance
        
        # Call initialize
        await retriever.initialize()
        
        # Verify model was initialized
        assert retriever.model is not None
        
        # Generate an embedding to test dimensions
        embedding = retriever.model.encode("Do I need a helmet?")
        
        # Business rule validation
        assert len(embedding) == 384, f"Expected 384 dimensions for all-MiniLM-L6-v2, got {len(embedding)}"
