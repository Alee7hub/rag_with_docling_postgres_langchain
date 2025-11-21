"""
Professional Document Processing Pipeline with Docling
Handles text documents (PDF, DOCX, MD) and audio files (MP3, WAV, M4A, FLAC)
"""

from pathlib import Path
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

from docling.document_converter import DocumentConverter, AudioFormatOption
from docling.datamodel.pipeline_options import AsrPipelineOptions
from docling.datamodel import asr_model_specs
from docling.datamodel.base_models import InputFormat
from docling.pipeline.asr_pipeline import AsrPipeline


class DocumentType(Enum):
    """Supported document types"""
    TEXT = "text"
    AUDIO = "audio"


@dataclass
class ProcessingResult:
    """Result metadata for document processing"""
    filename: str
    file_format: str
    status: str
    output_path: Optional[str] = None
    content_length: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    
    @property
    def success(self) -> bool:
        return self.status == "Success"


class DocumentProcessor:
    """
    Unified document processor for text and audio files using Docling.
    
    Attributes:
        output_dir: Directory where processed markdown files will be saved
        audio_extensions: Set of supported audio file extensions
        text_converter: Lazy-loaded text document converter
        audio_converter: Lazy-loaded audio document converter
    """
    
    AUDIO_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.flac'}
    
    def __init__(self, output_dir: Union[str, Path]):
        """
        Initialize the document processor.
        
        Args:
            output_dir: Directory path for saving processed documents
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Lazy initialization of converters
        self._text_converter: Optional[DocumentConverter] = None
        self._audio_converter: Optional[DocumentConverter] = None
    
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
    
    def _classify_document(self, file_path: Path) -> DocumentType:
        """Determine document type based on file extension"""
        return DocumentType.AUDIO if file_path.suffix.lower() in self.AUDIO_EXTENSIONS else DocumentType.TEXT
    
    def _process_text_document(self, file_path: Path) -> ProcessingResult:
        """
        Process text-based documents (PDF, DOCX, MD, etc.)
        
        Args:
            file_path: Path to the document file
            
        Returns:
            ProcessingResult with processing metadata
        """
        print(f"\n📄 Processing: {file_path.name}")
        
        try:
            # Convert document
            result = self.text_converter.convert(str(file_path))
            markdown = result.document.export_to_markdown()
            
            # Save output
            output_path = self.output_dir / f"{file_path.stem}.md"
            output_path.write_text(markdown, encoding='utf-8')
            
            print(f"   ✓ Converted successfully")
            print(f"   ✓ Output: {output_path}")
            
            return ProcessingResult(
                filename=file_path.name,
                file_format=file_path.suffix,
                status="Success",
                output_path=str(output_path),
                content_length=len(markdown)
            )
            
        except Exception as e:
            print(f"   ✗ Error: {e}")
            return ProcessingResult(
                filename=file_path.name,
                file_format=file_path.suffix,
                status="Failed",
                error_message=str(e)
            )
    
    def _process_audio_document(self, file_path: Path) -> ProcessingResult:
        """
        Process audio files with Whisper ASR transcription
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            ProcessingResult with transcription metadata
        """
        print(f"\n🎙️  Transcribing: {file_path.name}")
        print("   This may take a moment on first run (downloading Whisper model)...")
        
        try:
            # Transcribe audio
            result = self.audio_converter.convert(file_path.resolve())
            transcript = result.document.export_to_markdown()
            
            # Save output
            output_path = self.output_dir / f"{file_path.stem}.md"
            output_path.write_text(transcript, encoding='utf-8')
            
            # Extract timestamp metadata
            lines = transcript.split('\n')
            timestamp_lines = [line for line in lines if '[time:' in line]
            
            print(f"   ✓ Transcribed successfully")
            print(f"   ✓ Output: {output_path}")
            print(f"   ✓ Total length: {len(transcript)} characters")
            if timestamp_lines:
                print(f"   ✓ Found {len(timestamp_lines)} timestamped segments")
            
            return ProcessingResult(
                filename=file_path.name,
                file_format=file_path.suffix,
                status="Success",
                output_path=str(output_path),
                content_length=len(transcript),
                metadata={"timestamp_segments": len(timestamp_lines)}
            )
            
        except FileNotFoundError:
            error_msg = "FFmpeg not found. Please install FFmpeg and ensure it's in PATH."
            print(f"   ✗ Error: {error_msg}")
            return ProcessingResult(
                filename=file_path.name,
                file_format=file_path.suffix,
                status="Failed",
                error_message=error_msg
            )
            
        except Exception as e:
            print(f"   ✗ Error: {e}")
            return ProcessingResult(
                filename=file_path.name,
                file_format=file_path.suffix,
                status="Failed",
                error_message=str(e)
            )
    
    def process_document(self, file_path: Union[str, Path]) -> ProcessingResult:
        """
        Process a single document (auto-detects type)
        
        Args:
            file_path: Path to the document file
            
        Returns:
            ProcessingResult with processing metadata
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return ProcessingResult(
                filename=file_path.name,
                file_format=file_path.suffix,
                status="Failed",
                error_message="File not found"
            )
        
        doc_type = self._classify_document(file_path)
        
        if doc_type == DocumentType.AUDIO:
            return self._process_audio_document(file_path)
        else:
            return self._process_text_document(file_path)
    
    def process_directory(self, input_dir: Union[str, Path], 
                         recursive: bool = False) -> List[ProcessingResult]:
        """
        Process all documents in a directory
        
        Args:
            input_dir: Directory containing documents to process
            recursive: Whether to search subdirectories recursively
            
        Returns:
            List of ProcessingResult for all processed documents
        """
        input_dir = Path(input_dir)
        
        print("=" * 70)
        print("Multi-Format Document Processing with Docling")
        print("=" * 70)
        print(f"\nInput directory: {input_dir}")
        print(f"Output directory: {self.output_dir}")
        print(f"Recursive: {recursive}\n")
        
        # Gather files
        if recursive:
            files = [f for f in input_dir.rglob('*') if f.is_file()]
        else:
            files = [f for f in input_dir.iterdir() if f.is_file()]
        
        print(f"Found {len(files)} file(s) to process")
        
        # Process all documents
        results = [self.process_document(file_path) for file_path in files]
        
        # Print summary
        self._print_summary(results)
        
        return results
    
    def _print_summary(self, results: List[ProcessingResult]) -> None:
        """Print processing summary"""
        print("\n" + "=" * 70)
        print("PROCESSING SUMMARY")
        print("=" * 70)
        
        success_count = sum(1 for r in results if r.success)
        failed_count = len(results) - success_count
        
        # Group by status
        for result in results:
            status_icon = "✓" if result.success else "✗"
            print(f"\n{status_icon} {result.filename} ({result.file_format})")
            
            if result.success:
                print(f"   Length: {result.content_length:,} characters")
                if result.metadata:
                    for key, value in result.metadata.items():
                        print(f"   {key.replace('_', ' ').title()}: {value}")
            else:
                print(f"   Error: {result.error_message}")
        
        print("\n" + "=" * 70)
        print(f"✓ Success: {success_count} | ✗ Failed: {failed_count} | Total: {len(results)}")
        print("=" * 70)


# Usage example
def main():
    """Main execution function"""
    # Initialize processor
    processor = DocumentProcessor(output_dir="../documents/processed")
    
    # Process entire directory
    results = processor.process_directory(
        input_dir="../documents/raw",
        recursive=False
    )
    
    return results


# Run the processor
if __name__ == "__main__":
    main()