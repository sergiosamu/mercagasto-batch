# Archivos de Test

Esta carpeta contiene archivos de prueba para validar el funcionamiento del sistema.

## 📁 Estructura

```
tests/data/
├── pdfs/              # PDFs de tickets de Mercadona para testing
├── expected/          # Resultados esperados en JSON
└── README.md          # Este archivo
```

## 📄 Cómo añadir PDFs de prueba

1. **Subir PDFs**: Coloca tus tickets de Mercadona en `pdfs/`
   ```
   tests/data/pdfs/
   ├── ticket_001.pdf
   ├── ticket_002.pdf
   └── ticket_003.pdf
   ```

2. **Crear resultados esperados**: Para cada PDF, crea un JSON en `expected/`
   ```
   tests/data/expected/
   ├── ticket_001.json
   ├── ticket_002.json
   └── ticket_003.json
   ```

## 📋 Formato del JSON esperado

```json
{
  "store_name": "MERCADONA, S.A.",
  "cif": "A-46103834",
  "address": "C/ EJEMPLO 123",
  "postal_code": "28000",
  "city": "MADRID",
  "phone": "912345678",
  "date": "2025-12-07",
  "time": "14:30",
  "order_number": "123456789",
  "invoice_number": "001-123-456",
  "total": 25.45,
  "payment_method": "TARJETA BANCARIA",
  "products": [
    {
      "quantity": 1,
      "description": "PAN DE MOLDE",
      "unit_price": null,
      "total_price": 2.50,
      "weight": null
    },
    {
      "quantity": 2,
      "description": "LECHE ENTERA",
      "unit_price": 1.20,
      "total_price": 2.40,
      "weight": null
    }
  ],
  "iva_breakdown": {
    "4%": {
      "base": 2.40,
      "cuota": 0.10
    },
    "10%": {
      "base": 20.00,
      "cuota": 2.00
    }
  }
}
```

## 🧪 Ejecutar Tests de Integración

```bash
# Test de parsing individual
python -m pytest tests/test_integration.py::test_parse_pdf_tickets -v

# Test completo de integración
python -m pytest tests/test_integration.py -v

# Test con PDFs específicos
python -m pytest tests/test_integration.py::test_specific_pdf[ticket_001.pdf] -v
```

## 📝 Notas Importantes

- **Privacidad**: No subas PDFs con datos reales/personales al repositorio
- **Naming**: Usa nombres descriptivos: `ticket_basico.pdf`, `ticket_con_descuentos.pdf`
- **Variedad**: Incluye diferentes tipos de tickets:
  - Tickets básicos con pocos productos
  - Tickets con descuentos
  - Tickets con productos pesados (kg)
  - Tickets con diferentes tipos de IVA
  
## 🔄 Flujo de Testing

1. Añades un PDF nuevo → `tests/data/pdfs/nuevo_ticket.pdf`
2. Ejecutas el parser manualmente para ver el resultado
3. Si es correcto, guardas el resultado → `tests/data/expected/nuevo_ticket.json`
4. El test automático comparará ambos en futuras ejecuciones