with open("index_c4a3865.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Extract from line 5376 to 5647
extracted_lines = lines[5375:5648]
section_content = "".join(extracted_lines)

with open("scratch/developer_api_section.html", "w", encoding="utf-8") as f:
    f.write(section_content)

print(f"Extracted {len(extracted_lines)} lines.")
