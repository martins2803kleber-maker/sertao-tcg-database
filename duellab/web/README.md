# Duel Lab Web

Interface web do Duel Lab do SertãoTCG para Yu-Gi-Oh!, construída sobre o OCGCore/WASM já presente neste repositório.

## Recursos atuais

- carregamento de deck por YDKE;
- OCGCore real via `assets/duellab/engine`;
- banco de cartas local em `data/yugioh.json` e dados de core em `assets/duellab/core`;
- scripts de cartas Project Ignis carregados sob demanda;
- resolução de scripts nas pastas raiz, `official/`, `pre-errata/`, `goat/` e `unofficial/`;
- carregamento automático de dependências declaradas com `Duel.LoadScript(...)`;
- bibliotecas globais/procedures carregadas antes dos scripts das cartas;
- Main/Extra Deck, mão, campo, S/T, GY e banidas espelhados na interface;
- comandos legais por clique direito;
- prompts para seleção, posição, opções, chain, tributos, counters, sum e ordenar;
- fases, LP e mensagens do core refletidas na interface;
- modo tela cheia e layout responsivo;
- skin visual inspirada no fluxo de mesa do EDOPro, mantendo a identidade Duel Lab/SertãoTCG.

## Estrutura

`index.html` contém a mesa e os painéis. `styles.css` contém a skin. `app.js` carrega os blocos em `chunks/` e executa o runtime como uma única unidade. O engine e os grandes bancos ficam fora da camada visual para permitir atualização independente.

## Observação

O Duel Lab usa o OCGCore para regras e scripts, mas a interface web é própria. Compatibilidade total com todos os fluxos do cliente desktop depende de implementar, na interface, todos os tipos de mensagens/prompts que o core possa emitir.
