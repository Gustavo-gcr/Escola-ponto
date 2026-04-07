import streamlit as st
import calendar
import datetime
import io
import re
import os

# --- Tratamento de Erros e Imports ---
try:
    import holidays
except ImportError:
    holidays = None

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
except ImportError:
    st.error("Instale o reportlab: pip install reportlab")
    A4 = None

# --- Configuração da Página ---
st.set_page_config(page_title="Ponto IEC", page_icon="📝", layout="centered")

# --- Dados Básicos da Escola ---
NOME_ESCOLA = "Instituto Educacional Copacabana"
SIGLA_ESCOLA = "IEC"
CNPJ_ESCOLA = "09.238.103/0001-69"
LOGO_ESCOLA_PATH = "logo.jpeg"  # Certifique-se de que a imagem na pasta tenha EXATAMENTE este nome
TEXTO_RODAPE = "Bom trabalho! - IEC"

LISTA_NOMES = [
    "Agda Maria Coelho Cardoso", "Valdirene Ribeiro Luz", "Priscila Vitória dos Reis",
    "Mirlene Roza da Silveira", "Amanda Cristina Barbosa Serafim", "Rita Celita Miguel",
    "Edjane Reinaldo de Lima", "Valquiria Mendes Silva", "Ana Carolina Pires",
    "Creuza Aparecida de Souza Dias", "Carla Alexandra da Silva Andrade",
    "Gabrielly Silva Ramos", "Vitória Cristina Duarte Silva"
]

MESES_PT = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

# Dicionário de tradução e correção
TRADUCAO_FERIADOS = {
    "New Year's Day": "Confraternização Universal",
    "Carnival": "Carnaval",
    "Ash Wednesday": "Quarta-feira de Cinzas",
    "Good Friday": "Paixão de Cristo",
    "Easter Sunday": "Páscoa",
    "Easter": "Páscoa",
    "Tiradentes' Day": "Tiradentes",
    "Tiradentes": "Tiradentes",
    "Execução de Tiradentes": "Tiradentes",
    "Worker's Day": "Dia do Trabalhador",
    "Labor Day": "Dia do Trabalhador",
    "Corpus Christi": "Corpus Christi",
    "Independence Day": "Independência do Brasil",
    "Our Lady of Aparecida": "Nossa Senhora Aparecida",
    "All Souls' Day": "Finados",
    "Republic Proclamation Day": "Proclamação da República",
    "Black Awareness Day": "Dia da Consciência Negra",
    "National Day of Zumbi and Black Awareness": "Dia da Consciência Negra",
    "Christmas Day": "Natal",
    "Christmas": "Natal"
}

COR_FDS = "#E0E0E0"    # Cinza
COR_FERIADO = "#FFFACD" # Amarelo Claro
COR_SABADO_LETIVO = "#98FB98" # Verde Claro

# --- Inicialização de Estado ---
if 'dados_mes' not in st.session_state:
    st.session_state.dados_mes = {
        'feriados_removidos': [],
        'feriados_customizados': {},
        'sabados_letivos': {},
        'cores_feriados': {},
        'nomes_feriados': {}
    }

def get_feriados_padrao(ano, mes):
    feriados_mes = {}
    if holidays:
        try:
            br_holidays = holidays.BR(years=ano, subdiv='MG', language='pt_BR')
        except:
            br_holidays = holidays.BR(years=ano, subdiv='MG')

        for data, nome_original in br_holidays.items():
            if data.month == mes:
                if nome_original in TRADUCAO_FERIADOS:
                    nome_pt = TRADUCAO_FERIADOS[nome_original]
                else:
                    if any(palavra in nome_original for palavra in ["Day", "of", "The", "National"]):
                        nome_pt = "Feriado" 
                    else:
                        nome_pt = nome_original 
                
                feriados_mes[data] = nome_pt
    return feriados_mes

def sanitize_color(color_name):
    if re.match(r'^#[0-9A-Fa-f]{6}$', color_name): return color_name
    return COR_FDS

# --- Função de Geração do PDF ---
def gerar_pdf(mes, ano):
    if not A4: return None
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=20, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    
    style_normal = ParagraphStyle(name='NormalStyle', parent=styles['Normal'], fontSize=10)
    style_title_main = ParagraphStyle(name='TitleMain', parent=styles['Heading1'], alignment=TA_CENTER, spaceAfter=2, fontSize=16)
    style_title_sub = ParagraphStyle(name='TitleSub', parent=styles['Normal'], alignment=TA_CENTER, spaceAfter=15, fontSize=12)
    style_legend = ParagraphStyle(name='Legend', parent=styles['Normal'], fontSize=8, alignment=TA_LEFT)
    
    def my_footer(canvas, doc):
        canvas.saveState()
        p = Paragraph(f"<i>{TEXTO_RODAPE}</i>", ParagraphStyle(name='F', fontSize=8, alignment=TA_CENTER))
        p.wrap(doc.width, doc.bottomMargin)
        p.drawOn(canvas, doc.leftMargin, 15)
        canvas.restoreState()
    
    num_dias = calendar.monthrange(ano, mes)[1]
    feriados_padrao = get_feriados_padrao(ano, mes)
    estado = st.session_state.dados_mes

    for nome in LISTA_NOMES:
        if os.path.exists(LOGO_ESCOLA_PATH):
            logo_img = Image(LOGO_ESCOLA_PATH, width=50, height=50)
        else:
            logo_img = "" 
            
        texto_titulo = [
            Paragraph("<b>FOLHA DE PONTO</b>", style_title_main),
            Paragraph(f"{NOME_ESCOLA}", style_title_sub)
        ]
            
        t_cabecalho = Table([
            [logo_img, texto_titulo, ""]
        ], colWidths=[60, 415, 60]) 
        t_cabecalho.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
        elements.append(t_cabecalho)
        elements.append(Spacer(1, 10))
        
        # AQUI: ColWidths ajustados para dar mais espaço ao "Mês/Ano:" (aumentou para 65)
        info_data = [
            [Paragraph("<b>Empregador:</b>", style_normal), Paragraph(NOME_ESCOLA, style_normal), Paragraph("<b>CNPJ:</b>", style_normal), Paragraph(CNPJ_ESCOLA, style_normal)],
            [Paragraph("<b>Empregado:</b>", style_normal), Paragraph(nome, style_normal), Paragraph("<b>Mês/Ano:</b>", style_normal), Paragraph(f"{mes:02d}/{ano}", style_normal)]
        ]
        t_info = Table(info_data, colWidths=[75, 275, 65, 120])
        t_info.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
            ('BACKGROUND', (2,0), (2,-1), colors.whitesmoke),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(t_info)
        elements.append(Spacer(1, 15))
        
        cabecalho = ["Dia", "Entrada", "Início Int.", "Fim Int.", "Saída", "Extra", "Assinatura"]
        data = [cabecalho]
        
        table_style = TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('BACKGROUND', (0,0), (-1,0), colors.darkgrey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
        ])
        
        cores_usadas = set()

        for dia in range(1, num_dias + 1):
            data_atual = datetime.date(ano, mes, dia)
            ds = data_atual.weekday()
            
            is_feriado_padrao = data_atual in feriados_padrao and data_atual not in estado['feriados_removidos']
            is_feriado_custom = data_atual in estado['feriados_customizados']
            is_sab_letivo = ds == 5 and data_atual in estado['sabados_letivos']
            
            row = [str(dia), "", "", "", "", "", ""]
            
            if is_feriado_custom:
                info = estado['feriados_customizados'][data_atual]
                row[1] = info['nome']
                cor = info['cor']
                table_style.add('SPAN', (1, dia), (6, dia))
                table_style.add('BACKGROUND', (0, dia), (-1, dia), colors.HexColor(sanitize_color(cor)))
                table_style.add('ALIGN', (1, dia), (6, dia), 'CENTER')
                cores_usadas.add((cor, "Feriado Letivo"))
                
            elif is_feriado_padrao:
                nome_feriado = estado['nomes_feriados'].get(data_atual, feriados_padrao[data_atual])
                cor = estado['cores_feriados'].get(data_atual, COR_FERIADO)
                row[1] = nome_feriado
                table_style.add('SPAN', (1, dia), (6, dia))
                table_style.add('BACKGROUND', (0, dia), (-1, dia), colors.HexColor(sanitize_color(cor)))
                table_style.add('ALIGN', (1, dia), (6, dia), 'CENTER')
                cores_usadas.add((cor, "Feriado Letivo"))
                
            elif is_sab_letivo:
                cor = estado['sabados_letivos'][data_atual]
                row[1] = "Sábado Letivo"
                table_style.add('SPAN', (1, dia), (6, dia))
                table_style.add('BACKGROUND', (0, dia), (-1, dia), colors.HexColor(sanitize_color(cor)))
                table_style.add('ALIGN', (1, dia), (6, dia), 'CENTER') 
                cores_usadas.add((cor, "Sábado Letivo"))
                
            elif ds >= 5: 
                row[1] = "Sábado" if ds == 5 else "Domingo"
                table_style.add('SPAN', (1, dia), (6, dia))
                table_style.add('BACKGROUND', (0, dia), (-1, dia), colors.HexColor(COR_FDS))
                table_style.add('TEXTCOLOR', (1, dia), (1, dia), colors.dimgrey)
                table_style.add('ALIGN', (1, dia), (6, dia), 'CENTER')
                cores_usadas.add((COR_FDS, "Final de Semana"))
                
            data.append(row)
            
        t_main = Table(data, colWidths=[25, 55, 55, 55, 55, 45, 245], rowHeights=[18]*len(data))
        t_main.setStyle(table_style)
        elements.append(t_main)
        
        elements.append(Spacer(1, 10))
        legenda_texto = "<b>Legenda de Cores:</b> "
        for cor, desc in cores_usadas:
            legenda_texto += f'<font color="{cor}">■</font> {desc} &nbsp;&nbsp;&nbsp;'
        elements.append(Paragraph(legenda_texto, style_legend))
        
        elements.append(PageBreak())
        
    doc.build(elements, onFirstPage=my_footer, onLaterPages=my_footer)
    buffer.seek(0)
    return buffer

# --- Modal (Pop-up) de Edição com Preview ---
@st.dialog("🔧 Editor de Feriados e Dias Letivos", width="large")
def modal_editor(ano, mes):
    estado = st.session_state.dados_mes
    feriados_padrao = get_feriados_padrao(ano, mes)
    num_dias = calendar.monthrange(ano, mes)[1]
    
    col_edit, col_preview = st.columns([1.3, 1])
    
    with col_edit:
        st.write("### 1. Feriados Padrão")
        if not feriados_padrao:
            st.info("Nenhum feriado nacional/estadual detectado neste mês.")
        for data, nome_padrao in feriados_padrao.items():
            c1, c2, c3 = st.columns([1, 4, 1])
            c1.markdown(f"<div style='margin-top: 8px;'>Dia {data.day}</div>", unsafe_allow_html=True)
            
            nome_atual = estado['nomes_feriados'].get(data, nome_padrao)
            novo_nome = c2.text_input("Nome", value=nome_atual, key=f"nome_f_{data}", label_visibility="collapsed")
            if novo_nome != nome_atual:
                estado['nomes_feriados'][data] = novo_nome
            
            is_active = data not in estado['feriados_removidos']
            ativo = c3.checkbox("Ativo", value=is_active, key=f"chk_f_{data}")
            
            if ativo and data in estado['feriados_removidos']:
                estado['feriados_removidos'].remove(data)
            elif not ativo and data not in estado['feriados_removidos']:
                estado['feriados_removidos'].append(data)
                
        st.write("---")
        st.write("### 2. Sábados Letivos")
        sabados = [datetime.date(ano, mes, d) for d in range(1, num_dias+1) if datetime.date(ano, mes, d).weekday() == 5]
        for data in sabados:
            c1, c2, c3 = st.columns([1, 2, 2])
            c1.markdown(f"<div style='margin-top: 8px;'>Dia {data.day}</div>", unsafe_allow_html=True)
            
            cor_atual = estado['sabados_letivos'].get(data, COR_SABADO_LETIVO)
            nova_cor = c2.color_picker("Cor", cor_atual, key=f"cor_sab_{data}", label_visibility="collapsed")
            
            is_letivo = c3.checkbox("Sábado Letivo", value=(data in estado['sabados_letivos']), key=f"chk_sab_{data}")
            
            if is_letivo:
                estado['sabados_letivos'][data] = nova_cor
            else:
                if data in estado['sabados_letivos']:
                    del estado['sabados_letivos'][data]
                
        st.write("---")
        st.write("### 3. Feriado Customizado")
        c1, c2, c3, c4 = st.columns([1, 2, 1, 1])
        dia_cust = c1.number_input("Dia", 1, num_dias, 1, key="dia_cust")
        nome_cust = c2.text_input("Nome", placeholder="Ex: Recesso", key="nome_cust")
        cor_cust = c3.color_picker("Cor", COR_FERIADO, key="cor_cust")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if c4.button("Adicionar", key="btn_add_cust"):
            estado['feriados_customizados'][datetime.date(ano, mes, dia_cust)] = {'nome': nome_cust, 'cor': cor_cust}
            
        if estado['feriados_customizados']:
            for d, info in list(estado['feriados_customizados'].items()):
                if st.button(f"🗑️ Remover '{info['nome']}' (Dia {d.day})", key=f"rem_c_{d}"):
                    del estado['feriados_customizados'][d]

    with col_preview:
        st.write("### Preview da Folha")
        html = """<div style='height: 400px; overflow-y: scroll; border: 1px solid #ccc; border-radius: 5px;'>
        <table style='width: 100%; text-align: center; font-size: 13px; font-family: sans-serif; border-collapse: collapse;'>
        <tr style='background-color: #333; color: white;'><th>Dia</th><th>Status</th></tr>"""
        
        for dia in range(1, num_dias + 1):
            d_atual = datetime.date(ano, mes, dia)
            ds = d_atual.weekday()
            cor = "white"
            texto = "Dia Útil"
            
            if d_atual in estado['feriados_customizados']:
                cor = estado['feriados_customizados'][d_atual]['cor']
                texto = estado['feriados_customizados'][d_atual]['nome']
            elif d_atual in feriados_padrao and d_atual not in estado['feriados_removidos']:
                cor = estado['cores_feriados'].get(d_atual, COR_FERIADO)
                texto = estado['nomes_feriados'].get(d_atual, feriados_padrao[d_atual])
            elif ds == 5 and d_atual in estado['sabados_letivos']:
                cor = estado['sabados_letivos'][d_atual]
                texto = "Sábado Letivo"
            elif ds >= 5:
                cor = COR_FDS
                texto = "Sábado" if ds == 5 else "Domingo"
                
            html += f"<tr style='background-color: {cor}; color: #222; font-weight: 500; border-bottom: 1px solid #ddd; height: 28px;'><td>{dia}</td><td>{texto}</td></tr>"
            
        html += "</table></div>"
        st.markdown(html, unsafe_allow_html=True)
        
    st.markdown("---")
    # Botão para salvar e fechar o modal propositalmente recarregando a página principal
    if st.button("💾 Salvar e Fechar Edições", type="primary", use_container_width=True):
        st.rerun()

# --- Interface Principal ---
st.title(f"📝 Gerador de Folha de Ponto - {SIGLA_ESCOLA}")
st.write("Gere as folhas de ponto de todos os funcionários com um clique. Configure o mês antes de gerar.")

col1, col2 = st.columns(2)
with col1:
    mes_str = st.selectbox("Selecione o Mês", MESES_PT, index=datetime.date.today().month - 1)
    mes_num = MESES_PT.index(mes_str) + 1
with col2:
    ano_selecionado = st.number_input("Ano", 2020, 2100, datetime.date.today().year)

st.markdown("<br>", unsafe_allow_html=True)

col_btn1, col_btn2 = st.columns([1, 1])

with col_btn1:
    if st.button("⚙️ Configurar Feriados e Letivos", use_container_width=True):
        modal_editor(ano_selecionado, mes_num)

with col_btn2:
    if st.button("📄 GERAR FOLHAS EM PDF", type="primary", use_container_width=True):
        with st.spinner("Construindo o documento..."):
            pdf_bytes = gerar_pdf(mes_num, ano_selecionado)
            if pdf_bytes:
                st.download_button(
                    label="⬇️ Baixar PDF Pronto",
                    data=pdf_bytes,
                    file_name=f"Folha_Ponto_{mes_str}_{ano_selecionado}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )