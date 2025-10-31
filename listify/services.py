from decimal import Decimal
from typing import Dict, List, Tuple
from listify.models import Compra, ItemDaCompra, Produto


def _aggregate_items(items: List[ItemDaCompra]) -> Dict[int, Tuple[Decimal, int, Produto]]:
    """
    Aggregates items by produto_id returning a map:
    produto_id -> (total_value, total_qty, produto)
    where total_value is sum(preco_pago * quantidade) and total_qty is sum(quantidade).
    """
    acc: Dict[int, Tuple[Decimal, int, Produto]] = {}
    for it in items:
        pid = it.produto_id
        value = (it.preco_pago * it.quantidade)
        qty = it.quantidade
        if pid in acc:
            prev_value, prev_qty, prod = acc[pid]
            acc[pid] = (prev_value + value, prev_qty + qty, prod)
        else:
            acc[pid] = (value, qty, it.produto)
    return acc


def _avg_price(value: Decimal, qty: int) -> Decimal:
    if qty <= 0:
        return Decimal('0.00')
    # average unit price with 2 decimals
    return (value / Decimal(qty)).quantize(Decimal('0.01'))


def comparar_compras(compra_a: Compra, compra_b: Compra):
    """
    Compares two purchases on common products.
    Returns a dict with summary and per-product comparison (prices and deltas).
    """
    itens_a = ItemDaCompra.query.filter_by(compra_id=compra_a.id).all()
    itens_b = ItemDaCompra.query.filter_by(compra_id=compra_b.id).all()

    agg_a = _aggregate_items(itens_a)
    agg_b = _aggregate_items(itens_b)

    common_ids = sorted(set(agg_a.keys()) & set(agg_b.keys()))
    only_in_a = sorted(set(agg_a.keys()) - set(agg_b.keys()))
    only_in_b = sorted(set(agg_b.keys()) - set(agg_a.keys()))

    def _serialize_prod(prod: Produto):
        return {
            "id": prod.id,
            "codigo_barras": prod.codigo_barras,
            "nome": prod.nome,
            "marca": prod.marca,
        }

    items_report = []
    for pid in common_ids:
        total_val_a, total_qty_a, prod_a = agg_a[pid]
        total_val_b, total_qty_b, prod_b = agg_b[pid]
        # prod_a and prod_b should be same product record
        preco_a = _avg_price(total_val_a, total_qty_a)
        preco_b = _avg_price(total_val_b, total_qty_b)
        delta = (preco_b - preco_a).quantize(Decimal('0.01'))
        percent = None
        if preco_a > Decimal('0.00'):
            percent = float(((preco_b - preco_a) / preco_a * 100).quantize(Decimal('0.01')))

        items_report.append({
            "produto": _serialize_prod(prod_a or prod_b),
            "preco_a": float(preco_a),
            "preco_b": float(preco_b),
            "delta": float(delta),
            "percent": percent,
            "quantidade_a": total_qty_a,
            "quantidade_b": total_qty_b,
        })

    return {
        "compra_a": compra_a.id,
        "compra_b": compra_b.id,
        "common_count": len(common_ids),
        "only_in_a": list(only_in_a),
        "only_in_b": list(only_in_b),
        "items": items_report,
    }