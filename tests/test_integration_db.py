import pytest
from pathlib import Path

from src.mercagasto.parsers.mercadona import MercadonaTicketParser
from src.mercagasto.processors.pdf_extractor import PDFTextExtractor
from src.mercagasto.storage.postgresql import PostgreSQLTicketStorage
from src.mercagasto.config.settings import get_database_config

@pytest.fixture(scope="module")
def storage():
    config = get_database_config()
    return PostgreSQLTicketStorage(config)

@pytest.fixture
def pdf_files():
    pdfs_dir = Path(__file__).parent / 'data' / 'pdfs'
    return list(pdfs_dir.glob('*.pdf'))

def normalize_ticket(ticket):
    
    # Convierte TicketData a dict para comparación
    result = ticket.__dict__.copy()
    result['products'] = [p.__dict__.copy() for p in ticket.products]
    if hasattr(ticket, 'date') and ticket.date:
        result['date'] = str(ticket.date)
    return result

@pytest.mark.parametrize("pdf_file", [
    pytest.param(pdf, id=pdf.name)
    for pdf in (Path(__file__).parent / 'data' / 'pdfs').glob('*.pdf')
    if (Path(__file__).parent / 'data' / 'pdfs').exists()
])
def test_pdf_to_db_and_back(storage, pdf_file):
    print("Fichero PDF de test:", pdf_file)
    # 1. Extraer texto del PDF
    text = PDFTextExtractor.extract_text_from_pdf(str(pdf_file))
    assert text and len(text) > 50, f"Texto insuficiente en {pdf_file.name}"

    # 2. Parsear ticket
    parser = MercadonaTicketParser(text)
    ticket = parser.parse()
    assert ticket.total > 0
    assert len(ticket.products) > 0

    # 3. Guardar en base de datos
    ticket_id = storage.save_ticket(ticket)
    assert ticket_id is not None

    # 4. Recuperar desde base de datos
    db_ticket = storage.get_ticket_by_id(ticket_id)
    assert db_ticket is not None

    # 5. Normalizar y comparar
    t1 = normalize_ticket(ticket)
    t2 = normalize_ticket(db_ticket)

    # Comparar campos clave
    assert t1['invoice_number'] == t2['invoice_number']
    assert t1['total'] == pytest.approx(t2['total'], abs=0.01)
    assert len(t1['products']) == len(t2['products'])

    # Comparar productos
    for i, (p1, p2) in enumerate(zip(t1['products'], t2['products'])):
        assert p1['description'] == p2['description']
        assert p1['quantity'] == p2['quantity']
        assert p1['total_price'] == pytest.approx(p2['total_price'], abs=0.01)