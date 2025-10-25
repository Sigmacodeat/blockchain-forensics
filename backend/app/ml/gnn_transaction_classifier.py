"""
Graph Neural Network (GNN) Transaction Classifier
==================================================

Implements state-of-the-art GNN for blockchain transaction classification.
Uses Graph Convolutional Networks (GCN) to classify transactions based on:
- Transaction graph structure
- Node features (address metadata, transaction history)
- Edge features (transaction amounts, timestamps, gas prices)

Models:
1. GCN (Graph Convolutional Network) - Base model
2. GAT (Graph Attention Network) - Attention-based
3. GraphSAGE - Scalable for large graphs

Use Cases:
- Money laundering detection
- Fraud classification
- Risk scoring improvement
- Wallet clustering enhancement

Performance Target:
- 95%+ accuracy (vs. 88% with traditional ML)
- <500ms inference time
- Handles graphs with 1M+ nodes

Note: Requires PyTorch Geometric
Install: pip install torch-geometric torch-scatter torch-sparse
"""

from __future__ import annotations
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch_geometric.nn import GCNConv, GATConv, SAGEConv
    from torch_geometric.data import Data, DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch Geometric not available. GNN features disabled.")

logger = logging.getLogger(__name__)


@dataclass
class TransactionNode:
    """Node in transaction graph"""
    address: str
    chain: str
    features: np.ndarray  # 32-dim feature vector
    label: Optional[int] = None  # 0=legit, 1=suspicious, 2=high_risk


@dataclass
class TransactionEdge:
    """Edge in transaction graph"""
    from_address: str
    to_address: str
    amount: float
    timestamp: int
    gas_price: int
    features: np.ndarray  # 8-dim edge features


class GCNClassifier(nn.Module):
    """
    Graph Convolutional Network for transaction classification
    
    Architecture:
    - Input: Node features (32-dim) + Edge index
    - GCN Layer 1: 32 → 64
    - GCN Layer 2: 64 → 32
    - GCN Layer 3: 32 → num_classes
    - Output: Class probabilities
    """
    
    def __init__(self, num_features: int = 32, num_classes: int = 3, hidden_dim: int = 64):
        super().__init__()
        
        self.conv1 = GCNConv(num_features, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, hidden_dim // 2)
        self.conv3 = GCNConv(hidden_dim // 2, num_classes)
        
        self.dropout = nn.Dropout(0.5)
    
    def forward(self, x, edge_index):
        # Layer 1
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = self.dropout(x)
        
        # Layer 2
        x = self.conv2(x, edge_index)
        x = F.relu(x)
        x = self.dropout(x)
        
        # Layer 3
        x = self.conv3(x, edge_index)
        
        return F.log_softmax(x, dim=1)


class GATClassifier(nn.Module):
    """
    Graph Attention Network with multi-head attention
    
    Better performance than GCN but slower (4-head attention)
    """
    
    def __init__(self, num_features: int = 32, num_classes: int = 3, hidden_dim: int = 64, heads: int = 4):
        super().__init__()
        
        self.conv1 = GATConv(num_features, hidden_dim, heads=heads, dropout=0.6)
        self.conv2 = GATConv(hidden_dim * heads, num_classes, heads=1, concat=False, dropout=0.6)
    
    def forward(self, x, edge_index):
        x = F.dropout(x, p=0.6, training=self.training)
        x = F.elu(self.conv1(x, edge_index))
        x = F.dropout(x, p=0.6, training=self.training)
        x = self.conv2(x, edge_index)
        
        return F.log_softmax(x, dim=1)


class GraphSAGEClassifier(nn.Module):
    """
    GraphSAGE for scalable transaction classification
    
    Best for large graphs (1M+ nodes)
    """
    
    def __init__(self, num_features: int = 32, num_classes: int = 3, hidden_dim: int = 64):
        super().__init__()
        
        self.conv1 = SAGEConv(num_features, hidden_dim)
        self.conv2 = SAGEConv(hidden_dim, hidden_dim // 2)
        self.conv3 = SAGEConv(hidden_dim // 2, num_classes)
    
    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=0.5, training=self.training)
        
        x = self.conv2(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=0.5, training=self.training)
        
        x = self.conv3(x, edge_index)
        
        return F.log_softmax(x, dim=1)


class TransactionGNNClassifier:
    """
    Main GNN classifier for blockchain transactions
    
    Features:
    - Multiple model architectures (GCN, GAT, GraphSAGE)
    - Automatic feature extraction from transactions
    - Incremental learning (can update model with new data)
    - Explainability (attention weights for GAT)
    """
    
    def __init__(self, model_type: str = "gcn", num_features: int = 32, num_classes: int = 3):
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch Geometric not installed")
        
        self.model_type = model_type
        self.num_features = num_features
        self.num_classes = num_classes
        
        # Initialize model
        if model_type == "gcn":
            self.model = GCNClassifier(num_features, num_classes)
        elif model_type == "gat":
            self.model = GATClassifier(num_features, num_classes)
        elif model_type == "graphsage":
            self.model = GraphSAGEClassifier(num_features, num_classes)
        else:
            raise ValueError(f"Unknown model type: {model_type}")
        
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = self.model.to(self.device)
        
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.01, weight_decay=5e-4)
        
        logger.info(f"Initialized {model_type.upper()} classifier on {self.device}")
    
    def extract_node_features(self, address: str, metadata: Dict[str, Any]) -> np.ndarray:
        """
        Extract 32-dim feature vector from address
        
        Features:
        1-10: Transaction statistics (count, volume, avg_amount, etc.)
        11-20: Time-based features (first_seen, last_seen, activity_days, etc.)
        21-25: Risk indicators (sanctions, mixer_interaction, etc.)
        26-32: Graph features (degree, clustering_coef, betweenness, etc.)
        """
        features = np.zeros(32, dtype=np.float32)
        
        # Transaction stats (1-10)
        features[0] = np.log1p(metadata.get("tx_count", 0))
        features[1] = np.log1p(metadata.get("total_volume_usd", 0))
        features[2] = np.log1p(metadata.get("avg_tx_amount_usd", 0))
        features[3] = metadata.get("sent_tx_count", 0) / max(metadata.get("tx_count", 1), 1)
        features[4] = metadata.get("received_tx_count", 0) / max(metadata.get("tx_count", 1), 1)
        features[5] = np.log1p(metadata.get("unique_counterparties", 0))
        features[6] = metadata.get("self_transfers", 0) / max(metadata.get("tx_count", 1), 1)
        features[7] = np.log1p(metadata.get("max_tx_amount_usd", 0))
        features[8] = np.log1p(metadata.get("median_tx_amount_usd", 0))
        features[9] = metadata.get("std_tx_amount_usd", 0)
        
        # Time-based (11-20)
        features[10] = metadata.get("account_age_days", 0) / 365.0  # Normalize to years
        features[11] = metadata.get("days_since_last_tx", 0) / 30.0  # Normalize to months
        features[12] = metadata.get("active_days", 0) / max(metadata.get("account_age_days", 1), 1)
        features[13] = metadata.get("avg_tx_per_day", 0)
        features[14] = metadata.get("weekend_tx_ratio", 0)
        features[15] = metadata.get("night_tx_ratio", 0)  # 00:00-06:00
        features[16] = metadata.get("burst_activity_count", 0)
        features[17] = metadata.get("dormancy_periods", 0)
        features[18] = metadata.get("time_regularity_score", 0)  # 0-1
        features[19] = metadata.get("timezone_consistency", 0)  # 0-1
        
        # Risk indicators (21-25)
        features[20] = 1.0 if metadata.get("is_sanctioned", False) else 0.0
        features[21] = 1.0 if metadata.get("mixer_interaction", False) else 0.0
        features[22] = 1.0 if metadata.get("darknet_interaction", False) else 0.0
        features[23] = metadata.get("risk_score", 0) / 100.0  # Normalize 0-100 to 0-1
        features[24] = 1.0 if metadata.get("is_contract", False) else 0.0
        
        # Graph features (26-32)
        features[25] = np.log1p(metadata.get("in_degree", 0))
        features[26] = np.log1p(metadata.get("out_degree", 0))
        features[27] = metadata.get("clustering_coefficient", 0)
        features[28] = np.log1p(metadata.get("betweenness_centrality", 0))
        features[29] = np.log1p(metadata.get("closeness_centrality", 0))
        features[30] = np.log1p(metadata.get("eigenvector_centrality", 0))
        features[31] = metadata.get("community_id", 0) / 100.0  # Normalize
        
        return features
    
    def build_graph_data(
        self,
        nodes: List[TransactionNode],
        edges: List[TransactionEdge]
    ) -> Data:
        """
        Build PyTorch Geometric Data object from nodes and edges
        """
        # Create node features matrix
        node_features = torch.tensor(
            np.stack([node.features for node in nodes]),
            dtype=torch.float
        )
        
        # Create edge index
        address_to_idx = {node.address: i for i, node in enumerate(nodes)}
        edge_index = []
        for edge in edges:
            if edge.from_address in address_to_idx and edge.to_address in address_to_idx:
                edge_index.append([
                    address_to_idx[edge.from_address],
                    address_to_idx[edge.to_address]
                ])
        
        edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
        
        # Create labels if available
        labels = [node.label for node in nodes if node.label is not None]
        y = torch.tensor(labels, dtype=torch.long) if labels else None
        
        data = Data(x=node_features, edge_index=edge_index, y=y)
        
        return data
    
    def train(
        self,
        train_data: Data,
        epochs: int = 200,
        early_stopping_patience: int = 20
    ) -> Dict[str, List[float]]:
        """
        Train GNN model
        
        Returns training history
        """
        self.model.train()
        
        train_data = train_data.to(self.device)
        
        history = {"loss": [], "accuracy": []}
        best_loss = float('inf')
        patience_counter = 0
        
        for epoch in range(epochs):
            self.optimizer.zero_grad()
            
            out = self.model(train_data.x, train_data.edge_index)
            loss = F.nll_loss(out, train_data.y)
            
            loss.backward()
            self.optimizer.step()
            
            # Calculate accuracy
            pred = out.argmax(dim=1)
            accuracy = (pred == train_data.y).float().mean().item()
            
            history["loss"].append(loss.item())
            history["accuracy"].append(accuracy)
            
            # Early stopping
            if loss.item() < best_loss:
                best_loss = loss.item()
                patience_counter = 0
            else:
                patience_counter += 1
            
            if patience_counter >= early_stopping_patience:
                logger.info(f"Early stopping at epoch {epoch}")
                break
            
            if epoch % 20 == 0:
                logger.info(f"Epoch {epoch}: Loss={loss.item():.4f}, Acc={accuracy:.4f}")
        
        return history
    
    def predict(self, data: Data) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict transaction classes
        
        Returns:
        - predictions: Class labels
        - probabilities: Class probabilities
        """
        self.model.eval()
        
        data = data.to(self.device)
        
        with torch.no_grad():
            out = self.model(data.x, data.edge_index)
            pred = out.argmax(dim=1).cpu().numpy()
            probs = torch.exp(out).cpu().numpy()
        
        return pred, probs
    
    def save_model(self, path: str):
        """Save model weights"""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'model_type': self.model_type
        }, path)
        logger.info(f"Model saved to {path}")
    
    def load_model(self, path: str):
        """Load model weights"""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        logger.info(f"Model loaded from {path}")


# Example usage and benchmarks
def benchmark_gnn_models():
    """Benchmark different GNN architectures"""
    if not TORCH_AVAILABLE:
        logger.warning("PyTorch Geometric not available. Skipping benchmark.")
        return
    
    # Create synthetic dataset
    num_nodes = 1000
    num_edges = 5000
    
    # Random node features
    x = torch.randn(num_nodes, 32)
    
    # Random edges
    edge_index = torch.randint(0, num_nodes, (2, num_edges))
    
    # Random labels
    y = torch.randint(0, 3, (num_nodes,))
    
    data = Data(x=x, edge_index=edge_index, y=y)
    
    models = {
        "GCN": GCNClassifier(),
        "GAT": GATClassifier(),
        "GraphSAGE": GraphSAGEClassifier()
    }
    
    results = {}
    
    for name, model in models.items():
        import time
        start = time.time()
        
        # Forward pass
        out = model(data.x, data.edge_index)
        
        duration = time.time() - start
        
        results[name] = {
            "inference_time_ms": duration * 1000,
            "params": sum(p.numel() for p in model.parameters())
        }
        
        logger.info(f"{name}: {duration*1000:.2f}ms, {results[name]['params']} params")
    
    return results
