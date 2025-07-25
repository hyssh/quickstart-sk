# Copyright (c) Microsoft. All rights reserved.

import logging
import asyncio
import json
import os
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Annotated, Optional, List
from uuid import uuid4

from semantic_kernel.connectors.ai.open_ai import AzureTextEmbedding

from azure.identity import DefaultAzureCredential
from semantic_kernel.connectors.azure_cosmos_db import CosmosNoSqlCollection, CosmosNoSqlSettings
from semantic_kernel.data.vector import (
    SearchType,
    VectorSearchProtocol,
    VectorStoreCollection,
    VectorStoreField,
    vectorstoremodel,
)

# This is an example of a vector store and collection using Azure OpenAI embeddings
# Make sure to have your environment variables set up or provide credentials directly
# Using Azure OpenAI endpoint from your Azure AI Foundry project

from dotenv import load_dotenv  
load_dotenv()  # Load environment variables from .env file

# Load environment variables or use direct configuration
azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
embedding_deployment = os.getenv("EMBEDDING_DEPLOYMENT_NAME")

# Cosmos DB config for Caching
azure_cosmosdb_nosql_url = os.getenv("AZURE_COSMOS_DB_NO_SQL_URL")
azure_cosmosdb_nosql_database_name = os.getenv("AZURE_COSMOS_DB_NO_SQL_DATABASE_NAME")
azure_cosmosdb_nosql_key = os.getenv("AZURE_COSMOS_DB_NO_SQL_KEY")

CosmosNoSqlSettings(
    key=azure_cosmosdb_nosql_key,
    url=azure_cosmosdb_nosql_url,
    database_name=azure_cosmosdb_nosql_database_name,
)


# cosmos_client = CosmosClient(
#     url=azure_cosmosdb_nosql_url,
#     credential=azure_cosmosdb_nosql_key,)
# # "AccountEndpoint=https://aivectorstore.documents.azure.com:443/;AccountKey=")


# Assign user to CosmosNoSQL database as DocumentDB Account Contributor
# credential = DefaultAzureCredential()
# cosmos_client = CosmosClient(azure_cosmosdb_nosql_url, credential=credential)

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
    embedding: Annotated[
        list[float] | str | None,
        VectorStoreField('vector', dimensions=1536, distance_function="cosine_similarity", index_kind="disk_ann"),
    ] = None
    question: Annotated[str, VectorStoreField("data", is_full_text_indexed=True)] = ""
    answer: Annotated[str, VectorStoreField("data", is_full_text_indexed=True)] = ""
    category: Annotated[str, VectorStoreField("data", is_indexed=True)] = ""
    tags: Annotated[str, VectorStoreField("data", is_indexed=True)] = ""



# Load data from JSON file
def load_records_from_json():
    json_file_path = os.path.join(os.path.dirname(__file__), "cosmosdb-qna-items.json")
    
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    records = []
    for item in data:
        # Convert tags list to string if it exists
        tags_str = ", ".join(item.get("tags", [])) if item.get("tags") else ""

        # Get question and answer fields, always coerce None to empty string
        question = item.get("question", "") or ""
        answer = item.get("answer", "") or ""

        # Compose content: use item["content"] if present and non-empty, else build from question/answer
        content = item.get("content", "")
        if not content or not isinstance(content, str) or not content.strip():
            if question and answer:
                content = f"Question: {question}\nAnswer: {answer}"
            else:
                content = question or answer or ""

        # Always provide a string id, generate if missing
        record_id = str(item.get("id") or str(uuid4()))

        # Only add records with non-empty, non-whitespace content
        if isinstance(content, str) and content.strip():
            record = DataModel(
                content=content,
                id=record_id,
                question=question,
                answer=answer,
                category=item.get("category", "general") or "general",
                tags=tags_str,
                # Don't set embedding to None, let the system handle it
                embedding=[]  # Use empty list instead of None
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
    
    async def initialize(self) -> CosmosNoSqlCollection[str, DataModel]:
        """
        Initialize and return the FAQ collection.
        This method sets up the vector store collection and loads the data.
        
        Returns:
            CosmosNoSqlCollection: The initialized collection ready for use.
        """
        if not self._initialized:
            try:
                self.collection = CosmosNoSqlCollection[str, DataModel](
                    record_type=DataModel,
                    url=azure_cosmosdb_nosql_url,
                    key=azure_cosmosdb_nosql_key,                
                    collection_name="starbucksqna",
                    database_name=azure_cosmosdb_nosql_database_name,                
                    create_database=True,
                    embedding_generator=self.embedder,
                )
                
                # Ensure collection exists
                await self.collection.ensure_collection_exists()

                # Process records in smaller batches to avoid overwhelming the embedder
                batch_size = 5
                all_keys = []
                
                for i in range(0, len(self.records), batch_size):
                    batch = self.records[i:i + batch_size]
                    # Validate batch
                    valid_batch = [rec for rec in batch if isinstance(rec.content, str) and rec.content.strip()]
                    if valid_batch:
                        print(f"Processing batch {i//batch_size + 1} with {len(valid_batch)} records")
                        try:
                            batch_keys = await self.collection.upsert(valid_batch)
                            all_keys.extend(batch_keys)
                            print(f"Successfully processed batch {i//batch_size + 1}")
                        except Exception as e:
                            print(f"Error processing batch {i//batch_size + 1}: {str(e)}")
                            # Continue with next batch even if this one failed
                
                print(f"FAQ Memory initialized with {len(all_keys)} records out of {len(self.records)} total")
                self._initialized = True
            except Exception as e:
                print(f"Error initializing FAQ Memory: {str(e)}")
                raise
        return self.collection
    
    async def get_collection(self) -> CosmosNoSqlCollection[str, DataModel]:
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
            "vector_property_name": "embedding",  # Use the correct property name
        }
        
        # Add category filter if specified
        # if category_filter:
            # options["filter"] = lambda x: x.category == category_filter
            # options["filter"] = f"category == '{category_filter}'"
        
        # Perform the search
        search_results = await self.collection.search(
            values=query,
            **options,
        )

        results = []
        count = 0
        print(f"Searching for '{query}' with search_results '{search_results}'")
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
            tags=tags_str,
            embedding=None
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
