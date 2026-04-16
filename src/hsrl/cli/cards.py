import argparse
from hsrl.cards.registry import get_all_cards, get_card, is_implemented
import textwrap

def main():
    parser = argparse.ArgumentParser(description="Hearthstone Cards CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Search
    search_p = subparsers.add_parser("search", help="Search for cards by name or text")
    search_p.add_argument("query", type=str)

    # Show
    show_p = subparsers.add_parser("show", help="Show details of a specific card")
    show_p.add_argument("id", type=str)

    # List
    list_p = subparsers.add_parser("list", help="List cards")
    list_p.add_argument("--needs-effect", action="store_true", help="List cards that need effects implemented")
    list_p.add_argument("--implemented", action="store_true", help="List cards that are fully implemented and ready to use")
    
    args = parser.parse_args()

    cards = get_all_cards()

    if args.command == "search":
        q = args.query.lower()
        results = [c for c in cards if q in c.name.lower() or q in c.description.lower() or q in c.id]
        print(f"Found {len(results)} cards matching '{args.query}':")
        for c in results:
            print(f" - {c.id}: {c.name} ({c.cost} Mana {c.type.name.capitalize()})")
            
    elif args.command == "show":
        try:
            c = get_card(args.id)
            print(f"=== {c.name} ({c.id}) ===")
            print(f"[{c.hero_class.name}] {c.cost} Mana {c.type.name.capitalize()}")
            if c.attack > 0 or c.health > 0:
                stat = "Durability" if c.type.name == "WEAPON" else "Health"
                print(f"Stats: {c.attack} Attack / {c.health} {stat}")
            if getattr(c, "requires_target", False):
                print("Requires Target: Yes")
            print(f"Implemented: {is_implemented(c.id)}")
            print("-" * 20)
            print(textwrap.fill(c.description, width=60))
        except KeyError:
            print(f"Card '{args.id}' not found.")
            
    elif args.command == "list":
        if args.needs_effect:
            pending = [c for c in cards if not is_implemented(c.id) and c.description]
            print(f"{len(pending)} cards with descriptions are missing effect implementations:")
            for c in sorted(pending, key=lambda x: x.id):
                print(f" - {c.id}: {c.name}")
        elif args.implemented:
            done = [c for c in cards if is_implemented(c.id) or not c.description]
            print(f"{len(done)} cards are fully implemented:")
            for c in sorted(done, key=lambda x: x.id):
                print(f" - {c.id}: {c.name}")
        else:
            print(f"Total cards in registry: {len(cards)}")
            for c in cards:
                print(f" - {c.id}")

if __name__ == "__main__":
    main()
