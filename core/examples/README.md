# Personality DSL Examples

This directory contains example personality definitions written in the Callosum Personality DSL.

## Files

- `sample_personality.colo` - A comprehensive example showing all DSL features including traits, knowledge domains, behaviors, and evolution
- `test_personality.colo` - A simpler example used for testing basic functionality

## Usage

Parse and compile these examples using the DSL parser:

```bash
# Parse and validate
dsl-parser --input examples/sample_personality.colo --validate

# Compile to different targets
dsl-parser --input examples/sample_personality.colo --output prompt
dsl-parser --input examples/sample_personality.colo --output json
dsl-parser --input examples/sample_personality.colo --output lua
```

## Creating Your Own

Use these examples as templates for creating your own AI personality definitions. The DSL supports:

- **Dynamic Traits**: Personality characteristics that can evolve over time
- **Knowledge Domains**: Areas of expertise with interconnections
- **Behavioral Rules**: Context-aware response preferences
- **Evolution Specifications**: How the personality grows through interactions

See the main README for complete language documentation.
