"""
Test script to verify all functionality of the Digital Genetic Ark
"""
import os
import sys
from Bio import Entrez, SeqIO
from Bio.SeqUtils import gc_fraction
import requests

def test_ncbi_connection():
    """Test NCBI GenBank API connection"""
    print("Testing NCBI connection...")
    
    # Check credentials
    email = os.getenv("ENTREZ_EMAIL", "researcher@example.com")
    api_key = os.getenv("NCBI_API_KEY")
    
    print(f"Email configured: {email}")
    print(f"API Key configured: {'Yes' if api_key else 'No'}")
    
    # Configure Entrez
    Entrez.email = email
    if api_key:
        Entrez.api_key = api_key
    
    try:
        # Test search for a simple organism
        search = Entrez.esearch(db="nucleotide", term="Homo sapiens", retmax=1)
        record = Entrez.read(search)
        search.close()
        
        if record["IdList"]:
            print(f"✓ NCBI search successful. Found ID: {record['IdList'][0]}")
            
            # Test sequence fetch
            seq_id = record["IdList"][0]
            fetch = Entrez.efetch(db="nucleotide", id=seq_id, rettype="fasta", retmode="text")
            seq_record = SeqIO.read(fetch, "fasta")
            fetch.close()
            
            print(f"✓ Sequence fetch successful. Length: {len(seq_record.seq)} bp")
            print(f"✓ GC content calculation: {gc_fraction(str(seq_record.seq)) * 100:.2f}%")
            return True
        else:
            print("✗ No sequences found")
            return False
            
    except Exception as e:
        print(f"✗ NCBI connection failed: {e}")
        return False

def test_database_connection():
    """Test PostgreSQL database connection"""
    print("\nTesting database connection...")
    
    try:
        from database import create_tables, get_database_stats
        
        # Test table creation
        if create_tables():
            print("✓ Database tables created/verified")
        else:
            print("✗ Database table creation failed")
            return False
        
        # Test statistics query
        stats = get_database_stats()
        if stats:
            print(f"✓ Database query successful. Sequences: {stats.get('total_sequences', 0)}")
            return True
        else:
            print("✓ Database connected (empty)")
            return True
            
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def test_species_catalog():
    """Test species catalog functionality"""
    print("\nTesting species catalog...")
    
    try:
        from species_catalog import (
            FEATURED_SPECIES, get_species_info, 
            get_rarity_multiplier, suggest_search_terms
        )
        
        # Test catalog loading
        total_species = sum(len(cat['species']) for cat in FEATURED_SPECIES.values())
        print(f"✓ Species catalog loaded. {total_species} featured species")
        
        # Test species info lookup
        tiger_info = get_species_info("Panthera tigris altaica")
        if tiger_info:
            print(f"✓ Species lookup successful: {tiger_info['common_name']}")
        else:
            print("✗ Species lookup failed")
            return False
        
        # Test rarity multiplier
        rarity = get_rarity_multiplier("Panthera tigris altaica")
        print(f"✓ Rarity calculation: {rarity}x")
        
        # Test search suggestions
        suggestions = suggest_search_terms("tiger")
        print(f"✓ Search suggestions: {len(suggestions)} results")
        
        return True
        
    except Exception as e:
        print(f"✗ Species catalog test failed: {e}")
        return False

def test_blockchain_nft():
    """Test NFT/blockchain functionality"""
    print("\nTesting NFT functionality...")
    
    try:
        from blockchain_nft import nft_manager
        
        # Test blockchain status
        status = nft_manager.get_blockchain_status()
        print(f"✓ Blockchain status check: Connected={status.get('connected', False)}")
        
        # Test metadata generation (mock data)
        class MockSeqRecord:
            def __init__(self):
                self.id = "TEST_001"
                self.description = "Test sequence"
                self.seq = "ATCGATCGATCG" * 100
        
        mock_record = MockSeqRecord()
        metadata = nft_manager.create_nft_metadata(
            mock_record, "Homo sapiens", 50.0, 
            {'A': 300, 'T': 300, 'C': 300, 'G': 300}
        )
        
        if metadata and 'name' in metadata:
            print(f"✓ NFT metadata generation successful")
            print(f"✓ Rarity score: {next((attr['value'] for attr in metadata['attributes'] if attr['trait_type'] == 'Rarity Score'), 'N/A')}")
            return True
        else:
            print("✗ NFT metadata generation failed")
            return False
            
    except Exception as e:
        print(f"✗ NFT functionality test failed: {e}")
        return False

def test_streamlit_app():
    """Test if Streamlit app is running"""
    print("\nTesting Streamlit app...")
    
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        if response.status_code == 200:
            print("✓ Streamlit app is running and responsive")
            return True
        else:
            print(f"✗ Streamlit app returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Streamlit app test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=== Digital Genetic Ark - Functionality Test ===\n")
    
    tests = [
        ("NCBI GenBank API", test_ncbi_connection),
        ("PostgreSQL Database", test_database_connection),
        ("Species Catalog", test_species_catalog),
        ("NFT/Blockchain", test_blockchain_nft),
        ("Streamlit App", test_streamlit_app)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        results[test_name] = test_func()
    
    print("\n=== Test Summary ===")
    passed = 0
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All systems operational! Digital Genetic Ark ready for launch.")
    elif passed >= len(tests) * 0.8:
        print("⚠️  Most systems operational. Minor issues detected.")
    else:
        print("❌ Critical issues detected. Review required.")

if __name__ == "__main__":
    main()