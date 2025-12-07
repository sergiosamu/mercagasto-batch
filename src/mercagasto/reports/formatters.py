"""
Formateadores HTML para reportes.
"""

from ..models import WeeklyReport, MonthlyReport


class HTMLReportFormatter:
    """Formateador de reportes a HTML."""
    
    @staticmethod
    def format_weekly_email_html(report: WeeklyReport) -> str:
        """Genera HTML para email semanal."""
        
        # Emoji para tendencia
        if report.comparacion.diferencia > 0:
            tendencia = f"📈 +{report.comparacion.porcentaje:.1f}%"
            color_tendencia = "#e74c3c"
        elif report.comparacion.diferencia < 0:
            tendencia = f"📉 {report.comparacion.porcentaje:.1f}%"
            color_tendencia = "#27ae60"
        else:
            tendencia = "➡️ 0%"
            color_tendencia = "#95a5a6"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    background-color: white;
                    border-radius: 10px;
                    padding: 30px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    color: #2c3e50;
                    margin: 0;
                }}
                .header p {{
                    color: #7f8c8d;
                    margin: 5px 0 0 0;
                }}
                .metric {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 25px;
                    border-radius: 10px;
                    text-align: center;
                    margin: 20px 0;
                }}
                .metric h2 {{
                    margin: 0;
                    font-size: 42px;
                    font-weight: bold;
                }}
                .metric p {{
                    margin: 5px 0 0 0;
                    opacity: 0.9;
                }}
                .stats {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 15px;
                    margin: 20px 0;
                }}
                .stat-box {{
                    background-color: #ecf0f1;
                    padding: 15px;
                    border-radius: 8px;
                    text-align: center;
                }}
                .stat-box h3 {{
                    margin: 0;
                    font-size: 24px;
                    color: #2c3e50;
                }}
                .stat-box p {{
                    margin: 5px 0 0 0;
                    color: #7f8c8d;
                    font-size: 14px;
                }}
                .comparison {{
                    background-color: #fff3cd;
                    border-left: 4px solid {color_tendencia};
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 5px;
                }}
                .comparison strong {{
                    color: {color_tendencia};
                }}
                .products {{
                    margin: 20px 0;
                }}
                .products h3 {{
                    color: #2c3e50;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 10px;
                }}
                .product-item {{
                    background-color: #f8f9fa;
                    padding: 12px;
                    margin: 8px 0;
                    border-radius: 5px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .product-name {{
                    font-weight: 500;
                    color: #2c3e50;
                }}
                .product-amount {{
                    color: #e74c3c;
                    font-weight: bold;
                    font-size: 16px;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ecf0f1;
                    color: #7f8c8d;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🛒 Resumen Semanal Mercadona</h1>
                    <p>{report.periodo}</p>
                </div>
                
                <div class="metric">
                    <h2>{report.total:.2f}€</h2>
                    <p>Total gastado esta semana</p>
                </div>
                
                <div class="stats">
                    <div class="stat-box">
                        <h3>{report.num_tickets}</h3>
                        <p>Compras realizadas</p>
                    </div>
                    <div class="stat-box">
                        <h3>{report.promedio_ticket:.2f}€</h3>
                        <p>Ticket promedio</p>
                    </div>
                </div>
                
                <div class="comparison">
                    <strong>{tendencia}</strong> comparado con la {report.comparacion.periodo_anterior}
                    ({report.comparacion.total_anterior:.2f}€)
                </div>
                
                <div class="products">
                    <h3>🏆 Top 5 Productos de la Semana</h3>
        """
        
        for i, prod in enumerate(report.top_productos, 1):
            html += f"""
                    <div class="product-item">
                        <span class="product-name">
                            {i}. {prod.descripcion} 
                            <span style="color: #7f8c8d; font-size: 14px;">x{prod.cantidad_total}</span>
                        </span>
                        <span class="product-amount">{prod.gasto_total:.2f}€</span>
                    </div>
            """
        
        html += """
                </div>
                
                <div class="footer">
                    <p>📊 Reporte generado automáticamente</p>
                    <p>Sistema de Gestión de Tickets Mercadona</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    @staticmethod
    def format_monthly_email_html(report: MonthlyReport) -> str:
        """Genera HTML para email mensual."""
        
        # Emoji para tendencia
        if report.comparacion.diferencia > 0:
            tendencia = f"📈 +{report.comparacion.porcentaje:.1f}%"
            color_tendencia = "#e74c3c"
        elif report.comparacion.diferencia < 0:
            tendencia = f"📉 {report.comparacion.porcentaje:.1f}%"
            color_tendencia = "#27ae60"
        else:
            tendencia = "➡️ 0%"
            color_tendencia = "#95a5a6"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 700px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    background-color: white;
                    border-radius: 10px;
                    padding: 40px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    margin: -40px -40px 30px -40px;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 32px;
                }}
                .header p {{
                    margin: 10px 0 0 0;
                    opacity: 0.9;
                    font-size: 18px;
                }}
                .metric-big {{
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    text-align: center;
                    margin: 20px 0;
                }}
                .metric-big h2 {{
                    margin: 0;
                    font-size: 48px;
                    font-weight: bold;
                }}
                .metric-big p {{
                    margin: 10px 0 0 0;
                    opacity: 0.9;
                    font-size: 16px;
                }}
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 15px;
                    margin: 20px 0;
                }}
                .stat-card {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                    border: 2px solid #e9ecef;
                }}
                .stat-card h3 {{
                    margin: 0;
                    font-size: 28px;
                    color: #667eea;
                }}
                .stat-card p {{
                    margin: 8px 0 0 0;
                    color: #6c757d;
                    font-size: 13px;
                }}
                .comparison {{
                    background: linear-gradient(to right, #ffeaa7, #fdcb6e);
                    border-left: 5px solid {color_tendencia};
                    padding: 20px;
                    margin: 25px 0;
                    border-radius: 8px;
                }}
                .comparison h3 {{
                    margin: 0 0 10px 0;
                    color: #2d3436;
                }}
                .comparison strong {{
                    color: {color_tendencia};
                    font-size: 24px;
                }}
                .section {{
                    margin: 30px 0;
                }}
                .section h3 {{
                    color: #2c3e50;
                    border-bottom: 3px solid #667eea;
                    padding-bottom: 10px;
                    margin-bottom: 20px;
                }}
                .product-list {{
                    display: grid;
                    gap: 10px;
                }}
                .product-card {{
                    background: linear-gradient(to right, #f8f9fa, #ffffff);
                    padding: 15px;
                    border-radius: 8px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    border-left: 4px solid #667eea;
                }}
                .product-info {{
                    flex-grow: 1;
                }}
                .product-rank {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #667eea;
                    margin-right: 15px;
                }}
                .product-name {{
                    font-weight: 600;
                    color: #2c3e50;
                    font-size: 16px;
                }}
                .product-details {{
                    color: #7f8c8d;
                    font-size: 13px;
                    margin-top: 5px;
                }}
                .product-amount {{
                    color: #e74c3c;
                    font-weight: bold;
                    font-size: 20px;
                }}
                .day-stats {{
                    display: grid;
                    grid-template-columns: repeat(7, 1fr);
                    gap: 10px;
                    margin: 20px 0;
                }}
                .day-card {{
                    background-color: #ecf0f1;
                    padding: 15px 10px;
                    border-radius: 8px;
                    text-align: center;
                }}
                .day-card strong {{
                    display: block;
                    color: #2c3e50;
                    font-size: 12px;
                    margin-bottom: 8px;
                }}
                .day-card .amount {{
                    color: #e74c3c;
                    font-weight: bold;
                    font-size: 16px;
                }}
                .day-card .count {{
                    color: #7f8c8d;
                    font-size: 11px;
                    margin-top: 5px;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 2px solid #ecf0f1;
                    color: #7f8c8d;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Resumen Mensual Mercadona</h1>
                    <p>{report.mes}</p>
                </div>
                
                <div class="metric-big">
                    <h2>{report.total:.2f}€</h2>
                    <p>Total gastado este mes</p>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>{report.num_tickets}</h3>
                        <p>Compras realizadas</p>
                    </div>
                    <div class="stat-card">
                        <h3>{report.promedio_ticket:.2f}€</h3>
                        <p>Ticket promedio</p>
                    </div>
                    <div class="stat-card">
                        <h3>{len(report.top_productos)}</h3>
                        <p>Productos únicos</p>
                    </div>
                </div>
                
                <div class="comparison">
                    <h3>Comparación con {report.comparacion.periodo_anterior}</h3>
                    <strong>{tendencia}</strong>
                    <span style="color: #2d3436; margin-left: 10px;">
                        ({report.comparacion.total_anterior:.2f}€ → {report.total:.2f}€)
                    </span>
                </div>
                
                <div class="section">
                    <h3>🏆 Top 10 Productos del Mes</h3>
                    <div class="product-list">
        """
        
        for i, prod in enumerate(report.top_productos, 1):
            html += f"""
                        <div class="product-card">
                            <span class="product-rank">{i}</span>
                            <div class="product-info">
                                <div class="product-name">{prod.descripcion}</div>
                                <div class="product-details">
                                    Comprado {prod.veces_comprado} veces • Total: {prod.cantidad_total} unidades
                                </div>
                            </div>
                            <span class="product-amount">{prod.gasto_total:.2f}€</span>
                        </div>
            """
        
        html += """
                    </div>
                </div>
                
                <div class="section">
                    <h3>📅 Gastos por Día de la Semana</h3>
                    <div class="day-stats">
        """
        
        dias_orden = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
        for dia in dias_orden:
            if dia in report.gastos_por_dia:
                datos = report.gastos_por_dia[dia]
                html += f"""
                        <div class="day-card">
                            <strong>{dia}</strong>
                            <div class="amount">{datos.total_gastado:.0f}€</div>
                            <div class="count">{datos.num_compras} compras</div>
                        </div>
                """
            else:
                html += f"""
                        <div class="day-card" style="opacity: 0.5;">
                            <strong>{dia}</strong>
                            <div class="amount">0€</div>
                            <div class="count">0 compras</div>
                        </div>
                """
        
        html += """
                    </div>
                </div>
                
                <div class="footer">
                    <p style="font-size: 16px; font-weight: bold; color: #667eea;">
                        📊 Reporte generado automáticamente
                    </p>
                    <p>Sistema de Gestión de Tickets Mercadona</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html