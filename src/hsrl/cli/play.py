import argparse
import random
from hsrl.core.game import GameState
from hsrl.core.enums import PlayerId
from hsrl.cards.sets.basic import init_basic_set
from hsrl.cards.registry import get_card, _REGISTRY
from hsrl.cli.renderer import Renderer
from hsrl.cli.deck_manager import load_deck
from hsrl.agents.human_agent import HumanAgent
from hsrl.agents.random_agent import RandomAgent

def main():
    parser = argparse.ArgumentParser(description="Play CLI Hearthstone")
    parser.add_argument("--p1", choices=["human", "random"], default="human")
    parser.add_argument("--p2", choices=["human", "random"], default="random")
    parser.add_argument("--deck1", help="Path to deck JSON for P1", default=None)
    parser.add_argument("--deck2", help="Path to deck JSON for P2", default=None)
    args = parser.parse_args()

    # Init database
    from hsrl.cards.registry import load_database
    init_basic_set()
    load_database()
    
    # Setup agents
    agents = {}
    for p_id, agent_type in [(PlayerId.P1, args.p1), (PlayerId.P2, args.p2)]:
        if agent_type == "human":
            agents[p_id] = HumanAgent()
        else:
            agents[p_id] = RandomAgent()
            
    renderer = Renderer()
    game = GameState()
    
    # Populate decks 
    pool = list(_REGISTRY.keys())
    
    # helper for loading or randomizing
    def setup_deck(p_id, deck_path):
        if deck_path:
            try:
                deck_data = load_deck(deck_path)
                from hsrl.core.enums import HeroClass
                game.players[p_id].hero_class = HeroClass[deck_data['hero_class']]
                
                for c_id in deck_data['cards']:
                    game.players[p_id].deck.append(get_card(c_id))
            except Exception as e:
                print(f"Error loading deck for {p_id}: {e}")
                exit(1)
        else:
            for _ in range(30):
                game.players[p_id].deck.append(get_card(random.choice(pool)))

    setup_deck(PlayerId.P1, args.deck1)
    setup_deck(PlayerId.P2, args.deck2)
            
    game.setup_game()
    
    # Play loop
    while not game.is_terminal():
        current_p = game.current_player_id
        
        if args.p1 == "human" and args.p2 == "human":
            viewer = current_p
        elif args.p1 == "human":
            viewer = PlayerId.P1
        elif args.p2 == "human":
            viewer = PlayerId.P2
        else:
            viewer = PlayerId.P1
        
        # In a real game, only render if it's human's turn, or render briefly
        # Let's render always to observe
        renderer.render(game, viewer=viewer)
        
        agent = agents[current_p]
        legal_actions = game.get_legal_actions()
        
        action = agent.get_action(game, legal_actions)
        
        if isinstance(agent, RandomAgent) and (args.p1 == "human" or args.p2 == "human"):
            # Print AI action so human knows what happened
            renderer.console.print(f"[bold magenta]Opponent played:[/] {action}")
            
        game.step(action)
        
    # Game over
    winner = game.get_winner()
    if winner:
        renderer.console.print(f"\n[bold green]Game Over! {winner.name} wins![/]")
    else:
        renderer.console.print("\n[bold yellow]Game Over! It's a draw![/]")

if __name__ == "__main__":
    main()
