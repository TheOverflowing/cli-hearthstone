from hsrl.rl.env import HearthstoneEnv
from hsrl.agents.base import RandomAgent
from hsrl.core.enums import PlayerId

def test_gym_env_spaces():
    env = HearthstoneEnv(agent_plays_as=0)
    assert env.action_space.n == 233
    
    obs, info = env.reset()
    assert "my_hero" in obs
    assert "opp_hero" in obs
    assert "my_hand" in obs
    assert "my_board" in obs
    assert "opp_board" in obs
    
    assert "action_mask" in info
    mask = info["action_mask"]
    assert len(mask) == 233
    
def test_gym_env_random_play():
    env = HearthstoneEnv(opponent=RandomAgent(), agent_plays_as=0)
    obs, info = env.reset()
    
    done = False
    truncated = False
    
    # We will simulate 10 steps to make sure logic doesn't crash
    # Real random games could take a while to fatigue
    steps = 0
    while not done and not truncated and steps < 10:
        mask = info["action_mask"]
        valid_actions = [i for i, m in enumerate(mask) if m]
        
        # Pick the first valid action (probably just end turn or play card)
        action = valid_actions[-1] if valid_actions else 0 
        
        obs, reward, done, truncated, info = env.step(action)
        steps += 1
        
    assert steps > 0
