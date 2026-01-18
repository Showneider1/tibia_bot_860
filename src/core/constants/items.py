from src.core.entities.item import Item

# Exemplos; IDs reais podem ser ajustados depois
GOLD_COIN = Item(id=3031, name="Gold Coin", stackable=True, weight=0.1)
PLATINUM_COIN = Item(id=3035, name="Platinum Coin", stackable=True, weight=0.1)

ITEMS_BY_ID = {
    GOLD_COIN.id: GOLD_COIN,
    PLATINUM_COIN.id: PLATINUM_COIN,
}
