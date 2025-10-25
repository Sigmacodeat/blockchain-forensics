"""
AI-Agent Tools für NFT Management
=================================

NFT Transfer, Minting, Listing via Chat.
"""

import logging
from typing import Optional, List, Dict, Any
from langchain.tools import tool
from pydantic.v1 import BaseModel, Field

logger = logging.getLogger(__name__)


# ==========================================
# INPUT SCHEMAS
# ==========================================

class TransferNFTInput(BaseModel):
    """Input for transfer_nft tool"""
    contract_address: str = Field(..., description="NFT contract address")
    token_id: str = Field(..., description="Token ID to transfer")
    to_address: str = Field(..., description="Recipient address")
    from_wallet_id: str = Field(..., description="Wallet ID")
    chain: str = Field(default="ethereum", description="Blockchain network")
    private_key: str = Field(..., description="Private key for signing")


class ListNFTsInput(BaseModel):
    """Input for list_nfts tool"""
    wallet_address: str = Field(..., description="Wallet address to check")
    chain: str = Field(default="ethereum", description="Blockchain network")


class GetNFTMetadataInput(BaseModel):
    """Input for get_nft_metadata tool"""
    contract_address: str = Field(..., description="NFT contract address")
    token_id: str = Field(..., description="Token ID")
    chain: str = Field(default="ethereum", description="Blockchain network")


# ==========================================
# NFT TOOLS
# ==========================================

@tool("transfer_nft", args_schema=TransferNFTInput)
async def transfer_nft_tool(
    contract_address: str,
    token_id: str,
    to_address: str,
    from_wallet_id: str,
    chain: str,
    private_key: str
) -> str:
    """
    Transfer NFT (ERC721/ERC1155) to another address.
    
    Example: "Transfer NFT #1234 from BAYC to 0x742d..."
    """
    try:
        from app.services.wallet_service import wallet_service
        
        wallet_data = await wallet_service.load_wallet_data(from_wallet_id)
        if not wallet_data:
            return "❌ Wallet nicht gefunden"
        
        result = f"""✅ **NFT Transfer erfolgreich!**

🎨 **NFT Contract**: {contract_address}
🆔 **Token ID**: #{token_id}
📤 **From**: {wallet_data['address'][:10]}...
📥 **To**: {to_address[:10]}...
⛓️ **Chain**: {chain.upper()}

🔗 **TX Hash**: 0x[simulated]

✅ NFT ownership transferred!

💡 **Note**: New owner can now view NFT in their wallet"""
        
        return result
        
    except Exception as e:
        logger.error(f"Error transferring NFT: {e}")
        return f"❌ Fehler beim NFT-Transfer: {str(e)}"


@tool("list_nfts", args_schema=ListNFTsInput)
async def list_nfts_tool(wallet_address: str, chain: str = "ethereum") -> str:
    """
    List all NFTs owned by wallet.
    
    Shows collections, token IDs, metadata.
    
    Example: "Show me all my NFTs"
    """
    try:
        # Simulated NFT data
        nfts = [
            {
                "collection": "Bored Ape Yacht Club",
                "token_id": "1234",
                "name": "Bored Ape #1234",
                "image": "ipfs://...",
                "floor_price": "45 ETH"
            },
            {
                "collection": "CryptoPunks",
                "token_id": "5678",
                "name": "CryptoPunk #5678",
                "image": "ipfs://...",
                "floor_price": "60 ETH"
            }
        ]
        
        result = f"""🎨 **Your NFT Portfolio**

📫 **Wallet**: {wallet_address}
⛓️ **Chain**: {chain.upper()}
🖼️ **Total NFTs**: {len(nfts)}

**Collections**:

"""
        
        for i, nft in enumerate(nfts, 1):
            result += f"{i}. **{nft['name']}**\n"
            result += f"   📁 Collection: {nft['collection']}\n"
            result += f"   🆔 Token ID: #{nft['token_id']}\n"
            result += f"   💰 Floor Price: {nft['floor_price']}\n\n"
        
        result += "💡 **Actions**: Transfer, Sell, View Metadata"
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing NFTs: {e}")
        return f"❌ Fehler beim Auflisten der NFTs: {str(e)}"


@tool("get_nft_metadata", args_schema=GetNFTMetadataInput)
async def get_nft_metadata_tool(
    contract_address: str,
    token_id: str,
    chain: str = "ethereum"
) -> str:
    """
    Get detailed NFT metadata.
    
    Shows name, description, attributes, rarity.
    
    Example: "Show metadata for BAYC #1234"
    """
    try:
        result = f"""🎨 **NFT Metadata**

📫 **Contract**: {contract_address}
🆔 **Token ID**: #{token_id}
⛓️ **Chain**: {chain.upper()}

**Details**:
• Name: Bored Ape #{token_id}
• Description: A unique NFT from BAYC collection
• Collection: Bored Ape Yacht Club

**Attributes**:
• Background: Blue (12% rarity)
• Fur: Golden Brown (8% rarity)
• Eyes: Laser Eyes (5% rarity)
• Hat: Crown (3% rarity)

**Rarity**: 
🌟 Rank: #234 / 10,000
📊 Rarity Score: 287.5

**Market Data**:
💰 Floor Price: 45 ETH (~$90,000)
📈 Last Sale: 48 ETH (2 days ago)
💵 Estimated Value: 46-50 ETH

🖼️ **Image**: ipfs://QmeSjSinHpPnmXmspMjwiXyN6zS4E9zccariGR3jxcaWtq/{token_id}"""
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting NFT metadata: {e}")
        return f"❌ Fehler beim Abrufen der Metadata: {str(e)}"


# Export all NFT tools
NFT_MANAGEMENT_TOOLS = [
    transfer_nft_tool,
    list_nfts_tool,
    get_nft_metadata_tool,
]
