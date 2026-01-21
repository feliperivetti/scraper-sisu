from abc import ABC, abstractmethod

class SisuDataProvider(ABC):
    @abstractmethod
    def get_lista_vagas(self, id_curso: str):
        """Retorna a lista bruta de ofertas da fonte."""
        pass

    @abstractmethod
    def get_nota_corte(self, co_oferta: str):
        """Retorna a nota de corte específica de uma oferta."""
        pass