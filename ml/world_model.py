import torch
import torch.nn as nn
import torch.nn.functional as F

class TemporalAttention(nn.Module):
    """
    Native Attention Mechanism to fulfill the Explainability requirement.
    Calculates which past time-window (10s block) was most important for the prediction.
    """
    def __init__(self, hidden_dim):
        super(TemporalAttention, self).__init__()
        self.attention = nn.Linear(hidden_dim, 1, bias=False)

    def forward(self, lstm_outputs):
        # lstm_outputs shape: (batch_size, sequence_length, hidden_dim)
        attn_weights = F.softmax(self.attention(lstm_outputs), dim=1)
        # Context vector is the weighted sum of LSTM outputs
        context_vector = torch.sum(attn_weights * lstm_outputs, dim=1)
        return context_vector, attn_weights

class PrognosWorldModel(nn.Module):
    """
    CNN-LSTM Hybrid World Model.
    Learns P(S_{t+1} | S_t) and outputs MITRE ATT&CK stages + Infiltration Probability.
    """
    def __init__(self, input_features, cnn_out_channels=64, lstm_hidden_dim=128, num_classes=5):
        super(PrognosWorldModel, self).__init__()
        
        # 1. Spatial Encoder (1D-CNN)
        # Compresses the 27 Zeek features into a robust latent state vector
        self.cnn = nn.Sequential(
            nn.Conv1d(in_channels=input_features, out_channels=cnn_out_channels, kernel_size=1),
            nn.BatchNorm1d(cnn_out_channels),
            nn.ReLU(),
            nn.Dropout(0.2)
        )
        
        # 2. Dynamics Simulator (LSTM)
        # Learns the temporal transition dynamics over the sliding window
        self.lstm = nn.LSTM(
            input_size=cnn_out_channels, 
            hidden_size=lstm_hidden_dim, 
            num_layers=2, # Kept at 2 layers for fast edge-inference
            batch_first=True, 
            dropout=0.2
        )
        
        # 3. Explainability (Attention)
        self.attention = TemporalAttention(lstm_hidden_dim)
        
        # 4. Output Heads
        # Head A: MITRE ATT&CK Stage Classifier (Multiclass)
        # 0: Normal, 1: Recon, 2: Initial Access, 3: Lateral Movement, 4: C2
        self.mitre_classifier = nn.Sequential(
            nn.Linear(lstm_hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, num_classes)
        )
        
        # Head B: Infiltration Probability Score (Binary: 0 to 1)
        self.probability_head = nn.Sequential(
            nn.Linear(lstm_hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        # Input shape expected: (batch_size, sequence_length, features)
        batch_size, seq_len, features = x.size()
        
        # Reshape for CNN: (batch_size * seq_len, features, 1)
        x = x.view(batch_size * seq_len, features, 1)
        
        # Pass through CNN
        cnn_out = self.cnn(x)
        cnn_out = cnn_out.view(batch_size, seq_len, -1) # Shape: (batch_size, seq_len, cnn_out_channels)
        
        # Pass through LSTM
        lstm_out, (h_n, c_n) = self.lstm(cnn_out)
        
        # Pass through Attention Mechanism
        context_vector, attn_weights = self.attention(lstm_out)
        
        # Pass through Output Heads
        mitre_logits = self.mitre_classifier(context_vector)
        infiltration_prob = self.probability_head(context_vector)
        
        return mitre_logits, infiltration_prob, attn_weights

if __name__ == "__main__":
    # Quick architecture test
    model = PrognosWorldModel(input_features=27)
    dummy_input = torch.randn(32, 6, 27) # 32 batches, 6 windows (60s context), 27 features
    mitre, prob, attn = model(dummy_input)
    print(f"Model Parameters: {sum(p.numel() for p in model.parameters())}")
    print(f"MITRE Output Shape: {mitre.shape}") # Should be (32, 5)
    print(f"Probability Output Shape: {prob.shape}") # Should be (32, 1)
    print(f"Attention Weights Shape: {attn.shape}") # Should be (32, 6, 1)
