from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box
from hsrl.core.game import GameState
from hsrl.core.enums import PlayerId, Phase, CardType
from hsrl.core.minion import Minion

class Renderer:
    def __init__(self):
        self.console = Console()

    def _render_minion(self, m: Minion) -> str:
        sickness = "zZ" if m.summoning_sick else "  "
        has_atk = "*" if m.has_attacked else " "
        kw = ""
        if m.taunt: kw += "[T]"
        if m.divine_shield: kw += "[DS]"
        if m.stealth: kw += "[S]"
        if m.windfury: kw += "[WF]"
        return f"[{m.current_attack}/{m.current_health}] {m.card.name[:10]:<10} {kw}{sickness}{has_atk}"

    def render(self, state: GameState, viewer: PlayerId):
        my_p = state.players[viewer]
        opp_p = state.players[viewer.opponent()]

        self.console.print("\n" + "="*50, style="bold blue")
        
        # Opponent section
        opp_secrets = f" [?x{len(opp_p.secrets)}]" if opp_p.secrets else ""
        opp_weapon = f" [W: {opp_p.weapon.attack}/{opp_p.weapon.durability}]" if opp_p.weapon else ""
        opp_title = f"{opp_p.id.name} HP: {opp_p.health} | Mana: {opp_p.mana_crystals}/{opp_p.max_mana} | Hand: {len(opp_p.hand)} | Deck: {len(opp_p.deck)}{opp_secrets}{opp_weapon}"
        self.console.print(Panel(Text("OPPONENT HERO", justify="center"), title=opp_title, border_style="red"))
        
        # Opponent board
        opp_board = Table(show_header=False, box=box.ROUNDED, expand=True)
        opp_board.add_row(*[self._render_minion(m) for m in opp_p.board])
        self.console.print(Panel(opp_board, title="Opponent Board", border_style="red"))

        self.console.print("-" * 50)

        # My board
        my_board = Table(show_header=False, box=box.ROUNDED, expand=True)
        my_board.add_row(*[self._render_minion(m) for m in my_p.board])
        self.console.print(Panel(my_board, title="My Board", border_style="green"))
        
        # My hand
        hand_text = ""
        for i, card in enumerate(my_p.hand):
            stats = ""
            if card.type == CardType.MINION:
                stats = f", {card.attack}/{card.health}"
            elif card.type == CardType.WEAPON:
                stats = f", {card.weapon_stats[0]}/{card.weapon_stats[1]}"
            hand_text += f"[{i}] {card.name} [{card.type.name}] (Cost: {card.cost}{stats}) - {card.description}\n"
        self.console.print(Panel(hand_text.strip(), title="My Hand", border_style="green"))

        # My hero section
        my_secrets = f" [?x{len(my_p.secrets)}]" if my_p.secrets else ""
        my_weapon = f" [W: {my_p.weapon.attack}/{my_p.weapon.durability}]" if my_p.weapon else ""
        my_title = f"HERO HP: {my_p.health} | Mana: {my_p.mana_crystals}/{my_p.max_mana} | Deck: {len(my_p.deck)}{my_secrets}{my_weapon}"
        self.console.print(Panel(Text(my_title, justify="center"), title=f"{my_p.id.name}", border_style="bold green"))
        
        if state.phase == Phase.MULLIGAN:
            self.console.print("[bold yellow]MULLIGAN PHASE: Choose which cards to toss.[/]")
        
        self.console.print("="*50 + "\n", style="bold blue")
