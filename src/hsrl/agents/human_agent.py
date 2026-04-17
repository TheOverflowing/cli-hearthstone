from typing import List
from rich.console import Console
from .base import Agent
from hsrl.core.game import GameState
from hsrl.core.actions import Action, PlayMinion, Attack, EndTurn, MulliganCards, PlayWeapon, PlaySecret, PlaySpell, UseHeroPower
from hsrl.core.enums import Phase

class HumanAgent(Agent):
    def __init__(self):
        self.console = Console()

    def get_action(self, state: GameState, legal_actions: List[Action]) -> Action:
        while True:
            self.console.print("[bold yellow]Enter action (end | play_spell <h_idx> [tgt_p] [tgt_idx] | play <h_idx> <pos> [tgt_p] [tgt_idx] | hero_power [tgt_p] [tgt_idx] | attack <atk_idx> <tgt_idx>): [/]", end="")
            cmd = input().strip().lower().split()
            if not cmd:
                continue
            action = None
            p_id = state.current_player_id
            
            try:
                if state.phase == Phase.MULLIGAN:
                    if cmd[0] == "mulligan":
                        indices = [int(x) for x in cmd[1:]]
                        action = MulliganCards(player_id=p_id, indices=indices)
                    else:
                        self.console.print("[red]Invalid command in MULLIGAN phase. Use: mulligan [idx1] [idx2] ...[/]")
                        continue
                else:
                    if cmd[0] == "end":
                        action = EndTurn(player_id=p_id)
                    elif cmd[0] == "play" and len(cmd) >= 3:
                        target_p = PlayerId(int(cmd[3])) if len(cmd) > 3 else None
                        target_idx = int(cmd[4]) if len(cmd) > 4 else None
                        action = PlayMinion(player_id=p_id, hand_index=int(cmd[1]), board_position=int(cmd[2]), target_player_id=target_p, target_index=target_idx)
                    elif cmd[0] == "attack" and len(cmd) == 3:
                        action = Attack(player_id=p_id, attacker_index=int(cmd[1]), target_index=int(cmd[2]))
                    elif cmd[0] == "play_weapon" and len(cmd) == 2:
                        action = PlayWeapon(player_id=p_id, hand_index=int(cmd[1]))
                    elif cmd[0] == "play_secret" and len(cmd) == 2:
                        action = PlaySecret(player_id=p_id, hand_index=int(cmd[1]))
                    elif cmd[0] == "play_spell" and len(cmd) >= 2:
                        target_p = PlayerId(int(cmd[2])) if len(cmd) > 2 else None
                        target_idx = int(cmd[3]) if len(cmd) > 3 else None
                        action = PlaySpell(player_id=p_id, hand_index=int(cmd[1]), target_player_id=target_p, target_index=target_idx)
                    elif cmd[0] == "hero_power":
                        target_p = PlayerId(int(cmd[1])) if len(cmd) > 1 else None
                        target_idx = int(cmd[2]) if len(cmd) > 2 else None
                        action = UseHeroPower(player_id=p_id, target_player_id=target_p, target_index=target_idx)
                    else:
                        self.console.print("[red]Invalid command format.[/]")
                        continue
            except ValueError:
                self.console.print("[red]Indices must be integers.[/]")
                continue

            # Check if exactly this action is in the legal actions list
            if action in legal_actions:
                return action
            else:
                self.console.print("[red]Illegal action! Check your mana, summoning sickness, or board space.[/]")
