import os

def patch_mobile():
    path = 'trials.html'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    css_patch = """
        @media (max-width: 1024px) {
            body { overflow: auto !important; height: auto !important; }
            .flex.flex-1 { flex-direction: column !important; overflow: visible !important; height: auto !important; }
            aside.w-96 { width: 100% !important; border-right: none; border-bottom: 1px solid #e2e8f0; padding: 1.5rem; overflow: visible !important; }
            main { padding: 1.5rem !important; gap: 1.5rem !important; }
            header { padding: 1rem 1.5rem !important; flex-direction: column; gap: 1rem; align-items: flex-start; height: auto !important; }
            header .flex.gap-4 { width: 100%; }
            .tag-institutional { width: 100%; text-align: center; font-size: 8px; }
            .grid.grid-cols-3 { grid-template-cols: 1fr !important; height: auto !important; }
            .col-span-2 { grid-column: span 1 / span 1 !important; }
            .card-elite { padding: 1.5rem !important; border-radius: 1.5rem; min-height: 350px; }
            canvas { max-height: 300px; }
        }
    """
    
    if '</style>' in content:
        new_content = content.replace('    </style>', css_patch + '    </style>')
        # If it doesn't have 4 spaces
        if new_content == content:
             new_content = content.replace('</style>', css_patch + '</style>')
             
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(new_content)
        print("Patched trials.html for mobile.")
    else:
        print("Style tag not found.")

if __name__ == "__main__":
    patch_mobile()
