from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# =====================================================================
# 1. CORE MESSAGING MODELS
# =====================================================================

class MessageRole(str):
    """Roles in a chat conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"

class ChatMessage(BaseModel):
    """Base model for a single message in a chat session."""
    role: str
    content: str
    
    tool_calls: Optional[List[Dict[str, Any]]] = None 
    tool_call_id: Optional[str] = None


class ChatRequest(BaseModel):
    """Schema for the main message payload received from the Main Backend."""
    user_id: str = Field(..., description="Anonymized ID for data fetching/tool calls.")
    user_plan: str = Field(..., description="User's SaaS tier (e.g., 'pro', 'free').")
    history: List[ChatMessage] = Field(..., description="Full conversation history for context.")
    new_message: ChatMessage = Field(..., description="The latest message from the user.")


# =====================================================================
# 2. AI TOOL CALLING & DATA FETCHING MODELS
# =====================================================================

class TradeSummary(BaseModel):
    """Anonymized and minimized schema for trade data requested by the AI tool."""
    id: str
    symbol: str
    direction: str
    entry_datetime: str
    exit_datetime: Optional[str]
    pnl: Optional[float]
    tags: List[str]

class ToolOutput(BaseModel):
    """Standardized format for tool output when sent back to the LLM."""
    tool_name: str
    content: str

# =====================================================================
# 3. AUTO-TAGGING MODELS
# =====================================================================

class TaggingRequest(BaseModel):
    """Schema for the trade auto-tagging request from the Main Backend."""
    notes: str = Field(..., description="Anonymized trade notes/journal entry.")

class TaggingResponse(BaseModel):
    """Structured JSON response the AI is mandated to return for tagging."""
    tags: List[str] = Field(..., description="A list of generated tags (e.g., 'FOMO', 'Breakout').")