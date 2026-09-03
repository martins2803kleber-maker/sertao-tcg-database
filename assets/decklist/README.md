# Template Universal de Decklists — Sertão TCG

Motor compartilhado para Blogger com suporte a One Piece Card Game, Pokémon TCG e Yu-Gi-Oh!.

## Recursos
- Um único CSS e um único JavaScript para os três jogos.
- Renderização de capa, contadores, grids e modal de carta.
- Banco remoto do próprio repositório.
- Fallback de imagens.
- Botão **Copiar Deck**.
- Yu-Gi-Oh!: copia o YDKE original ou uma lista textual.
- One Piece/Pokémon: copia a lista de importação original.
- Layout responsivo.

## One Piece
```html
<div class="stcg-deck" data-game="onepiece" data-title="Deck" data-author="Jogador">
<textarea class="stcg-source" hidden>
1xOP13-001
4xEB04-007
</textarea>
</div>
```

## Pokémon
```html
<div class="stcg-deck" data-game="pokemon" data-title="Deck" data-author="Jogador">
<textarea class="stcg-source" hidden>
Pokémon: 2
2 Pikachu MEW 25

Trainer: 0

Energy: 0
</textarea>
</div>
```

## Yu-Gi-Oh!
```html
<div class="stcg-deck" data-game="yugioh" data-title="Deck" data-author="Jogador">
<textarea class="stcg-source" hidden>ydke://COLE_AQUI_O_YDKE</textarea>
</div>
```

## CDN
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/martins2803kleber-maker/sertao-tcg-database@main/assets/decklist/sertao-decklist.css">
<script src="https://cdn.jsdelivr.net/gh/martins2803kleber-maker/sertao-tcg-database@main/assets/decklist/sertao-decklist.js"></script>
```