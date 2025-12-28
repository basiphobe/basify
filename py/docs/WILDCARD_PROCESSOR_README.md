# Wildcard Processor

## Overview

The **Wildcard Processor** is a ComfyUI custom node that enables dynamic text generation using wildcard tokens. Wildcards are placeholders (formatted as `__token__`) that get replaced with random values from text files, allowing for automated variation in prompts, descriptions, and other text-based inputs. The node features intelligent caching, unique selection to avoid duplicates, and enhanced randomness control.

## Key Features

- **Dynamic Text Replacement**: Replaces wildcard tokens with random selections from files
- **Unique Selection**: Avoids duplicate replacements within a single text
- **Enhanced Randomness**: Optional force_refresh for increased variation
- **Global Caching**: Stores processed text for access by other nodes
- **Passthrough Design**: Returns both processed and original text
- **Flexible Directory**: Configurable wildcard file location
- **Memory Management**: Automatic cache cleanup to prevent overflow
- **Error Resilient**: Graceful handling of missing files or invalid tokens
- **Colored Logging**: Console output with color-coded status messages

## Node Information

- **Node Name**: `BasifyWildcardProcessor`
- **Display Name**: `Basify: Wildcard Processor`
- **Category**: `utils`
- **Output Node**: Yes (triggers execution)

## Input Parameters

### Required Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | STRING | `""` | Input text containing wildcard tokens (multiline supported) |

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_wildcards` | BOOLEAN | `True` | Enable/disable wildcard processing |
| `wildcard_directory` | STRING | `"/llm/models/image/wildcards"` | Directory containing wildcard files |
| `force_refresh` | STRING | `""` | Any value forces enhanced randomness |

### Hidden Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `prompt` | PROMPT | ComfyUI prompt information |
| `unique_id` | UNIQUE_ID | Node instance identifier for caching |

## Output Values

| Output | Type | Description |
|--------|------|-------------|
| `processed_text` | STRING | Text with wildcards replaced |
| `original_text` | STRING | Original input text (unchanged) |

## Wildcard Syntax

### Token Format

Wildcards are enclosed in double underscores:
```
__wildcard_name__
```

**Examples**:
```
__color__
__animal__
__weather__
__style/artistic__
```

### Wildcard Files

Wildcard tokens map to `.txt` files in the wildcard directory:

**Token**: `__color__`
**File**: `color.txt`

**Token**: `__style/artistic__`
**File**: `style/artistic.txt`

### File Format

Each wildcard file contains one option per line:

**color.txt**:
```
red
blue
green
yellow
orange
purple
# This is a comment and will be ignored
pink
```

**Rules**:
- One option per line
- Lines starting with `#` are comments (ignored)
- Empty lines are ignored
- Leading/trailing whitespace is stripped

## How It Works

### Processing Flow

1. **Input Validation**:
   - Check if text is provided
   - Verify wildcards are enabled
   - Resolve wildcard directory path

2. **Token Detection**:
   - Scan text for `__token__` patterns using regex
   - Find all wildcard occurrences
   - Log number of tokens found

3. **Unique Selection**:
   - For each token, load corresponding file
   - Track previously used replacements
   - Select random line not yet used
   - Reset tracking if all lines exhausted

4. **Text Replacement**:
   - Replace tokens from end to beginning (avoid position shifts)
   - Substitute each `__token__` with selected value
   - Preserve text formatting and structure

5. **Caching**:
   - Store processed text with node ID as key
   - Store as "latest" for easy access
   - Clean up old cache entries if needed

6. **Output**:
   - Return processed text
   - Return original text for comparison

### Randomness Enhancement

**Standard Mode** (`force_refresh` empty):
- Uses Python's standard `random.choice()`
- Good randomness for most use cases

**Enhanced Mode** (`force_refresh` has any value):
- Creates entropy from multiple sources:
  - Current timestamp
  - Force refresh value
  - Wildcard name
  - Available options count
  - Attempt number
- Uses MD5 hashing for seed generation
- Adds microsecond-based secondary randomization
- Results in more varied selections

### Duplicate Prevention

Within a single text:
```
Input: "A __color__ car and a __color__ truck"

Prevents: "A red car and a red truck"
Ensures: "A red car and a blue truck"
```

The node tracks used values and selects different ones for each occurrence.

## Usage Examples

### Basic Wildcard Processing

**Wildcard File** (`animal.txt`):
```
dog
cat
bird
rabbit
```

**Input Text**:
```
A cute __animal__ playing in the park
```

**Possible Outputs**:
```
A cute dog playing in the park
A cute cat playing in the park
A cute bird playing in the park
A cute rabbit playing in the park
```

### Multiple Wildcards

**Wildcard Files**:

`color.txt`:
```
red
blue
green
```

`animal.txt`:
```
dog
cat
bird
```

**Input Text**:
```
A __color__ __animal__ sitting on a __color__ blanket
```

**Possible Output**:
```
A red dog sitting on a blue blanket
```

**Note**: Both `__color__` tokens will get different values.

### Nested Directory Structure

**Directory Structure**:
```
wildcards/
├── animals/
│   ├── domestic.txt
│   ├── wild.txt
│   └── birds.txt
├── colors/
│   ├── warm.txt
│   └── cool.txt
└── styles/
    └── artistic.txt
```

**Input Text**:
```
A __colors/warm__ __animals/domestic__ in __styles/artistic__ style
```

**Possible Output**:
```
A orange dog in impressionist style
```

### Integration with Image Generation

```
[Wildcard Processor] -> processed_text -> [CLIP Text Encode] -> [KSampler]
```

**Input**:
```
__quality__ portrait of a __person__ in __setting__, __lighting__, __style__
```

**Processed**:
```
highly detailed portrait of a young woman in ancient library, soft golden lighting, oil painting style
```

### Batch Variation Generation

```
[Wildcard Processor] -> processed_text ──┐
                     -> original_text ──┐│
                                        ││
[Loop 10 times] ────────────────────────┴┴─> [Generate Image]
```

Each iteration produces different prompt variations.

### Filename Generation

```
[Wildcard Processor] -> processed_text -> [Sanitize Text] -> [Save Image with dynamic filename]
```

**Input**:
```
__theme__-__date__-__number__
```

**Output**:
```
fantasy-2025-12-28-0042
```

### Conditional Wildcards

Use different wildcard sets based on conditions:

**Directory**: `wildcards/seasons/`
```
spring.txt: "blooming flowers", "green grass", "baby animals"
summer.txt: "bright sun", "beach", "heat waves"
autumn.txt: "falling leaves", "harvest", "cool breeze"
winter.txt: "snow", "frost", "ice crystals"
```

**Input**:
```
A landscape with __seasons/winter__, peaceful atmosphere
```

## Wildcard Organization

### Recommended Structure

```
wildcards/
├── README.md                    # Documentation
├── characters/
│   ├── male.txt
│   ├── female.txt
│   ├── fantasy.txt
│   └── scifi.txt
├── settings/
│   ├── indoor.txt
│   ├── outdoor.txt
│   ├── urban.txt
│   └── nature.txt
├── styles/
│   ├── artistic.txt
│   ├── photographic.txt
│   └── digital.txt
├── lighting/
│   ├── natural.txt
│   ├── studio.txt
│   └── dramatic.txt
├── quality/
│   ├── high.txt
│   └── modifiers.txt
└── colors/
    ├── warm.txt
    ├── cool.txt
    └── neutral.txt
```

### File Naming Best Practices

**Good**:
- ✅ `animal.txt` - Simple, descriptive
- ✅ `setting_indoor.txt` - Clear category
- ✅ `style-artistic.txt` - Readable separator

**Poor**:
- ❌ `stuff.txt` - Too vague
- ❌ `temp1.txt` - Meaningless
- ❌ `MyWildcards.txt` - Non-standard capitalization

### Content Organization

**Themed Collections**:
```
# fantasy.txt
ancient wizard casting spells
knight in shining armor
dragon soaring through clouds
mystical forest with glowing mushrooms
enchanted castle on a hilltop
```

**Modifiers**:
```
# quality.txt
masterpiece
best quality
highly detailed
8k resolution
professional
award-winning
```

**Combinations**:
```
# colors.txt
deep crimson
soft pastel blue
vibrant neon green
warm golden yellow
cool steel gray
```

## Caching System

### Cache Structure

```python
_wildcard_output_cache = {
    "node_123": "processed text for node 123",
    "node_456": "processed text for node 456",
    "latest": "most recently processed text"
}
```

### Cache Access Functions

**Get Latest Output**:
```python
from basify.py.wildcard_processor import get_latest_wildcard_output

latest = get_latest_wildcard_output()
# Returns most recent processed text or None
```

**Get by Node ID**:
```python
from basify.py.wildcard_processor import get_wildcard_output_by_node_id

text = get_wildcard_output_by_node_id("node_123")
# Returns text for specific node or None
```

**Get All Outputs**:
```python
from basify.py.wildcard_processor import get_all_wildcard_outputs

all_outputs = get_all_wildcard_outputs()
# Returns dict of all cached outputs
```

### Cache Management

- **Max Size**: 100 entries
- **Cleanup**: Automatic when limit exceeded
- **Retention**: Keeps "latest" and node ID entries
- **Removal**: Timestamp-based entries removed first

## Parameter Details

### enable_wildcards

**When True** (default):
- Processes all wildcard tokens
- Replaces `__token__` with random values

**When False**:
- Returns original text unchanged
- Bypasses all wildcard processing
- Useful for testing or temporarily disabling

### wildcard_directory

**Absolute Paths**:
```
/home/user/wildcards
C:\Users\user\wildcards
```

**Relative Paths** (from ComfyUI root):
```
./wildcards
../shared/wildcards
```

**Default**: `/llm/models/image/wildcards`

### force_refresh

Any non-empty value triggers enhanced randomness:

**Examples**:
- `"1"` - Simple counter
- `"refresh"` - Static trigger
- `str(random.random())` - Dynamic per execution
- `str(time.time())` - Timestamp-based
- `"batch_42"` - Batch identifier

**Use Cases**:
- Generating multiple variations quickly
- Ensuring different results in rapid succession
- Batch processing with guaranteed variation

## Error Handling

### Missing Files

**Problem**: Wildcard file doesn't exist

**Behavior**:
```
Input: "A __nonexistent__ object"
Output: "A __nonexistent__ object" (token unchanged)
Log: [WARNING] Wildcard file not found: /path/to/nonexistent.txt
```

### Empty Files

**Problem**: Wildcard file has no valid lines

**Behavior**:
```
Input: "A __empty__ scene"
Output: "A __empty__ scene" (token unchanged)
Log: [WARNING] No valid lines in wildcard file: empty.txt
```

### Invalid Directory

**Problem**: Wildcard directory doesn't exist

**Behavior**:
- All wildcard lookups fail
- Tokens remain unchanged
- Console warnings logged

### Malformed Tokens

**Problem**: Incorrect token format

**Valid**: `__token__`
**Invalid**: `_token__`, `__token_`, `token`, `_token_`

Invalid tokens are treated as regular text (not replaced).

## Console Logging

### Log Colors

| Color | Meaning | Example |
|-------|---------|---------|
| 🔵 Blue | Info/Status | `[BASIFY Wildcards Node] Successfully processed wildcards` |
| 🟢 Green | Success | `Selected from color.txt: blue` |
| 🟡 Yellow | Warning | `Wildcards disabled, returning original text` |
| 🔴 Red | Error | `Error processing wildcards: ...` |

### Log Messages

**Processing Success**:
```
[BASIFY Wildcards Node] Successfully processed wildcards in text
[BASIFY Wildcards] Found 3 wildcard token occurrences to process
[BASIFY Wildcards] Selected from color.txt: red
```

**Wildcards Disabled**:
```
[BASIFY Wildcards Node] Wildcards disabled, returning original text
```

**Missing File**:
```
[BASIFY Wildcards] Wildcard file not found: /path/to/missing.txt
```

**Caching**:
```
[BASIFY Wildcards Node] Cached processed text for node node_123: A red car...
```

## Best Practices

### 1. File Organization

**By Category**:
```
wildcards/
├── objects/
├── actions/
├── descriptors/
└── locations/
```

**By Use Case**:
```
wildcards/
├── portraits/
├── landscapes/
├── abstract/
└── product/
```

### 2. Content Quality

**Descriptive Entries**:
```
# Good: descriptive, specific
wearing an elegant red evening gown
standing in dramatic heroic pose
surrounded by swirling magical energy

# Poor: too vague
red dress
standing
magic
```

**Consistent Style**:
```
# Consistent grammatical structure
flowing white gown with golden embroidery
fitted black suit with silver buttons
casual jeans with colorful patches

# Inconsistent (harder to use)
flowing white gown
she wears a black suit
patches on jeans
```

### 3. Token Naming

**Clear and Consistent**:
- Use lowercase: `__style__` not `__Style__`
- Descriptive names: `__character_pose__` not `__cp__`
- Logical paths: `__lighting/natural__` not `__nat_light__`

### 4. Testing Wildcards

Test individual wildcards before using in production:

```
Input: __color__
Run multiple times to verify variety and quality
```

### 5. Version Control

Track wildcard files in Git:

```bash
git add wildcards/
git commit -m "Add fantasy character wildcards"
```

Allows tracking changes and reverting problematic updates.

### 6. Documentation

Include README.md in wildcard directories:

```markdown
# Color Wildcards

## color.txt
Basic color names for general use.

## colors/warm.txt
Warm tones: reds, oranges, yellows

## colors/cool.txt
Cool tones: blues, greens, purples
```

## Advanced Usage

### Dynamic Prompts

Create complex, varied prompts:

```
__quality__, __detail__ __shot_type__ of __subject__ __action__ in __location__, 
__lighting__, __atmosphere__, __style__, __technical__
```

**Produces**:
```
masterpiece, highly detailed close-up of a warrior wielding a sword in ancient temple,
dramatic side lighting, misty atmosphere, oil painting style, 8k resolution
```

### Layered Wildcards

Wildcards can reference other wildcards in their content:

**base.txt**:
```
A __color__ __animal__
```

**color.txt**:
```
bright red
deep blue
```

**animal.txt**:
```
dog
cat
```

Process recursively by running processor multiple times.

### Conditional Logic

Use multiple wildcard processors with conditions:

```
[Check Condition] ──┐
                    ├─ If True  -> [Wildcard Processor A (fantasy)]
                    └─ If False -> [Wildcard Processor B (scifi)]
```

### Weighted Selection

Create weighted randomness by repeating entries:

**rarity.txt**:
```
common
common
common
uncommon
uncommon
rare
```

`common` has 3× chance of selection vs `rare`.

### Template System

Create reusable templates:

**portrait_template.txt**:
```
__quality__ portrait of __person__ with __expression__, __pose__, __clothing__, __background__
```

**Input**:
```
__portrait_template__
```

### Batch Processing Script

Generate multiple variations:

```python
from basify.py.wildcard_processor import WildcardProcessor

processor = WildcardProcessor()
template = "A __color__ __animal__ in __location__"

variations = []
for i in range(10):
    result = processor.process_text(template, force_refresh=str(i))
    variations.append(result[0])

# Save variations
with open('variations.txt', 'w') as f:
    for var in variations:
        f.write(var + '\n')
```

## Integration Examples

### Text-to-Image Workflow

```
[Wildcard Processor] -> processed_text -> [CLIP Text Encode (Positive)]
                     -> original_text -> [Log/Display]
```

### Automated Caption Generation

```
[Image] -> [Describe Image] -> description -> [Wildcard Processor (add style)]
                                                    |
                                                    v
                                            [Enhanced Caption]
```

### Multi-Language Support

**Directory**:
```
wildcards/
├── en/
│   └── colors.txt
├── es/
│   └── colors.txt
└── fr/
    └── colors.txt
```

**Usage**:
```
wildcard_directory: /wildcards/en/
text: A __colors__ car

vs

wildcard_directory: /wildcards/es/
text: Un coche __colors__
```

### Metadata Integration

```
[Wildcard Processor] -> processed_text ──┐
                                          ├─> [Metadata Viewer]
                     -> original_text ────┘
```

Store both original template and processed result.

## Performance Considerations

### Processing Speed

- **Token detection**: < 1ms (regex compiled once)
- **File reading**: 1-10ms per file (depends on size)
- **Replacement**: < 1ms per token
- **Total**: ~10-50ms for typical prompts

### Memory Usage

- **Cache**: ~1KB per cached entry
- **Max cache**: ~100KB at limit
- **Wildcard files**: Loaded on-demand, not kept in memory

### Optimization Tips

**Small Files**:
- Keep wildcard files under 1000 lines
- Large files slow down random selection

**Efficient Patterns**:
- Use specific tokens: `__color__` not `__c__`
- Avoid excessive nesting in directories

**Caching**:
- Leverage cache for repeated access
- Clear cache if memory constrained

## Troubleshooting

### Tokens Not Replaced

**Problem**: Wildcards remain as `__token__` in output

**Solutions**:
1. Check `enable_wildcards` is `True`
2. Verify file exists: `wildcard_directory/token.txt`
3. Check file has valid (non-comment, non-empty) lines
4. Ensure correct token format: `__token__` not `_token_`

### Same Value Repeated

**Problem**: Multiple tokens get same replacement

**Unlikely** due to duplicate prevention, but if it occurs:

**Solutions**:
1. Verify file has multiple distinct entries
2. Check if file has only one valid line
3. Use `force_refresh` for enhanced randomness

### Directory Not Found

**Problem**: All wildcards fail to load

**Solutions**:
```bash
# Verify directory exists
ls -la /llm/models/image/wildcards

# Check permissions
chmod 755 /llm/models/image/wildcards

# Use absolute path
wildcard_directory: /full/path/to/wildcards
```

### Encoding Errors

**Problem**: Special characters display incorrectly

**Solutions**:
1. Save wildcard files as UTF-8
2. Verify text editor encoding settings
3. Check console supports UTF-8 output

## Compatibility

- **ComfyUI**: Any version with STRING input support
- **Python**: 3.7+
- **File Encoding**: UTF-8 (recommended)
- **OS**: Windows, Linux, macOS
- **Path Format**: Supports both Unix (/) and Windows (\) paths

## Comparison with Other Solutions

| Feature | Wildcard Processor | Manual Prompts | Dynamic Prompts Extension |
|---------|-------------------|----------------|---------------------------|
| Variation | ✅ Automatic | ❌ Manual | ✅ Automatic |
| File-based | ✅ Yes | ❌ No | ✅ Yes |
| Duplicate Prevention | ✅ Yes | ⚠️ Manual | ⚠️ Varies |
| Caching | ✅ Built-in | ❌ No | ⚠️ Limited |
| Pass-through | ✅ Original + Processed | ✅ Text only | ⚠️ Varies |
| Enhanced Randomness | ✅ force_refresh | ❌ No | ⚠️ Varies |
| Integration | ✅ Native ComfyUI | ✅ Any | ⚠️ Extension-specific |

## FAQ

**Q: Can I use wildcards within wildcard files?**
A: The current implementation doesn't recursively process wildcards. Process the output again through another Wildcard Processor node for nested behavior.

**Q: How many wildcards can I use in one text?**
A: No hard limit, but performance degrades with many tokens (100+). Typical use (5-15 tokens) is very fast.

**Q: Can wildcard files contain multiple languages?**
A: Yes, UTF-8 encoding supports all Unicode characters. Organize by language in subdirectories.

**Q: What happens if I delete a wildcard file while ComfyUI is running?**
A: The token won't be replaced on next execution. File is read each time, not cached.

**Q: Can I use the same wildcard file for different purposes?**
A: Yes, wildcard files are reusable across any text using the same token name.

**Q: How do I share wildcard collections?**
A: Zip the wildcard directory and share. Users extract to their wildcard_directory path.

**Q: Does force_refresh slow down processing?**
A: Minimal impact (~1-2ms extra per token). The enhanced randomness is worth it for most use cases.

**Q: Can I use wildcards in negative prompts?**
A: Yes, process negative prompts through a separate Wildcard Processor node.

**Q: How do I debug which values are being selected?**
A: Check ComfyUI console for green log messages showing selected values.

**Q: Can I weight selections without repeating lines?**
A: Not directly. Repeat entries in the file for weighted selection, or create separate files with different distributions.
