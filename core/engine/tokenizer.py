import os
from typing import List, Dict, Any, Tuple, Optional

# Try importing tiktoken and transformers
try:
    import tiktoken
    HAS_TIKTOKEN = True
except ImportError:
    HAS_TIKTOKEN = False

try:
    from transformers import AutoTokenizer
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False


class TokenizerEngine:
    """
    Dual Tokenization engine supporting:
    1. Hugging Face AutoTokenizer (e.g. gpt2, Qwen2.5) - 100% free open-source
    2. Tiktoken (cl100k_base / o200k_base) - 100% free local BPE token counting
    """

    def __init__(self, hf_model_name: str = "gpt2", tiktoken_encoding: str = "cl100k_base"):
        self.hf_model_name = hf_model_name
        self.tiktoken_encoding = tiktoken_encoding
        self._hf_tokenizer = None
        self._tiktoken_enc = None

        if HAS_TRANSFORMERS:
            try:
                # Load lightweight local HF tokenizer
                self._hf_tokenizer = AutoTokenizer.from_pretrained(hf_model_name)
            except Exception as e:
                print(f"Warning loading HF tokenizer '{hf_model_name}': {e}")

        if HAS_TIKTOKEN:
            try:
                self._tiktoken_enc = tiktoken.get_encoding(tiktoken_encoding)
            except Exception as e:
                print(f"Warning loading tiktoken encoding '{tiktoken_encoding}': {e}")

    def count_tokens_tiktoken(self, text: str) -> int:
        """Counts tokens using tiktoken (cl100k_base)."""
        if self._tiktoken_enc:
            return len(self._tiktoken_enc.encode(text))
        # Fallback approximation: 1 token ~ 4 chars or 0.75 words
        return max(1, int(len(text) / 4))

    def count_tokens_hf(self, text: str) -> int:
        """Counts tokens using Hugging Face AutoTokenizer."""
        if self._hf_tokenizer:
            return len(self._hf_tokenizer.encode(text))
        return self.count_tokens_tiktoken(text)

    def tokenize_with_subwords(self, text: str, engine: str = "tiktoken") -> List[Tuple[str, int]]:
        """
        Returns list of (subword_str, token_id) pairs to inspect exact tokenization.
        """
        results = []
        if engine == "tiktoken" and self._tiktoken_enc:
            token_ids = self._tiktoken_enc.encode(text)
            for tid in token_ids:
                # Decode individual token bytes
                subword_bytes = self._tiktoken_enc.decode_single_token_bytes(tid)
                try:
                    subword_str = subword_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    subword_str = repr(subword_bytes)
                results.append((subword_str, tid))
        elif engine == "hf" and self._hf_tokenizer:
            token_ids = self._hf_tokenizer.encode(text)
            subwords = self._hf_tokenizer.convert_ids_to_tokens(token_ids)
            for tid, subw in zip(token_ids, subwords):
                results.append((subw, tid))
        else:
            # Fallback simple word split
            words = text.split()
            for idx, w in enumerate(words):
                results.append((w, idx))
        return results

    def format_turns_as_text(self, turns: List[Dict[str, Any]]) -> str:
        """Converts turns list to formatted transcript text block."""
        lines = []
        for t in turns:
            idx = t.get("turn_index", "")
            speaker = t.get("speaker", "UNKNOWN")
            text = t.get("text", "")
            lines.append(f"Turn {idx} [{speaker}]: {text}")
        return "\n".join(lines)

    def count_turns_tokens(self, turns: List[Dict[str, Any]], engine: str = "tiktoken") -> int:
        """Counts total tokens in a list of transcript turns."""
        formatted_text = self.format_turns_as_text(turns)
        if engine == "hf":
            return self.count_tokens_hf(formatted_text)
        return self.count_tokens_tiktoken(formatted_text)

    def calculate_savings(
        self,
        full_turns: List[Dict[str, Any]],
        filtered_turns: List[Dict[str, Any]],
        rule_name: str = "AI Disclosure Rule"
    ) -> Dict[str, Any]:
        """
        Calculates token & context savings comparing full transcript vs turn-filtered context.
        """
        full_tokens_tiktoken = self.count_turns_tokens(full_turns, engine="tiktoken")
        filtered_tokens_tiktoken = self.count_turns_tokens(filtered_turns, engine="tiktoken")

        full_tokens_hf = self.count_turns_tokens(full_turns, engine="hf")
        filtered_tokens_hf = self.count_turns_tokens(filtered_turns, engine="hf")

        tokens_saved_tiktoken = full_tokens_tiktoken - filtered_tokens_tiktoken
        pct_savings_tiktoken = (
            (tokens_saved_tiktoken / full_tokens_tiktoken * 100) if full_tokens_tiktoken > 0 else 0.0
        )

        tokens_saved_hf = full_tokens_hf - filtered_tokens_hf
        pct_savings_hf = (
            (tokens_saved_hf / full_tokens_hf * 100) if full_tokens_hf > 0 else 0.0
        )

        return {
            "rule_name": rule_name,
            "full_turns_count": len(full_turns),
            "filtered_turns_count": len(filtered_turns),
            "tiktoken": {
                "full_tokens": full_tokens_tiktoken,
                "filtered_tokens": filtered_tokens_tiktoken,
                "tokens_saved": tokens_saved_tiktoken,
                "percentage_saved": round(pct_savings_tiktoken, 2)
            },
            "huggingface": {
                "model": self.hf_model_name,
                "full_tokens": full_tokens_hf,
                "filtered_tokens": filtered_tokens_hf,
                "tokens_saved": tokens_saved_hf,
                "percentage_saved": round(pct_savings_hf, 2)
            }
        }
