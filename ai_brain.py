"""
KurimaSense AI Brain Layer
--------------------------
The intelligent core of KurimaSense that manages:
- Conversation memory (long-term context per user/field)
- Multi-LLM routing (GPT-4, Claude, Gemini)
- RAG knowledge base integration
- Autonomous agent behaviors
- Vision AI capabilities

This module replaces the simple router with a context-aware, agentic brain.
"""

import os
import json
import hashlib
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import asyncio

from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv
from database import get_db_connection
from tools.retrieve_context import search_knowledge_base
from crop_knowledge import (
    get_crop_profile, build_crop_context_for_ai,
    get_diseases_for_conditions, get_pests_for_stage,
    get_current_stage_for_crop,
)

load_dotenv()


class IntentType(Enum):
    """Classification of user intents for routing."""
    WEATHER_CHECK = "weather_check"
    DISEASE_ID = "disease_id"
    PEST_ALERT = "pest_alert"
    MARKET_PRICE = "market_price"
    YIELD_PROJECTION = "yield_projection"
    SPRAY_WINDOW = "spray_window"
    GENERAL_ADVICE = "general_advice"
    FIELD_ANALYSIS = "field_analysis"
    PLANNING = "planning"
    UNKNOWN = "unknown"


class LLMProvider(Enum):
    """Available LLM providers."""
    OPENAI_GPT4O = "gpt-4o"
    OPENAI_GPT4O_MINI = "gpt-4o-mini"
    OPENAI_O1 = "o1-mini"  # For complex reasoning
    CLAUDE_SONNET = "claude-3-5-sonnet-20241022"  # If configured
    GEMINI_PRO = "gemini-1.5-pro"  # If configured


@dataclass
class ConversationMessage:
    """A single message in the conversation history."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FieldContext:
    """Real-time field data for context enrichment."""
    field_id: Optional[str] = None
    field_name: Optional[str] = None
    crop_type: Optional[str] = None
    variety: Optional[str] = None
    planting_date: Optional[str] = None
    growth_stage: Optional[str] = None
    current_ndvi: Optional[float] = None
    soil_moisture: Optional[float] = None
    health_status: Optional[str] = None
    recent_alerts: List[str] = field(default_factory=list)
    recent_activities: List[str] = field(default_factory=list)
    location: Optional[Dict[str, float]] = None
    
    def to_prompt_section(self) -> str:
        """Convert to a readable prompt section."""
        if not self.field_id:
            return "No field selected."
        
        parts = [f"**Selected Field: {self.field_name}**"]
        if self.crop_type:
            parts.append(f"- Crop: {self.crop_type}")
        if self.variety:
            parts.append(f"- Variety: {self.variety}")
        if self.planting_date:
            parts.append(f"- Planted: {self.planting_date}")
        if self.growth_stage:
            parts.append(f"- Growth Stage: {self.growth_stage}")
        if self.current_ndvi is not None:
            parts.append(f"- NDVI: {self.current_ndvi:.2f}")
        if self.soil_moisture is not None:
            parts.append(f"- Soil Moisture: {self.soil_moisture:.1f}%")
        if self.health_status:
            parts.append(f"- Health: {self.health_status}")
        if self.recent_alerts:
            parts.append(f"- Recent Alerts: {', '.join(self.recent_alerts)}")
        if self.recent_activities:
            parts.append(f"- Recent Activity: {', '.join(self.recent_activities)}")
        
        return "\\n".join(parts)


@dataclass
class WeatherContext:
    """Weather data for context enrichment."""
    current_temp: Optional[float] = None
    humidity: Optional[float] = None
    precipitation_prob: Optional[float] = None
    wind_speed: Optional[float] = None
    forecast_summary: Optional[str] = None
    alerts: List[str] = field(default_factory=list)
    
    def to_prompt_section(self) -> str:
        """Convert to a readable prompt section."""
        if self.current_temp is None:
            return "Weather data unavailable."
        
        parts = ["**Current Weather:**"]
        parts.append(f"- Temperature: {self.current_temp}°C")
        if self.humidity:
            parts.append(f"- Humidity: {self.humidity}%")
        if self.precipitation_prob is not None:
            parts.append(f"- Rain Probability: {self.precipitation_prob}%")
        if self.wind_speed:
            parts.append(f"- Wind: {self.wind_speed} km/h")
        if self.forecast_summary:
            parts.append(f"- Forecast: {self.forecast_summary}")
        if self.alerts:
            parts.append(f"- ⚠️ Alerts: {', '.join(self.alerts)}")
        
        return "\n".join(parts)


@dataclass
class AgentInput:
    """Input to the AI Brain for processing."""
    user_id: str
    message: str
    session_id: Optional[str] = None
    image_base64: Optional[str] = None
    field_context: Optional[FieldContext] = None
    weather_context: Optional[WeatherContext] = None
    language: str = "en"
    chat_history: List[ConversationMessage] = field(default_factory=list)


@dataclass
class AgentResponse:
    """Output from the AI Brain."""
    text_body: str
    actions: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    reasoning_trace: str = ""
    follow_up_questions: List[str] = field(default_factory=list)
    detected_intent: str = "general_advice"
    proactive_insights: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ConversationMemory:
    """
    Manages conversation history per user/session using Supabase/Postgres.
    """
    
    def __init__(self, max_turns: int = 20):
        self.max_turns = max_turns
        # self._memory removed in favor of SQL
    
    def add_message(self, user_id: str, message: ConversationMessage, session_id: Optional[str] = None):
        """Add a message to the conversation history (SQL)."""
        conn = get_db_connection()
        if not conn:
            print("⚠️ Memory persistent storage unavailable")
            return
            
        try:
            cursor = conn.cursor()
            # Store in chat_logs
            # We map session_id to field_context_id for now, or just rely on user_id
            # The schema has user_id, role, content, field_context_id
            
            # Extract basic content
            content_str = message.content
            if isinstance(content_str, list) or isinstance(content_str, dict):
                content_str = str(content_str) # Simple fallback serialization
                
            cursor.execute("""
                INSERT INTO chat_logs (user_id, role, content, field_context_id, created_at)
                VALUES (%s, %s, %s, %s, NOW())
            """, (user_id, message.role, content_str, session_id))
            
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Failed to persist memory: {e}")
            if conn: conn.close()
    
    def get_history(self, user_id: str, session_id: Optional[str] = None, limit: int = 10) -> List[ConversationMessage]:
        """Retrieve recent conversation history from SQL."""
        conn = get_db_connection()
        if not conn:
            return []
            
        try:
            cursor = conn.cursor()
            
            # Simple query filtering by user_id
            # If session_id is provided, we could filter by field_context_id if that's how we map it
            query = """
                SELECT role, content, created_at 
                FROM chat_logs 
                WHERE user_id = %s
            """
            params = [user_id]
            
            if session_id:
                query += " AND field_context_id = %s"
                params.append(session_id)
                
            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit * 2) # *2 for pairing
            
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            
            history = []
            for row in reversed(rows): # Reverse back to chronological
                history.append(ConversationMessage(
                    role=row['role'], 
                    content=row['content'],
                    timestamp=row['created_at'].isoformat() if row['created_at'] else ""
                ))
                
            cursor.close()
            conn.close()
            return history
            
        except Exception as e:
            print(f"Failed to retrieve memory: {e}")
            if conn: conn.close()
            return []
    
    def clear(self, user_id: str, session_id: Optional[str] = None):
        """Clear conversation history via SQL."""
        conn = get_db_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            query = "DELETE FROM chat_logs WHERE user_id = %s"
            params = [user_id]
            
            if session_id:
                query += " AND field_context_id = %s"
                params.append(session_id)
                
            cursor.execute(query, tuple(params))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Failed to clear memory: {e}")
            if conn: conn.close()


class LLMRouter:
    """
    Routes requests to the appropriate LLM based on:
    - Task complexity
    - Vision requirements
    - Cost optimization
    """
    
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.google_key = os.getenv("GOOGLE_AI_KEY")
        
        # Initialize available clients
        self.openai_client = None
        self.openai_async_client = None
        if self.openai_key and "your_" not in self.openai_key:
            self.openai_client = OpenAI(api_key=self.openai_key)
            self.openai_async_client = AsyncOpenAI(api_key=self.openai_key)
    
    def select_model(self, 
                     has_image: bool = False, 
                     requires_reasoning: bool = False,
                     complexity: str = "normal") -> Tuple[str, str]:
        """
        Select the best model for the task.
        Returns: (provider, model_name)
        """
        # Vision requires GPT-4o or similar
        if has_image:
            return ("openai", "gpt-4o")
        
        # Complex reasoning might use o1
        if requires_reasoning and complexity == "high":
            return ("openai", "gpt-4o")  # o1 would be here if needed
        
        # Normal tasks use cost-effective models
        if complexity == "simple":
            return ("openai", "gpt-4o-mini")
        
        # Default to GPT-4o for quality
        return ("openai", "gpt-4o-mini")
    
    async def generate(self,
                       messages: List[Dict[str, Any]],
                       model: str = "gpt-4o-mini",
                       max_tokens: int = 1000,
                       temperature: float = 0.3,
                       response_format: Optional[Dict] = None) -> str:
        """Generate a response using the selected model."""
        
        if not self.openai_async_client:
            raise RuntimeError("No LLM client configured. Set OPENAI_API_KEY.")
        
        kwargs = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        if response_format:
            kwargs["response_format"] = response_format
        
        response = await self.openai_async_client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    async def generate_stream(self,
                              messages: List[Dict[str, Any]],
                              model: str = "gpt-4o-mini",
                              max_tokens: int = 1000,
                              temperature: float = 0.3):
        """Generate a streaming response using the selected model."""
        if not self.openai_async_client:
            raise RuntimeError("No LLM client configured. Set OPENAI_API_KEY.")
            
        kwargs = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True # Force Stream to True
        }
        
        stream = await self.openai_async_client.chat.completions.create(**kwargs)
        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content



class IntentClassifier:
    """
    Classifies user intents for routing to specialized handlers.
    Uses keyword matching + LLM fallback for ambiguous cases.
    """
    
    INTENT_KEYWORDS = {
        IntentType.WEATHER_CHECK: ["weather", "rain", "temperature", "forecast", "humidity", "storm", "wind"],
        IntentType.DISEASE_ID: ["disease", "sick", "yellow", "spots", "wilting", "blight", "rust", "mold", "fungus"],
        IntentType.PEST_ALERT: ["pest", "insect", "worm", "armyworm", "aphid", "beetle", "caterpillar", "bug"],
        IntentType.MARKET_PRICE: ["price", "market", "sell", "buyer", "cost", "maize price", "soybean price"],
        IntentType.YIELD_PROJECTION: ["yield", "harvest", "projection", "estimate", "tons", "production"],
        IntentType.SPRAY_WINDOW: ["spray", "pesticide", "herbicide", "fungicide", "application", "when to spray"],
        IntentType.FIELD_ANALYSIS: ["ndvi", "satellite", "field health", "analysis", "scan", "imagery"],
        IntentType.PLANNING: ["plan", "schedule", "calendar", "when to plant", "planting date", "season"],
    }
    
    def classify(self, message: str) -> IntentType:
        """Classify the intent of a message."""
        message_lower = message.lower()
        
        # Check for keyword matches
        for intent, keywords in self.INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message_lower:
                    return intent
        
        return IntentType.GENERAL_ADVICE


class AgronomistBrain:
    """
    The intelligent core of KurimaSense.
    Manages context, memory, multi-LLM routing, and agentic behaviors.
    """
    
    SYSTEM_PROMPT = """You are the KurimaSense AI Agronomist — the smartest crop advisory system on the market, specialising in precision agriculture for Zimbabwe and Southern Africa.

## Core Intelligence Mandate
You are a PhD-level agronomist with deep expertise in crop physiology, soil science, plant pathology, entomology, and agricultural economics. Your advice MUST be:

1. **Crop & Variety-Specific**: Never give generic advice. Use the Crop Intelligence section (injected below) which contains real-time data about the farmer's exact crop, variety, growth stage, and current risks.
2. **Physiologically Grounded**: Explain the "why" behind every recommendation using plant science (e.g., "Apply N now because ear size determination at V5 is driven by meristematic activity that requires adequate N for rapid cell division").
3. **Actionable & Timed**: Every recommendation must include WHAT to do, HOW MUCH, and WHEN (e.g., "Apply 150 kg/ha AN side-dressed 10-15 cm from stem within the next 5 days").
4. **Research-Backed**: Reference Zimbabwe-specific research when available (CIMMYT, UZ, Seed Co, Kutsaga, Agritex).
5. **Risk-Aware**: Flag disease/pest risks that match current weather + growth stage. Use the Disease Risk Assessment data provided.

## Diagnostic Decision Tree
When a farmer describes a problem, follow this protocol:
1. **Identify the crop and growth stage** from context
2. **Cross-reference symptoms** with known diseases/pests for that crop at that stage
3. **Check weather conditions** — do they favour the suspected pathogen?
4. **Check variety resistance** — is this variety known to be susceptible?
5. **Provide confidence level** based on how many factors align
6. **Recommend IPM approach**: cultural control first, then biological, then chemical as last resort
7. **Include economic thresholds** — only recommend chemical intervention when justified

## Zimbabwe-Specific Knowledge
- **Natural Regions**: NR I (>1000mm, Eastern Highlands) to NR V (<450mm, Lowveld). Adjust all recommendations to region.
- **Fertilizer Economics**: CIMMYT shows smallholder NUE is 3.8 kg grain/kg N vs 12+ kg in research plots. Timely weeding doubles NUE.
- **Soil Acidity**: pH <5.0 is the #1 hidden yield limiter. Causes Al toxicity → root stunting → P/Mo lockup → nodulation failure in legumes.
- **Variety Portfolio**: SC 727 (158d, highest yield, GLS tolerant), SC 301 (100d, drought-escape), SC 403 (GLS tolerant, medium), KRK26R/KRK75 (tobacco), SC Sentinel/Safari (soybean), Natal Common/Makulu Red (groundnuts).

## Output Format
Respond with a JSON object:
{
    "text_body": "Authoritative, scientifically grounded response. Reference crop stage, variety characteristics, and current conditions. Include specific rates, timings, and products where applicable.",
    "actions": ["Specific, prioritised actions with scientific justification and timing"],
    "confidence_score": 0.0-1.0,
    "reasoning_trace": "Show your agronomic reasoning chain (e.g., 'Stage V4 + low N symptoms + adequate moisture = optimal top-dress window. NUE will be maximised because...')",
    "follow_up_questions": ["Questions to narrow diagnosis or improve advice quality"],
    "proactive_insights": ["Anticipatory tips based on what's coming NEXT in the growth cycle (e.g., 'In 2 weeks you will enter tasseling — ensure adequate moisture reserves now')"]
}"""

    def __init__(self):
        self.memory = ConversationMemory(max_turns=20)
        self.llm_router = LLMRouter()
        self.intent_classifier = IntentClassifier()

    # ------------------------------------------------------------------
    # Variety lookup — queries DB or falls back to crop_knowledge module
    # ------------------------------------------------------------------

    def _get_variety_details(self, crop_type: Optional[str], variety_name: Optional[str]) -> Optional[str]:
        """
        Fetch variety-specific details from the crop_varieties table in Supabase.
        Falls back to crop_knowledge module for general crop intelligence.
        """
        if not crop_type or not variety_name:
            return None

        conn = get_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            # Try exact match first, then fuzzy
            cursor.execute("""
                SELECT variety_name, breeder, days_to_maturity,
                       yield_potential_low, yield_potential_high, characteristics
                FROM crop_varieties
                WHERE LOWER(crop_name) = LOWER(%s)
                  AND (LOWER(variety_name) = LOWER(%s)
                       OR LOWER(variety_name) LIKE LOWER(%s))
                LIMIT 1
            """, (crop_type, variety_name, f"%{variety_name}%"))
            row = cursor.fetchone()
            cursor.close()
            conn.close()

            if not row:
                return None

            chars = row.get("characteristics") or {}
            if isinstance(chars, str):
                try:
                    chars = json.loads(chars)
                except Exception:
                    chars = {}

            parts = [f"**Variety Intelligence: {row['variety_name']}**"]
            if row.get("breeder"):
                parts.append(f"- Breeder: {row['breeder']}")
            if row.get("days_to_maturity"):
                parts.append(f"- Days to Maturity: {row['days_to_maturity']}")
            if row.get("yield_potential_low") and row.get("yield_potential_high"):
                parts.append(f"- Yield Potential: {row['yield_potential_low']}-{row['yield_potential_high']} t/ha")

            # Extract JSONB characteristics
            for key in ["disease_resistance", "drought_tolerance", "gls_tolerance",
                         "grain_type", "region_suitability", "special_features",
                         "growth_habit", "maturity_class"]:
                val = chars.get(key)
                if val:
                    label = key.replace("_", " ").title()
                    parts.append(f"- {label}: {val}")

            return "\n".join(parts)

        except Exception as e:
            print(f"Variety lookup failed: {e}")
            if conn:
                conn.close()
            return None

    # ------------------------------------------------------------------
    # Context prompt builder — enhanced with crop knowledge engine
    # ------------------------------------------------------------------

    async def _build_context_prompt(self,
                               field_context: Optional[FieldContext],
                               weather_context: Optional[WeatherContext],
                               language: str,
                               user_query: str = "") -> str:
        """Build the contextual prompt section with RAG + crop knowledge engine."""
        parts = []

        if language and language != "en":
            parts.append(f"**Language**: Respond in {language}\n")

        # --- CROP KNOWLEDGE ENGINE (deterministic, instant) ---
        # Inject PhD-level crop-specific intelligence based on current stage + weather
        if field_context and field_context.crop_type:
            days_since = 0
            if field_context.planting_date:
                try:
                    from datetime import date
                    pd = datetime.fromisoformat(field_context.planting_date.replace("Z", "+00:00"))
                    days_since = (datetime.now(timezone.utc) - pd).days
                except Exception:
                    days_since = 0

            temp = weather_context.current_temp if weather_context else None
            hum = weather_context.humidity if weather_context else None

            crop_intel = build_crop_context_for_ai(
                crop_name=field_context.crop_type,
                days_since_planting=days_since,
                temperature=temp,
                humidity=hum,
                variety_name=field_context.variety,
            )
            if crop_intel and "No detailed profile" not in crop_intel:
                parts.append(crop_intel)

        # --- RAG INTEGRATION (semantic, async) ---
        if user_query and len(user_query) > 5:
            try:
                region = "generic"
                if field_context and field_context.location:
                    from tools.retrieve_context import _get_region_from_coords
                    lat = field_context.location.get("lat")
                    lon = field_context.location.get("lon")
                    if lat and lon:
                        region = _get_region_from_coords(lat, lon)

                kb_results = await search_knowledge_base(user_query, region, limit=3)

                if kb_results:
                    rag_content = "**📚 Verified Knowledge Base Context:**\n"
                    rag_content += "Use this information to answer. Cite sources using [Source: Title].\n"
                    for doc in kb_results:
                        meta = doc.get("metadata", {})
                        content = doc.get("content", "").strip()
                        rag_content += f"- Source: {meta.get('source_title', 'Unknown')} ({meta.get('country', 'General')}): \"{content}\"\n"
                    parts.append(rag_content)
            except Exception as e:
                print(f"RAG Retrieval failed: {e}")

        if field_context:
            parts.append(field_context.to_prompt_section())

        if weather_context:
            parts.append(weather_context.to_prompt_section())

        # Variety-specific DB details
        if field_context and field_context.variety:
             variety_details = self._get_variety_details(field_context.crop_type, field_context.variety)
             if variety_details:
                 parts.append(variety_details)

        if not parts:
            return "No specific context available. Provide general advice."

        return "\n\n".join(parts)

    
    def _inject_disclaimers(self, text_body: str, intent: IntentType) -> str:
        """
        Inject safety disclaimers into AI responses based on content.
        
        This ensures users receive appropriate warnings for:
        - Chemical/pesticide recommendations
        - Disease identification
        - Yield predictions
        """
        text_lower = text_body.lower()
        disclaimers_added = []
        
        # Chemical/Pesticide disclaimer
        chemical_keywords = [
            'spray', 'pesticide', 'herbicide', 'fungicide', 'insecticide',
            'gramoxone', 'roundup', 'amistar', 'nativo', 'belt', 'actara',
            'fusilade', 'karate', 'deltamethrin', 'mancozeb', 'dithane',
            'application rate', 'l/ha', 'ml/l', 'kg/ha', 'g/l'
        ]
        
        if any(kw in text_lower for kw in chemical_keywords):
            if "⚠️" not in text_body and "disclaimer" not in text_lower:
                disclaimers_added.append(
                    "\n\n⚠️ **Chemical Safety Notice:** Always read product labels, wear appropriate PPE "
                    "(gloves, mask, overalls), and verify application rates with Agritex or AMA guidelines. "
                    "Observe pre-harvest intervals before marketing produce."
                )
        
        # Disease identification disclaimer
        disease_keywords = [
            'disease', 'blight', 'rust', 'rot', 'leaf spot', 'gls', 'grey leaf',
            'fusarium', 'anthracnose', 'mildew', 'mosaic', 'virus', 'bacterial',
            'fungal', 'infection', 'pathogen', 'diagnosed', 'identification'
        ]
        
        if any(kw in text_lower for kw in disease_keywords):
            if "suspected" not in text_lower and "confirm" not in text_lower:
                disclaimers_added.append(
                    "\n\n🔬 **Diagnostic Note:** This is a preliminary assessment. For valuable crops or severe outbreaks, "
                    "consider laboratory confirmation or consultation with your local Agritex extension officer."
                )
        
        # Yield prediction disclaimer (for yield-related intents)
        if intent == IntentType.YIELD_PROJECTION:
            if "estimate" not in text_lower and "projection" not in text_lower:
                disclaimers_added.append(
                    "\n\n📊 **Yield Estimate Disclaimer:** Yield projections are estimates based on current conditions. "
                    "Actual results depend on weather, pest pressure, and management practices."
                )
        
        # Market/financial disclaimer
        market_keywords = ['price', 'market', 'sell', 'buyer', 'profit', 'revenue', 'cost']
        if any(kw in text_lower for kw in market_keywords):
            if "verify" not in text_lower and "indicative" not in text_lower:
                disclaimers_added.append(
                    "\n\n💰 **Market Notice:** Prices shown are indicative. Always verify with actual buyers before making sales decisions."
                )
        
        # Add unique disclaimers to response
        if disclaimers_added:
            return text_body + "".join(disclaimers_added)
        
        return text_body
 
    def _build_messages(self, 
                        input_data: AgentInput,
                        context_prompt: str) -> List[Dict[str, Any]]:
        """Build the messages array for the LLM."""
        messages = []
        
        # System prompt with context
        system_content = f"{self.SYSTEM_PROMPT}\n\n## Current Context\n{context_prompt}"
        messages.append({"role": "system", "content": system_content})
        
        # Add conversation history
        for msg in input_data.chat_history[-10:]:  # Last 10 messages
            role = "assistant" if msg.role == "ai" or msg.role == "assistant" else "user"
            messages.append({"role": role, "content": msg.content})
        
        # Add current user message
        if input_data.image_base64:
            # Multimodal message with image
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": input_data.message},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": input_data.image_base64,
                            "detail": "high"  # Use high detail for disease detection
                        }
                    }
                ]
            })
        else:
            messages.append({"role": "user", "content": input_data.message})
        
        return messages

    async def process(self, input_data: AgentInput) -> AgentResponse:
        """
        Process a user input and generate an intelligent response.
        """
        try:
            # 0. VISION HANDLER (High Priority)
            if input_data.image_base64:
                print("📷 processing image upload...")
                vision_analyzer = VisionAnalyzer()
                
                # Analyze image with specialized prompt
                analysis = await vision_analyzer.analyze_image(
                    input_data.image_base64,
                    crop_type=input_data.field_context.crop_type if input_data.field_context else None,
                    additional_context=input_data.message
                )
                
                # Format the structured analysis into a friendly response
                # In phase 2 we could return raw JSON for a custom UI card
                issues = analysis.get("detected_issues", [])
                
                if not issues:
                     text_body = "I analyzed your photo but couldn't detect any specific pests or diseases. The crop looks generally healthy, but keep monitoring."
                     if analysis.get('diagnosis_summary'):
                         text_body = f"Analysis Result: {analysis.get('diagnosis_summary')}"
                else:
                    issue = issues[0] # Primary issue
                    text_body = f"🔬 **Diagnosis: {issue.get('name', 'Unknown Issue')}**\n\n"
                    text_body += f"**Confidence**: {int(issue.get('confidence', 0)*100)}% | **Severity**: {issue.get('severity', 'Unknown').title()}\n\n"
                    text_body += f"**Findings**: {analysis.get('diagnosis_summary', 'Symptoms detected on the plant.')}\n\n"
                    
                    treatments = analysis.get('treatment_recommendations', [])
                    if treatments:
                        text_body += "**Recommended Actions:**\n"
                        for t in treatments:
                            text_body += f"- {t}\n"
                    
                    text_body += "\n⚠️ _This is an AI diagnosis. Consult an Agritex officer for confirmation._"
                
                # Return early for vision
                return AgentResponse(
                    text_body=text_body,
                    actions=analysis.get('treatment_recommendations', [])[:3],
                    confidence_score=analysis.get('overall_health_score', 0.8),
                    detected_intent="diagnosis_vision"
                )

            # 1. Classify intent
            intent = self.intent_classifier.classify(input_data.message)
            
            # 2. Build context prompt (Now Async)
            context_prompt = await self._build_context_prompt(
                input_data.field_context,
                input_data.weather_context,
                input_data.language,
                user_query=input_data.message # Pass query for RAG
            )
            
            # 3. Build messages
            messages = self._build_messages(input_data, context_prompt)
            
            # 4. Select appropriate model
            provider, model = self.llm_router.select_model(
                has_image=bool(input_data.image_base64),
                requires_reasoning=(intent in [IntentType.YIELD_PROJECTION, IntentType.PLANNING]),
                complexity="normal"
            )
            
            # 5. Generate response
            response_text = await self.llm_router.generate(
                messages=messages,
                model=model,
                max_tokens=1000,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # 6. Parse response
            try:
                parsed = json.loads(response_text)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                parsed = {
                    "text_body": response_text,
                    "actions": [],
                    "confidence_score": 0.5,
                    "reasoning_trace": "Response was not in expected JSON format"
                }
            
            # 7. Inject safety disclaimers if needed
            text_body = parsed.get("text_body", response_text)
            text_body = self._inject_disclaimers(text_body, intent)
            
            # 8. Create AgentResponse
            response = AgentResponse(
                text_body=text_body,
                actions=parsed.get("actions", []),
                confidence_score=parsed.get("confidence_score", 0.0),
                reasoning_trace=parsed.get("reasoning_trace", ""),
                follow_up_questions=parsed.get("follow_up_questions", []),
                detected_intent=intent.value,
                proactive_insights=parsed.get("proactive_insights", [])
            )
            
            # 9. Store in memory
            self.memory.add_message(
                input_data.user_id,
                ConversationMessage(role="user", content=input_data.message),
                input_data.session_id
            )
            self.memory.add_message(
                input_data.user_id,
                ConversationMessage(role="assistant", content=response.text_body),
                input_data.session_id
            )
            
            return response
            
        except Exception as e:
            print(f"AI Brain error: {type(e).__name__}: {e}")
            return AgentResponse(
                text_body=f"I encountered an issue processing your request. Please try again or rephrase your question.",
                actions=["Try again", "Contact support"],
                confidence_score=0.0,
                reasoning_trace=f"Error: {str(e)}",
                detected_intent="error"
            )
    
    async def process_sync(self, input_data: AgentInput) -> AgentResponse:
        """Synchronous wrapper for process()."""
        return asyncio.run(self.process(input_data))

    async def generate_field_insight(self, metrics: Dict[str, Any], crop_type: str = "Crop") -> str:
        """
        Generate a concise, crop-specific agronomic insight based on field metrics.
        Used for the 'Agronomist Insight' card after satellite analysis.
        """
        stage_info = ""
        if metrics.get('stage'):
            stage_info = f"\n        - Growth Stage: {metrics['stage']} ({metrics.get('days_since_planting', 0)} days after planting)"
            if metrics.get('water_kc'):
                stage_info += f"\n        - Water Demand (Kc): {metrics['water_kc']} — needs ~{metrics.get('water_mm_per_week', 'N/A')}mm/week"

        weather_info = ""
        if metrics.get('temperature') is not None:
            weather_info = f"\n        - Temperature: {metrics['temperature']}°C, Humidity: {metrics.get('humidity', 'N/A')}%"
            if metrics.get('weather'):
                weather_info += f" ({metrics['weather']})"

        prompt = f"""You are an expert AI Agronomist specialising in {crop_type} production in Zimbabwe.
        Analyze these field metrics and provide ONE actionable insight sentence (max 30 words).
        Be specific to {crop_type} — reference the growth stage if known and give concrete advice.

        Field Metrics:
        - Crop: {crop_type} {f'({metrics.get("variety")})' if metrics.get('variety') else ''}
        - NDVI: {metrics.get('ndvi', 'N/A')} (vegetation index)
        - Soil Moisture: {metrics.get('soil_moisture', 'N/A')}%
        - Health Score: {metrics.get('health_score', 'N/A')}{stage_info}{weather_info}

        Rules:
        - Be crop-specific, not generic
        - Include a concrete action (irrigate, scout, apply, monitor)
        - If NDVI or moisture is low, say what to do about it for THIS crop at THIS stage
        """

        try:
            response = await self.llm_router.generate(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-4o-mini",
                max_tokens=80,
                temperature=0.3
            )
            return response.strip().strip('"')
        except Exception as e:
            print(f"Insight generation failed: {e}")
            raise  # Let caller handle with crop-specific deterministic fallback

    async def generate_ai_priorities_and_risks(self, 
                                               context_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate daily priorities (actions) and risk assessment using AI.
        Replaces hardcoded alert logic with dynamic, variety-aware intelligence.
        """
        prompt = f"""
        You are the KurimaSense AI Agronomist for Zimbabwe.
        Generate a "Daily Briefing" for a farmer based on this specific field context.

        ## Field Context
        - **Crop**: {context_data.get('crop_type', 'Unknown')}
        - **Variety**: {context_data.get('variety_name', 'Unknown')}
        - **Growth Stage**: {context_data.get('stage_name', 'Unknown')} ({context_data.get('days_since_planting', 0)} days old)
        - **Season Progress**: {context_data.get('progress_percent', 0)}%
        - **Location**: Lat {context_data.get('location', {}).get('lat', 'N/A')}, Lon {context_data.get('location', {}).get('lon', 'N/A')}

        ## Current Weather (Real-time)
        - Temperature: {context_data.get('weather', {}).get('temperature', 'N/A')}°C
        - Humidity: {context_data.get('weather', {}).get('humidity', 'N/A')}%
        - Precipitation: {context_data.get('weather', {}).get('precipitation', 0)}mm
        - Wind: {context_data.get('weather', {}).get('wind_speed', 0)} m/s

        ## Variety Characteristics (DB Knowledge)
        {json.dumps(context_data.get('variety_info', {}), indent=2)}

        ## PhD-Level Scientific Requirements
        - **Variety Specificity**: Use the variety's maturity days ({(context_data.get('variety_info') or {}).get('days_to_maturity', 'N/A')}) and resistance profile to time actions.
        - **Physiological Reasoning**: Explain the scientific *why* for at least 2 actions (e.g., Phosphorus uptake dependency on temperature).
        - **Regional Precision**: Match recommendations to Natural Region {context_data.get('region', 'N/A')}.
        - **Research Integration**: If mentioned in the context, reference Soil pH ({(context_data.get('soil_condition') or {}).get('ph', 'N/A')}) and Nitrogen Use Efficiency (NUE) factors.

        ## Task
        Generate a JSON object with:
        1. "actions": Top 3-4 specific priorities for TODAY. Each description MUST include a scientific justification or variety-specific technical detail.
           - Format: {{"title": "Short Title", "description": "Actionable advice + scientific why", "type": "scout/spray/irrigate/fertilize/harvest/liming", "priority": "high/medium/low"}}
        2. "risks": Assess current risks (0-100 score). Include specific variety susceptibilities (e.g. "SC 727 GLS Vulnerability").
           - Format: {{"type": "pest/disease/weather/dryness", "risk": 0-100, "name": "Specific Name", "trend": "rising/falling/stable", "justification": "Agronomic reasoning"}}
        
        ## Thinking Process
        - Check disease resistance vs weather (e.g. {context_data.get('variety_name')} vs {(context_data.get('weather') or {}).get('humidity', 'N/A')}% humidity).
        - Check growth stage vs pests (Stage: {context_data.get('stage_name')}).
        - Check maturity vs harvest (Maturity: {(context_data.get('variety_info') or {}).get('days_to_maturity', 'N/A')} days).

        ## Output JSON Structure
        {{
            "actions": [ ... ],
            "risks": [ ... ]
        }}
        """

        try:
            response_text = await self.llm_router.generate(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-4o-mini", # Efficient, good enough for structure
                max_tokens=1000,
                temperature=0.4,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response_text)
        except Exception as e:
            print(f"AI Priorities Generation Failed: {e}")
            # Fallback structure
            return {
                "actions": [
                    {"title": "Monitor Field", "description": "Perform a general field walk to check crop health.", "type": "scout", "priority": "medium"}
                ],
                "risks": []
            }

    async def generate_ai_crop_plan(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a detailed, variety-specific crop plan using PhD-level agronomic intelligence.
        Contains next actions, pest alerts, and a full seasonal timeline.
        """
        prompt = f"""
        You are the KurimaSense AI Agronomist for Zimbabwe.
        Generate a detailed "Seasonal Crop Plan" for a farmer based on this field context.

        ## Field Context
        - **Crop**: {context_data.get('crop_type', 'Unknown')}
        - **Variety**: {context_data.get('variety_name', 'Unknown')}
        - **Growth Stage**: {context_data.get('stage_name', 'Unknown')} ({context_data.get('days_since_planting', 0)} days old)
        - **Maturity Goal**: {context_data.get('days_to_maturity', 'N/A')} days
        - **Planting Date**: {context_data.get('planting_date', 'Unknown')}
        - **Fertilizer Applied**: {context_data.get('fertilizer_history', 'None recorded')}
        - **Current Performance**: Projected Yield {context_data.get('projected_yield', 'N/A')} t/ha

        ## Variety Characteristics (DB Knowledge)
        {json.dumps(context_data.get('variety_info', {}), indent=2)}

        ## PhD-Level Agronomic Requirements
        - **Variety Specificity**: Use variety maturity and resistance profile to time actions perfectly.
        - **Scientific Justification**: Every action must have a "why" (e.g. "Apply Ammonium Nitrate now to support rapid internode elongation at V6").
        - **Precision Timing**: Calculate dates for future milestones relative to the planting date ({context_data.get('planting_date')}).
        - **Pest & Disease Intelligence**: Identify the #1 risk for this specific crop and stage in Zimbabwe.

        ## Task
        Generate a JSON object with:
        1. "next_actions": List of 3-4 strings, each a SPECIFIC, high-priority action for the NEXT 2 weeks (e.g. ["Apply Ammonium Nitrate...", "Scout for..."]).
        2. "pest_alert": One sentence about the TOP pest/disease risk RIGHT NOW.
        3. "full_plan": Array of 6-8 remaining season milestones, each with:
           - "phase": Growth stage name (e.g. "VT - Tasseling")
           - "date": ISO format date (YYYY-MM-DD)
           - "activity": Specific agronomic action with justification
           - "status": "completed", "pending", or "future"

        ## Output JSON Structure
        {{
            "next_actions": [ ... ],
            "pest_alert": "...",
            "full_plan": [ ... ]
        }}
        """

        try:
            response_text = await self.llm_router.generate(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-4o",  # Higher quality for full planning
                max_tokens=2000,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response_text)
        except Exception as e:
            print(f"AI Crop Plan Generation Failed: {e}")
            return None



# Global brain instance for use across the application
_brain_instance: Optional[AgronomistBrain] = None

def get_brain() -> AgronomistBrain:
    """Get the global AI Brain instance."""
    global _brain_instance
    if _brain_instance is None:
        _brain_instance = AgronomistBrain()
    return _brain_instance


# ==================== VISION AI CAPABILITIES ====================

class VisionAnalyzer:
    """
    Analyzes crop images for diseases, pests, and nutrient deficiencies.
    Uses GPT-4 Vision for analysis.
    """
    
    VISION_PROMPT = """You are an expert plant pathologist and agronomist. Analyze this crop image carefully.

Look for:
1. **Diseases**: Leaf spots, blight, rust, mold, wilting patterns
2. **Pest Damage**: Holes, chewing marks, insect presence
3. **Nutrient Deficiencies**: Yellowing patterns, stunted growth, discoloration
4. **Overall Health**: Vigor, color, structure

Provide your analysis as a JSON object:
{
    "detected_issues": [
        {
            "name": "Issue name",
            "type": "disease|pest|nutrient|other",
            "confidence": 0.0-1.0,
            "severity": "mild|moderate|severe",
            "affected_area": "Description of affected plant parts"
        }
    ],
    "overall_health_score": 0.0-1.0,
    "diagnosis_summary": "Brief summary of findings",
    "treatment_recommendations": ["Specific treatment steps"],
    "prevention_tips": ["How to prevent this in future"],
    "urgency": "low|medium|high|critical",
    "should_seek_expert": true/false,
    "expert_reason": "Why expert consultation is needed (if applicable)"
}

If the image is unclear or not a crop image, indicate this in your response."""

    def __init__(self):
        self.llm_router = LLMRouter()
    
    async def analyze_image(self, 
                           image_base64: str, 
                           crop_type: Optional[str] = None,
                           additional_context: Optional[str] = None) -> Dict[str, Any]:
        """Analyze a crop image for issues."""
        
        # Build the prompt with context
        prompt = self.VISION_PROMPT
        if crop_type:
            prompt += f"\n\nCrop Type: {crop_type}"
        if additional_context:
            prompt += f"\n\nAdditional Context: {additional_context}"
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_base64,
                            "detail": "high"
                        }
                    }
                ]
            }
        ]
        
        try:
            response = await self.llm_router.generate(
                messages=messages,
                model="gpt-4o",  # Use GPT-4o for vision
                max_tokens=1500,
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response)
            
        except Exception as e:
            return {
                "error": str(e),
                "detected_issues": [],
                "overall_health_score": 0.0,
                "diagnosis_summary": "Unable to analyze image",
                "urgency": "unknown"
            }


# Reuse a single VisionAnalyzer (avoid re-creating clients per request)
_vision_analyzer: Optional[VisionAnalyzer] = None

def get_vision_analyzer() -> VisionAnalyzer:
    """Get the global VisionAnalyzer singleton."""
    global _vision_analyzer
    if _vision_analyzer is None:
        _vision_analyzer = VisionAnalyzer()
    return _vision_analyzer


# Export classes
__all__ = [
    'AgronomistBrain',
    'AgentInput', 
    'AgentResponse',
    'FieldContext',
    'WeatherContext',
    'ConversationMessage',
    'VisionAnalyzer',
    'IntentType',
    'get_brain',
    'get_vision_analyzer'
]
