# Sertão TCG Database

Banco de dados leve para o buscador de cartas do Sertão TCG.

## Pokémon

`data/pokemon.json` é gerado automaticamente a partir do repositório público `PokemonTCG/pokemon-tcg-data`.

O arquivo final mantém apenas os campos necessários para busca e exibição no site: ID, nome, número, coleção, série, data, raridade, tipo e URLs de imagem fornecidas pelo dataset de origem.

O workflow `Atualizar banco Pokemon` verifica o dataset diariamente e atualiza o JSON quando houver mudanças.
