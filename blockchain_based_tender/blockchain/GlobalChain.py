from .Chain import Blockchain

# Создаем единственный экземпляр глобальной цепочки, которая фиксирует все тендеры
GLOBAL_TENDER_CHAIN = Blockchain(
    genesis_data={'message': 'Global Tender Registry initialized (Chain 2)'}
)

def add_tender_event_to_global_chain(data):
    """
    Добавляет событие, связанное с тендером, в Глобальную Цепочку.
    """
    GLOBAL_TENDER_CHAIN.add_block(data)
    # Возвращаем хэш последнего блока, чтобы использовать его как "ссылку"
    return GLOBAL_TENDER_CHAIN.chain[-1].hash

def get_global_chain():
    """Возвращает текущий экземпляр Глобальной Цепочки."""
    return GLOBAL_TENDER_CHAIN

def get_global_chain_data():
    """Возвращает данные Глобальной Цепочки в виде списка объектов Block для сериализации."""
    # Возвращаем именно chain, так как views.py использует cls=BlockChainJSONEncoder
    return GLOBAL_TENDER_CHAIN.chain