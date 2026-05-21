"""
Tier 2 — PyTorch Neural Decision Model
Feedforward network for Traders, Business Owners, Bankers, Manufacturers.

Input vector (13 features):
    wealth_norm, inflation_norm, market_confidence_norm,
    unemployment_norm, resource_index_norm,
    emotion_fear, emotion_greed, emotion_trust,
    emotion_optimism, emotion_stress, emotion_panic,
    social_pressure, risk_score

Output (6 classes):
    BUY, SELL, SAVE, INVEST, PANIC, COOPERATE
"""
import os
import logging
import numpy as np

logger = logging.getLogger(__name__)

ACTIONS = ['buy', 'sell', 'save', 'invest', 'panic', 'cooperate']
INPUT_DIM = 13
HIDDEN_DIM = 64
OUTPUT_DIM = len(ACTIONS)

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'neural_weights.pt')

_model = None
_device = None


def _get_device():
    global _device
    if _device is None:
        try:
            import torch
            _device = torch.device('cpu')
        except ImportError:
            _device = None
    return _device


def build_model():
    """Build and return the neural network model."""
    import torch
    import torch.nn as nn

    class EconomyNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(INPUT_DIM, HIDDEN_DIM),
                nn.ReLU(),
                nn.Dropout(0.1),
                nn.Linear(HIDDEN_DIM, HIDDEN_DIM),
                nn.ReLU(),
                nn.Linear(HIDDEN_DIM, OUTPUT_DIM),
            )

        def forward(self, x):
            return self.net(x)

    return EconomyNet()


def get_model():
    """Lazy-load model with fallback retrain if weights are corrupt."""
    global _model
    if _model is not None:
        return _model

    import torch
    device = _get_device()
    model = build_model().to(device)

    if os.path.exists(MODEL_PATH):
        try:
            model.load_state_dict(
                torch.load(MODEL_PATH, map_location=device, weights_only=True)
            )
            model.eval()
            logger.info('Neural model loaded from disk.')
            _model = model
            return _model
        except Exception as e:
            logger.warning(f'Model load failed ({e}) — retraining.')
            # Delete corrupt weights file
            try:
                os.remove(MODEL_PATH)
            except Exception:
                pass

    _model = train_synthetic(model, device)
    return _model

def generate_synthetic_data(n_samples: int = 5000):
    """
    Generate synthetic economic scenarios for offline training.
    Labels are heuristically assigned based on economic conditions.
    """
    import torch

    X = []
    y = []

    for _ in range(n_samples):
        wealth_norm = np.random.uniform(0, 1)
        inflation = np.random.uniform(0, 1)
        confidence = np.random.uniform(0, 1)
        unemployment = np.random.uniform(0, 1)
        resource_idx = np.random.uniform(0, 1)
        fear = np.random.uniform(0, 1)
        greed = np.random.uniform(0, 1)
        trust = np.random.uniform(0, 1)
        optimism = np.random.uniform(0, 1)
        stress = np.random.uniform(0, 1)
        panic = np.random.uniform(0, 1)
        social_pressure = np.random.uniform(0, 1)
        risk_score = np.random.uniform(0, 1)

        features = [
            wealth_norm, inflation, confidence, unemployment, resource_idx,
            fear, greed, trust, optimism, stress, panic,
            social_pressure, risk_score,
        ]

        # Heuristic label assignment
        if panic > 0.7 or fear > 0.8:
            label = 4  # PANIC
        elif greed > 0.7 and confidence > 0.6 and wealth_norm > 0.5:
            label = 3  # INVEST
        elif inflation > 0.7 or unemployment > 0.7:
            label = 2  # SAVE
        elif optimism > 0.6 and confidence > 0.5:
            label = 0  # BUY
        elif fear > 0.5 or confidence < 0.3:
            label = 1  # SELL
        elif trust > 0.6:
            label = 5  # COOPERATE
        else:
            label = 2  # SAVE default

        X.append(features)
        y.append(label)

    return (
        torch.tensor(X, dtype=torch.float32),
        torch.tensor(y, dtype=torch.long),
    )


def train_synthetic(model, device, epochs: int = 30):
    """Train the model on synthetic data and save weights."""
    import torch
    import torch.nn as nn
    import torch.optim as optim

    logger.info('Training neural model on synthetic economic data...')

    X, y = generate_synthetic_data(5000)
    X, y = X.to(device), y.to(device)

    optimizer = optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.CrossEntropyLoss()

    model.train()
    for epoch in range(epochs):
        optimizer.zero_grad()
        output = model(X)
        loss = criterion(output, y)
        loss.backward()
        optimizer.step()
        if (epoch + 1) % 10 == 0:
            logger.info(f'  Epoch {epoch+1}/{epochs} loss={loss.item():.4f}')

    model.eval()

    try:
        torch.save(model.state_dict(), MODEL_PATH)
        logger.info(f'Neural model saved to {MODEL_PATH}')
    except Exception as e:
        logger.warning(f'Could not save model: {e}')

    return model


def build_input_vector(agent, economy: dict, social_pressure: float = 0.5) -> list:
    """Build normalised input vector for the neural network."""
    return [
        min(agent.wealth / 100000.0, 1.0),
        min(economy.get('inflation', 2.0) / 50.0, 1.0),
        economy.get('market_confidence', 70.0) / 100.0,
        economy.get('unemployment', 5.0) / 100.0,
        economy.get('resource_index', 100.0) / 100.0,
        agent.emotion_fear,
        agent.emotion_greed,
        agent.emotion_trust,
        agent.emotion_optimism,
        agent.emotion_stress,
        agent.emotion_panic,
        social_pressure,
        agent.risk_score,
    ]


def run_neural_decision(agent, economy: dict, social_pressure: float = 0.5) -> dict:
    """
    Run neural inference for one agent.
    Returns decision dict with action, confidence, probabilities.
    """
    try:
        import torch
        model = get_model()
        device = _get_device()

        input_vec = build_input_vector(agent, economy, social_pressure)
        x = torch.tensor([input_vec], dtype=torch.float32).to(device)

        with torch.no_grad():
            logits = model(x)
            probs = torch.softmax(logits, dim=1).squeeze().cpu().numpy()

        action_idx = int(np.argmax(probs))
        confidence = float(probs[action_idx])
        action = ACTIONS[action_idx]

        return {
            'action': action,
            'confidence': round(confidence, 4),
            'probabilities': {ACTIONS[i]: round(float(p), 4) for i, p in enumerate(probs)},
            'tier': 2,
            'reasoning': f'Neural inference: {action} with {confidence:.1%} confidence',
        }

    except Exception as e:
        logger.error(f'Neural inference failed for agent {agent.id}: {e}')
        return {'action': 'save', 'confidence': 0.5, 'tier': 2, 'reasoning': f'Neural fallback: {e}'}