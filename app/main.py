from fastapi import FastAPI, HTTPException
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
import os
from typing import Optional
from datetime import datetime

from app.models.models import Venda, Quebra, RelatorioFaturacao, ComparativoLojas, RelatorioVendasPorHora, RelatorioRentabilidade
from app.services import excel_manager

app = FastAPI()

# Montar ficheiros estáticos para o Dashboard
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.on_event("startup")
async def startup_event():
    await excel_manager.inicializar_excel()

@app.get("/")
async def dashboard():
    return FileResponse("app/static/index.html")

@app.post("/vendas/")
async def adicionar_venda(venda: Venda):
    try:
        await excel_manager.adicionar_venda(venda)
        return {"message": "Venda adicionada com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao adicionar venda: {e}")

@app.post("/quebras/")
async def adicionar_quebra(quebra: Quebra):
    try:
        await excel_manager.adicionar_quebra(quebra)
        return {"message": "Quebra adicionada com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao adicionar quebra: {e}")

@app.get("/vendas/")
async def obter_vendas():
    try:
        vendas = await excel_manager.obter_vendas()
        if not vendas:
            raise HTTPException(status_code=404, detail="Ficheiro Excel não encontrado ou sem vendas registadas.")
        return vendas
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter vendas: {e}")

@app.get("/quebras/")
async def obter_quebras():
    try:
        quebras = await excel_manager.obter_quebras()
        if not quebras:
            raise HTTPException(status_code=404, detail="Ficheiro Excel não encontrado ou sem quebras registadas.")
        return quebras
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter quebras: {e}")

@app.get("/relatorio/faturacao/{loja}", response_model=RelatorioFaturacao)
async def gerar_relatorio_faturacao(loja: str, data_inicio: Optional[datetime] = None, data_fim: Optional[datetime] = None):
    try:
        relatorio = await excel_manager.gerar_relatorio_faturacao(loja, data_inicio, data_fim)
        if relatorio is None:
            # Retornar um relatório vazio em vez de erro para não quebrar o frontend
            return RelatorioFaturacao(loja=loja, data_inicio=data_inicio, data_fim=data_fim, faturacao_total=0, ticket_medio=0)
        return relatorio
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar relatório de faturação: {e}")

@app.get("/relatorio/produtos_mais_vendidos/{loja}")
async def produtos_mais_vendidos(loja: str, top_n: int = 5, data_inicio: Optional[datetime] = None, data_fim: Optional[datetime] = None):
    try:
        produtos = await excel_manager.produtos_mais_vendidos(loja, top_n, data_inicio, data_fim)
        if produtos is None:
            return {"loja": loja, "produtos_mais_vendidos": {}}
        return produtos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter produtos mais vendidos: {e}")

@app.get("/relatorio/quebras_por_produto/{loja}")
async def quebras_por_produto(loja: str, data_inicio: Optional[datetime] = None, data_fim: Optional[datetime] = None):
    try:
        quebras = await excel_manager.quebras_por_produto(loja, data_inicio, data_fim)
        if quebras is None:
            return {"loja": loja, "quebras_por_produto": {}}
        return quebras
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter quebras por produto: {e}")

@app.get("/relatorio/comparativo_lojas", response_model=ComparativoLojas)
async def comparativo_lojas(data_inicio: Optional[datetime] = None, data_fim: Optional[datetime] = None):
    try:
        comparativo = await excel_manager.gerar_comparativo_lojas(data_inicio, data_fim)
        if comparativo is None:
            return ComparativoLojas(data_inicio=data_inicio, data_fim=data_fim, comparativo=[])
        return comparativo
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar comparativo entre lojas: {e}")

@app.get("/relatorio/vendas_por_horario/{loja}", response_model=RelatorioVendasPorHora)
async def vendas_por_horario(loja: str, data_inicio: Optional[datetime] = None, data_fim: Optional[datetime] = None):
    try:
        relatorio = await excel_manager.relatorio_vendas_por_horario(loja, data_inicio, data_fim)
        if relatorio is None:
            return RelatorioVendasPorHora(loja=loja, vendas_por_hora=[])
        return relatorio
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter vendas por horário: {e}")

@app.get("/relatorio/rentabilidade/{loja}", response_model=RelatorioRentabilidade)
async def relatorio_rentabilidade(loja: str, data_inicio: Optional[datetime] = None, data_fim: Optional[datetime] = None):
    try:
        relatorio = await excel_manager.relatorio_rentabilidade(loja, data_inicio, data_fim)
        if relatorio is None:
            return RelatorioRentabilidade(loja=loja, rentabilidade=[])
        return relatorio
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar relatório de rentabilidade: {e}")

@app.get("/relatorio/excel_completo")
async def exportar_excel_completo(data_inicio: Optional[datetime] = None, data_fim: Optional[datetime] = None):
    try:
        excel_data = await excel_manager.gerar_excel_dashboard(data_inicio, data_fim)
        filename = f"Dashboard_Mafraria_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        return Response(
            content=excel_data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar Excel completo: {e}")

@app.get("/exportar/vendas/csv", response_class=Response)
async def exportar_vendas_csv():
    try:
        csv_data = await excel_manager.exportar_vendas_csv()
        if csv_data is None:
            raise HTTPException(status_code=404, detail="Nenhuma venda registada para exportar.")
        return Response(content=csv_data, media_type="text/csv")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao exportar vendas para CSV: {e}")

@app.get("/exportar/quebras/csv", response_class=Response)
async def exportar_quebras_csv():
    try:
        csv_data = await excel_manager.exportar_quebras_csv()
        if csv_data is None:
            raise HTTPException(status_code=404, detail="Nenhuma quebra registada para exportar.")
        return Response(content=csv_data, media_type="text/csv")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao exportar quebras para CSV: {e}")