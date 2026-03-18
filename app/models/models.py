from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Venda(BaseModel):
    loja: str
    produto: str
    valor: float
    quantidade: int
    horario: datetime

class Quebra(BaseModel):
    loja: str
    produto: str
    quantidade: int
    motivo: str
    data: datetime

class RelatorioFaturacao(BaseModel):
    loja: str
    data_inicio: Optional[datetime]
    data_fim: Optional[datetime]
    faturacao_total: float
    ticket_medio: float

class ResumoLoja(BaseModel):
    loja: str
    faturacao_total: float
    ticket_medio: float
    total_quebras: int

class ComparativoLojas(BaseModel):
    data_inicio: Optional[datetime]
    data_fim: Optional[datetime]
    comparativo: list[ResumoLoja]

class VendasPorHora(BaseModel):
    hora: int
    quantidade_vendas: int
    valor_total: float

class RelatorioVendasPorHora(BaseModel):
    loja: str
    vendas_por_hora: list[VendasPorHora]

class RentabilidadeProduto(BaseModel):
    produto: str
    quantidade_vendida: int
    valor_vendas: float
    quantidade_quebras: int
    racio_quebra_venda: float # % de quebra em relação à venda (quantidade)

class RelatorioRentabilidade(BaseModel):
    loja: str
    rentabilidade: list[RentabilidadeProduto]