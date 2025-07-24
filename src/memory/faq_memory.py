# Copyright (c) Microsoft. All rights reserved.

import logging
from azure.cosmos import CosmosClient, PartitionKey
import asyncio
import json
import os
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Annotated, Optional, List
from uuid import uuid4

from semantic_kernel.connectors.ai.open_ai import AzureTextEmbedding
# InMemoryCollection is used for in-memory vector store
from semantic_kernel.connectors.in_memory import InMemoryCollection
from semantic_kernel.data.vector import VectorStoreField, vectorstoremodel

# InMemoryCollection is used for in-memory vector store
# from semantic_kernel.connectors.memory import CosmosNoSqlCollection
# from semantic_kernel.data.vector import (
#     SearchType,
#     VectorSearchProtocol,
#     VectorStoreCollection,
#     VectorStoreField,
#     vectorstoremodel,
# )

# This is an example of a vector store and collection using Azure OpenAI embeddings
# Make sure to have your environment variables set up or provide credentials directly
# Using Azure OpenAI endpoint from your Azure AI Foundry project

# Load environment variables or use direct configuration
azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
embedding_deployment = os.getenv("EMBEDDING_DEPLOYMENT_NAME")
# azure_cosmosdb_nosql_url = os.getenv("AZURE_COSMOS_DB_NO_SQL_URL", "https://aivectorstore.documents.azure.com:443/")
# azure_cosmosdb_nosql_database_name = os.getenv("AZURE_COSMOS_DB_NO_SQL_DATABASE_NAME", "quickstartmemory")
# azure_cosmosdb_nosql_key = os.getenv("AZURE_COSMOS_DB_NO_SQL_KEY")

# cosmos_client = CosmosClient(
#     url=azure_cosmosdb_nosql_url,
#     credential=azure_cosmosdb_nosql_key,)
# # "AccountEndpoint=https://aivectorstore.documents.azure.com:443/;AccountKey=)


embedder = AzureTextEmbedding(
    api_key=azure_openai_api_key,
    deployment_name=embedding_deployment,
    endpoint=azure_openai_endpoint,
    service_id="azure_embedding"
)

# Next, you need to define your data structure
# In this case, we are using a dataclass to define our data structure
# you can also use a pydantic model, or a vanilla python class, see "data_models.py" for more examples
# Inside the model we define which fields we want to use, and which fields are vectors
# and for vector fields we define what kind of index we want to use, and what distance function we want to use
# This has been done in constants here for simplicity, but you can also define them in the model itself
# Next we create three records using that model


@vectorstoremodel(collection_name="starbucks_qna")
@dataclass
class DataModel:
    content: Annotated[str, VectorStoreField("data")]
    id: Annotated[str, VectorStoreField("key")] = field(default_factory=lambda: str(uuid4()))
    vector: Annotated[
        list[float] | str | None,
        VectorStoreField("vector", dimensions=1536),
    ] = None
    question: Annotated[str, VectorStoreField("data", is_full_text_indexed=True)] = ""
    answer: Annotated[str, VectorStoreField("data", is_full_text_indexed=True)] = ""
    category: Annotated[str, VectorStoreField("data", is_indexed=True)] = "general"
    item_type: Annotated[str, VectorStoreField("data", is_indexed=True)] = "question"
    tags: Annotated[str, VectorStoreField("data", is_indexed=True)] = ""

    def __post_init__(self):
        if self.vector is None:
            self.vector = self.content


# Load data from JSON file
def load_records_from_json():
    json_file_path = os.path.join(os.path.dirname(__file__), "cosmosdb-qna-items.json")
    
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    records = []
    for item in data:
        # Convert tags list to string if it exists
        tags_str = ", ".join(item.get("tags", [])) if item.get("tags") else ""
        
        # Get question and answer fields
        question = item.get("question", "")
        answer = item.get("answer", "")
        
        # Create content by combining question and answer for vector search
        content = f"Q: {question}\nA: {answer}" if question and answer else question or answer
        
        record = DataModel(
            content=content,
            id=item["id"],
            question=question,
            answer=answer,
            category=item.get("category", "general"),
            item_type=item.get("type", "question"),
            tags=tags_str
        )
        records.append(record)
    
    return records


class FAQMemory:
    """
    FAQ Memory class for managing Q&A data with vector search capabilities.
    This class provides methods to initialize, search, and manage FAQ collections.
    """
    
    def __init__(self):
        """Initialize the FAQ Memory with default configuration."""
        logging.info("Initializing FAQ Memory")
        self.embedder = AzureTextEmbedding(
            api_key=azure_openai_api_key,
            deployment_name=embedding_deployment,
            endpoint=azure_openai_endpoint,
            service_id="azure_embedding"
        )
        self.collection = None
        self.records = load_records_from_json()
        self._initialized = False
    
    async def initialize(self) -> InMemoryCollection[str, DataModel]:
        """
        Initialize and return the FAQ collection.
        This method sets up the vector store collection and loads the data.
        
        Returns:
            InMemoryCollection: The initialized collection ready for use.
        """
        if not self._initialized:
            self.collection = InMemoryCollection[str, DataModel](
                record_type=DataModel,
                create_database=True,
                embedding_generator=self.embedder,
            )
            
            # Ensure collection exists and add data
            await self.collection.ensure_collection_exists()
            
            # Add records to the collection
            keys = await self.collection.upsert(self.records)
            print(f"FAQ Memory initialized with {len(keys)} records")
            self._initialized = True
            
        return self.collection
    
    async def get_collection(self) -> InMemoryCollection[str, DataModel]:
        """
        Get the FAQ collection, initializing it if necessary.
        
        Returns:
            InMemoryCollection: The FAQ collection ready for use.
        """
        if not self._initialized:
            await self.initialize()
        return self.collection

    async def search_faq(self, query: str, category_filter: Optional[str] = None, limit: int = 3, score: float = 0.19) -> List[DataModel]:
        """
        Search the FAQ collection for relevant answers.
        
        Args:
            query (str): The search query
            category_filter (Optional[str]): Filter by category (e.g., 'coffee', 'general')
            limit (int): Maximum number of results to return
            
        Returns:
            List[DataModel]: List of matching FAQ records
        """
        if not self._initialized:
            await self.initialize()
        
        # Prepare search options
        options = {
            "vector_property_name": "vector",
        }
        
        # Add category filter if specified
        if category_filter:
            options["filter"] = lambda x: x.category == category_filter
        
        # Perform the search
        search_results = await self.collection.search(
            values=query,
            **options,
        )

        results = []
        count = 0
        async for result in search_results.results:
            if result.score is not None and result.score >= score:
                continue
            if count >= limit:
                break
            results.append(result.record)
            count += 1
            logging.info(f"Found record: {result.record.id} with score: {result.score}")
        return results
    
    async def get_answer(self, query: str, category_filter: Optional[str] = None) -> Optional[str]:
        """
        Get the best answer for a query.
        
        Args:
            query (str): The search query
            category_filter (Optional[str]): Filter by category
            
        Returns:
            Optional[str]: The best matching answer or None if no good match found
        """
        results = await self.search_faq(query, category_filter, limit=1)
        
        if results:
            return results[0].answer
        return None
    
    async def add_faq(self, question: str, answer: str, category: str = "general", tags: List[str] = None) -> str:
        """
        Add a new FAQ item to the collection.
        
        Args:
            question (str): The question
            answer (str): The answer
            category (str): The category (default: "general")
            tags (List[str]): List of tags
            
        Returns:
            str: The ID of the added record
        """
        if not self._initialized:
            await self.initialize()
        
        tags_str = ", ".join(tags) if tags else ""
        content = f"Q: {question}\nA: {answer}"
        
        new_record = DataModel(
            content=content,
            question=question,
            answer=answer,
            category=category,
            item_type="question",
            tags=tags_str
        )
        
        keys = await self.collection.upsert([new_record])
        return keys[0] if keys else new_record.id
    
    async def close(self):
        """Close and cleanup the collection."""
        if self.collection and self._initialized:
            await self.collection.ensure_collection_deleted()
            self._initialized = False


# Global instance for use in server.py
_faq_memory_instance = None

async def get_faq_memory() -> FAQMemory:
    """
    Get or create the global FAQ memory instance.
    This function ensures singleton behavior for the FAQ memory.
    
    Returns:
        FAQMemory: The global FAQ memory instance
    """
    global _faq_memory_instance
    if _faq_memory_instance is None:
        _faq_memory_instance = FAQMemory()
        await _faq_memory_instance.initialize()
    return _faq_memory_instance


records = load_records_from_json()


async def main():
    """
    Main function demonstrating the FAQ Memory usage.
    This function shows how to use the FAQMemory class for searching and managing FAQ data.
    """
    print("-" * 30)
    print("FAQ Memory Demo")
    print("-" * 30)
    
    # Create and initialize FAQ memory
    faq_memory = FAQMemory()
    await faq_memory.initialize()
    
    # Search for coffee-related content
    query = "What does Hyunsuk do at Microsoft?"
    print(f"Searching for '{query}'")
    
    # Try searching with coffee filter first
    results = await faq_memory.search_faq(query, category_filter="coffee", limit=3)
    
    if not results:
        print("Nothing found with coffee filter, trying general search...")
        results = await faq_memory.search_faq(query, limit=3)
    
    if not results:
        print("Nothing found...")
    else:
        for i, result in enumerate(results, 1):
            print(f"Result {i}:")
            print(f"Category: {result.category}")
            print(f"Question: {result.question}")
            print(f"Answer: {result.answer[:100]}...")
            print("-" * 20)
    
    print("-" * 30)
    
    # Demonstrate getting a direct answer
    answer = await faq_memory.get_answer("popular drinks")
    if answer:
        print("Direct answer for 'popular drinks':")
        print(f"Answer: {answer[:100]}...")
    else:
        print("No direct answer found for 'popular drinks'")
    
    print("-" * 30)
    
    # Cleanup
    print("Cleaning up...")
    await faq_memory.close()
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
