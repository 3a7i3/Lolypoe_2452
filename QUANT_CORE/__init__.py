import sys
sys.modules['QUANT_CORE.data'] = sys.modules.get('QUANT_CORE.data', None)
sys.modules['QUANT_CORE.features'] = sys.modules.get('QUANT_CORE.features', None)
sys.modules['QUANT_CORE.backtesting'] = sys.modules.get('QUANT_CORE.backtesting', None)
sys.modules['QUANT_CORE.risk'] = sys.modules.get('QUANT_CORE.risk', None)
sys.modules['QUANT_CORE.portfolio'] = sys.modules.get('QUANT_CORE.portfolio', None)
sys.modules['QUANT_CORE.strategy'] = sys.modules.get('QUANT_CORE.strategy', None)
sys.modules['QUANT_CORE.validation'] = sys.modules.get('QUANT_CORE.validation', None)
sys.modules['QUANT_CORE.interfaces'] = sys.modules.get('QUANT_CORE.interfaces', None)

from .quant_core import QuantCore
