#projeto de controle financeiro 
#um sistema para cadastrar receitas e despesas, editar lancçamentos, excluir registros e consultar o saldo atual, além de gerar relatórios financeiros.
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Lancamento:
    descricao:str
    valor: float
    tipo:str #"receita" ou "despesa"
    categoria: str ="Geral"
    data: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    id: int | None = None

    @property
    def valor_com_sinal(self) -> float:
        return self.valor if self.tipo == "receita" else - self.valor
    
