# KAG System Troubleshooting Guide

This document provides solutions for common issues you might encounter when setting up and running the KAG system.

## Installation Issues

### Conda Environment Problems

**Issue**: Error creating or activating the conda environment.

**Solution**:
1. Ensure you have conda installed correctly. Run `conda --version` to verify.
2. Try creating the environment manually:
   ```bash
   conda create -n kag python=3.10 -y
   conda activate kag
   ```
3. Install dependencies manually by copying commands from conda.txt.

### CUDA/GPU Issues

**Issue**: CUDA not found or GPU acceleration not working.

**Solution**:
1. Verify CUDA installation with `nvcc --version` and `nvidia-smi`.
2. Ensure you have compatible CUDA drivers for your GPUs.
3. Check that your PyTorch installation includes CUDA support:
   ```python
   import torch
   print(torch.cuda.is_available())
   print(torch.cuda.device_count())
   ```
4. For H100 GPUs, ensure you're using CUDA 12.x.

### Model Loading Failures

**Issue**: Error loading the Qwen2-30B model.

**Solution**:
1. Verify the model is downloaded correctly in the `./qwq` directory.
2. Ensure all model files are present by comparing with the official repository.
3. Try downloading the model again using:
   ```bash
   huggingface-cli download Qwen/Qwen2-30B --local-dir ./qwq
   ```
4. Check if you have enough GPU memory for the model.

## Runtime Issues

### KV Cache Management

**Issue**: Errors related to KV cache management.

**Solution**:
1. Check if you have sufficient GPU memory. Try lowering the `--gpu-memory-utilization` value.
2. Reduce the document chunk size in the configuration (settings.chunk_size).
3. Monitor GPU memory usage with `nvidia-smi` during operation.
4. Check the logs for specific error messages related to KV cache.

### Database Errors

**Issue**: Problems with document storage or retrieval.

**Solution**:
1. Check if the database file exists and has the correct permissions.
2. Try deleting the database file (kag.db) and let the system recreate it.
3. Ensure your SQLite version is 3.24.0 or newer.
4. Check disk space if you're storing many documents.

### API Connection Issues

**Issue**: Cannot connect to the KAG API.

**Solution**:
1. Verify the server is running with `curl http://localhost:11434/health`.
2. Check firewall settings if connecting from another machine.
3. Ensure the `--host` and `--port` arguments are set correctly.
4. Check the server logs for binding errors.

## Frontend Integration Issues

### OpenWebUI Connection

**Issue**: OpenWebUI cannot connect to KAG server.

**Solution**:
1. Verify the KAG server is running and accessible.
2. Check that you've configured the OpenWebUI API settings correctly:
   - API URL: `http://your_server_ip:11434/v1`
   - API Key: as configured in your setup
3. If running in Docker, ensure network connectivity between containers.
4. Check OpenWebUI logs for specific error messages.

### Authentication Issues

**Issue**: Problems with user authentication.

**Solution**:
1. Verify your JWT secret is set correctly in the .env file.
2. Check if the database has the user tables created correctly.
3. If using external auth providers, verify your configuration.
4. Reset user password if necessary.

## Document Processing Issues

### Document Upload Failures

**Issue**: Cannot upload documents or errors during processing.

**Solution**:
1. Check the file format is supported (PDF, DOCX, TXT, etc.).
2. Verify the document isn't corrupted by opening it normally.
3. Check for encoding issues, especially with non-UTF8 text.
4. Try converting the document to another format before uploading.
5. Check server logs for specific processing errors.

### Memory Issues with Large Documents

**Issue**: Out of memory when processing large documents.

**Solution**:
1. Reduce the chunk size in settings (settings.chunk_size).
2. Split very large documents before uploading.
3. Increase available RAM if possible.
4. Configure document processing to use disk for temporary storage.

## Performance Tuning

### Slow Response Times

**Issue**: Responses are too slow.

**Solution**:
1. Verify you're using sufficient GPU resources (2x H100 recommended).
2. Adjust `--tensor-parallel-size` to match your GPU count.
3. Optimize document chunking - smaller chunks can be more efficient.
4. Monitor and tune the KV cache settings for your specific workload.
5. Consider scaling horizontally with multiple KAG instances for more users.

### High Memory Usage

**Issue**: System using too much memory.

**Solution**:
1. Reduce `--gpu-memory-utilization` to a lower value (e.g., 0.6).
2. Configure session timeout to clean up unused sessions more quickly.
3. Implement a cache eviction policy for less frequently used documents.
4. Monitor memory usage patterns to identify optimization opportunities.

## Contact Support

If you continue to experience issues after trying these solutions, please:

1. Check the full logs using `KAG_LOG_LEVEL=DEBUG` for more detailed information.
2. Visit our GitHub repository for the latest updates and community support.
3. Include relevant logs and system information when reporting issues. 