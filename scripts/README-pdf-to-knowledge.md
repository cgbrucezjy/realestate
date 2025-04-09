# PDF to Knowledge Converter for KAG

This utility converts PDF documents to markdown files that can be used with the KAG (Knowledge Augmented Generation) system. It uses LlamaIndex to process PDFs, extract their content, and optionally upload them directly to your KAG server.

## Prerequisites

Before using this script, you need to install the required dependencies:

```bash
pip install llama-index-readers-file llama-index-core requests
```

## Usage

1. Place your PDF files in a `pdfs` folder (or specify another folder with `--pdf_folder`)
2. Run the script:

```bash
python pdf_to_knowledge.py
```

The script will:
1. Process all PDFs in the specified folder
2. Create markdown files in the `knowledge` folder (or specify another folder with `--output_folder`)
3. Optionally upload the files to your KAG server if `--upload` is specified

## Command Line Options

The script supports the following command line options:

```
--pdf_folder FOLDER    Folder containing PDF files (default: 'pdfs')
--output_folder FOLDER Output folder for markdown files (default: 'knowledge')
--upload               Upload processed files to KAG server
--kag_server URL       KAG server URL (default: 'http://localhost:11434')
--chunk_size SIZE      Chunk size for document splitting (default: 512)
--chunk_overlap SIZE   Chunk overlap for document splitting (default: 128)
```

## Examples

### Basic Usage

Process PDFs and save as markdown files:

```bash
python pdf_to_knowledge.py
```

### Specify Custom Folders

Process PDFs from `my_pdfs` and save to `my_knowledge`:

```bash
python pdf_to_knowledge.py --pdf_folder my_pdfs --output_folder my_knowledge
```

### Upload to KAG Server

Process PDFs and upload directly to the KAG server:

```bash
python pdf_to_knowledge.py --upload
```

### Custom Server URL

Process PDFs and upload to a custom KAG server:

```bash
python pdf_to_knowledge.py --upload --kag_server http://my-kag-server:8080
```

### Adjust Chunking Parameters

Change chunk size and overlap for better document splitting:

```bash
python pdf_to_knowledge.py --chunk_size 1024 --chunk_overlap 256
```

## Integration with KAG

The markdown files created by this script are formatted to work with the KAG system. When you use the `--upload` option, the script will:

1. Connect to your KAG server
2. Upload each markdown file as a document
3. The KAG system will process these documents and make them available for querying

Once uploaded, you can use these documents in your OpenWebUI conversations by selecting them when creating a new chat or via the document selection interface.

## Troubleshooting

If you encounter issues:

1. Ensure your PDF files are readable and not password-protected
2. Check that the KAG server is running if using the upload option
3. Adjust chunk sizes if your documents have complex structures
4. Look at the console output for detailed error messages 