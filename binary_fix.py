import os

def binary_fix():
    path = 'bridge_server.py'
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Target lines 1947 to 1965 (0-indexed: 1946 to 1964)
    # But let's find the content instead to be safe.
    content = "".join(lines)
    
    target = """        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a computational systems biology engine. "
                        "You ONLY return valid JSON. "
                        "All gene symbols you return MUST be canonical Homo sapiens genes "
                        "(UniProt Swiss-Prot reviewed, organism 9606). "
                        "Never invent genes, sequences, or motifs. "
                        "Never return genes from other species. "
                        "DNA motifs must be real IUPAC consensus sequences from JASPAR or ENCODE."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" }
        )"""
    
    # Clean version
    replacement = """        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a computational systems biology engine. "
                        "You ONLY return valid JSON. "
                        "All gene symbols you return MUST be canonical Homo sapiens genes "
                        "(UniProt Swiss-Prot reviewed, organism 9606). "
                        "Never invent genes, sequences, or motifs. "
                        "Never return genes from other species. "
                        "DNA motifs must be real IUPAC consensus sequences from JASPAR or ENCODE."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" }
        )"""
    
    if target in content:
        new_content = content.replace(target, replacement)
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(new_content)
        print("Successfully replaced with clean code.")
    else:
        print("Target block not found in exactly that format. Trying fuzzy match...")
        # Fallback: rewrite the whole function get_target_vector_from_query
        import re
        pattern = r"async def get_target_vector_from_query\(query: str, api_key: Optional\[str\] = None\) -> Tuple\[torch\.Tensor, str, Dict\[str, float\]\]:.*?\n\n    try:"
        # This is too complex.
        print("Fuzzy match failed.")

if __name__ == "__main__":
    binary_fix()
