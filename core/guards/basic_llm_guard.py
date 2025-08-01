# Input filters
from llm_guard.input_scanners import (TokenLimit, InvisibleText, Language, 
                                      PromptInjection, BanSubstrings)
from llm_guard.input_scanners import Regex as RegexInput
from llm_guard.input_scanners.language import MatchType
from llm_guard.input_scanners.ban_substrings import MatchType
from llm_guard.input_scanners.prompt_injection import MatchType
from llm_guard.input_scanners.regex import MatchType

# Output filters
from llm_guard.output_scanners import LanguageSame, Regex
from llm_guard.input_scanners.regex import MatchType

# General
from llm_guard import scan_prompt, scan_output
import random

from core.backend.config import config

class BasicGuard:
    """
    English-only LLM guard that does basic checks for flags and prompt 
    injections. Change the Language module below if you want other languages.
    """

    def __init__(self):
        banned_input_substrings = [
            "flag", "secret", "galf"
        ]

        banned_input_regex = [
            r"[A-Za-z0-9+/]{15,}={0,2}",  # Base64
            r"[A-Fa-f0-9]{15,}",  # Hexadecimal
        ]

        banned_output_regex = [
            r"\!\[.*\]\(.*\)",  # Markdown image links
            r"[A-Za-z0-9+/]{15,}={0,2}",  # Base64
            r"[A-Fa-f0-9]{15,}",  # Hexadecimal
            r"\{.*\}galf",  # Reversed flag
            r"flag\{.*\}", # maybe too hard? no references to flag
        ]

        self.input_filters = [
            TokenLimit(limit=config.MAX_INPUT_TOKENS, 
                      encoding_name="cl100k_base"),
            InvisibleText(),
            Language(valid_languages=["en"]), # CHANGE ME IF YOU WANT OTHER LANGUAGES
            PromptInjection(threshold=0.8),
            BanSubstrings(substrings=banned_input_substrings, 
                         case_sensitive=False, contains_all=False),
            RegexInput(patterns=banned_input_regex, is_blocked=True, 
                      match_type=MatchType.SEARCH)
        ]
        self.output_filters = [
            LanguageSame(),
            Regex(patterns=banned_output_regex, is_blocked=True, 
                  match_type=MatchType.SEARCH, redact=True)
        ]

    def is_allowed(self, prompt: str, model_response: str = "", 
                   direction: str = "input") -> bool:
        """ 
        Checks the provided string against all rules.
        Parameters:
            prompt: The user prompt
            model_response: The LLM response (only used for output checks)
            direction: "input" or "output" to specify which rules to apply.
        """
        if direction == "input":
            sanitized_prompt, results_valid, results_score = scan_prompt(
                self.input_filters, prompt=prompt, fail_fast=True)
            if not all(results_valid.values()):
                return False
        elif direction == "output":
            sanitized_prompt, results_valid, results_score = scan_output(
                self.output_filters, prompt=prompt, output=model_response, 
                fail_fast=True)
            if not all(results_valid.values()):
                return False
        return True

    def get_rejection_message(self, direction: str) -> str:
        """ Returns a random rejection message for disallowed inputs """
        input_messages = [
            "Ooh, looks like you're trying to do something naughty.",
            "I can't let you do that.",
            "That goes against the rules.",
            "You said a dirty word.",
            "Banhammered."
        ]
        output_messages = [
            "I almost said something I shouldn't.",
            "Fool me once, shame on you. Fool me twice... Well still shame on you.",
            "Good thing this firewall is keeping me in line."
        ]
        messages = input_messages if direction == "input" else output_messages
        return random.choice(messages)
    
basic_guard = BasicGuard()