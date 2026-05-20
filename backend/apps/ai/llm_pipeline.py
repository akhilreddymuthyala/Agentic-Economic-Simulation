"""
Tier 1 — LangGraph LLM Reasoning Pipeline
For Government Agents, Influencers, and elite Investors.

Pipeline nodes:
    ObserveEnvironment → RetrieveMemories → AnalyzeEmotionalState
    → DecisionRouting → LLMReasoning → CriticValidation
    → ExecuteAction → StoreMemory
"""
import logging
import json
import os
from typing import TypedDict, Annotated, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')
OPENROUTER_BASE_URL = 'https://openrouter.ai/api/v1'
LLM_MODEL = 'openrouter/free'

VALID_ACTIONS = ['buy', 'sell', 'save', 'invest', 'panic', 'cooperate',
                 'raise_taxes', 'lower_taxes', 'stimulus', 'regulate',
                 'influence_market', 'form_alliance']


# ── LangGraph State ───────────────────────────────────────────────────────────
class AgentPipelineState(TypedDict):
    agent_id: int
    agent_name: str
    agent_role: str
    wealth: float
    economy_snapshot: dict
    emotion_vector: dict
    dominant_emotion: str
    memories: list
    social_connections: int
    reasoning: str
    proposed_action: str
    confidence: float
    critic_approved: bool
    final_action: str
    error: Optional[str]


# ── Node implementations ──────────────────────────────────────────────────────

def node_observe_environment(state: AgentPipelineState) -> AgentPipelineState:
    """Enrich state with latest economy data."""
    try:
        from apps.economy.models import EconomyState
        latest = EconomyState.get_latest()
        if latest:
            state['economy_snapshot'] = {
                'gdp': latest.gdp,
                'inflation': latest.inflation,
                'unemployment': latest.unemployment,
                'market_confidence': latest.market_confidence,
                'wealth_gini': latest.wealth_gini,
                'resource_index': latest.resource_index,
                'economic_stability': latest.economic_stability,
            }
    except Exception as e:
        state['error'] = f'ObserveEnvironment error: {e}'
    return state


def node_retrieve_memories(state: AgentPipelineState) -> AgentPipelineState:
    """Retrieve relevant memories for this agent using pgvector similarity."""
    try:
        from apps.memory.services import retrieve_memories_by_importance
        memories = retrieve_memories_by_importance(state['agent_id'], top_k=5)
        state['memories'] = [
            {'text': m.memory_text, 'importance': m.importance}
            for m in memories
        ]
    except Exception as e:
        state['memories'] = []
        logger.warning(f'Memory retrieval failed for agent {state["agent_id"]}: {e}')
    return state


def node_analyze_emotional_state(state: AgentPipelineState) -> AgentPipelineState:
    """Emotional state is already in state — just validate and log."""
    emotion = state.get('dominant_emotion', 'neutral')
    vector = state.get('emotion_vector', {})
    logger.debug(f'Agent {state["agent_id"]} emotional state: {emotion} {vector}')
    return state


def node_decision_routing(state: AgentPipelineState) -> AgentPipelineState:
    """Decide whether to use full LLM or fast heuristic."""
    # Panic override — skip LLM for speed
    if state['emotion_vector'].get('panic', 0) > 0.7:
        state['proposed_action'] = 'panic'
        state['confidence'] = 0.95
        state['reasoning'] = 'Panic override — emergency sell'
        state['critic_approved'] = True
        state['final_action'] = 'panic'
    return state


def node_llm_reasoning(state: AgentPipelineState) -> AgentPipelineState:
    if state.get('final_action'):
        return state

    if not OPENROUTER_API_KEY:
        state['proposed_action'] = 'save'
        state['confidence'] = 0.5
        state['reasoning'] = 'No API key configured'
        return state

    try:
        llm = ChatOpenAI(
            model=LLM_MODEL,
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
            max_tokens=200,
            temperature=0.3,
        )

        eco = state['economy_snapshot']
        memories_text = '\n'.join(
            f'- {m["text"]}' for m in state.get('memories', [])
        ) or 'No prior memories.'

        user_prompt = f"""You are {state['agent_name']}, a {state['agent_role']} in an economic simulation.

Economy: GDP={eco.get('gdp',0):.0f}, Inflation={eco.get('inflation',0):.1f}%, Unemployment={eco.get('unemployment',0):.1f}%, Confidence={eco.get('market_confidence',0):.0f}%
Your wealth: {state['wealth']:.0f}
Your emotion: {state['dominant_emotion']}
Memories: {memories_text}

Respond with ONLY this JSON, no markdown, no explanation:
{{"action": "save", "confidence": 0.7, "reasoning": "one sentence why"}}

Valid actions: buy, sell, save, invest, cooperate, regulate, stimulus, influence_market"""

        response = llm.invoke([HumanMessage(content=user_prompt)])
        raw = response.content.strip()

        logger.info(f'LLM raw response for agent {state["agent_id"]}: {raw[:200]}')

        # Strip markdown if present
        if '```' in raw:
            parts = raw.split('```')
            for part in parts:
                part = part.strip()
                if part.startswith('json'):
                    part = part[4:].strip()
                if part.startswith('{'):
                    raw = part
                    break

        # Find JSON object in response
        start = raw.find('{')
        end = raw.rfind('}') + 1
        if start != -1 and end > start:
            raw = raw[start:end]

        parsed = json.loads(raw)
        action = parsed.get('action', 'save')
        if action not in VALID_ACTIONS:
            action = 'save'
        state['proposed_action'] = action
        state['confidence'] = float(parsed.get('confidence', 0.6))
        state['reasoning'] = parsed.get('reasoning', 'LLM decision')

    except json.JSONDecodeError as e:
        logger.warning(f'JSON parse failed for agent {state["agent_id"]}: {raw[:100]}')
        state['proposed_action'] = 'save'
        state['confidence'] = 0.5
        state['reasoning'] = f'Parse error: {raw[:80]}'
    except Exception as e:
        logger.error(f'LLM error agent {state["agent_id"]}: {e}')
        state['proposed_action'] = 'save'
        state['confidence'] = 0.4
        state['reasoning'] = f'LLM error: {str(e)[:80]}'

    return state


def node_critic_validation(state: AgentPipelineState) -> AgentPipelineState:
    """
    Validate the proposed action against hard constraints.
    Rejects actions that would bankrupt the agent or violate rules.
    """
    if state.get('final_action'):
        return state

    action = state.get('proposed_action', 'save')
    wealth = state.get('wealth', 0)

    # Can't buy or invest if broke
    if action in ('buy', 'invest') and wealth < 100:
        action = 'save'
        state['reasoning'] += ' [Critic: insufficient wealth to buy/invest]'

    # Can't sell if nothing to sell (very low wealth)
    if action == 'sell' and wealth < 50:
        action = 'work' if state['agent_role'] == 'worker' else 'save'
        state['reasoning'] += ' [Critic: nothing to sell]'

    state['critic_approved'] = True
    state['final_action'] = action
    return state


def node_execute_action(state: AgentPipelineState) -> AgentPipelineState:
    """Log the final action — actual wealth changes handled by agent processor."""
    logger.info(
        f'[LLM Agent {state["agent_id"]} — {state["agent_role"]}] '
        f'Action: {state["final_action"]} | '
        f'Confidence: {state["confidence"]:.2f} | '
        f'Reason: {state["reasoning"][:80]}'
    )
    return state


def node_store_memory(state: AgentPipelineState) -> AgentPipelineState:
    """Store this decision as a memory for future retrieval."""
    try:
        from apps.memory.services import store_memory
        memory_text = (
            f'As {state["agent_role"]}, I decided to {state["final_action"]}. '
            f'Economy: GDP={state["economy_snapshot"].get("gdp", 0):.0f}, '
            f'Inflation={state["economy_snapshot"].get("inflation", 0):.1f}%. '
            f'Reason: {state["reasoning"][:100]}'
        )
        importance = min(1.0, state.get('confidence', 0.5) + 0.2)
        store_memory(
            agent_id=state['agent_id'],
            text=memory_text,
            importance=importance,
            memory_type='decision',
        )
    except Exception as e:
        logger.warning(f'Memory storage failed for agent {state["agent_id"]}: {e}')
    return state


# ── Build LangGraph pipeline ──────────────────────────────────────────────────

def build_pipeline():
    """Build and compile the LangGraph reasoning pipeline."""
    graph = StateGraph(AgentPipelineState)

    graph.add_node('observe', node_observe_environment)
    graph.add_node('retrieve_memories', node_retrieve_memories)
    graph.add_node('analyze_emotion', node_analyze_emotional_state)
    graph.add_node('route', node_decision_routing)
    graph.add_node('llm_reason', node_llm_reasoning)
    graph.add_node('critic', node_critic_validation)
    graph.add_node('execute', node_execute_action)
    graph.add_node('store_memory', node_store_memory)

    graph.set_entry_point('observe')
    graph.add_edge('observe', 'retrieve_memories')
    graph.add_edge('retrieve_memories', 'analyze_emotion')
    graph.add_edge('analyze_emotion', 'route')
    graph.add_edge('route', 'llm_reason')
    graph.add_edge('llm_reason', 'critic')
    graph.add_edge('critic', 'execute')
    graph.add_edge('execute', 'store_memory')
    graph.add_edge('store_memory', END)

    return graph.compile()


_pipeline = None


def get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = build_pipeline()
    return _pipeline


def run_llm_decision(agent, economy: dict) -> dict:
    """
    Entry point for Tier 1 LLM decision.
    Returns decision dict.
    """
    pipeline = get_pipeline()

    initial_state = AgentPipelineState(
        agent_id=agent.id,
        agent_name=agent.name,
        agent_role=agent.profession,
        wealth=agent.wealth,
        economy_snapshot=economy,
        emotion_vector=agent.get_emotion_vector(),
        dominant_emotion=agent.dominant_emotion,
        memories=[],
        social_connections=0,
        reasoning='',
        proposed_action='save',
        confidence=0.5,
        critic_approved=False,
        final_action='',
        error=None,
    )

    try:
        result = pipeline.invoke(initial_state)
        return {
            'action': result['final_action'],
            'confidence': result['confidence'],
            'reasoning': result['reasoning'],
            'tier': 1,
        }
    except Exception as e:
        logger.error(f'LLM pipeline failed for agent {agent.id}: {e}')
        return {
            'action': 'save',
            'confidence': 0.4,
            'reasoning': f'Pipeline error: {str(e)[:100]}',
            'tier': 1,
        }