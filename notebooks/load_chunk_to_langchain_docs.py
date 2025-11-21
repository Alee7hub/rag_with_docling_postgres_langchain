"""
Professional Document Processing and Chunking Pipeline with Docling
Handles text documents (PDF, DOCX, MD, HTML, TXT) and audio files (MP3, WAV, M4A, FLAC)
Converts to markdown → chunks → returns LangChain Document objects
"""

from pathlib import Path
from typing import List, Optional, Union
from dataclasses import dataclass
from enum import Enum

from docling.document_converter import DocumentConverter, AudioFormatOption
from docling.datamodel.pipeline_options import AsrPipelineOptions
from docling.datamodel import asr_model_specs
from docling.datamodel.base_models import InputFormat
from docling.pipeline.asr_pipeline import AsrPipeline
from docling.chunking import HybridChunker
from langchain_core.documents import Document
from transformers import AutoTokenizer


class DocumentType(Enum):
    """Supported document types"""
    TEXT = "text"
    AUDIO = "audio"


@dataclass
class ConversionResult:
    """Result of document conversion"""
    filename: str
    file_format: str
    success: bool
    docling_document: Optional[object] = None
    error_message: Optional[str] = None


class UnifiedDocumentProcessor:
    """
    Unified processor for text and audio documents with chunking support.
    
    Converts documents to markdown (in-memory) and chunks them using HybridChunker.
    Returns LangChain Document objects ready for vector store ingestion.
    
    Attributes:
        max_tokens: Maximum tokens per chunk
        tokenizer_model: Model ID for the tokenizer
        audio_extensions: Set of supported audio file extensions
    """
    
    AUDIO_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.flac'}
    
    def __init__(self, max_tokens: int = 512, tokenizer_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize the unified document processor.
        
        Args:
            max_tokens: Maximum tokens per chunk
            tokenizer_model: Model ID for tokenization
        """
        self.max_tokens = max_tokens
        self.tokenizer_model = tokenizer_model
        
        # Lazy initialization
        self._text_converter: Optional[DocumentConverter] = None
        self._audio_converter: Optional[DocumentConverter] = None
        self._tokenizer: Optional[AutoTokenizer] = None
        self._chunker: Optional[HybridChunker] = None
    
    @property
    def text_converter(self) -> DocumentConverter:
        """Lazy-load text document converter"""
        if self._text_converter is None:
            self._text_converter = DocumentConverter()
        return self._text_converter
    
    @property
    def audio_converter(self) -> DocumentConverter:
        """Lazy-load audio document converter with Whisper ASR"""
        if self._audio_converter is None:
            pipeline_options = AsrPipelineOptions()
            pipeline_options.asr_options = asr_model_specs.WHISPER_TURBO
            
            self._audio_converter = DocumentConverter(
                format_options={
                    InputFormat.AUDIO: AudioFormatOption(
                        pipeline_cls=AsrPipeline,
                        pipeline_options=pipeline_options,
                    )
                }
            )
        return self._audio_converter
    
    @property
    def tokenizer(self) -> AutoTokenizer:
        """Lazy-load tokenizer"""
        if self._tokenizer is None:
            print(f"Initializing tokenizer ({self.tokenizer_model})...")
            self._tokenizer = AutoTokenizer.from_pretrained(self.tokenizer_model)
        return self._tokenizer
    
    @property
    def chunker(self) -> HybridChunker:
        """Lazy-load chunker"""
        if self._chunker is None:
            self._chunker = HybridChunker(
                tokenizer=self.tokenizer,
                max_tokens=self.max_tokens,
                merge_peers=True
            )
        return self._chunker
    
    def _classify_document(self, file_path: Path) -> DocumentType:
        """Determine document type based on file extension"""
        return DocumentType.AUDIO if file_path.suffix.lower() in self.AUDIO_EXTENSIONS else DocumentType.TEXT
    
    def _convert_document(self, file_path: Path) -> ConversionResult:
        """
        Convert a document to Docling document object (in-memory).
        Handles both text and audio files automatically.
        
        Args:
            file_path: Path to the document
            
        Returns:
            ConversionResult with docling document or error
        """
        doc_type = self._classify_document(file_path)
        doc_type_icon = "🎙️" if doc_type == DocumentType.AUDIO else "📄"
        
        print(f"\n{doc_type_icon} Processing: {file_path.name}")
        
        try:
            # Select appropriate converter
            if doc_type == DocumentType.AUDIO:
                print("   Converting audio to text (Whisper ASR)...")
                converter = self.audio_converter
            else:
                print("   Converting document to markdown...")
                converter = self.text_converter
            
            # Convert to Docling document
            result = converter.convert(file_path.resolve())
            docling_doc = result.document
            
            print(f"   ✓ Conversion successful")
            
            return ConversionResult(
                filename=file_path.name,
                file_format=file_path.suffix,
                success=True,
                docling_document=docling_doc
            )
            
        except FileNotFoundError as e:
            error_msg = "FFmpeg not found (required for audio files)" if doc_type == DocumentType.AUDIO else str(e)
            print(f"   ✗ Error: {error_msg}")
            return ConversionResult(
                filename=file_path.name,
                file_format=file_path.suffix,
                success=False,
                error_message=error_msg
            )
            
        except Exception as e:
            print(f"   ✗ Error: {e}")
            return ConversionResult(
                filename=file_path.name,
                file_format=file_path.suffix,
                success=False,
                error_message=str(e)
            )
    
    def _chunk_document(self, docling_doc: object, source_path: Path) -> List[Document]:
        """
        Chunk a Docling document and convert to LangChain Documents.
        
        Args:
            docling_doc: Docling document object
            source_path: Original file path for metadata
            
        Returns:
            List of LangChain Document objects with chunks
        """
        print("   Generating chunks...")
        
        # Generate chunks
        chunk_iter = self.chunker.chunk(dl_doc=docling_doc)
        chunks = list(chunk_iter)
        
        print(f"   Creating {len(chunks)} LangChain Document objects...")
        
        langchain_docs = []
        for i, chunk in enumerate(chunks):
            # Contextualize chunk (preserves headings and metadata)
            contextualized_text = self.chunker.contextualize(chunk=chunk)
            
            # Create LangChain Document
            langchain_doc = Document(
                page_content=contextualized_text,
                metadata={
                    "source": str(source_path),
                    "source_name": source_path.name,
                    "document_chunk_index": i,
                    "total_chunks_in_document": len(chunks),
                    "file_format": source_path.suffix
                }
            )
            
            langchain_docs.append(langchain_doc)
        
        return langchain_docs
    
    def process_directory(self, documents_dir: Union[str, Path], 
                         recursive: bool = False) -> List[Document]:
        """
        Process all documents in a directory: convert → chunk → return LangChain Documents.
        
        Handles both text documents (PDF, DOCX, MD, HTML, TXT) and 
        audio files (MP3, WAV, M4A, FLAC) automatically.
        
        Args:
            documents_dir: Directory containing documents to process
            recursive: Whether to search subdirectories recursively
            
        Returns:
            List of LangChain Document objects (all chunks from all documents)
        """
        documents_path = Path(documents_dir)
        
        print("=" * 70)
        print("UNIFIED DOCUMENT PROCESSING & CHUNKING")
        print("=" * 70)
        print(f"\nInput directory: {documents_path}")
        print(f"Max tokens per chunk: {self.max_tokens}")
        print(f"Recursive: {recursive}\n")
        
        # Gather files
        if recursive:
            all_files = [f for f in documents_path.rglob('*') if f.is_file()]
        else:
            all_files = [f for f in documents_path.iterdir() if f.is_file()]
        
        all_files = sorted(all_files)  # Sort for consistent ordering
        
        if not all_files:
            print(f"\n✗ No files found in {documents_path}")
            return []
        
        print(f"Found {len(all_files)} file(s) to process\n")
        
        # Process all documents
        all_langchain_documents = []
        successful_docs = 0
        failed_docs = []
        
        for file_path in all_files:
            # Step 1: Convert to Docling document
            conversion_result = self._convert_document(file_path)
            
            if not conversion_result.success:
                failed_docs.append((file_path.name, conversion_result.error_message))
                continue
            
            # Step 2: Chunk the document
            try:
                chunks = self._chunk_document(
                    docling_doc=conversion_result.docling_document,
                    source_path=file_path
                )
                
                all_langchain_documents.extend(chunks)
                successful_docs += 1
                print(f"   ✓ Success! {len(chunks)} chunks created")
                
            except Exception as e:
                print(f"   ✗ Chunking error: {e}")
                failed_docs.append((file_path.name, f"Chunking failed: {str(e)}"))
        
        # Print summary
        self._print_summary(all_files, successful_docs, failed_docs, all_langchain_documents)
        
        return all_langchain_documents
    
    def _print_summary(self, all_files: List[Path], successful_docs: int, 
                      failed_docs: List[tuple], langchain_documents: List[Document]) -> None:
        """Print processing summary"""
        print("\n" + "=" * 70)
        print("PROCESSING COMPLETE")
        print("=" * 70)
        print(f"✓ Successfully processed: {successful_docs}/{len(all_files)} documents")
        print(f"✓ Total LangChain Documents (chunks): {len(langchain_documents)}")
        
        if failed_docs:
            print(f"\n✗ Failed documents ({len(failed_docs)}):")
            for filename, error in failed_docs:
                print(f"   - {filename}: {error}")
        
        print("\n" + "=" * 70)
        print("LANGCHAIN DOCUMENTS READY")
        print("=" * 70)
        print("✓ All documents converted to markdown (in-memory)")
        print("✓ All chunks are LangChain Document objects")
        print("✓ Each chunk has contextualized text with headings")
        print("✓ Metadata: source, source_name, chunk_index, file_format")
        print("✓ Ready for vector store ingestion")


def process_documents_to_langchain(documents_dir: str, max_tokens: int = 512, 
                                   recursive: bool = False) -> List[Document]:
    """
    Convenience function: Process documents from directory and return chunked LangChain Documents.
    
    Supports both text documents (PDF, DOCX, MD, HTML, TXT) and 
    audio files (MP3, WAV, M4A, FLAC).
    
    Args:
        documents_dir: Directory containing documents to process
        max_tokens: Maximum tokens per chunk
        recursive: Whether to search subdirectories recursively
        
    Returns:
        List of LangChain Document objects with page_content and metadata
    """
    processor = UnifiedDocumentProcessor(max_tokens=max_tokens)
    return processor.process_directory(documents_dir, recursive=recursive)