# Garante que os modulos de teste (ex.: harness_combate) sejam importaveis
# independente do modo de import do pytest. So mexe no sys.path do processo de teste.
import os
import sys

_AQUI = os.path.dirname(__file__)
if _AQUI not in sys.path:
    sys.path.insert(0, _AQUI)
