# Basify Custom Nodes for ComfyUI

A comprehensive collection of custom nodes for ComfyUI providing workflow automation, AI integration, computer vision, and utility functionality to enhance your image generation pipelines.

## 🎯 Overview

Basify extends ComfyUI with powerful nodes for:
- **Automated Workflows**: Batch processing and directory iteration
- **AI Integration**: LLM-powered image description with Ollama
- **Smart Loading**: Intelligent checkpoint scanning with symbolic link support
- **Dynamic Content**: Wildcard-based text variation
- **Workflow Management**: Metadata extraction and organization
- **Image Generation**: Enhanced latent generators with preset resolutions
- **Output Management**: Advanced image saving with flexible naming and metadata embedding

## 📦 Nodes

### 🔄 Workflow Automation

#### **Directory Auto Iterator**
Automatically processes all images in a directory, one per workflow execution.

**Key Features**:
- State persistence across runs
- Recursive subdirectory scanning
- Progress tracking and completion detection
- Handles missing/corrupted files gracefully

**Use Cases**: Batch processing, automated captioning, dataset generation

📖 [**Full Documentation**](py/docs/DIRECTORY_AUTO_ITERATOR_README.md)

---

#### **Directory Checkpoint Scanner**
Scans directories for model checkpoints with advanced filtering and selection memory.

**Key Features**:
- Recursive scanning with subdirectory organization
- Symbolic link support and deduplication
- Remembers last selection per directory
- Shows relative paths with folder structure

**Use Cases**: Model organization, quick model switching, workflow templates

📖 [**Full Documentation**](py/docs/DIRECTORY_CHECKPOINT_SCANNER_README.md)

---

### 🤖 AI & LLM Integration

#### **Describe Image (LLM)**
Uses Ollama vision models to generate detailed descriptions of images.

**Key Features**:
- Local processing with Ollama (privacy-friendly)
- Supports LLaVA, Llama 3.2 Vision, and other vision models
- Configurable temperature and token limits
- Automatic model memory management

**Use Cases**: Automated captioning, image analysis, metadata generation, prompt enhancement

📖 [**Full Documentation**](py/docs/LLM_DESCRIBE_README.md)

**Prerequisites**: Requires [Ollama](https://ollama.ai) with a vision model installed

---

### 🎨 Image Generation

#### **Latent Generator**
Enhanced empty latent generator with predefined resolutions and aspect ratios.

**Key Features**:
- 25+ predefined resolutions organized by aspect ratio
- Manual dimension input with validation
- Batch support for multiple variations
- Outputs dimensions for downstream use

**Aspect Ratios**: 1:1, 16:9, 9:16, 3:4, 4:3, 2:3, 3:2, Golden Ratio

**Use Cases**: Quick setup, social media formats, consistent sizing

📖 [**Full Documentation**](py/docs/LATENT_GENERATOR_README.md)

---

### 🔧 Utilities

#### **Wildcard Processor**
Dynamic text generation using file-based wildcard tokens.

**Key Features**:
- Token replacement from text files (`__token__` → random value)
- All-contents mode (`__*token__` → all values)
- Unique selection prevents duplicates within text
- Enhanced randomness with force_refresh
- Global caching for multi-node access
- Nested directory support

**Use Cases**: Dynamic prompts, variation generation, template systems

📖 [**Full Documentation**](py/docs/WILDCARD_PROCESSOR_README.md)

**Examples**:
```
Standard: "A __color__ __animal__ in __location__"
Output:   "A blue cat in ancient forest"

All-Contents: "Available colors: __*color__"
Output:       "Available colors: red
              blue
              green"
```

---

#### **Metadata Viewer**
Extracts and structures workflow metadata from ComfyUI images.

**Key Features**:
- Parses workflow data into clean JSON
- Filters and organizes node information
- Excludes display-only nodes
- Preserves execution order

**Use Cases**: Workflow documentation, version control, parameter tracking, A/B testing

📖 [**Full Documentation**](py/docs/METADATA_VIEWER_README.md)

---

#### **Display Anything as Text**
Universal debugging and inspection tool that displays any input value as human-readable text.

**Key Features**:
- Accepts any input type (`*` wildcard)
- Intelligent type conversion with detailed formatting
- Tensor statistics (shape, dtype, min/max/mean/std)
- JSON formatting for collections
- Passthrough design for inline debugging
- 50,000 character limit with truncation

**Supported Types**: Primitives, strings, dicts, lists, tuples, PyTorch tensors, NumPy arrays, custom objects

**Use Cases**: Workflow debugging, data inspection, type verification, tensor analysis

📖 [**Full Documentation**](py/docs/DISPLAY_ANYTHING_README.md)

**Example**:
```
Input:  torch.randn(3, 512, 512)
Display: 
  PyTorch Tensor
    Shape: (3, 512, 512)
    Dtype: torch.float32
    Min: -3.924561
    Max: 4.127832
    Mean: 0.001234
```

---

#### **Batch Append**
Flexible batch accumulation and item appending for building dynamic batches during workflow execution.

**Key Features**:
- Internal accumulating collection when batch input not connected
- Appends to external batches when connected
- Supports any data type (images, latents, tensors, lists, etc.)
- Smart type detection and automatic collection creation
- Type change detection with automatic reset
- Tensor concatenation along batch dimension
- Stateful operation across executions

**Behavior Modes**:
- **Accumulation Mode**: Build persistent batch when input not connected
- **New Collection Mode**: Create fresh collection from None input
- **Append Mode**: Add item to provided batch

**Use Cases**: Dynamic batch building, image collection, latent accumulation, iterative workflows, queue processing

📖 [**Full Documentation**](py/docs/BATCH_APPEND_README.md)

---

#### **Sound Notifier**
Plays audio notifications when workflows complete execution.

**Key Features**:
- Supports WAV, MP3, and OGG formats
- Configurable volume control
- Enable/disable toggle
- Optional trigger input for workflow chaining
- Non-blocking execution

**Use Cases**: Long-running workflow alerts, batch processing completion, monitoring multiple workflows

📖 [**Full Documentation**](py/docs/SOUND_NOTIFIER_README.md)

---

#### **Save Image (Enhanced)**
Advanced image saving with flexible naming, metadata embedding, and wildcard integration.

**Key Features**:
- Custom filename templates with variable substitution (`{date}`, `{counter}`, `{prompt}`, etc.)
- Automatic counter management with persistent state
- Metadata embedding in PNG chunks
- Wildcard processor integration for dynamic filenames
- Subfolder organization support
- High-quality JPEG/PNG output with configurable compression

**Variables Supported**:
- `{date}` - Current date (YYYY-MM-DD)
- `{time}` - Current time (HHMMSS)
- `{counter}` - Auto-incrementing number
- `{prompt}` - Processed prompt text
- `{seed}` - Generation seed value
- `{width}` x `{height}` - Image dimensions
- And more...

**Use Cases**: Organized output management, automated naming, batch processing, metadata preservation

📖 [**Full Documentation**](py/docs/SAVE_IMAGE_README.md)

**Example**:
```
Filename: "{date}_{counter}_{prompt}"
Output:   "2025-12-28_0042_beautiful-landscape.png"
```

---

## 🚀 Installation

### Method 1: Git Clone (Recommended)

```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/yourusername/basify.git
cd basify
pip install -r requirements.txt
```

### Method 2: Conda Environment

```bash
cd ComfyUI/custom_nodes/basify
conda env create -f environment.yml
conda activate basify_env
```

### Dependencies

**System Requirements**:
- Python 3.11 (or compatible version)
- pip package manager

**Required Python Packages**:
- `numpy>=1.21.0` - Image processing and array operations
- `pillow>=9.0.0` - Image loading and manipulation (PIL)
- `requests>=2.25.0` - HTTP requests for LLM Describe Image node

**Provided by ComfyUI** (do not install separately):
- `torch` - PyTorch for tensor operations
- `comfy` - ComfyUI's internal modules
- `folder_paths` - ComfyUI path management

**Note**: All dependencies are listed in `requirements.txt` for pip installation or `environment.yml` for conda.

---

## 📖 Quick Start

### Basic Workflow Examples

#### Automated Batch Processing
```
[Directory Auto Iterator] → [Processing Nodes] → [Save Image]
         ↓
    [status] → [Display]
    [completed] → [Conditional Logic]
```

#### Dynamic Prompt Generation
```
[Wildcard Processor] → processed_text → [CLIP Text Encode] → [KSampler]
      ↓
  "A __color__ __subject__"
      ↓
  "A vibrant red dragon"
```

#### AI-Powered Captioning
```
[Load Image] → [Describe Image] → description → [Save Text]
                      ↓
              (Uses Ollama LLaVA)
```

#### Smart Model Management
```
[Directory Checkpoint Scanner] → model → [KSampler]
                                → clip → [CLIP Text Encode]
                                → vae → [VAE Decode]
```

---

## 🗂️ Project Structure

```
basify/
├── __init__.py                          # Node registration
├── README.md                            # This file
├── requirements.txt                     # Pip dependencies
├── environment.yml                      # Conda environment
├── js/                                  # Frontend JavaScript
│   ├── directory_checkpoint_scanner.js
│   ├── latent_generator.js
│   ├── metadata_viewer.js
│   └── save_image.js
└── py/                                  # Python nodes
    ├── batch_append.py
    ├── directory_auto_iterator.py
    ├── directory_checkpoint_scanner.py
    ├── latent_generator.py
    ├── llm_describe.py
    ├── metadata_viewer.py
    ├── save_image.py
    ├── wildcard_processor.py
    ├── wildcard_handler.py
    ├── routes.py
    │
    └── docs/                            # Documentation
        ├── BATCH_APPEND_README.md
        ├── DIRECTORY_AUTO_ITERATOR_README.md
        ├── DIRECTORY_CHECKPOINT_SCANNER_README.md
        ├── LATENT_GENERATOR_README.md
        ├── LLM_DESCRIBE_README.md
        ├── METADATA_VIEWER_README.md
        ├── SAVE_IMAGE_README.md
        └── WILDCARD_PROCESSOR_README.md
```

---

## 💡 Use Case Examples

### Dataset Generation Pipeline
```
[Directory Iterator] → [Describe Image] → [Save with Caption]
```
Automatically generate captions for all images in a folder.

### Dynamic Content Creation
```
[Wildcard Processor] → [Multiple Variations] → [Batch Generate]
```
Create dozens of unique prompts from templates.

### Model Testing & Comparison
```
[Checkpoint Scanner A] ─┐
[Checkpoint Scanner B] ─┼→ [Same Prompt] → [Compare Results]
[Checkpoint Scanner C] ─┘
```
Test multiple models with identical prompts.

### Workflow Documentation
```
[Metadata Viewer] → [Export JSON] → Version Control
```
Track workflow configurations over time.

---

## 🔧 Configuration

### Wildcard Directory Setup

Create a wildcards folder structure:
```
wildcards/
├── colors.txt
├── animals.txt
├── styles/
│   ├── artistic.txt
│   └── photographic.txt
└── locations/
    ├── indoor.txt
    └── outdoor.txt
```

Default path: `/llm/models/image/wildcards`

### Ollama Setup (for LLM Describe)

```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Pull a vision model
ollama pull llava:latest

# Verify
ollama list
```

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add documentation for new nodes
4. Submit a pull request

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🐛 Troubleshooting

### Common Issues

**Nodes not appearing in ComfyUI**:
- Ensure dependencies are installed: `pip install -r requirements.txt`
- Restart ComfyUI completely
- Check console for import errors

**Directory Auto Iterator not processing**:
- Verify directory path is correct and exists
- Check file permissions
- Ensure images have supported extensions

**LLM Describe not working**:
- Confirm Ollama is running: `ollama serve`
- Verify vision model is installed: `ollama list`
- Check server URL matches Ollama endpoint

**Wildcards not replacing**:
- Ensure wildcard files exist in specified directory
- Check file encoding is UTF-8
- Verify token format: `__token__` (double underscores)

**Checkpoint Scanner empty**:
- Verify directory contains checkpoint files (.safetensors, .ckpt, .pt)
- Check directory permissions
- Ensure path is correct (absolute or relative to ComfyUI root)

---

## 📚 Additional Resources

### Documentation
Each node has comprehensive documentation covering:
- Detailed feature descriptions
- Parameter explanations
- Usage examples
- Best practices
- Troubleshooting guides
- FAQ sections

### ComfyUI Resources
- [ComfyUI GitHub](https://github.com/comfyanonymous/ComfyUI)
- [ComfyUI Wiki](https://github.com/comfyanonymous/ComfyUI/wiki)
- [LiteGraph.js Documentation](https://github.com/jagenjo/litegraph.js)

### External Tools
- [Ollama](https://ollama.ai) - Local LLM server

---

## 🙏 Acknowledgments

- ComfyUI team for the excellent framework
- Ollama team for local LLM capabilities
- Community contributors and testers

---

## 📧 Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Check existing documentation
- Review troubleshooting section

---

**Made with ❤️ for the ComfyUI community**

