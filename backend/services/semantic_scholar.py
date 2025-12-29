"""
Semantic Scholar API Service
Handles academic paper search with rate limiting.
"""

import asyncio
import time
import httpx
from typing import Optional
from datetime import datetime

from config import semantic_scholar_config
from utils.logger import logger


class SemanticScholarService:
    """Semantic Scholar API client with rate limiting"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = semantic_scholar_config.BASE_URL
        self._last_request_time: Optional[float] = None
        self._lock = asyncio.Lock()
        self._min_interval = 1.0 / semantic_scholar_config.RATE_LIMIT_RPS
        self._timeout = semantic_scholar_config.REQUEST_TIMEOUT
        self._paper_fields = semantic_scholar_config.PAPER_FIELDS
        self._max_authors = semantic_scholar_config.MAX_AUTHORS_DISPLAY
        self._backoff_time = 5.0
        self._max_retries = 2
    
    async def _wait_for_rate_limit(self):
        """Ensure request interval satisfies rate limit"""
        async with self._lock:
            if self._last_request_time is not None:
                now = time.time()
                elapsed = now - self._last_request_time
                if elapsed < self._min_interval:
                    wait_time = self._min_interval - elapsed
                    await asyncio.sleep(wait_time)
    
    def _record_request_time(self):
        """Record request time after completion"""
        self._last_request_time = time.time()
    
    async def search_papers(
        self,
        query: str,
        limit: int = None,
        year_range: Optional[str] = None,
        fields_of_study: Optional[str] = None
    ) -> dict:
        """Search for academic papers"""
        if limit is None:
            limit = semantic_scholar_config.DEFAULT_SEARCH_LIMIT
        
        logger.separator("semantic_scholar", "Starting paper search")
        
        params = {
            "query": query,
            "limit": limit,
            "fields": self._paper_fields
        }
        
        if year_range:
            params["year"] = year_range
        
        if fields_of_study:
            params["fieldsOfStudy"] = fields_of_study
        
        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        
        # Request logic with retry
        last_error = None
        for attempt in range(self._max_retries + 1):
            # Wait for rate limit
            await self._wait_for_rate_limit()
            
            start_time = time.time()
            
            try:
                logger.api_call_start("semantic_scholar", "paper/search", {
                    **params,
                    "attempt": attempt + 1,
                })
                
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.get(
                        f"{self.base_url}/paper/search",
                        params=params,
                        headers=headers
                    )
                    
                    elapsed_ms = (time.time() - start_time) * 1000
                    
                    # Record request time regardless of success or failure
                    self._record_request_time()
                    
                    logger.debug("semantic_scholar", f"HTTP response status: {response.status_code}", {
                        "elapsed_ms": f"{elapsed_ms:.2f}",
                        "attempt": attempt + 1,
                    })
                    
                    # Handle 429 error - retry
                    if response.status_code == 429:
                        if attempt < self._max_retries:
                            backoff = self._backoff_time * (attempt + 1)
                            logger.warning("semantic_scholar", f"429 Rate Limit, retrying in {backoff}s")
                            await asyncio.sleep(backoff)
                            continue
                        else:
                            logger.error("semantic_scholar", "429 Rate Limit, max retries reached")
                            return {
                                "success": False,
                                "error": "API rate limit exceeded. Please try again later.",
                                "papers": []
                            }
                    
                    response.raise_for_status()
                    data = response.json()
                    
                    # Process data and extract authors
                    papers = []
                    for paper in data.get("data", []):
                        authors = paper.get("authors") or []
                        author_names = [a.get("name") or "" for a in authors[:self._max_authors]]
                        if len(authors) > self._max_authors:
                            author_names.append("et al.")
                        
                        papers.append({
                            "title": paper.get("title") or "",
                            "authors": ", ".join(author_names),
                            "year": paper.get("year") or "",
                            "venue": paper.get("venue") or "",
                            "tldr": (paper.get("tldr") or {}).get("text") or "",
                            "abstract": paper.get("abstract") or "",
                            "citationCount": paper.get("citationCount"),
                            "influentialCitationCount": paper.get("influentialCitationCount")
                        })
                    
                    logger.api_call_end("semantic_scholar", "paper/search", True)
                    logger.separator("semantic_scholar", "Paper search complete")
                    
                    return {
                        "success": True,
                        "total": data.get("total", 0),
                        "papers": papers
                    }
                    
            except httpx.TimeoutException:
                self._record_request_time()
                logger.error("semantic_scholar", "Request timeout")
                last_error = "Request timeout. Please try again later."
                if attempt < self._max_retries:
                    await asyncio.sleep(self._backoff_time)
                    continue
            except httpx.HTTPStatusError as e:
                self._record_request_time()
                logger.error("semantic_scholar", f"HTTP Error: {e.response.status_code}")
                return {
                    "success": False,
                    "error": f"API request failed: {e.response.status_code}",
                    "papers": []
                }
            except Exception as e:
                self._record_request_time()
                logger.error("semantic_scholar", f"Search exception: {str(e)}")
                last_error = f"Search failed: {str(e)}"
                if attempt < self._max_retries:
                    await asyncio.sleep(self._backoff_time)
                    continue
        
        return {
            "success": False,
            "error": last_error or "Request failed",
            "papers": []
        }


_service_instance: Optional[SemanticScholarService] = None


def get_semantic_scholar_service(api_key: Optional[str] = None) -> SemanticScholarService:
    """Get Semantic Scholar service singleton"""
    global _service_instance
    if _service_instance is None:
        _service_instance = SemanticScholarService(api_key)
    return _service_instance
