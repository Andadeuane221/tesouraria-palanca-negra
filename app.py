import os
import re
import io
import sqlite3
import unicodedata
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_file

# ReportLab imports for professional PDF generation
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

# Data export imports
import pandas as pd

app = Flask(__name__)
app.secret_key = "palanca_negra_secret_key_production" # Change this for production environments
DATABASE = "database.db"

# ==========================================
# CONFIGURATION & CUSTOMIZATION PARAMETERS
# ==========================================
# To customize the application for another club or entity, update these constants:
CLUB_NAME = "Clube de Desbravadores Palanca Negra"
DEFAULT_DEPT = "Tesouraria"
CURRENCY_SYMBOL = "AOA"
LOGO_PATH = "static/logo.png"

def get_db_connection():
    """Establishes connection to the SQLite database with row factory enabled."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema if it doesn't already exist."""
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS recibos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference_code TEXT UNIQUE NOT NULL,
                nome TEXT NOT NULL,
                periodo TEXT NOT NULL,
                valor REAL NOT NULL,
                tesoureiro TEXT NOT NULL,
                departamento TEXT NOT NULL,
                observacoes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def clean_string(text):
    """Removes accents, special characters, converts to uppercase and replaces spaces with hyphens."""
    if not text:
        return ""
    # Normalize unicode to remove accents
    nfkd_form = unicodedata.normalize('NFKD', text)
    only_ascii = nfkd_form.encode('ASCII', 'ignore').decode('utf-8')
    # Remove any character that isn't alphanumeric, space, or hyphen
    cleaned = re.sub(r'[^a-zA-Z0-9\s-]', '', only_ascii)
    # Replace whitespace/multiple hyphens with a single hyphen
    cleaned = re.sub(r'[\s-]+', '-', cleaned)
    return cleaned.strip('-').upper()

def generate_reference_code(tesoureiro, nome):
    """Generates a unique reference code following YYYYMMDD-HHMMSS-TESOUREIRO-NOME rules."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    clean_t = clean_string(tesoureiro)
    clean_n = clean_string(nome)
    return f"{timestamp}-{clean_t}-{clean_n}"

def format_currency(value):
    """Formats a float value to the exact requested format: AOA 1.234,56"""
    return f"{CURRENCY_SYMBOL} {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

@app.context_processor
def utility_processor():
    """Registers the currency formatter to be accessible within HTML Jinja templates."""
    return dict(format_currency=format_currency, logo_exists=os.path.exists(LOGO_PATH))

# ==========================================
# CORE CONTROLLERS / ROUTES
# ==========================================

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Data Retrieval & Validation
        nome = request.form.get("nome", "").strip()
        periodo = request.form.get("periodo", "").strip()
        valor_raw = request.form.get("valor", "").strip()
        tesoureiro = request.form.get("tesoureiro", "").strip()
        departamento = request.form.get("departamento", "").strip() or DEFAULT_DEPT
        observacoes = request.form.get("observacoes", "").strip()

        if not (nome and periodo and valor_raw and tesoureiro):
            flash("Todos os campos obrigatórios devem ser preenchidos.", "danger")
            return redirect(url_for("index"))

        try:
            valor = float(valor_raw)
            if valor < 0:
                raise ValueError
        except ValueError:
            flash("O valor de pagamento deve ser um número válido e positivo.", "danger")
            return redirect(url_for("index"))

        # Unique reference generation
        reference_code = generate_reference_code(tesoureiro, nome)

        # Database Insertion
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO recibos (reference_code, nome, periodo, valor, tesoureiro, departamento, observacoes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (reference_code, nome, periodo, valor, tesoureiro, departamento, observacoes))
                conn.commit()
                receipt_id = cursor.lastrowid
            
            flash("Recibo gerado e registrado com sucesso!", "success")
            return redirect(url_for("download_pdf", receipt_id=receipt_id))
        except sqlite3.IntegrityError:
            flash("Erro de duplicidade ao gerar o código de referência. Tente novamente.", "danger")
            return redirect(url_for("index"))

    # System metrics Calculations for Dashboard
    with get_db_connection() as conn:
        total_arrecadado = conn.execute("SELECT SUM(valor) FROM recibos").fetchone()[0] or 0.0
        num_recibos = conn.execute("SELECT COUNT(*) FROM recibos").fetchone()[0] or 0
        
        current_month_str = datetime.now().strftime("%Y-%m")
        arrecadacao_mes = conn.execute(
            "SELECT SUM(valor) FROM recibos WHERE strftime('%Y-%m', created_at) = ?", 
            (current_month_str,)
        ).fetchone()[0] or 0.0

        ultimos_recibos = conn.execute(
            "SELECT * FROM recibos ORDER BY created_at DESC LIMIT 10"
        ).fetchall()

    return render_template(
        "index.html",
        total_arrecadado=total_arrecadado,
        num_recibos=num_recibos,
        arrecadacao_mes=arrecadacao_mes,
        ultimos_recibos=ultimos_recibos,
        default_dept=DEFAULT_DEPT
    )

@app.route("/recibos")
def recibos_history():
    search = request.args.get("search", "").strip()
    filter_month = request.args.get("month", "").strip() # Format Expected: YYYY-MM
    page = request.args.get("page", 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    query = "SELECT * FROM recibos WHERE 1=1"
    count_query = "SELECT COUNT(*) FROM recibos WHERE 1=1"
    params = []

    if search:
        query += " AND (nome LIKE ? OR reference_code LIKE ? OR tesoureiro LIKE ?)"
        count_query += " AND (nome LIKE ? OR reference_code LIKE ? OR tesoureiro LIKE ?)"
        like_str = f"%{search}%"
        params.extend([like_str, like_str, like_str])

    if filter_month:
        query += " AND strftime('%Y-%m', created_at) = ?"
        count_query += " AND strftime('%Y-%m', created_at) = ?"
        params.append(filter_month)

    # Calculate Pagination elements
    with get_db_connection() as conn:
        total_items = conn.execute(count_query, params).fetchone()[0]
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        extended_params = params + [per_page, offset]
        recibos = conn.execute(query, extended_params).fetchall()

    total_pages = (total_items + per_page - 1) // per_page

    return render_template(
        "recibos.html",
        recibos=recibos,
        search=search,
        filter_month=filter_month,
        page=page,
        total_pages=total_pages
    )

@app.route("/download/<int:receipt_id>")
def download_pdf(receipt_id):
    with get_db_connection() as conn:
        receipt = conn.execute("SELECT * FROM recibos WHERE id = ?", (receipt_id,)).fetchone()
    
    if not receipt:
        flash("Recibo não encontrado.", "danger")
        return redirect(url_for("index"))

    # Instantiating ReportLab PDF Byte stream Document
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )
    
    # Document Palette Setup
    primary_color = colors.HexColor("#1A365D")   # Deep Corporate Navy Blue
    secondary_color = colors.HexColor("#D69E2E") # Elegant Gold Accent
    text_dark = colors.HexColor("#2D3748")       # Charcoal Body Text
    light_bg = colors.HexColor("#F7FAFC")        # Soft Ash Background Tables

    styles = getSampleStyleSheet()
    
    # Custom Typography Styles Structure
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=22,
        leading=26, textColor=primary_color, alignment=TA_CENTER
    )
    subtitle_style = ParagraphStyle(
        'DocSub', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12,
        leading=16, textColor=secondary_color, alignment=TA_CENTER
    )
    meta_style = ParagraphStyle(
        'MetaText', parent=styles['Normal'], fontName='Helvetica', fontSize=10,
        leading=14, textColor=text_dark
    )
    meta_bold = ParagraphStyle(
        'MetaTextBold', parent=meta_style, fontName='Helvetica-Bold'
    )
    body_style = ParagraphStyle(
        'BodyTextCustom', parent=styles['Normal'], fontName='Helvetica', fontSize=11,
        leading=18, textColor=text_dark, alignment=TA_JUSTIFY
    )
    sign_style = ParagraphStyle(
        'SignText', parent=styles['Normal'], fontName='Helvetica', fontSize=11,
        leading=15, textColor=text_dark, alignment=TA_CENTER
    )

    story = []

    # --- HEADER BLOCK ---
    header_data = []
    # Dynamic Check for Club Logo availability inside the structural workspace
    if os.path.exists(LOGO_PATH):
        from reportlab.platypus import Image
        logo_img = Image(LOGO_PATH, width=65, height=65)
        header_text = [
            Paragraph(CLUB_NAME.upper(), title_style),
            Spacer(1, 4),
            Paragraph(f"Departamento de {receipt['departamento']}", subtitle_style)
        ]
        header_data = [[logo_img, header_text]]
        header_table = Table(header_data, colWidths=[80, 430])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (1,0), (1,0), 'CENTER'),
        ]))
    else:
        header_text = [
            Paragraph(CLUB_NAME.upper(), title_style),
            Spacer(1, 4),
            Paragraph(f"Departamento de {receipt['departamento']}", subtitle_style)
        ]
        header_data = [[header_text]]
        header_table = Table(header_data, colWidths=[510])
        header_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))

    story.append(header_table)
    story.append(Spacer(1, 15))
    
    # Structural Visual Separator Rule
    rule_table = Table([[""]], colWidths=[515], rowHeights=[3])
    rule_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), secondary_color),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(rule_table)
    story.append(Spacer(1, 20))

    # --- METADATA PANEL BLOCK ---
    created_dt = datetime.strptime(receipt['created_at'], "%Y-%m-%d %H:%M:%S")
    formatted_date = created_dt.strftime("%d/%m/%Y às %H:%M:%S")
    
    meta_info_data = [
        [Paragraph("<b>Número de Referência:</b>", meta_bold), Paragraph(receipt['reference_code'], meta_style)],
        [Paragraph("<b>Data/Hora de Emissão:</b>", meta_bold), Paragraph(formatted_date, meta_style)]
    ]
    meta_table = Table(meta_info_data, colWidths=[140, 375])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), light_bg),
        ('PADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 25))

    # --- RECEIPT MAIN TRANSACTION CONTENT ---
    transaction_title = ParagraphStyle('TransTitle', parent=title_style, fontSize=16, leading=20, alignment=TA_LEFT)
    story.append(Paragraph("RECIBO DE PAGAMENTO", transaction_title))
    story.append(Spacer(1, 12))

    main_content_data = [
        [Paragraph("<b>Nome do Membro:</b>", meta_bold), Paragraph(receipt['nome'], meta_style)],
        [Paragraph("<b>Período de Referência:</b>", meta_bold), Paragraph(receipt['periodo'], meta_style)],
        [Paragraph("<b>Valor Pago:</b>", meta_bold), Paragraph(f"<b>{format_currency(receipt['valor'])}</b>", ParagraphStyle('ValCol', parent=meta_style, textColor=primary_color, fontSize=12))]
    ]
    
    if receipt['observacoes']:
        main_content_data.append([Paragraph("<b>Observações:</b>", meta_bold), Paragraph(receipt['observacoes'], meta_style)])

    content_table = Table(main_content_data, colWidths=[140, 375])
    content_table.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-2), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0,0), (-1,-1), 10),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(content_table)
    story.append(Spacer(1, 25))

    # Legal Declaration Statement
    declaration_text = "Declaramos que recebemos do membro acima identificado o valor indicado neste recibo referente ao período mencionado."
    story.append(Paragraph(declaration_text, body_style))
    story.append(Spacer(1, 50))

    # --- SIGNATURE BLOCK & FOOTER MODULE ---
    signature_elements = [
        Spacer(1, 20),
        Paragraph("________________________________________________", sign_style),
        Spacer(1, 5),
        Paragraph("<b>Assinatura do Tesoureiro</b>", sign_style),
        Spacer(1, 3),
        Paragraph(receipt['tesoureiro'], ParagraphStyle('TesSub', parent=sign_style, textColor=colors.HexColor("#4A5568")))
    ]
    story.append(KeepTogether(signature_elements))
    
    story.append(Spacer(1, 60))
    footer_text = "Documento gerado eletronicamente pelo Sistema de Tesouraria do Clube de Desbravadores Palanca Negra."
    story.append(Paragraph(footer_text, ParagraphStyle('Foot', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=8, alignment=TA_CENTER, textColor=colors.gray)))

    # Document assembly rendering pipeline Execution
    doc.build(story)
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=False,
        mimetype="application/pdf",
        download_name=f"Recibo-{receipt['reference_code']}.pdf"
    )

@app.route("/export/<string:export_type>")
def export_data(export_type):
    with get_db_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM recibos ORDER BY created_at DESC", conn)
    
    # Beautify DataFrame naming headers for production exporting data standards
    df.columns = [
        'ID', 'Código de Referência', 'Nome do Membro', 'Período', 
        'Valor (AOA)', 'Tesoureiro Emissor', 'Departamento', 'Observações', 'Data de Emissão'
    ]

    if export_type == "csv":
        proxy = io.StringIO()
        df.to_csv(proxy, index=False, encoding="utf-8-sig")
        mem = io.BytesIO()
        mem.write(proxy.getvalue().encode('utf-8-sig'))
        mem.seek(0)
        return send_file(
            mem,
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"Historico_Tesouraria_{datetime.now().strftime('%Y%m%d')}.csv"
        )
    
    elif export_type == "excel":
        proxy = io.BytesIO()
        with pd.ExcelWriter(proxy, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Recibos Emitidos')
        proxy.seek(0)
        return send_file(
            proxy,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"Historico_Tesouraria_{datetime.now().strftime('%Y%m%d')}.xlsx"
        )
    
    flash("Formato de exportação inválido.", "danger")
    return redirect(url_for("recibos_history"))

if __name__ == "__main__":
    init_db()
    # Runs locally on port 5000 by default
    app.run(host="0.0.0.0", port=5000, debug=True)