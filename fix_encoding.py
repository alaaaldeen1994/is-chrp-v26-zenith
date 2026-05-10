import os

replacements = {
    "ÃƒÂ°ÅÂ¸–Ã‚Â¨ÃƒÂ¯Ã‚Â¸Ã‚Â ": "🖨️",
    "Ã¢Å¡Â Ã¯Â¸Â ": "⚠️",
    "Ã¢Â Å’": "❌",
    "Ã¢ËœÂ£Ã¯Â¸Â ": "☣️",
    "Ã°Å¸â€ºÂ¡Ã¯Â¸Â ": "🛡️",
    "Ã°Å¸â€“Â¥Ã¯Â¸Â ": "🖥️",
    "Ã¢Å“â€¦": "✅",
    "Ã¢Å“â€œ": "✓",
    "Ã¢Å“â€”": "✖",
    "Ã°Å¸â€™Â¡": "💡",
    "Ã°Å¸â€ Â¬": "🔬",
    "Ã°Å¸Å’Â ": "🌐",
    "Ã°Å¸Å½Â¯": "🎯",
    "Ã°Å¸Å¡â‚¬": "🚀",
    "Ã°Å¸Â Å’": "🏎️",
    "â€”": "—",
    "â†’": "→",
    "â€¦": "...",
    "Ã…": "Å",
    "Ã¢â€ â€™": "→",
    "Ã¢â€°Â¥": "≥",
    "Â±": "±",
    "Âµ": "μ",
    "Â©": "©",
    "Ã‚Â©": "©",
    "ÃŽÂ²": "β",
    "ÃŽÂ´": "δ",
    "Ã¢â€ Å’": "┌",
    "Ã¢â€ â‚¬": "─",
    "Ã¢â€ Â ": "┐",
    "Ã¢â€ â€š": "│",
    "Ã¢â€ Å“": "├",
    "Ã¢â€ Â¬": "┬",
    "Ã¢â€ Â¤": "┤",
    "Ã¢â€ Â´": "┴",
    "Ã¢â€ â€ ": "└",
    "Ã¢â€ Ëœ": "┘",
    "âš¡": "⚡",
    "âœ…": "✅",
    "âš ï¸": "⚠️",
    "âœ“": "✓",
    "Ã‚Â·": "·",
    "Â·": "·",
    "Ã¢â‚¬â€œ": "–",
}

html_files = [f for f in os.listdir(".") if f.endswith(".html")]

for filename in html_files:
    with open(filename, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    initial_len = len(content)
    changed = False
    for old, new in replacements.items():
        if old in content:
            content = content.replace(old, new)
            changed = True
    
    if changed:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Fixed {filename}. Content length: {initial_len} -> {len(content)}")
    else:
        print(f"No garbled characters found in {filename}.")
