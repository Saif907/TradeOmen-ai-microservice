from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import List, Dict, Any, Annotated
import json
import httpx
from google import genai
from google.genai import types as genai_types
from google.genai.errors import APIError

# --- CRITICAL FIX: Direct imports from the schema file ---
from ..schemas.llm_schemas import (
    TaggingRequest, TaggingResponse, ChatRequest, ChatMessage, MessageRole,
    TradeSummary, ToolOutput
)
from ..libs.config import settings
# --------------------------------------------------------

# Initialize the router
router = APIRouter()

# ... (rest of the file is the same as provided previously, but using 
# the now-correctly-imported schema classes directly) ...

# --- Security Dependency ---

def verify_internal_auth(
    auth_key: Annotated[str, Header(alias="X-Microservice-Auth")]
) -> bool:
    """
    Verifies that the incoming request is from a trusted internal service 
    using the shared secret key.
    """
    if auth_key != settings.AI_SERVICE_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid microservice authentication key.",
        )
    return True

VerifyInternalAuth = Depends(verify_internal_auth)


# --- LLM Client Initialization ---
try:
    LLM_CLIENT = genai.Client(api_key=settings.GEMINI_API_KEY)
except Exception as e:
    print(f"FATAL LLM ERROR: Failed to initialize Gemini Client. Check GEMINI_API_KEY. Error: {e}")
    LLM_CLIENT = None

# --- Internal HTTP Client for Data Fetching ---
DATA_FETCHER_CLIENT = httpx.AsyncClient(
    base_url=settings.MAIN_BACKEND_URL,
)


# =====================================================================
# 1. AUTO-TAGGING ENDPOINT
# =====================================================================

@router.post(
    "/tag-trade",
    response_model=TaggingResponse, # CORRECT USAGE
    dependencies=[VerifyInternalAuth],
)
async def tag_trade(
    request: TaggingRequest,
):
    """
    Analyzes trade notes and returns a structured JSON list of tags.
    This is called synchronously during the trade creation process.
    """
    if not LLM_CLIENT:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI Service is not initialized.")
        
    tagging_prompt = f"""
    Analyze the following trading journal notes and generate a list of 
    relevant tags. The tags should be short (e.g., 'FOMO', 'Breakout', 
    'Poor Exit', 'Reversal', 'Good R:R'). 
    Only return the JSON object.

    NOTES: {request.notes}
    """
    
    try:
        response = LLM_CLIENT.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[tagging_prompt],
            config=genai_types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=TaggingResponse, # CORRECT USAGE
            ),
        )

        return TaggingResponse.model_validate_json(response.text)

    except APIError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini API Error during tagging: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}",
        )


# =====================================================================
# 2. CHAT & TOOL CALLING ENDPOINT
# =====================================================================

async def get_user_trade_summary(user_id: str) -> str:
    """Mocks fetching anonymized trade data for the LLM."""
    return f"""
        [Anonymized Trade Summary for ID {user_id}]:
        - Total Trades in Q4: 150
        - Net P/L: +$12,500
        - Best Strategy: Breakout (70% Win Rate)
        - Worst Mistake: Over-leveraging on Fridays.
    """

TOOL_CONFIG = genai_types.Tool(
    function_declarations=[
        genai_types.FunctionDeclaration(
            name="get_user_trade_summary",
            description="Use this tool to fetch the user's current, anonymized trading performance summary (PNL, best strategy, mistakes) from the database to answer analytical questions.",
            parameters=genai_types.Schema(
                type=genai_types.Type.OBJECT,
                properties={
                    "user_id": genai_types.Schema(
                        type=genai_types.Type.STRING,
                        description="The anonymous ID of the user whose data should be retrieved."
                    )
                },
                required=["user_id"],
            ),
        )
    ]
)

@router.post(
    "/chat/{session_id}",
    response_model=ChatMessage, # CORRECT USAGE
    dependencies=[VerifyInternalAuth],
)
async def chat_with_ai(
    session_id: str,
    request: ChatRequest, # CORRECT USAGE
):
    """
    Processes the chat request, handles history, calls tools, and returns the AI's response.
    """
    if not LLM_CLIENT:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI Service is not initialized.")

    gemini_contents = []
    for msg in request.history:
        gemini_contents.append(
            genai_types.Content(
                role="user" if msg.role in [MessageRole.USER, MessageRole.TOOL] else "model",
                parts=[genai_types.Part.from_text(msg.content)]
            )
        )
    
    system_instruction = f"""
    You are TradeLM, an expert AI Trading Analyst. Your persona is professional, 
    data-driven, and focused on helping the user improve their trading performance. 
    The user's current plan is: {request.user_plan.upper()}.
    If the user asks an analytical question (e.g., 'What is my win rate?', 'Why did I lose money?'), 
    you MUST use the available tool: 'get_user_trade_summary' to gather data 
    before generating your final answer.
    """
    
    try:
        gemini_response = LLM_CLIENT.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=gemini_contents,
            config=genai_types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=[TOOL_CONFIG]
            ),
        )

        if gemini_response.function_calls:
            first_call = gemini_response.function_calls[0]
            
            if first_call.name == "get_user_trade_summary":
                tool_output = await get_user_trade_summary(request.user_id)

                tool_response = LLM_CLIENT.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=gemini_contents + [
                         genai_types.Content(
                             role="tool", 
                             parts=[
                                genai_types.Part.from_function_response(
                                    name="get_user_trade_summary", 
                                    response={"summary": tool_output}
                                )
                             ]
                         )
                    ],
                )
                
                response_text = tool_response.text
            else:
                 response_text = "ERROR: Unknown tool requested."
        
        else:
            response_text = gemini_response.text

        return ChatMessage(
            role=MessageRole.ASSISTANT, 
            content=response_text
        )

    except APIError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini API Error: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred in the chat processing flow: {e}",
        )