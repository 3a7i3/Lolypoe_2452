from rl_trader.trading_env import TradingEnv
from rl_trader.agent import RLTrader

def train_rl(df):
    env = TradingEnv(df)
    agent = RLTrader(state_size=3, action_size=3)
    for episode in range(100):
        state = env.reset()
        done = False
        total_reward = 0
        while not done:
            action = agent.act(state)
            next_state, reward, done = env.step(action)
            total_reward += reward
            state = next_state
        print("Episode", episode, "reward:", total_reward)

    # Sauvegarde du modèle RL après entraînement
    import torch
    torch.save(agent.model.state_dict(), "rl_trader/rl_trader_model.pth")
    print("Modèle RL sauvegardé dans rl_trader/rl_trader_model.pth")
