import pandas as pd
import os
import io
import sqlite3
import aiosqlite
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager
from app.models.models import Venda, Quebra, RelatorioFaturacao, ComparativoLojas, ResumoLoja, RelatorioVendasPorHora, VendasPorHora, RelatorioRentabilidade, RentabilidadeProduto

EXCEL_FILE = "data/dados_mafraria.xlsx"
DB_FILE = "data/mafraria.db"

@asynccontextmanager
async def get_db_connection():
    async with aiosqlite.connect(DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        yield db

async def inicializar_excel():
    if not os.path.exists("data"):
        os.makedirs("data")
        
    # Inicializar SQLite assincronamente
    async with get_db_connection() as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS vendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                loja TEXT,
                produto TEXT,
                valor REAL,
                quantidade INTEGER,
                horario TIMESTAMP
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS quebras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                loja TEXT,
                produto TEXT,
                quantidade INTEGER,
                motivo TEXT,
                data TIMESTAMP
            )
        ''')
        await db.commit()
        
        # Verificar se o banco está vazio para inserir dados iniciais
        async with db.execute("SELECT COUNT(*) FROM vendas") as cursor:
            row = await cursor.fetchone()
            if row[0] == 0:
                dados_vendas = [
                    ("Barreiro", "Pastel de Nata", 1.2, 50, '2025-12-27 08:30:00'),
                    ("Barreiro", "Pão de Ló", 15.0, 5, '2025-12-27 10:00:00'),
                    ("Barreiro", "Café", 0.7, 80, '2025-12-27 09:00:00'),
                    ("Barreiro", "Pastel de Nata", 1.2, 30, '2025-12-28 08:45:00'),
                    ("Quinta da Lomba", "Pastel de Nata", 1.2, 40, '2025-12-27 09:15:00'),
                    ("Quinta da Lomba", "Bolo Rei", 18.0, 10, '2025-12-27 16:30:00'),
                    ("Quinta da Lomba", "Café", 0.7, 60, '2025-12-27 10:30:00'),
                    ("Pinhal Novo", "Pastel de Nata", 1.2, 60, '2025-12-27 08:00:00'),
                    ("Pinhal Novo", "Croissant", 1.5, 25, '2025-12-27 09:30:00'),
                    ("Pinhal Novo", "Café", 0.7, 100, '2025-12-27 08:30:00'),
                ]
                await db.executemany("INSERT INTO vendas (loja, produto, valor, quantidade, horario) VALUES (?, ?, ?, ?, ?)", dados_vendas)
                
                dados_quebras = [
                    ("Barreiro", "Pastel de Nata", 5, "Excesso de produção", '2025-12-27 19:00:00'),
                    ("Quinta da Lomba", "Bolo Rei", 2, "Data de validade", '2025-12-28 10:00:00'),
                    ("Pinhal Novo", "Croissant", 3, "Dano no transporte", '2025-12-27 07:30:00'),
                ]
                await db.executemany("INSERT INTO quebras (loja, produto, quantidade, motivo, data) VALUES (?, ?, ?, ?, ?)", dados_quebras)
                await db.commit()
    
    # Sincronizar com Excel (Pandas é síncrono, então usamos sqlite3 normal aqui)
    exportar_para_excel()

def exportar_para_excel():
    # Usamos sqlite3 síncrono aqui porque o Pandas não suporta aiosqlite diretamente
    conn = sqlite3.connect(DB_FILE)
    df_vendas = pd.read_sql_query("SELECT loja, produto, valor, quantidade, horario FROM vendas", conn)
    df_quebras = pd.read_sql_query("SELECT loja, produto, quantidade, motivo, data FROM quebras", conn)
    conn.close()
    
    with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
        df_vendas.to_excel(writer, sheet_name='Vendas', index=False)
        df_quebras.to_excel(writer, sheet_name='Quebras', index=False)

async def adicionar_venda(venda: Venda):
    async with get_db_connection() as db:
        horario_str = venda.horario.strftime('%Y-%m-%d %H:%M:%S')
        await db.execute(
            "INSERT INTO vendas (loja, produto, valor, quantidade, horario) VALUES (?, ?, ?, ?, ?)",
            (venda.loja, venda.produto, venda.valor, venda.quantidade, horario_str)
        )
        await db.commit()
    exportar_para_excel()

async def adicionar_quebra(quebra: Quebra):
    async with get_db_connection() as db:
        data_str = quebra.data.strftime('%Y-%m-%d %H:%M:%S')
        await db.execute(
            "INSERT INTO quebras (loja, produto, quantidade, motivo, data) VALUES (?, ?, ?, ?, ?)",
            (quebra.loja, quebra.produto, quebra.quantidade, quebra.motivo, data_str)
        )
        await db.commit()
    exportar_para_excel()

async def obter_vendas():
    async with get_db_connection() as db:
        async with db.execute("SELECT * FROM vendas") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def obter_quebras():
    async with get_db_connection() as db:
        async with db.execute("SELECT * FROM quebras") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def gerar_relatorio_faturacao(loja: str, data_inicio: Optional[datetime] = None, data_fim: Optional[datetime] = None):
    async with get_db_connection() as db:
        query = "SELECT valor FROM vendas WHERE LOWER(loja) = LOWER(?)"
        params = [loja]
        
        if data_inicio:
            query += " AND horario >= ?"
            params.append(data_inicio.strftime('%Y-%m-%d %H:%M:%S'))
        if data_fim:
            query += " AND horario <= ?"
            params.append(data_fim.strftime('%Y-%m-%d %H:%M:%S'))
            
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            if not rows:
                return None
            
            valores = [row['valor'] for row in rows]
            faturacao_total = sum(valores)
            ticket_medio = faturacao_total / len(valores)

            return RelatorioFaturacao(
                loja=loja,
                data_inicio=data_inicio,
                data_fim=data_fim,
                faturacao_total=faturacao_total,
                ticket_medio=ticket_medio
            )

async def produtos_mais_vendidos(loja: str, top_n: int = 5, data_inicio: Optional[datetime] = None, data_fim: Optional[datetime] = None):
    async with get_db_connection() as db:
        query = "SELECT produto, SUM(quantidade) as total FROM vendas WHERE LOWER(loja) = LOWER(?)"
        params = [loja]
        
        if data_inicio:
            query += " AND horario >= ?"
            params.append(data_inicio.strftime('%Y-%m-%d %H:%M:%S'))
        if data_fim:
            query += " AND horario <= ?"
            params.append(data_fim.strftime('%Y-%m-%d %H:%M:%S'))
            
        query += " GROUP BY produto ORDER BY total DESC LIMIT ?"
        params.append(top_n)
        
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            if not rows:
                return None
            return {"loja": loja, "produtos_mais_vendidos": {row['produto']: row['total'] for row in rows}}

async def quebras_por_produto(loja: str, data_inicio: Optional[datetime] = None, data_fim: Optional[datetime] = None):
    async with get_db_connection() as db:
        query = "SELECT produto, SUM(quantidade) as total FROM quebras WHERE LOWER(loja) = LOWER(?)"
        params = [loja]
        
        if data_inicio:
            query += " AND data >= ?"
            params.append(data_inicio.strftime('%Y-%m-%d %H:%M:%S'))
        if data_fim:
            query += " AND data <= ?"
            params.append(data_fim.strftime('%Y-%m-%d %H:%M:%S'))
            
        query += " GROUP BY produto"
        
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            if not rows:
                return None
            return {"loja": loja, "quebras_por_produto": {row['produto']: row['total'] for row in rows}}

async def gerar_comparativo_lojas(data_inicio: Optional[datetime] = None, data_fim: Optional[datetime] = None):
    async with get_db_connection() as db:
        # Vendas por loja
        v_query = "SELECT loja, SUM(valor) as faturacao, AVG(valor) as ticket FROM vendas"
        v_params = []
        if data_inicio or data_fim:
            v_query += " WHERE 1=1"
            if data_inicio:
                v_query += " AND horario >= ?"
                v_params.append(data_inicio.strftime('%Y-%m-%d %H:%M:%S'))
            if data_fim:
                v_query += " AND horario <= ?"
                v_params.append(data_fim.strftime('%Y-%m-%d %H:%M:%S'))
        v_query += " GROUP BY loja"
        
        # Quebras por loja
        q_query = "SELECT loja, SUM(quantidade) as quebras FROM quebras"
        q_params = []
        if data_inicio or data_fim:
            q_query += " WHERE 1=1"
            if data_inicio:
                q_query += " AND data >= ?"
                q_params.append(data_inicio.strftime('%Y-%m-%d %H:%M:%S'))
            if data_fim:
                q_query += " AND data <= ?"
                q_params.append(data_fim.strftime('%Y-%m-%d %H:%M:%S'))
        q_query += " GROUP BY loja"

        async with db.execute(v_query, v_params) as v_cursor, db.execute(q_query, q_params) as q_cursor:
            v_rows = await v_cursor.fetchall()
            q_rows = await q_cursor.fetchall()
    
    if not v_rows: return None
    
    # Processamento funcional dos dados (como Haskell faria)
    vendas_map = {row['loja']: row for row in v_rows}
    quebras_map = {row['loja']: row['quebras'] for row in q_rows}
    
    lojas = set(list(vendas_map.keys()) + list(quebras_map.keys()))
    
    comparativo = [
        ResumoLoja(
            loja=loja,
            faturacao_total=float(vendas_map.get(loja, {'faturacao': 0})['faturacao']),
            ticket_medio=float(vendas_map.get(loja, {'ticket': 0})['ticket']),
            total_quebras=int(quebras_map.get(loja, 0))
        ) for loja in lojas
    ]

    return ComparativoLojas(data_inicio=data_inicio, data_fim=data_fim, comparativo=comparativo)

async def relatorio_vendas_por_horario(loja: str, data_inicio: Optional[datetime] = None, data_fim: Optional[datetime] = None):
    async with get_db_connection() as db:
        query = "SELECT strftime('%H', horario) as hora, SUM(quantidade) as qtd, SUM(valor) as total FROM vendas WHERE LOWER(loja) = LOWER(?)"
        params = [loja]
        
        if data_inicio:
            query += " AND horario >= ?"
            params.append(data_inicio.strftime('%Y-%m-%d %H:%M:%S'))
        if data_fim:
            query += " AND horario <= ?"
            params.append(data_fim.strftime('%Y-%m-%d %H:%M:%S'))
            
        query += " GROUP BY hora ORDER BY hora"
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()

    if not rows: return None

    return RelatorioVendasPorHora(
        loja=loja,
        vendas_por_hora=[
            VendasPorHora(hora=int(row['hora']), quantidade_vendas=int(row['qtd']), valor_total=float(row['total']))
            for row in rows
        ]
    )

async def relatorio_rentabilidade(loja: str, data_inicio: Optional[datetime] = None, data_fim: Optional[datetime] = None):
    async with get_db_connection() as db:
        v_query = "SELECT produto, SUM(quantidade) as qtd_v, SUM(valor) as val_v FROM vendas WHERE LOWER(loja) = LOWER(?)"
        v_params = [loja]
        if data_inicio:
            v_query += " AND horario >= ?"
            v_params.append(data_inicio.strftime('%Y-%m-%d %H:%M:%S'))
        if data_fim:
            v_query += " AND horario <= ?"
            v_params.append(data_fim.strftime('%Y-%m-%d %H:%M:%S'))
        v_query += " GROUP BY produto"
        
        q_query = "SELECT produto, SUM(quantidade) as qtd_q FROM quebras WHERE LOWER(loja) = LOWER(?)"
        q_params = [loja]
        if data_inicio:
            q_query += " AND data >= ?"
            q_params.append(data_inicio.strftime('%Y-%m-%d %H:%M:%S'))
        if data_fim:
            q_query += " AND data <= ?"
            q_params.append(data_fim.strftime('%Y-%m-%d %H:%M:%S'))
        q_query += " GROUP BY produto"

        async with db.execute(v_query, v_params) as v_cursor, db.execute(q_query, q_params) as q_cursor:
            v_rows = await v_cursor.fetchall()
            q_rows = await q_cursor.fetchall()

    if not v_rows and not q_rows: return None

    # Lógica de Rentabilidade (Abordagem Funcional)
    v_map = {row['produto']: row for row in v_rows}
    q_map = {row['produto']: row['qtd_q'] for row in q_rows}
    produtos = set(list(v_map.keys()) + list(q_map.keys()))
    
    rentabilidade = []
    for p in produtos:
        qv = v_map.get(p, {'qtd_v': 0})['qtd_v']
        vv = v_map.get(p, {'val_v': 0})['val_v']
        qq = q_map.get(p, 0)
        racio = (qq / (qv + qq) * 100) if (qv + qq) > 0 else 0
        
        rentabilidade.append(RentabilidadeProduto(
            produto=p,
            quantidade_vendida=int(qv),
            valor_vendas=float(vv),
            quantidade_quebras=int(qq),
            racio_quebra_venda=float(racio)
        ))

    return RelatorioRentabilidade(loja=loja, rentabilidade=rentabilidade)

async def gerar_excel_dashboard(data_inicio: Optional[datetime] = None, data_fim: Optional[datetime] = None):
    # Para o Excel, geramos os dados assincronamente e depois usamos Pandas
    comp = await gerar_comparativo_lojas(data_inicio, data_fim)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if comp:
            pd.DataFrame([r.dict() for r in comp.comparativo]).to_excel(writer, sheet_name='Comparativo Lojas', index=False)
        
        for loja in ["Barreiro", "Quinta da Lomba", "Pinhal Novo"]:
            rent = await relatorio_rentabilidade(loja, data_inicio, data_fim)
            if rent:
                pd.DataFrame([r.dict() for r in rent.rentabilidade]).to_excel(writer, sheet_name=f'Rentabilidade {loja[:10]}', index=False)
            hor = await relatorio_vendas_por_horario(loja, data_inicio, data_fim)
            if hor:
                pd.DataFrame([h.dict() for h in hor.vendas_por_hora]).to_excel(writer, sheet_name=f'Horários {loja[:10]}', index=False)
    output.seek(0)
    return output.getvalue()

async def exportar_vendas_csv():
    async with get_db_connection() as db:
        async with db.execute("SELECT * FROM vendas") as cursor:
            rows = await cursor.fetchall()
            df = pd.DataFrame([dict(row) for row in rows])
            return df.to_csv(index=False)

async def exportar_quebras_csv():
    async with get_db_connection() as db:
        async with db.execute("SELECT * FROM quebras") as cursor:
            rows = await cursor.fetchall()
            df = pd.DataFrame([dict(row) for row in rows])
            return df.to_csv(index=False)
