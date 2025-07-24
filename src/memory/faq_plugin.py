# Copyright (c) Microsoft. All rights reserved.

from typing import Annotated
from semantic_kernel.functions import kernel_function
from semantic_kernel.kernel import Kernel
from .faq_memory import get_faq_memory, FAQMemory


class FAQPlugin:
    """
    Semantic Kernel plugin for FAQ functionality.
    This plugin provides FAQ search capabilities to the Azure AI Agent.
    """
    
    def __init__(self):
        """Initialize the FAQ plugin."""
        self.faq_memory: FAQMemory = None
    
    async def _ensure_memory_initialized(self):
        """Ensure the FAQ memory is initialized."""
        if self.faq_memory is None:
            self.faq_memory = await get_faq_memory()
    
    @kernel_function(
        description="Search for FAQ answers based on a user query",
        name="search_faq"
    )
    async def search_faq(
        self,
        query: Annotated[str, "The user's query to search for in the FAQ database"],
        category: Annotated[str, "Optional category filter (e.g., 'coffee', 'general', 'non-coffee')"] = None,
        limit: Annotated[int, "Maximum number of results to return"] = 3,
        score: Annotated[float, "Minimum score threshold for results"] = 0.21
    ) -> str:
        """
        Search the FAQ database for relevant answers.
        
        Args:
            query: The user's query
            category: Optional category filter
            limit: Maximum number of results to return
            
        Returns:
            Formatted string with FAQ results
        """
        await self._ensure_memory_initialized()
        
        try:
            results = await self.faq_memory.search_faq(query, category, limit, score)
            
            if not results:
                return f"No FAQ entries found for query: '{query}'"
            
            response = f"Found {len(results)} FAQ result(s) for '{query}':\n\n"
            
            for i, result in enumerate(results, 1):
                response += f"**Result {i}:**\n"
                response += f"Category: {result.category}\n"
                response += f"Question: {result.question}\n"
                response += f"Answer: {result.answer}\n"
                response += f"Score: {result.score}\n"
                if result.tags:
                    response += f"Tags: {result.tags}\n"
                response += "\n---\n\n"
            
            return response
            
        except Exception as e:
            return f"Error searching FAQ: {str(e)}"
    
    @kernel_function(
        description="Get the best answer for a specific question from the FAQ database",
        name="get_faq_answer"
    )
    async def get_faq_answer(
        self,
        query: Annotated[str, "The user's question to find the best answer for"],
        category: Annotated[str, "Optional category filter"] = None
    ) -> str:
        """
        Get the best matching answer for a query.
        
        Args:
            query: The user's question
            category: Optional category filter
            
        Returns:
            The best matching answer or a message if no answer found
        """
        await self._ensure_memory_initialized()
        
        try:
            answer = await self.faq_memory.get_answer(query, category)
            
            if answer:
                return f"FAQ Answer: {answer}"
            else:
                return f"No specific answer found in FAQ for: '{query}'"
                
        except Exception as e:
            return f"Error getting FAQ answer: {str(e)}"
    
    @kernel_function(
        description="Add a new FAQ entry to the database",
        name="add_faq_entry"
    )
    async def add_faq_entry(
        self,
        question: Annotated[str, "The question to add"],
        answer: Annotated[str, "The answer to the question"],
        category: Annotated[str, "The category for the FAQ entry"] = "general",
        tags: Annotated[str, "Comma-separated tags for the entry"] = ""
    ) -> str:
        """
        Add a new FAQ entry to the database.
        
        Args:
            question: The question
            answer: The answer
            category: The category (default: "general")
            tags: Comma-separated tags
            
        Returns:
            Confirmation message with the entry ID
        """
        await self._ensure_memory_initialized()
        
        try:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []
            
            entry_id = await self.faq_memory.add_faq(question, answer, category, tag_list)
            
            return f"Successfully added FAQ entry with ID: {entry_id}\nQuestion: {question}\nAnswer: {answer[:100]}..."
            
        except Exception as e:
            return f"Error adding FAQ entry: {str(e)}"


def create_faq_plugin() -> FAQPlugin:
    """
    Create and return a new FAQ plugin instance.
    
    Returns:
        FAQPlugin: A new FAQ plugin instance
    """
    return FAQPlugin()
