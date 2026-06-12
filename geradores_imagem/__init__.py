"""
Adapters async pras 3 APIs de geração de imagem do Módulo 4.6.

- gerador_flux:   FLUX Kontext via fal-client      (PRIMÁRIO — consistência)
- gerador_gemini: Gemini Nano Banana 2 via google-genai  (SECUNDÁRIO — custo/PT-BR)
- gerador_gpt:    GPT Image 1.5 via AsyncOpenAI    (TERCIÁRIO — edição regional)

Cada adapter expõe uma função `gerar_*()` async que retorna ResultadoXxx
(dataclass). O pipeline_geracao.py orquestra qual usar.
"""
