from __future__ import annotations
from dataclasses import dataclass

CATEGORIAS = ["Admissões", "Férias", "Rescisões"]
MESES = {1:"Janeiro",2:"Fevereiro",3:"Março",4:"Abril",5:"Maio",6:"Junho",7:"Julho",8:"Agosto",9:"Setembro",10:"Outubro",11:"Novembro",12:"Dezembro"}
MESES_ABREV = {1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}
COLORS = {
    "bg":"#F6F7F8","surface":"#FFFFFF","text":"#22272E","muted":"#6D7680","border":"#DFE4E8","grid":"#E9EDF0","primary":"#34404B",
    "Admissões":"#A5525A","Férias":"#478A84","Rescisões":"#68717A",
}
PLOT_CONFIG = {"displayModeBar":False,"responsive":True,"scrollZoom":False}
@dataclass(frozen=True)
class Filters:
    year:int; start_month:int; end_month:int; categories:tuple[str,...]
    @property
    def months(self): return list(range(self.start_month,self.end_month+1))
    @property
    def period_label(self): return f"{MESES_ABREV[self.start_month]}–{MESES_ABREV[self.end_month]} {self.year}" if self.start_month != self.end_month else f"{MESES_ABREV[self.start_month]} {self.year}"
