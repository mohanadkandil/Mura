"""
Catalog tools for supplier agents.

These tools let the LLM look up real data instead of hallucinating.
"""

from langchain_core.tools import tool


def create_catalog_tools(catalog: dict, max_discount_pct: float):
    """
    Factory that creates tools with catalog baked in.

    Each supplier gets its own set of tools with its own catalog.

    Args:
        catalog: The supplier's product catalog dict
        max_discount_pct: Maximum discount this supplier allows

    Returns:
        List of tools: [lookup_part, check_stock, calculate_quote, evaluate_discount]
    """

    @tool
    def lookup_part(part_name: str) -> dict:
        """Look up a part in the supplier's catalog.

        Use this tool to find price, specs, and availability for a specific part.

        Args:
            part_name: The part identifier (e.g., "brushless_motor", "esc", "battery")

        Returns:
            Part details including:
            - part_name: Full product name
            - unit_price: Price in EUR
            - specs: Technical specifications
            - stock: Available quantity
            - lead_time_days: Days to ship
            - category: Product category

            Returns {"error": "..."} if part not found.
        """
        if part_name in catalog:
            part = catalog[part_name]
            return {
                "found": True,
                "part_name": part.get("part_name", part_name),
                "unit_price": part.get("unit_price", 0),
                "specs": part.get("specs", ""),
                "stock": part.get("stock", 0),
                "lead_time_days": part.get("lead_time_days", 7),
                "category": part.get("category", ""),
            }

        # Part not in catalog - suggest similar parts
        available = list(catalog.keys())
        return {
            "found": False,
            "error": f"Part '{part_name}' not in catalog",
            "available_parts": available,
        }

    @tool
    def check_stock(part_name: str, quantity: int) -> dict:
        """Check if requested quantity of a part is available.

        Use this after lookup_part to verify the supplier can fulfill
        the requested quantity.

        Args:
            part_name: The part identifier
            quantity: How many units the buyer needs

        Returns:
            - available: True if stock >= quantity
            - stock: Current stock level
            - requested: Quantity requested
            - shortage: How many units short (only if unavailable)
        """
        if part_name not in catalog:
            return {
                "available": False,
                "reason": f"Part '{part_name}' not in catalog",
            }

        stock = catalog[part_name].get("stock", 0)

        if stock >= quantity:
            return {
                "available": True,
                "stock": stock,
                "requested": quantity,
            }
        else:
            return {
                "available": False,
                "stock": stock,
                "requested": quantity,
                "shortage": quantity - stock,
            }

    @tool
    def calculate_quote(items: list[dict]) -> dict:
        """Calculate a complete quote for a list of items.

        Use this to generate the final quote after confirming parts exist.
        Handles multiple items at once and calculates totals.

        Args:
            items: List of items to quote. Each item should have:
                - part_name: The part identifier (e.g., "brushless_motor")
                - quantity: How many units needed

        Returns:
            - items: List of line items with individual prices
            - subtotal: Total cost before any discounts
            - currency: "EUR"
            - max_lead_time_days: Longest lead time among all items
            - all_available: True if all items are in stock

        Example input:
            [{"part_name": "brushless_motor", "quantity": 4},
             {"part_name": "esc", "quantity": 4}]
        """
        quote_items = []
        subtotal = 0.0
        max_lead_time = 0
        all_available = True

        for item in items:
            part_name = item.get("part_name", "")
            quantity = item.get("quantity", 1)

            if part_name not in catalog:
                quote_items.append({
                    "part_name": part_name,
                    "quantity": quantity,
                    "status": "NOT_IN_CATALOG",
                    "line_total": 0,
                })
                all_available = False
                continue

            part = catalog[part_name]
            unit_price = part.get("unit_price", 0)
            stock = part.get("stock", 0)
            lead_time = part.get("lead_time_days", 7)
            line_total = unit_price * quantity

            # Check stock
            if stock < quantity:
                status = "INSUFFICIENT_STOCK"
                all_available = False
            else:
                status = "AVAILABLE"

            subtotal += line_total
            max_lead_time = max(max_lead_time, lead_time)

            quote_items.append({
                "part_name": part.get("part_name", part_name),
                "unit_price": unit_price,
                "quantity": quantity,
                "line_total": round(line_total, 2),
                "lead_time_days": lead_time,
                "stock": stock,
                "status": status,
            })

        return {
            "items": quote_items,
            "subtotal": round(subtotal, 2),
            "currency": "EUR",
            "max_lead_time_days": max_lead_time,
            "all_available": all_available,
        }

    @tool
    def evaluate_discount(requested_pct: float, current_total: float) -> dict:
        """Evaluate a discount request against supplier policy.

        Use this when a buyer requests a discount. Checks against
        the supplier's maximum allowed discount percentage.

        Args:
            requested_pct: Discount percentage the buyer wants (e.g., 15.0 for 15%)
            current_total: Current quote total before discount (in EUR)

        Returns:
            - decision: "ACCEPT", "COUNTER", or "REJECT"
            - approved_pct: The discount percentage being offered
            - original_total: The total before discount
            - new_total: New total after approved discount
            - savings: Amount saved
            - reason: Explanation of the decision

        Decision logic:
            - If requested <= max_discount/2: ACCEPT (comfortable margin)
            - If requested <= max_discount: COUNTER (offer middle ground)
            - If requested > max_discount: COUNTER with max possible
        """
        # Capture max_discount_pct from closure
        max_discount = max_discount_pct

        if requested_pct <= 0:
            return {
                "decision": "ACCEPT",
                "approved_pct": 0,
                "original_total": current_total,
                "new_total": current_total,
                "savings": 0,
                "reason": "No discount requested",
            }

        if requested_pct <= max_discount / 2:
            # Easy accept - well within limits
            new_total = current_total * (1 - requested_pct / 100)
            return {
                "decision": "ACCEPT",
                "approved_pct": requested_pct,
                "original_total": round(current_total, 2),
                "new_total": round(new_total, 2),
                "savings": round(current_total - new_total, 2),
                "reason": "Discount approved - within comfortable margin",
            }

        elif requested_pct <= max_discount:
            # Counter with middle ground
            counter_pct = (requested_pct + max_discount / 2) / 2
            counter_pct = round(counter_pct, 1)
            new_total = current_total * (1 - counter_pct / 100)
            return {
                "decision": "COUNTER",
                "requested_pct": requested_pct,
                "approved_pct": counter_pct,
                "original_total": round(current_total, 2),
                "new_total": round(new_total, 2),
                "savings": round(current_total - new_total, 2),
                "reason": f"Can offer {counter_pct}% instead of {requested_pct}%",
            }

        else:
            # Too high - counter with maximum
            new_total = current_total * (1 - max_discount / 100)
            return {
                "decision": "COUNTER",
                "requested_pct": requested_pct,
                "approved_pct": max_discount,
                "original_total": round(current_total, 2),
                "new_total": round(new_total, 2),
                "savings": round(current_total - new_total, 2),
                "reason": f"Maximum possible discount is {max_discount}%",
            }

    # Return all tools as a list
    return [lookup_part, check_stock, calculate_quote, evaluate_discount]
