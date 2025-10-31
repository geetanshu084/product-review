"""
Chat routes - Q&A interactions
"""

from fastapi import APIRouter, HTTPException
from api.models.schemas import (
    ChatRequest,
    ClearChatRequest,
    ChatResponse,
    ChatHistoryResponse,
)
from api.services.chat_service import chat_service

router = APIRouter()


@router.post("/ask", response_model=ChatResponse)
async def ask_question(request: ChatRequest):
    """
    Ask a question about a product

    Args:
        request: ChatRequest with session_id, product_id (ASIN), and question

    Returns:
        ChatResponse with answer
    """
    try:
        answer = chat_service.ask_question(
            session_id=request.session_id,
            product_id=request.product_id,
            question=request.question
        )

        return ChatResponse(
            success=True,
            message="Question answered successfully",
            answer=answer
        )

    except ValueError as e:
        print(f"❌ Chat ValueError: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"❌ Chat Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str):
    """
    Get chat history for a session

    Args:
        session_id: User session ID

    Returns:
        ChatHistoryResponse with message history
    """
    try:
        history = chat_service.get_chat_history(session_id)

        return ChatHistoryResponse(
            success=True,
            message="Chat history retrieved successfully",
            history=history
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")


@router.post("/clear")
async def clear_chat(request: ClearChatRequest):
    """
    Clear chat history for a session

    Args:
        request: ClearChatRequest with session_id

    Returns:
        Success message
    """
    try:
        return {
            "success": True,
            "message": f"Chat history for session {request.session_id} will be cleared"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear history: {str(e)}")
