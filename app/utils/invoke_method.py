    async def invoke(self, prompt: str, **kwargs) -> str:
        """
        Invoke the LLM with caching.
        
        Args:
            prompt: The prompt to send to the LLM
            **kwargs: Additional arguments for the LLM
            
        Returns:
            The LLM response
        """
        self.total_calls += 1
        
        # If caching is enabled, try to get from cache
        if self.cache_enabled:
            cache_key = self._get_cache_key(prompt)
            if cache_key in LLM_CACHE:
                self.cache_hits += 1
                logger.info(f"Cache hit ({self.cache_hits}/{self.total_calls})")
                return LLM_CACHE[cache_key]
        
        # No cache hit, call the LLM
        try:
            start_time = time.time()
            
            if self.llm is None:
                # Return a simulated response if no LLM is available
                response = self._get_simulated_response(prompt)
            elif hasattr(self.llm, 'ainvoke'):
                # For async LLMs with LangChain's new interface
                try:
                    response = await self.llm.ainvoke(prompt, **kwargs)
                    # Check if response is None or doesn't have expected structure
                    if response is None:
                        logger.warning("LLM returned None response")
                        response = self._get_simulated_response(prompt)
                except Exception as inner_e:
                    logger.error(f"Error in ainvoke method: {str(inner_e)}")
                    response = self._get_simulated_response(prompt)
            elif hasattr(self.llm, 'agenerate'):
                # For async LLMs with LangChain's older interface
                result = await self.llm.agenerate([prompt], **kwargs)
                response = result.generations[0][0].text
            elif hasattr(self.llm, 'invoke'):
                # For sync LLMs with new interface
                try:
                    response = self.llm.invoke(prompt, **kwargs)
                    # Check if response is None or doesn't have expected structure
                    if response is None:
                        logger.warning("LLM returned None response")
                        response = self._get_simulated_response(prompt)
                except Exception as inner_e:
                    logger.error(f"Error in invoke method: {str(inner_e)}")
                    response = self._get_simulated_response(prompt)
            elif hasattr(self.llm, 'generate'):
                # For sync LLMs with older interface
                result = self.llm.generate([prompt], **kwargs)
                response = result.generations[0][0].text
            elif hasattr(self.llm, '__call__'):
                # Fall back to __call__ for older LLM interfaces
                response = self.llm(prompt, **kwargs)
            else:
                # Can't find a method to call, use simulated response
                logger.warning(f"No compatible invoke method found for LLM of type {type(self.llm)}")
                response = self._get_simulated_response(prompt)
            
            # Log time taken for LLM call
            elapsed_time = time.time() - start_time
            logger.info(f"LLM call took {elapsed_time:.2f} seconds")
            
            # Cache the response
            if self.cache_enabled:
                LLM_CACHE[cache_key] = response
                
                # Periodically save the cache
                if len(LLM_CACHE) % 10 == 0:
                    self._save_cache()
            
            return response
            
        except Exception as e:
            logger.error(f"Error invoking LLM: {str(e)}")
            return self._get_simulated_response(prompt)
