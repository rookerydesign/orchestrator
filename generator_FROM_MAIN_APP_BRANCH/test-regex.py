import re
LORA_BLOCK_PATTERN = re.compile(r"\{\{lora::([^\{\}]+?)\}\}")
matches = LORA_BLOCK_PATTERN.findall(" professional illustration, concept art {{lora::loras/flux/artist_styles::0.7-0.9}},")
print(matches)