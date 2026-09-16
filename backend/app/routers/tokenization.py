from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from core.engine.tokenizer import TokenizerEngine

router = APIRouter(prefix="/api/v1/tokenization", tags=["tokenization"])
tokenizer = TokenizerEngine(hf_model_name="gpt2", tiktoken_encoding="cl100k_base")


class TokenizeRequest(BaseModel):
    text: str
    engine: Optional[str] = "tiktoken"  # "tiktoken" or "hf"


class TurnModel(BaseModel):
    turn_index: int
    speaker: str
    text: str


class CompareSavingsRequest(BaseModel):
    all_turns: List[TurnModel]
    rule_name: Optional[str] = "AI Disclosure Rule"
    max_turn_index: Optional[int] = 2


@router.post("/tokenize")
def tokenize_text(req: TokenizeRequest) -> Dict[str, Any]:
    """Tokenizes text and returns token count + subwords breakdown."""
    if req.engine == "hf":
        token_count = tokenizer.count_tokens_hf(req.text)
        subwords = tokenizer.tokenize_with_subwords(req.text, engine="hf")
    else:
        token_count = tokenizer.count_tokens_tiktoken(req.text)
        subwords = tokenizer.tokenize_with_subwords(req.text, engine="tiktoken")

    return {
        "text": req.text,
        "engine": req.engine,
        "token_count": token_count,
        "subwords_sample": [
            {"token_id": tid, "subword": subw.encode("ascii", "backslashreplace").decode("ascii")}
            for subw, tid in subwords[:20]
        ]
    }


@router.post("/savings-benchmark")
def calculate_turn_savings(req: CompareSavingsRequest) -> Dict[str, Any]:
    """Calculates context window token savings by evaluating rules on turn subsets."""
    turns_dict = [t.model_dump() for t in req.all_turns]
    max_idx = req.max_turn_index or 2
    filtered_turns = [t for t in turns_dict if t.get("turn_index", 0) <= max_idx]

    savings = tokenizer.calculate_savings(
        full_turns=turns_dict,
        filtered_turns=filtered_turns,
        rule_name=req.rule_name or "AI Disclosure Rule"
    )
    return savings
