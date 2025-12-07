"""
Utilidades para formatear tickets.
"""

from ..models import TicketData


def format_ticket(ticket: TicketData) -> str:
    """
    Formatea el ticket para impresión legible.
    
    Args:
        ticket: Datos del ticket
        
    Returns:
        String formateado del ticket
    """
    output = []
    output.append("=" * 60)
    output.append(f"TICKET DE COMPRA - {ticket.store_name}")
    output.append("=" * 60)
    output.append(f"CIF: {ticket.cif}")
    output.append(f"Dirección: {ticket.address}")
    output.append(f"Ciudad: {ticket.postal_code} {ticket.city}")
    output.append(f"Teléfono: {ticket.phone}")
    output.append(f"Fecha: {ticket.date.strftime('%d/%m/%Y') if ticket.date else 'N/A'}")
    output.append(f"Hora: {ticket.time}")
    output.append(f"Nº Pedido: {ticket.order_number}")
    output.append(f"Factura: {ticket.invoice_number}")
    output.append("-" * 60)
    output.append("\nPRODUCTOS:")
    output.append("-" * 60)
    
    for p in ticket.products:
        unit_price = f"{p.unit_price:.2f}€" if p.unit_price else "-"
        weight = f"({p.weight})" if p.weight else ""
        output.append(
            f"{p.quantity:2d} {p.description:30s} {unit_price:>8s} {p.total_price:>6.2f}€ {weight}"
        )
    
    output.append("-" * 60)
    output.append(f"{'TOTAL:':>50s} {ticket.total:>6.2f}€")
    
    if ticket.iva_breakdown:
        output.append("\nDESGLOSE IVA:")
        output.append("-" * 60)
        
        for rate, values in ticket.iva_breakdown.items():
            output.append(
                f"{rate:>5s} - Base: {values['base']:>6.2f}€  Cuota: {values['cuota']:>6.2f}€"
            )
    
    output.append("=" * 60)
    
    return '\n'.join(output)