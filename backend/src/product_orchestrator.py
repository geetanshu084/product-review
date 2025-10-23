"""
Product Data Orchestrator
Orchestrates the complete flow: scrape → search competitors → search reviews → LLM structure → save → analyze
"""

import json
from typing import Dict, Optional, List
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from src.llm_provider import get_llm
from src.prompts import get_structured_extraction_prompt, get_product_analysis_prompt


class BankOfferModel(BaseModel):
    """Bank offer model"""
    bank: Optional[str] = Field(default=None, description="Bank name (optional for generic offers)")
    offer_type: str = Field(description="Type of offer: Cashback, EMI, Discount, Exchange")
    description: str = Field(description="Offer description")
    discount_amount: Optional[float] = Field(default=None, description="Numeric discount amount extracted from description (e.g., 3000 from '₹3,000 discount')")
    terms: Optional[str] = Field(default=None, description="Terms and conditions")


class CompetitorPriceModel(BaseModel):
    """Competitor price model"""
    site: str = Field(description="Competitor site name")
    price: str = Field(description="Price on competitor site")
    url: str = Field(description="URL to product on competitor site")
    availability: str = Field(description="Availability status")


class StructuredProductData(BaseModel):
    """Structured product data model"""
    # Basic info
    asin: str
    title: str
    brand: Optional[str] = None
    price: Optional[str] = None
    rating: Optional[str] = None
    total_reviews: Optional[str] = None
    category: Optional[str] = None
    availability: Optional[str] = None

    # Details
    description: Optional[str] = None
    features: List[str] = Field(default_factory=list)
    specifications: Dict[str, str] = Field(default_factory=dict)
    product_details: Dict[str, str] = Field(default_factory=dict)
    images: List[str] = Field(default_factory=list)

    # Financial info
    bank_offers: List[BankOfferModel] = Field(default_factory=list)
    competitor_prices: List[CompetitorPriceModel] = Field(default_factory=list)

    # Reviews
    reviews: List[Dict] = Field(default_factory=list)
    external_reviews_summary: Optional[str] = None

    # Web search insights
    key_findings: List[str] = Field(default_factory=list)
    red_flags: List[str] = Field(default_factory=list)
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    web_search_analysis: Optional[Dict] = None  # Complete web search data


class ProductOrchestrator:
    """
    Orchestrates the complete product analysis pipeline:
    1. Scrape Amazon page
    2. Search internet for competitive prices
    3. Search internet for reviews/feedback
    4. Send all to LLM for structured JSON extraction
    5. Save to Redis
    6. Send to LLM for markdown analysis
    7. Return both structured data and analysis
    """

    def __init__(self, redis_client=None):
        """
        Initialize orchestrator

        All configuration is read from environment variables:
        - LLM_PROVIDER: LLM provider to use (default: google)
        - LLM_MODEL: Model name (optional)
        - GOOGLE_API_KEY (or provider-specific key): For LLM operations

        Args:
            redis_client: Redis client for caching (optional)
        """
        self.redis_client = redis_client

        # Initialize LLM for structured extraction
        self.extraction_llm = get_llm(temperature=0.1)  # Low temp for factual extraction

        # Initialize LLM for analysis
        self.analysis_llm = get_llm(temperature=0.3)  # Slightly higher for analysis

        # Initialize parsers
        self.json_parser = JsonOutputParser()

        # Create extraction chain
        self._create_extraction_chain()

        # Create analysis chain
        self._create_analysis_chain()

    def _create_extraction_chain(self):
        """Create LangChain chain for structured data extraction"""

        extraction_template = get_structured_extraction_prompt()

        self.extraction_prompt = PromptTemplate(
            template=extraction_template,
            input_variables=["amazon_data", "competitor_data", "external_reviews"],
            partial_variables={"format_instructions": self.json_parser.get_format_instructions()}
        )

        self.extraction_chain = self.extraction_prompt | self.extraction_llm | self.json_parser

    def _prepare_competitor_prices(self, competitor_data: Optional[Dict]) -> List[Dict]:
        """
        Pre-process competitor data from Serper into clean flat array

        Args:
            competitor_data: Raw competitor data from SerperPriceComparison

        Returns:
            List of competitor price dictionaries
        """
        if not competitor_data:
            return []

        competitor_prices = []

        # Extract from price_comparison nested structure
        price_comparison = competitor_data.get('price_comparison', {})

        for platform, products in price_comparison.items():
            if not products:
                continue

            for product in products:
                # Convert numeric price to formatted string
                price_num = product.get('price', 0)
                currency = product.get('currency', 'INR')

                # Format price with currency symbol
                if currency == 'INR':
                    price_str = f"₹{price_num:,.0f}" if price_num else "N/A"
                else:
                    price_str = f"{currency} {price_num:,.2f}" if price_num else "N/A"

                competitor_prices.append({
                    "site": product.get('seller', platform),
                    "price": price_str,
                    "url": product.get('url', ''),
                    "availability": "In Stock" if product.get('in_stock', True) else "Out of Stock"
                })

        # Sort by numeric price (lowest first) and return top 5
        def get_numeric_price(item):
            price_str = item['price']
            # Extract numeric value from formatted string
            import re
            match = re.search(r'[\d,]+\.?\d*', price_str)
            if match:
                return float(match.group().replace(',', ''))
            return float('inf')

        competitor_prices.sort(key=get_numeric_price)
        return competitor_prices[:5]  # Return top 5 lowest prices

    def _create_analysis_chain(self):
        """Create LangChain chain for product analysis"""

        analysis_template = get_product_analysis_prompt()

        self.analysis_prompt = PromptTemplate(
            template=analysis_template,
            input_variables=["product_data", "title"]
        )

        self.analysis_chain = self.analysis_prompt | self.analysis_llm

    async def process_product(
        self,
        amazon_raw_data: Dict,
        competitor_data: Optional[Dict] = None,
        external_reviews: Optional[Dict] = None
    ) -> Dict:
        """
        Process product through complete pipeline

        Args:
            amazon_raw_data: Raw Amazon scraping data
            competitor_data: Price comparison data from web search
            external_reviews: External reviews and feedback from web search

        Returns:
            Dictionary with structured_data and analysis
        """

        # Step 1: Format inputs for LLM
        amazon_str = json.dumps(amazon_raw_data, indent=2, ensure_ascii=False)
        competitor_str = json.dumps(competitor_data or {}, indent=2, ensure_ascii=False)
        external_str = json.dumps(external_reviews or {}, indent=2, ensure_ascii=False)

        print("\n🤖 Step 1: Extracting structured data with LLM...")

        # Step 2: Extract structured data using LLM
        try:
            structured_data = await self.extraction_chain.ainvoke({
                "amazon_data": amazon_str,
                "competitor_data": competitor_str,
                "external_reviews": external_str
            })

            print(f"✓ Extracted structured data: {len(str(structured_data))} chars")

        except Exception as e:
            print(f"⚠ Structured extraction failed: {str(e)}")
            # Fallback to raw data
            structured_data = amazon_raw_data

        # Step 3: Save structured data to Redis
        if self.redis_client and amazon_raw_data.get('asin'):
            try:
                asin = amazon_raw_data['asin']
                cache_key = f"product:{asin}"
                self.redis_client.setex(
                    cache_key,
                    86400,  # 24 hour TTL
                    json.dumps(structured_data, ensure_ascii=False)
                )
                print(f"✓ Saved to Redis: {cache_key}")
            except Exception as e:
                print(f"⚠ Redis save failed: {str(e)}")

        # Step 4: Generate analysis using LLM
        print("\n🤖 Step 2: Generating product analysis with LLM...")

        try:
            analysis_result = await self.analysis_chain.ainvoke({
                "product_data": json.dumps(structured_data, indent=2, ensure_ascii=False),
                "title": structured_data.get('title', 'Product')
            })

            analysis = analysis_result.content if hasattr(analysis_result, 'content') else str(analysis_result)
            print(f"✓ Generated analysis: {len(analysis)} chars")

        except Exception as e:
            print(f"⚠ Analysis generation failed: {str(e)}")
            analysis = "Analysis generation failed. Please try again."

        # Step 5: Return both structured data and analysis
        return {
            "structured_data": structured_data,
            "analysis": analysis
        }

    def process_product_sync(
        self,
        amazon_raw_data: Dict,
        competitor_data: Optional[Dict] = None,
        external_reviews: Optional[Dict] = None
    ) -> Dict:
        """
        Synchronous version of process_product

        Args:
            amazon_raw_data: Raw Amazon scraping data
            competitor_data: Price comparison data from web search
            external_reviews: External reviews and feedback from web search

        Returns:
            Dictionary with structured_data and analysis
        """

        # Step 1: Pre-process competitor data into clean flat array
        print("\n📊 Pre-processing competitor prices...")
        competitor_prices = self._prepare_competitor_prices(competitor_data)
        print(f"  ✓ Extracted {len(competitor_prices)} competitor prices")
        if competitor_prices:
            print(f"  Lowest: {competitor_prices[0]['site']} at {competitor_prices[0]['price']}")

        # Step 2: Format inputs for LLM
        amazon_str = json.dumps(amazon_raw_data, indent=2, ensure_ascii=False)

        # Pass pre-processed competitor prices instead of raw data
        competitor_str = json.dumps({
            "competitor_prices": competitor_prices,
            "raw_data": competitor_data  # Keep raw data for reference
        }, indent=2, ensure_ascii=False)

        external_str = json.dumps(external_reviews or {}, indent=2, ensure_ascii=False)

        print("\n🤖 Step 3: Extracting structured data with LLM...")

        # Step 2: Extract structured data using LLM
        try:
            structured_data = self.extraction_chain.invoke({
                "amazon_data": amazon_str,
                "competitor_data": competitor_str,
                "external_reviews": external_str
            })

            print(f"✓ Extracted structured data: {len(str(structured_data))} chars")

            # Debug: Check what competitor_prices the LLM extracted
            print("\n📊 DEBUG: LLM extracted competitor_prices:")
            if isinstance(structured_data, dict):
                comp_prices = structured_data.get('competitor_prices', [])
                print(f"  Count: {len(comp_prices)}")
                if comp_prices:
                    print(f"  Sample: {comp_prices[0] if len(comp_prices) > 0 else 'None'}")
                else:
                    print("  ⚠ No competitor_prices extracted by LLM!")

                # Debug: Check bank offers
                bank_offers = structured_data.get('bank_offers', [])
                print(f"\n💳 DEBUG: LLM extracted bank_offers:")
                print(f"  Count: {len(bank_offers)}")
                if bank_offers:
                    print(f"  Sample: {bank_offers[0]}")
                else:
                    print("  ⚠ No bank_offers extracted by LLM!")
            else:
                print(f"  ⚠ structured_data is not a dict: {type(structured_data)}")

        except Exception as e:
            print(f"⚠ Structured extraction failed: {str(e)}")
            print(f"   Error details: {type(e).__name__}")
            # Fallback to raw data
            structured_data = amazon_raw_data

        # Step 2.5: Attach complete web search data to structured_data
        if external_reviews:
            structured_data['web_search_analysis'] = external_reviews
            print(f"\n📊 Attached web_search_analysis with {len(external_reviews.get('external_reviews', []))} external reviews")

        # Step 3: Save structured data to Redis
        if self.redis_client and amazon_raw_data.get('asin'):
            try:
                asin = amazon_raw_data['asin']
                cache_key = f"product:{asin}"
                self.redis_client.setex(
                    cache_key,
                    86400,  # 24 hour TTL
                    json.dumps(structured_data, ensure_ascii=False)
                )
                print(f"✓ Saved to Redis: {cache_key}")
            except Exception as e:
                print(f"⚠ Redis save failed: {str(e)}")

        # Step 4: Generate analysis using LLM
        print("\n🤖 Step 2: Generating product analysis with LLM...")

        try:
            analysis_result = self.analysis_chain.invoke({
                "product_data": json.dumps(structured_data, indent=2, ensure_ascii=False),
                "title": structured_data.get('title', 'Product')
            })

            analysis = analysis_result.content if hasattr(analysis_result, 'content') else str(analysis_result)
            print(f"✓ Generated analysis: {len(analysis)} chars")

        except Exception as e:
            print(f"⚠ Analysis generation failed: {str(e)}")
            analysis = "Analysis generation failed. Please try again."

        # Step 5: Return both structured data and analysis
        return {
            "structured_data": structured_data,
            "analysis": analysis
        }
