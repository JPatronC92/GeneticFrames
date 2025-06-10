"""
Blockchain NFT Integration for DNA Art Generator
Supports Ethereum mainnet, testnets, and IPFS for metadata storage
"""
import os
import json
import hashlib
import base64
from datetime import datetime
from typing import Optional, Dict, Any
import requests
from web3 import Web3
from eth_account import Account
import ipfshttpclient
from PIL import Image
import io
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DNANFTManager:
    """Manages NFT creation and blockchain interactions for DNA art"""
    
    def __init__(self):
        # Blockchain configuration
        self.rpc_url = os.getenv("ETH_RPC_URL", "https://mainnet.infura.io/v3/")
        self.private_key = os.getenv("ETH_PRIVATE_KEY")
        self.contract_address = os.getenv("NFT_CONTRACT_ADDRESS")
        
        # IPFS configuration
        self.ipfs_gateway = os.getenv("IPFS_GATEWAY", "https://ipfs.infura.io:5001")
        self.ipfs_api_key = os.getenv("IPFS_API_KEY")
        self.ipfs_secret = os.getenv("IPFS_API_SECRET")
        
        # Initialize Web3
        self.w3 = None
        self.account = None
        self._initialize_blockchain()
        
        # NFT Contract ABI (simplified ERC-721)
        self.contract_abi = [
            {
                "inputs": [
                    {"name": "to", "type": "address"},
                    {"name": "tokenURI", "type": "string"}
                ],
                "name": "mint",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"name": "tokenId", "type": "uint256"}],
                "name": "tokenURI",
                "outputs": [{"name": "", "type": "string"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
    
    def _initialize_blockchain(self):
        """Initialize blockchain connection"""
        try:
            if self.rpc_url and "infura" in self.rpc_url:
                infura_key = os.getenv("INFURA_API_KEY")
                if infura_key:
                    self.rpc_url = f"https://mainnet.infura.io/v3/{infura_key}"
            
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            
            if self.private_key:
                self.account = Account.from_key(self.private_key)
                logger.info(f"Blockchain initialized. Account: {self.account.address}")
            else:
                logger.warning("No private key provided. NFT minting will be unavailable.")
                
        except Exception as e:
            logger.error(f"Blockchain initialization failed: {e}")
    
    def generate_dna_hash(self, sequence: str, organism: str) -> str:
        """Generate unique hash from DNA sequence"""
        data = f"{organism}_{sequence}_{datetime.now().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def create_nft_metadata(self, seq_record, organism_name: str, gc_content: float, 
                          base_counts: Dict, image_data: bytes = None) -> Dict[str, Any]:
        """Create NFT metadata following OpenSea standards"""
        
        dna_hash = self.generate_dna_hash(str(seq_record.seq), organism_name)
        
        # Calculate rarity traits
        sequence_length = len(seq_record.seq)
        rarity_score = self._calculate_rarity_score(gc_content, sequence_length, base_counts)
        
        metadata = {
            "name": f"DNA Art: {organism_name}",
            "description": f"Unique DNA visualization artwork generated from {organism_name} genetic sequence. "
                          f"This NFT represents {sequence_length:,} base pairs with {gc_content:.2f}% GC content.",
            "image": "",  # Will be filled with IPFS hash
            "external_url": "https://your-dna-art-generator.com",
            "attributes": [
                {
                    "trait_type": "Organism",
                    "value": organism_name
                },
                {
                    "trait_type": "Sequence Length",
                    "value": sequence_length,
                    "display_type": "number"
                },
                {
                    "trait_type": "GC Content",
                    "value": gc_content,
                    "display_type": "number"
                },
                {
                    "trait_type": "Adenine Count",
                    "value": base_counts.get('A', 0),
                    "display_type": "number"
                },
                {
                    "trait_type": "Thymine Count",
                    "value": base_counts.get('T', 0),
                    "display_type": "number"
                },
                {
                    "trait_type": "Cytosine Count",
                    "value": base_counts.get('C', 0),
                    "display_type": "number"
                },
                {
                    "trait_type": "Guanine Count",
                    "value": base_counts.get('G', 0),
                    "display_type": "number"
                },
                {
                    "trait_type": "Rarity Score",
                    "value": rarity_score,
                    "display_type": "number"
                },
                {
                    "trait_type": "DNA Hash",
                    "value": dna_hash
                },
                {
                    "trait_type": "NCBI ID",
                    "value": seq_record.id
                },
                {
                    "trait_type": "Generation Date",
                    "value": datetime.now().strftime("%Y-%m-%d")
                }
            ],
            "properties": {
                "dna_sequence_sample": str(seq_record.seq)[:100],
                "generation_timestamp": datetime.now().isoformat(),
                "ncbi_accession": seq_record.id,
                "sequence_description": seq_record.description
            }
        }
        
        return metadata
    
    def _calculate_rarity_score(self, gc_content: float, length: int, base_counts: Dict) -> float:
        """Calculate rarity score based on genetic characteristics"""
        # Base rarity on GC content deviation from 50%
        gc_deviation = abs(gc_content - 50.0)
        
        # Length rarity (very short or very long sequences are rarer)
        if length < 1000:
            length_rarity = (1000 - length) / 1000 * 20
        elif length > 100000:
            length_rarity = min((length - 100000) / 100000 * 30, 50)
        else:
            length_rarity = 0
        
        # Base composition balance rarity
        total_bases = sum(base_counts.values())
        if total_bases > 0:
            expected_per_base = total_bases / 4
            composition_variance = sum(abs(count - expected_per_base) for count in base_counts.values())
            composition_rarity = composition_variance / total_bases * 25
        else:
            composition_rarity = 0
        
        rarity_score = gc_deviation + length_rarity + composition_rarity
        return round(min(rarity_score, 100), 2)
    
    def upload_to_ipfs(self, data: bytes, filename: str) -> Optional[str]:
        """Upload data to IPFS and return hash"""
        try:
            if self.ipfs_api_key and self.ipfs_secret:
                # Use Infura IPFS
                url = "https://ipfs.infura.io:5001/api/v0/add"
                auth = (self.ipfs_api_key, self.ipfs_secret)
                files = {'file': (filename, data)}
                
                response = requests.post(url, files=files, auth=auth)
                if response.status_code == 200:
                    result = response.json()
                    ipfs_hash = result.get('Hash')
                    logger.info(f"File uploaded to IPFS: {ipfs_hash}")
                    return ipfs_hash
            else:
                # Try local IPFS node
                with ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001/http') as client:
                    result = client.add_bytes(data)
                    logger.info(f"File uploaded to local IPFS: {result}")
                    return result
                    
        except Exception as e:
            logger.error(f"IPFS upload failed: {e}")
            return None
    
    def create_nft_image(self, plotly_figure, width: int = 1200, height: int = 800) -> bytes:
        """Convert Plotly figure to high-quality image for NFT"""
        try:
            # Export as PNG with high DPI
            img_bytes = plotly_figure.to_image(
                format="png", 
                width=width, 
                height=height, 
                scale=3  # High resolution for NFT
            )
            
            # Optionally enhance the image
            img = Image.open(io.BytesIO(img_bytes))
            
            # Add watermark or signature if needed
            # img = self._add_nft_watermark(img)
            
            # Convert back to bytes
            output = io.BytesIO()
            img.save(output, format='PNG', quality=100, optimize=True)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Image creation failed: {e}")
            return None
    
    def prepare_nft_package(self, seq_record, organism_name: str, gc_content: float, 
                          base_counts: Dict, plotly_figure) -> Optional[Dict]:
        """Prepare complete NFT package with image and metadata"""
        try:
            # Create high-quality image
            image_data = self.create_nft_image(plotly_figure)
            if not image_data:
                return None
            
            # Upload image to IPFS
            image_filename = f"dna_art_{seq_record.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            image_hash = self.upload_to_ipfs(image_data, image_filename)
            if not image_hash:
                logger.warning("IPFS upload failed, using base64 encoding")
                image_url = f"data:image/png;base64,{base64.b64encode(image_data).decode()}"
            else:
                image_url = f"https://ipfs.io/ipfs/{image_hash}"
            
            # Create metadata
            metadata = self.create_nft_metadata(seq_record, organism_name, gc_content, base_counts)
            metadata["image"] = image_url
            
            # Upload metadata to IPFS
            metadata_json = json.dumps(metadata, indent=2)
            metadata_filename = f"dna_metadata_{seq_record.id}.json"
            metadata_hash = self.upload_to_ipfs(metadata_json.encode(), metadata_filename)
            
            if metadata_hash:
                metadata_uri = f"https://ipfs.io/ipfs/{metadata_hash}"
            else:
                # Fallback to base64 encoding
                metadata_uri = f"data:application/json;base64,{base64.b64encode(metadata_json.encode()).decode()}"
            
            return {
                "metadata": metadata,
                "metadata_uri": metadata_uri,
                "image_data": image_data,
                "image_uri": image_url,
                "ipfs_hashes": {
                    "image": image_hash,
                    "metadata": metadata_hash
                }
            }
            
        except Exception as e:
            logger.error(f"NFT package preparation failed: {e}")
            return None
    
    def mint_nft(self, to_address: str, metadata_uri: str) -> Optional[Dict]:
        """Mint NFT on blockchain"""
        if not self.w3 or not self.account or not self.contract_address:
            return {"error": "Blockchain not properly configured"}
        
        try:
            # Get contract instance
            contract = self.w3.eth.contract(
                address=self.contract_address,
                abi=self.contract_abi
            )
            
            # Build transaction
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            gas_price = self.w3.eth.gas_price
            
            transaction = contract.functions.mint(to_address, metadata_uri).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gas': 300000,  # Adjust as needed
                'gasPrice': gas_price,
            })
            
            # Sign transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return {
                "success": True,
                "transaction_hash": receipt.transactionHash.hex(),
                "gas_used": receipt.gasUsed,
                "block_number": receipt.blockNumber,
                "contract_address": self.contract_address
            }
            
        except Exception as e:
            logger.error(f"NFT minting failed: {e}")
            return {"error": str(e)}
    
    def get_blockchain_status(self) -> Dict:
        """Get current blockchain connection status"""
        status = {
            "connected": False,
            "network": "unknown",
            "account_configured": bool(self.account),
            "contract_configured": bool(self.contract_address),
            "balance": "0"
        }
        
        try:
            if self.w3 and self.w3.is_connected():
                status["connected"] = True
                status["network"] = self.w3.eth.chain_id
                
                if self.account:
                    balance_wei = self.w3.eth.get_balance(self.account.address)
                    status["balance"] = f"{self.w3.from_wei(balance_wei, 'ether'):.4f} ETH"
                    status["address"] = self.account.address
                    
        except Exception as e:
            status["error"] = str(e)
            
        return status

# Global instance
nft_manager = DNANFTManager()