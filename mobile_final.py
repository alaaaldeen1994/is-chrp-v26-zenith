import os

def apply_mobile_css():
    path = 'trials.html'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    mobile_css = """
        /* --- Mobile Responsiveness (Institutional Overhaul) --- */
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
        new_content = content.replace('    </style>', mobile_css + '    </style>')
        # Safety check for different indentations
        if new_content == content:
            new_content = content.replace('</style>', mobile_css + '</style>')
            
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(new_content)
        print("Successfully applied mobile CSS to trials.html")
    else:
        print("Style tag not found.")

if __name__ == "__main__":
    apply_mobile_css()
