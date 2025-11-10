# Multi-Move Input Feature

## Overview

The Chess MCP server now supports multi-move input, allowing you to execute multiple chess moves in a single tool call. This feature makes it easier to quickly set up positions or replay game sequences.

## New Tool: `chess_multimove`

### Description
Make multiple moves on the chess board at once using algebraic notation.

### Parameters
- **moves** (required): A string containing multiple moves in standard algebraic notation
- **fen** (optional): FEN string representing the current position. If not provided, starts from the initial position.

### Supported Formats

The tool supports several input formats:

1. **Simple space-separated moves**
   ```
   e4 c5
   ```

2. **Standard chess notation with move numbers**
   ```
   1. e4 c5
   ```

3. **Full game sequences**
   ```
   1. e4 c5 2. Nf3 d6 3. d4 cxd4 4. Nxd4
   ```

### Examples

#### Example 1: Sicilian Defense Opening
```json
{
  "tool": "chess_multimove",
  "arguments": {
    "moves": "e4 c5"
  }
}
```

**Response:**
```
2 moves played: e4, c5
Turn: white
FEN: rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2
```

#### Example 2: Sicilian Najdorf
```json
{
  "tool": "chess_multimove",
  "arguments": {
    "moves": "1. e4 c5 2. Nf3 d6 3. d4 cxd4 4. Nxd4 Nf6 5. Nc3 a6"
  }
}
```

**Response:**
```
10 moves played: e4, c5, Nf3, d6, d4, cxd4, Nxd4, Nf6, Nc3, a6
Turn: white
```

#### Example 3: Continue from a position
```json
{
  "tool": "chess_multimove",
  "arguments": {
    "moves": "Nf3 Nc6",
    "fen": "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
  }
}
```

## Error Handling

If an invalid move is encountered in the sequence, the tool will:
1. Stop processing further moves
2. Return an error message indicating which move failed
3. Report which moves were successfully played before the error
4. Return the FEN of the position reached before the error

**Example Error:**
```
Invalid move sequence. Error at move 'Nf9': invalid square name 'f9' in '{}'. 
Successfully played: e4, c5
```

## Use Cases

1. **Setting up positions quickly**: Instead of playing moves one at a time, you can set up a specific position in one call
2. **Replaying games**: Input a sequence of moves from a game to reach a specific position
3. **Testing openings**: Quickly test opening variations
4. **Educational purposes**: Demonstrate tactical sequences or endgame techniques

## Local Testing

You can test the new feature using the local test script:

```bash
python3 chess_local_test.py
```

Then use the command:
```
multimove e4 c5
multimove 1. e4 c5 2. Nf3 d6
```

## Comparison with Single Move Tool

| Feature | `chess_move` | `chess_multimove` |
|---------|--------------|-------------------|
| Moves per call | 1 | Multiple |
| Input format | Single move (e.g., "e4") | Space-separated moves (e.g., "e4 c5") |
| Move numbers | Not supported | Supported (stripped automatically) |
| Use case | Playing individual moves | Setting up positions, replaying sequences |

## Implementation Details

- Moves are parsed by removing move numbers (e.g., "1.", "2.") and splitting by whitespace
- Each move is validated and applied sequentially to the board
- The tool maintains full compatibility with standard algebraic notation (SAN)
- All chess rules are enforced (legal moves, turn order, check/checkmate detection)

## Future Enhancements

Potential future improvements:
- Support for PGN format import
- Support for move annotations (!, ?, !!, etc.)
- Support for comments in move sequences
- Batch validation before applying any moves

## Version

Added in: Chess MCP Server v1.1
Date: November 8, 2025

