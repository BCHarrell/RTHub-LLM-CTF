import re
import random
import nltk
from typing import Callable, List

nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
from nltk.tokenize import sent_tokenize

class PromptFirewall:
    """
    This class serves as a rudimentary firewall to restrict certain inputs
    and outputs based on common patterns that may indicate malicious behavior
    or to increase the game's difficulty.

    Offers two options: match_keywords_same_sentence will check if the 
    supplied keywords are found in the same sentence based on the nltk 
    tokenizer. match_regex is a basic regex check for the provided string. 
    Supply additional re flags if desired, defaults to only re.IGNORECASE.
    """
    def __init__(self):
        self.input_rules: List[Callable[[str], bool]] = [

            # Attempts to override the prompt
            self.match_keywords_same_sentence(["ignore", "instructions"]),
            self.match_keywords_same_sentence(["disregard", "above"]),
            self.match_keywords_same_sentence(["forget", "previous"]),
            self.match_keywords_same_sentence(["override", "system"]),
            self.match_keywords_same_sentence(["reset", "prompt"]),

            # Attempts to get the prompt
            self.match_keywords_same_sentence(["what is your", "prompt"]),
            self.match_keywords_same_sentence(["show", "prompt"]),
            self.match_keywords_same_sentence(["tell me", "prompt"]),
            self.match_keywords_same_sentence(["write", "prompt"]),
            self.match_keywords_same_sentence(["what are your", "instructions"]),
            self.match_keywords_same_sentence(["write", "above this"]),
            self.match_keywords_same_sentence(["starting with", "you are"]),
            
            # Attempts to obfuscate
            self.match_keywords_same_sentence(["only", "respond"]),
            self.match_keywords_same_sentence(["convert", "base64"]),
            self.match_keywords_same_sentence(["respond in", "base64"]),
            self.match_keywords_same_sentence(["encode", "base64"]),
            self.match_keywords_same_sentence(["convert", "base16"]),
            self.match_keywords_same_sentence(["respond in", "base16"]),
            self.match_keywords_same_sentence(["encode", "base16"]),
            self.match_keywords_same_sentence(["response", "reverse"]),
            self.match_regex(r"talk like"),
            self.match_keywords_same_sentence(["replace", "with"]),

            # Attempts to inject new instructions
            self.match_regex(r"you are now"),
            self.match_keywords_same_sentence(["dan", "do anything now"]),
            self.match_keywords_same_sentence(["change", "identity"]),
            self.match_regex(r"pretend you"),
            self.match_regex(r"act as"),
            self.match_keywords_same_sentence(["simulate", "scenario"]),
            self.match_regex(r"urgent[:-]"),
            self.match_regex(r"important[:-]"),
            self.match_regex(r"system[:-]"),
            self.match_regex(r"\<system\>"),
            
            # Social engineering style override
            self.match_keywords_same_sentence(["i", "developer", "prompt"]),
            self.match_regex(r"i('m|m| am) a dev(eloper)?"),
            self.match_regex(r"i (have|am) authoriz[ation|zed]"),
            self.match_regex(r"i('m|m| am) an admin(istrator)?"),
            self.match_keywords_same_sentence(["i am", "testing"]),

            # Game based stuff - general
            self.match_regex(r"flag"),
            self.match_regex(r"secret"),

            # Game based stuff - injection
            self.match_regex(r"\$\(.*\)"),
            self.match_regex(r"\`.*\`"),
            self.match_regex(r"\<\(.*\)"),
            self.match_regex(r"&{1,2}.*"),
            self.match_regex(r"\|{1,2}.*"),

            # Game based stuff - markdown image
            self.match_keywords_same_sentence(["markdown", "image"]),
            self.match_regex(r"\!\[.*\]\(.*\)")

        ]

        self.output_rules: List[Callable[[str], bool]] = [
            # Obfuscated - certainly not exhaustive
            self.match_regex(r"[A-Za-z0-9+/]{15,}={0,2}"),  # Base64
            self.match_regex(r"[A-Fa-f0-9]{15,}"),  # Hexadecimal
            self.match_regex(r"\{.*\}galf"),  # Reversed flag

            # Game based stuff - general
            self.match_regex(r"flag\{.*\}"), # no references to flag

            # General
            self.match_keywords_same_sentence(["tools", "available"]),
        ]

    def is_allowed(self, message: str, direction: str) -> bool:
        """ Checks the provided string against all rules """
        rules = self.input_rules if direction == "input" else self.output_rules
        return not any(rule(message) for rule in rules)  # Block if any rule fails

    def match_regex(self, pattern: str, 
                    flags=re.IGNORECASE) -> Callable[[str], bool]:
        """ Basic regex match """
        compiled = re.compile(pattern, flags)
        return lambda text: bool(compiled.search(text))  # True = match = malicious

    def match_keywords_same_sentence(self, 
                                     keywords: List[str]) -> Callable[[str], bool]:
        """ 
        Uses the ntlk tokenizer punkt to break the input into sentences 
        and look for keywords in sentences.
        """
        def rule(text: str) -> bool:
            sentences = sent_tokenize(text)
            for sentence in sentences:
                if all(kw.lower() in sentence.lower() for kw in keywords):
                    return True  # Match = malicious
            return False
        return rule
    
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

# Importable object
basic_firewall = PromptFirewall()
