#!/bin/bash
# Script to convert PDFs to knowledge markdown for KAG system

set -e

echo "==== PDF to Knowledge Converter for KAG ===="

# Check for python
if ! command -v python &> /dev/null; then
    echo "Python is not installed. Please install Python first."
    exit 1
fi

# Check for conda environment
if [ -n "$CONDA_DEFAULT_ENV" ]; then
    echo "Using conda environment: $CONDA_DEFAULT_ENV"
else
    # Check if kag environment exists and activate it
    if conda env list | grep -q "kag"; then
        echo "Activating kag conda environment..."
        source "$(conda info --base)/etc/profile.d/conda.sh"
        conda activate kag
    fi
fi

# Check for required packages
echo "Checking required packages..."
python -c "import importlib.util; \
  packages=['llama_index', 'requests']; \
  missing=[p for p in packages if importlib.util.find_spec(p) is None]; \
  exit(1 if missing else 0)" || {
    echo "Installing required packages..."
    pip install llama-index-readers-file llama-index-core requests
}

# Create folders if they don't exist
mkdir -p pdfs
mkdir -p knowledge

# Check if PDFs exist
if [ -z "$(ls -A pdfs 2>/dev/null)" ]; then
    echo "No PDF files found in pdfs folder. Please add PDF files to convert."
    exit 1
fi

# Process command line args
PDF_FOLDER="pdfs"
OUTPUT_FOLDER="knowledge"
UPLOAD_FLAG=""
KAG_SERVER="http://localhost:11434"
CHUNK_SIZE=512
CHUNK_OVERLAP=128

while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --pdf_folder)
        PDF_FOLDER="$2"
        shift
        shift
        ;;
        --output_folder)
        OUTPUT_FOLDER="$2"
        shift
        shift
        ;;
        --upload)
        UPLOAD_FLAG="--upload"
        shift
        ;;
        --kag_server)
        KAG_SERVER="$2"
        shift
        shift
        ;;
        --chunk_size)
        CHUNK_SIZE="$2"
        shift
        shift
        ;;
        --chunk_overlap)
        CHUNK_OVERLAP="$2"
        shift
        shift
        ;;
        *)
        echo "Unknown option: $1"
        shift
        ;;
    esac
done

# Run the converter script
echo "Starting PDF conversion process..."
echo "PDF folder: $PDF_FOLDER"
echo "Output folder: $OUTPUT_FOLDER"
if [ -n "$UPLOAD_FLAG" ]; then
    echo "Will upload to KAG server: $KAG_SERVER"
fi

# Run the Python script
python "$(dirname "$0")/pdf_to_knowledge.py" \
    --pdf_folder "$PDF_FOLDER" \
    --output_folder "$OUTPUT_FOLDER" \
    $UPLOAD_FLAG \
    --kag_server "$KAG_SERVER" \
    --chunk_size "$CHUNK_SIZE" \
    --chunk_overlap "$CHUNK_OVERLAP"

echo "==== PDF Conversion Complete ===="

# Check if files were created
FILE_COUNT=$(ls -1 "$OUTPUT_FOLDER"/*.md 2>/dev/null | wc -l)
if [ "$FILE_COUNT" -gt 0 ]; then
    echo "Successfully created $FILE_COUNT markdown files in $OUTPUT_FOLDER folder."
    
    # Provide a summary of what to do next
    if [ -z "$UPLOAD_FLAG" ]; then
        echo ""
        echo "To upload these files to KAG server, run:"
        echo "  $0 --upload"
        echo ""
        echo "Or manually upload them using the KAG web interface."
    fi
else
    echo "Warning: No markdown files were created. Check the logs for errors."
fi 