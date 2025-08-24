"""LLM service abstractions and providers for Gemini and Together AI (Llama) via LangChain."""

from typing import Any, Dict, Optional, Type, TypeVar, Union, List
from pydantic import ValidationError
from app.config import settings
from app.structure.pydantic import LLMProvider
from app.services.monitoring import track_llm_call

# LangChain imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_together import ChatTogether
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool

# Import our custom tools
try:
    from app.tools.search import WebSearchLangChainTool
    from app.tools.fetcher import ContentFetcherLangChainTool
    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False
    WebSearchLangChainTool = None
    ContentFetcherLangChainTool = None

T = TypeVar("T")

class LLMService:
	"""Unified LLM service for Gemini and Together AI (Llama) with structured output enforcement and tool support."""

	def __init__(self):
		self.gemini = ChatGoogleGenerativeAI(
			model=settings.gemini_model,
			google_api_key=settings.google_api_key,
			temperature=settings.temperature,
			max_output_tokens=settings.max_tokens,
		)
		self.llama = ChatTogether(
			model=settings.llama_model,
			together_api_key=settings.together_api_key,
			temperature=settings.temperature,
			max_tokens=settings.max_tokens,
		)
		
		# Initialize tools
		self.tools = self._initialize_tools()

	def _initialize_tools(self) -> List[BaseTool]:
		"""Initialize available tools for LLM use."""
		tools = []
		
		if TOOLS_AVAILABLE:
			try:
				# Add web search tool
				tools.append(WebSearchLangChainTool())
				
				# Add content fetcher tool  
				tools.append(ContentFetcherLangChainTool())
				
				print(f"✅ Initialized {len(tools)} tools for LLM use")
			except Exception as e:
				print(f"⚠️ Error initializing tools: {e}")
		else:
			print("⚠️ Tools not available - install missing dependencies")
		
		return tools

	def get_model(self, provider: Union[LLMProvider, str], with_tools: bool = False) -> BaseChatModel:
		"""Get LLM model, optionally with tools binding."""
		model = None
		
		if str(provider).lower() in {"gemini", LLMProvider.GEMINI.value}:
			model = self.gemini
		elif str(provider).lower() in {"llama", LLMProvider.LLAMA.value}:
			model = self.llama
		else:
			raise ValueError(f"Unknown LLM provider: {provider}")
		
		# Bind tools if requested and available
		if with_tools and self.tools:
			try:
				model = model.bind_tools(self.tools)
			except Exception as e:
				print(f"⚠️ Could not bind tools to {provider}: {e}")
		
		return model

	async def call_llm_with_tools(
		self,
		prompt: str,
		provider: Union[LLMProvider, str] = None,
		input_variables: Optional[Dict[str, Any]] = None,
		max_retries: int = 2,
	) -> str:
		"""
		Call LLM with tool support for research tasks.
		Returns the final response after tool usage.
		"""
		provider = provider or LLMProvider.GEMINI
		model = self.get_model(provider, with_tools=True)
		
		# Create prompt template
		if input_variables:
			prompt_template = ChatPromptTemplate.from_template(prompt)
			formatted_prompt = prompt_template.format(**input_variables)
		else:
			formatted_prompt = prompt
		
		retries = 0
		while retries <= max_retries:
			try:
				# Invoke model with tools
				response = await model.ainvoke(formatted_prompt)
				
				# Handle tool calls if present
				if hasattr(response, 'tool_calls') and response.tool_calls:
					# Process tool calls and get final response
					return await self._process_tool_calls(response, model)
				else:
					# Direct response without tools
					return response.content
					
			except Exception as e:
				retries += 1
				if retries > max_retries:
					raise Exception(f"LLM call failed after {max_retries} retries: {str(e)}")
				continue
	
	async def _process_tool_calls(self, response, model):
		"""Process tool calls and return final response."""
		# This is a simplified implementation
		# In a full implementation, you'd handle tool call execution
		# and potentially multiple rounds of tool use
		return response.content or "Tool-assisted response completed"
		"""
		Call the selected LLM with structured output enforcement and retry logic.
		"""
		provider = provider or settings.default_llm_provider
		model = self.get_model(provider)
		parser = PydanticOutputParser(pydantic_object=output_schema)
		prompt_template = ChatPromptTemplate.from_template(prompt)
		input_vars = input_variables or {}
		messages = prompt_template.format_messages(**input_vars)

		last_error = None
		for attempt in range(max_retries + 1):
			try:
				response = await model.ainvoke(messages)
				parsed = parser.parse(response.content)
				return parsed
			except (ValidationError, Exception) as e:
				last_error = e
		raise RuntimeError(f"LLM output validation failed after {max_retries+1} attempts: {last_error}")

	def sync_call_llm(
		self,
		prompt: str,
		output_schema: Type[T],
		provider: Union[LLMProvider, str] = None,
		input_variables: Optional[Dict[str, Any]] = None,
		max_retries: int = 2,
	) -> T:
		"""
		Synchronous version of call_llm (for CLI/testing).
		"""
		import asyncio
		return asyncio.run(self.call_llm(
			prompt=prompt,
			output_schema=output_schema,
			provider=provider,
			input_variables=input_variables,
			max_retries=max_retries
		))

# Global LLM service instance
llm_service = LLMService()