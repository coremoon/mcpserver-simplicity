# SimplicityHL Examples

Diese Beispiele zeigen verschiedene Features von SimplicityHL basierend auf der offiziellen Dokumentation.

## Verfügbare Beispiele

### 1. **witness_equality.simf** / .wit
Vergleicht zwei Witness-Werte und verifiziert, dass sie gleich sind.
- **Zeigt**: Witness-Handling, jet::eq_32, jet::verify

### 2. **arithmetic.simf** / .wit
Demonstriert arithmetische Operationen und Assertions.
- **Zeigt**: jet::add_32, jet::max_32, assert!, Berechnungen

### 3. **scoping.simf** / .wit
Zeigt Variable Shadowing und Scope-Regeln.
- **Zeigt**: Nested blocks, Variable shadowing, Outer scope access

### 4. **witness_computation.simf** / .wit
Liest Witness-Daten, führt Berechnungen durch und verifiziert das Ergebnis.
- **Zeigt**: Multiple witnesses, Computation mit witness data

## SimplicityHL Syntax Overview

### Variablen
```rust
let a: u32 = 10;        // Expliziter Typ
let b = 20;             // Type inference
```

### Witness Data
```rust
let value: u32 = witness;  // Liest einen Witness-Wert
```

### Blocks
```rust
let result = {
    let temp = 5;
    jet::add_32(temp, 10)  // Letzter Ausdruck wird zurückgegeben (kein ;)
};
```

### Jets (Built-in Functions)
- `jet::add_32(a, b)` - 32-bit Addition
- `jet::eq_32(a, b)` - 32-bit Equality check (returns bool)
- `jet::max_32(a, b)` - Maximum von zwei Werten
- `jet::verify(bool)` - Verifiziert dass der Wert true ist

### Assertions
```rust
assert!(condition);  // Programm schlägt fehl wenn false
```

## Kompilierung

### Mit pysimplicityhl (Python)
```python
import pysimplicityhl

source = open('examples/arithmetic.simf').read()
witness = open('examples/arithmetic.wit').read()

result = pysimplicityhl.compile(source, witness)
```

### Mit simc (Rust Compiler)
```bash
# Ohne witness
simc examples/arithmetic.simf

# Mit witness
simc examples/witness_computation.simf examples/witness_computation.wit
```

## Testing mit MCP Server

```python
# Via MCP Server
result = await session.call_tool(
    "compile_simplicity",
    arguments={
        "source_code": open('examples/arithmetic.simf').read(),
        "witness_data": open('examples/arithmetic.wit').read()
    }
)
```

## Typische Fehler

### Fehler 1: Type Mismatch
```rust
let a: u32 = 10;
let b: u64 = 20;
jet::add_32(a, b)  // ❌ Type mismatch: b ist u64, erwartet u32
```

### Fehler 2: Missing Witness
```rust
let value: u32 = witness;  // ❌ Witness-Datei fehlt oder ist leer
```

### Fehler 3: Assertion Failed
```rust
assert!(jet::eq_32(10, 20));  // ❌ Assertion fails: 10 != 20
```

### Fehler 4: Wrong Witness Count
```rust
// Code erwartet 3 witnesses
let a: u32 = witness;
let b: u32 = witness;
let c: u32 = witness;

// Aber .wit Datei hat nur 2 Werte
// ❌ Not enough witness data
```

## Weitere Ressourcen

- [SimplicityHL GitHub](https://github.com/BlockstreamResearch/SimplicityHL)
- [Offizielle Beispiele](https://github.com/BlockstreamResearch/SimplicityHL/tree/master/examples)
- [Simplicity Whitepaper](https://blockstream.com/simplicity.pdf)
