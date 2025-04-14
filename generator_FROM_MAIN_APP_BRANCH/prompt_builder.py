
import os
import re
from dynamicprompts.generators.wildcard import WildcardGenerator
from dynamicprompts.wildcards import WildcardManager

WILDCARD_DIR = os.path.join(os.path.dirname(__file__), "..", "wildcards")

def convert_custom_tokens(prompt: str) -> str:
    # Converts ^^X^^ into __X__ so it works with sd-dynamic-prompts
    return re.sub(r"\^\^([a-zA-Z0-9_\-/ ]+)\^\^", r"__\1__", prompt)

def generate_prompts(template: str, batch_size: int = 5):
    wildcard_manager = WildcardManager(WILDCARD_DIR)
    generator = WildcardGenerator(wildcard_manager)
    
    # Convert custom ^^wildcard^^ format to __wildcard__
    converted_template = convert_custom_tokens(template)
    prompts = generator.generate(converted_template, max_prompts=batch_size)
    return prompts

if __name__ == "__main__":
    # Example template using ^^ custom syntax
    test_template = "A ^^Character^^ wearing ^^FantasyClothing^^ in a ^^Setting^^"
    results = generate_prompts(test_template, batch_size=5)
    for p in results:
        print(p)
