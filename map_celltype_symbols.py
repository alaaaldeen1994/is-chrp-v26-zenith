import json
import os

def main():
    map_path = "data/hca_full/ensembl_to_symbol_map.json"
    ct_path = "models/cell_type_genes.json"
    
    if not os.path.exists(map_path):
        print(f"Error: {map_path} not found.")
        return
        
    if not os.path.exists(ct_path):
        print(f"Error: {ct_path} not found.")
        return
        
    print("Loading mapping file...")
    with open(map_path) as f:
        mapping_data = json.load(f)
    ensembl_to_symbol = mapping_data.get("full_ensembl_to_symbol", {})
    print(f"Loaded {len(ensembl_to_symbol)} mappings.")
    
    print("Loading cell type genes...")
    with open(ct_path) as f:
        ct_data = json.load(f)
        
    mapped_count = 0
    total_genes = 0
    
    for ct_key, ct_info in ct_data.get("cell_types", {}).items():
        # Map pro-rejuvenation genes
        new_pro = []
        for g_entry in ct_info.get("pro_rejuvenation_genes", []):
            ensembl = g_entry["gene"]
            symbol = ensembl_to_symbol.get(ensembl, ensembl)
            g_entry["gene_symbol"] = symbol
            new_pro.append(g_entry)
            total_genes += 1
            if symbol != ensembl:
                mapped_count += 1
        ct_info["pro_rejuvenation_genes"] = new_pro
        
        # Map aging marker genes
        new_aging = []
        for g_entry in ct_info.get("aging_marker_genes", []):
            ensembl = g_entry["gene"]
            symbol = ensembl_to_symbol.get(ensembl, ensembl)
            g_entry["gene_symbol"] = symbol
            new_aging.append(g_entry)
            total_genes += 1
            if symbol != ensembl:
                mapped_count += 1
        ct_info["aging_marker_genes"] = new_aging
        
    print(f"Mapped {mapped_count}/{total_genes} genes to their symbols.")
    
    # Save back
    with open(ct_path, "w") as f:
        json.dump(ct_data, f, indent=2)
    print("Successfully updated cell_type_genes.json with gene_symbol mappings!")

if __name__ == "__main__":
    main()
