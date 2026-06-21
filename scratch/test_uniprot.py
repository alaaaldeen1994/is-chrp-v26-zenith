import json
import asyncio
from bridge_server import uniprot_lookup

async def test_gene(gene):
    try:
        res = await uniprot_lookup(gene)
        print(f"Gene: {gene}")
        print(f"  Accession: {res.get('accession')}")
        print(f"  Length: {res.get('sequence_length')} AA")
        seq = res.get('sequence')
        print(f"  Seq (first 50): {seq[:50]}..." if seq else "  No sequence")
    except Exception as e:
        print(f"Gene: {gene} failed: {e}")

async def main():
    await test_gene("SOX5")
    await test_gene("ZFHX3")
    await test_gene("NKX2-5")

if __name__ == "__main__":
    asyncio.run(main())
