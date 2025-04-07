# Documentação do Bot RPG - Sistema de Iniciativa

Este documento contém informações sobre os comandos disponíveis para gerenciar a iniciativa em combates de RPG através do bot de Discord. O sistema facilita o trabalho do Mestre, mantendo a ordem dos turnos, os efeitos ativos nos personagens e a progressão das rodadas.

## Prefixo

Todos os comandos do bot usam o prefixo `$`. Por exemplo: `$init`

## Comandos Gerais

| Comando | Descrição |
|---------|-----------|
| `$msg [texto]` | Envia uma mensagem como o bot e apaga o comando original |
| `$driscol` | Grita "DRISCOOOOOOL!" no canal |

## Comandos de Iniciativa

Todos os comandos relacionados à iniciativa começam com `$init`.

### Comando Base

| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `$init` | Exibe a lista atual de iniciativa | `$init` |

### Gerenciamento de Personagens

| Comando | Descrição | Exemplo | Observações |
|---------|-----------|---------|-------------|
| `$init add [nome] [iniciativa] [tipo]` | Adiciona um personagem à ordem de iniciativa | `$init add "Goblin Arqueiro" 15 npc` | [tipo] pode ser "pc"/"player" para jogadores ou "npc" para monstros (padrão: npc) |
| `$init remove [nome]` | Remove um personagem da lista de iniciativa | `$init remove "Goblin Arqueiro"` | Também pode ser usado como `$init rm` |
| `$init clear` | Remove todos os personagens da lista de iniciativa | `$init clear` | Também encerra o combate ativo |

### Controle de Combate

| Comando | Descrição | Exemplo | Observações |
|---------|-----------|---------|-------------|
| `$init start` | Inicia o combate com os personagens na lista | `$init start` | Define o primeiro personagem da lista como ativo |
| `$init end` | Encerra o combate atual | `$init end` | Mantém os personagens na lista para um possível novo combate |
| `$init next` | Avança para o próximo personagem na ordem de iniciativa | `$init next` | Também pode ser usado como `$init n`. Atualiza automaticamente as rodadas |

### Gerenciamento de Efeitos

| Comando | Descrição | Exemplo | Observações |
|---------|-----------|---------|-------------|
| `$init effect [personagem] [efeito] [duração] [descrição]` | Adiciona um efeito a um personagem | `$init effect "Thrain" "Bênção" 5 "Bônus de +1d4 nas jogadas"` | Também pode ser usado como `$init ef`. [descrição] é opcional |
| `$init remove_effect [personagem] [efeito]` | Remove um efeito de um personagem | `$init remove_effect "Thrain" "Bênção"` | Também pode ser usado como `$init rmef` |

## Fluxo de Uso Típico

Aqui está um exemplo de como usar o sistema de iniciativa durante uma sessão de jogo:

### 1. Preparando o Combate

```
$init add "Aragorn" 18 pc
$init add "Legolas" 20 pc
$init add "Gimli" 12 pc
$init add "Orc Capitão" 15 npc
$init add "Orc Guerreiro" 11 npc
$init add "Orc Guerreiro 2" 11 npc
```

### 2. Iniciando o Combate

```
$init start
```

O bot responderá:
```
⚔️ Combate iniciado! Rodada 1
📋 INICIATIVA (Rodada 1)
➡️ 👤 Legolas - Iniciativa: 20
   👤 Aragorn - Iniciativa: 18
   👹 Orc Capitão - Iniciativa: 15
   👤 Gimli - Iniciativa: 12
   👹 Orc Guerreiro - Iniciativa: 11
   👹 Orc Guerreiro 2 - Iniciativa: 11

É o turno de Legolas!
```

### 3. Avançando os Turnos

```
$init next
```

O bot responderá:
```
➡️ Agora é o turno de Aragorn!
📋 INICIATIVA (Rodada 1)
   👤 Legolas - Iniciativa: 20
➡️ 👤 Aragorn - Iniciativa: 18
   👹 Orc Capitão - Iniciativa: 15
   👤 Gimli - Iniciativa: 12
   👹 Orc Guerreiro - Iniciativa: 11
   👹 Orc Guerreiro 2 - Iniciativa: 11
```

Continue usando `$init next` para avançar pelos turnos.

### 4. Aplicando Efeitos

```
$init effect "Aragorn" "Inspirado" 3 "Bônus de +2 nos ataques"
```

O bot responderá:
```
✨ Efeito Inspirado (3 turnos) adicionado a Aragorn.
📋 INICIATIVA (Rodada 1)
   👤 Legolas - Iniciativa: 20
➡️ 👤 Aragorn - Iniciativa: 18 (Inspirado (3 turnos))
   👹 Orc Capitão - Iniciativa: 15
   👤 Gimli - Iniciativa: 12
   👹 Orc Guerreiro - Iniciativa: 11
   👹 Orc Guerreiro 2 - Iniciativa: 11
```

### 5. Removendo Personagens

```
$init remove "Orc Guerreiro"
```

O bot responderá:
```
✅ Orc Guerreiro removido da iniciativa.
📋 INICIATIVA (Rodada 1)
   👤 Legolas - Iniciativa: 20
➡️ 👤 Aragorn - Iniciativa: 18 (Inspirado (3 turnos))
   👹 Orc Capitão - Iniciativa: 15
   👤 Gimli - Iniciativa: 12
   👹 Orc Guerreiro 2 - Iniciativa: 11
```

### 6. Encerrando o Combate

```
$init end
```

O bot responderá:
```
🕊️ Combate encerrado!
```

## Notas Importantes

- Os efeitos têm sua duração reduzida automaticamente quando o turno do personagem chega.
- Quando um efeito atinge duração 0, ele é removido automaticamente.
- Os personagens de jogadores são marcados com 👤, enquanto NPCs são marcados com 👹.
- O personagem atual é indicado com uma seta ➡️ na lista de iniciativa.
- A lista de iniciativa é ordenada automaticamente pela iniciativa (valor mais alto primeiro).
- O sistema mantém um tracker de iniciativa separado para cada canal, então você pode ter combates diferentes acontecendo em canais diferentes.

## Comandos Rápidos

- `$init` - Ver a lista atual
- `$init n` - Avançar para o próximo turno
- `$init add` - Adicionar personagem
- `$init rm` - Remover personagem
- `$init ef` - Adicionar efeito
- `$init rmef` - Remover efeito
