"""
Phase 1: Data ETL (Extract, Transform, Load) & Chunking Strategy

This module handles the NON-TRIVIAL parsing challenge of the Folger Shakespeare PDF:
1. PDF extraction with table-based dialogue handling
2. Aggressive cleaning of Folger artifacts (FTLN numbers, headers, footers, page numbers)
3. Intelligent scene-based and speech-based chunking with rich metadata
4. Handling of fragmented text, merged words, and complex formatting
"""

import os
import pdfplumber
import re
import json
import jsonlines
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from tqdm import tqdm
from collections import defaultdict


@dataclass
class Chunk:
    """Represents a text chunk with metadata"""
    text: str
    act: int
    scene: int
    speaker: str = ""
    type: str = ""  # 'stage_direction', 'dialogue', 'soliloquy', 'scene_intro'
    chunk_id: str = ""


class JuliusCaesarETL:
    """
    Robust ETL pipeline for Folger Shakespeare Julius Caesar PDF
    
    Handles non-trivial parsing challenges:
    - FTLN line numbers embedded in text
    - Page headers/footers in various formats
    - Table-based dialogue layout
    - Fragmented words across lines
    - Character name variations and stage directions
    """
    
    def __init__(self):
        self.raw_pages: List[str] = []
        self.cleaned_text = ""
        self.chunks: List[Chunk] = []
        
        # Comprehensive regex patterns for Folger artifacts
        self.ftln_pattern = re.compile(r'\bFTLN\s+\d{4,5}\b')
        
        # Page headers in multiple formats
        self.page_header_patterns = [
            re.compile(r'^\d+\s+Julius Caesar\s+ACT\s+\d+\.\s*SC\.\s*\d+', re.MULTILINE | re.IGNORECASE),
            re.compile(r'^\d+\s+The Tragedy of Julius Caesar\s+ACT', re.MULTILINE | re.IGNORECASE),
            re.compile(r'^Julius Caesar\s+\d+', re.MULTILINE),
            re.compile(r'^ACT\s+\d+\.\s*SC\.\s*\d+\s+\d+$', re.MULTILINE),
        ]
        
        # Page numbers and footers
        self.page_number_pattern = re.compile(r'^\s*\d+\s*$', re.MULTILINE)
        self.footer_pattern = re.compile(r'^\d+\s+(?:The Tragedy of )?Julius Caesar', re.MULTILINE)
        
        # Structure detection patterns
        self.act_pattern = re.compile(r'^\s*ACT\s+(\d+|[IVX]+)\s*$', re.MULTILINE | re.IGNORECASE)
        self.scene_pattern = re.compile(r'^\s*Scene\s+(\d+|[ivx]+)\s*$', re.MULTILINE | re.IGNORECASE)
        
        # Speaker patterns - more robust
        self.speaker_pattern = re.compile(
            r'^([A-Z][A-Z\s,\'\-]+?)(?:\s*\([^)]+\))?\s*(?::|(?=\s+[A-Z]))', 
            re.MULTILINE
        )
        
        # Stage directions in italics or brackets
        self.stage_direction_patterns = [
            re.compile(r'\[([^\]]+)\]'),
            re.compile(r'^(?:Enter|Exit|Exeunt|They|He|She)\s+.*?\.', re.MULTILINE),
        ]
        
        # Roman numeral conversion
        self.roman_to_int = {
            'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5,
            'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5
        }
    
    def extract_text(self, pdf_path: str) -> List[str]:
        """
        Extract raw text from PDF using pdfplumber
        Handle table-based dialogue layout
        """
        print(f"Extracting text from {pdf_path}...")
        
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        all_pages = []
        
        with pdfplumber.open(pdf_file) as pdf:
            # Skip front matter (usually first ~5-8 pages)
            # Start from where "ACT 1" appears
            start_page = 0
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text and 'ACT 1' in text.upper():
                    start_page = i
                    break
            
            print(f"Found Act 1 on page {start_page + 1}, starting extraction...")
            
            for page_num in tqdm(range(start_page, len(pdf.pages)), desc="Extracting pages"):
                page = pdf.pages[page_num]
                
                # Try table extraction first (for dialogue)
                tables = page.extract_tables()
                if tables:
                    # Combine table cells
                    table_text = []
                    for table in tables:
                        for row in table:
                            if row:
                                row_text = ' '.join([cell.strip() if cell else '' for cell in row])
                                if row_text.strip():
                                    table_text.append(row_text)
                    if table_text:
                        all_pages.append('\n'.join(table_text))
                        continue
                
                # Fallback to regular text extraction
                text = page.extract_text(layout=True)
                if text:
                    all_pages.append(text)
        
        self.raw_pages = all_pages
        print(f"Extracted {len(self.raw_pages)} pages")
        return self.raw_pages
    
    def clean_page(self, page_text: str) -> str:
        """
        Clean a single page of Folger artifacts
        """
        text = page_text
        
        # Remove FTLN numbers
        text = self.ftln_pattern.sub('', text)
        
        # Remove page headers (multiple patterns)
        for pattern in self.page_header_patterns:
            text = pattern.sub('', text)
        
        # Remove footers
        text = self.footer_pattern.sub('', text)
        
        # Remove standalone page numbers
        text = self.page_number_pattern.sub('', text)
        
        # Remove excessive whitespace but preserve structure
        text = re.sub(r' +', ' ', text)  # Multiple spaces to single
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Multiple newlines to double
        
        return text.strip()
    
    def clean_text(self, raw_pages: List[str]) -> str:
        """
        Clean each page separately to handle varying artifacts
        """
        print("Cleaning Folger artifacts from all pages...")
        
        cleaned_pages = []
        for page in tqdm(raw_pages, desc="Cleaning pages"):
            cleaned = self.clean_page(page)
            if cleaned:
                cleaned_pages.append(cleaned)
        
        # Combine pages with clear separation
        self.cleaned_text = '\n\n'.join(cleaned_pages)
        
        # Additional global cleaning
        # Fix common OCR/formatting issues
        self.cleaned_text = re.sub(r'(\w)-\s+(\w)', r'\1\2', self.cleaned_text)  # Fix hyphenated words
        self.cleaned_text = re.sub(r'\s+([.,!?;:])', r'\1', self.cleaned_text)  # Fix spacing before punctuation
        
        print(f"Cleaned text: {len(self.cleaned_text)} characters")
        return self.cleaned_text
    
    def convert_roman(self, numeral: str) -> int:
        """Convert Roman numeral to integer"""
        return self.roman_to_int.get(numeral.upper(), int(numeral) if numeral.isdigit() else 0)
    
    def parse_structure(self) -> List[Dict[str, Any]]:
        """
        Parse the play structure into acts and scenes with content
        """
        print("Parsing play structure (Acts and Scenes)...")
        
        lines = self.cleaned_text.split('\n')
        
        current_act = 0
        current_scene = 0
        scene_buffer = []
        structured_data = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                i += 1
                continue
            
            # Detect Act
            act_match = self.act_pattern.search(line)
            if act_match:
                # Save previous scene if exists
                if scene_buffer and current_act > 0:
                    structured_data.append({
                        'act': current_act,
                        'scene': current_scene,
                        'content': '\n'.join(scene_buffer),
                        'type': 'scene'
                    })
                    scene_buffer = []
                
                act_num = act_match.group(1)
                current_act = self.convert_roman(act_num) if not act_num.isdigit() else int(act_num)
                current_scene = 0
                print(f"  Found ACT {current_act}")
                i += 1
                continue
            
            # Detect Scene
            scene_match = self.scene_pattern.search(line)
            if scene_match:
                # Save previous scene if exists
                if scene_buffer and current_act > 0:
                    structured_data.append({
                        'act': current_act,
                        'scene': current_scene,
                        'content': '\n'.join(scene_buffer),
                        'type': 'scene'
                    })
                    scene_buffer = []
                
                scene_num = scene_match.group(1)
                current_scene = self.convert_roman(scene_num) if not scene_num.isdigit() else int(scene_num)
                print(f"    Found Scene {current_scene}")
                scene_buffer.append(line)
                i += 1
                continue
            
            # Add line to current scene buffer
            if current_act > 0:
                scene_buffer.append(line)
            
            i += 1
        
        # Add last scene
        if scene_buffer and current_act > 0:
            structured_data.append({
                'act': current_act,
                'scene': current_scene,
                'content': '\n'.join(scene_buffer),
                'type': 'scene'
            })
        
        print(f"Parsed {len(structured_data)} scenes across {current_act} acts")
        return structured_data
    
    def extract_speaker_and_text(self, line: str) -> Tuple[str, str]:
        """
        Extract speaker name and their dialogue from a line
        Returns (speaker, text) tuple
        """
        speaker_match = re.match(r'^([A-Z][A-Z\s,\'\-]+?)(?:\s*\([^)]+\))?\s*[:\s]+(.+)$', line)
        if speaker_match:
            speaker = speaker_match.group(1).strip()
            text = speaker_match.group(2).strip()
            return speaker, text
        return "", line
    
    def is_stage_direction(self, line: str) -> bool:
        """Check if line is a stage direction"""
        line = line.strip()
        if not line:
            return False
        
        # Check for brackets
        if line.startswith('[') or line.startswith('('):
            return True
        
        # Check for common stage direction starts
        stage_starts = ['Enter', 'Exit', 'Exeunt', 'They', 'He ', 'She ', 'Alarum', 'Flourish', 'Aside']
        if any(line.startswith(start) for start in stage_starts):
            return True
        
        return False
    
    def chunk_by_speech(self, scene_data: Dict[str, Any]) -> List[Chunk]:
        """
        Chunk a scene by individual speeches with logical grouping
        This is the CORE CHUNKING STRATEGY - scene and speech based
        """
        chunks = []
        content = scene_data['content']
        act = scene_data['act']
        scene = scene_data['scene']
        
        lines = content.split('\n')
        current_speaker = ""
        current_speech = []
        chunk_counter = 0
        
        # Add scene introduction chunk
        scene_intro_lines = []
        i = 0
        while i < len(lines) and i < 5:  # First few lines might be scene description
            line = lines[i].strip()
            if line and (self.is_stage_direction(line) or 'Scene' in line):
                scene_intro_lines.append(line)
            else:
                break
            i += 1
        
        if scene_intro_lines:
            chunks.append(Chunk(
                text='\n'.join(scene_intro_lines),
                act=act,
                scene=scene,
                speaker="",
                type='scene_intro',
                chunk_id=f"act{act}_scene{scene}_intro"
            ))
            chunk_counter += 1
        
        # Process remaining lines
        for line_idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check if this is a stage direction
            if self.is_stage_direction(line):
                # Save previous speech if exists
                if current_speech and current_speaker:
                    speech_text = '\n'.join(current_speech).strip()
                    if speech_text:
                        # Determine if soliloquy (longer, introspective speech)
                        is_soliloquy = len(current_speech) > 8
                        chunk_type = 'soliloquy' if is_soliloquy else 'dialogue'
                        
                        chunks.append(Chunk(
                            text=speech_text,
                            act=act,
                            scene=scene,
                            speaker=current_speaker,
                            type=chunk_type,
                            chunk_id=f"act{act}_scene{scene}_chunk{chunk_counter}"
                        ))
                        chunk_counter += 1
                        current_speech = []
                
                # Add stage direction as separate chunk
                chunks.append(Chunk(
                    text=line,
                    act=act,
                    scene=scene,
                    speaker="",
                    type='stage_direction',
                    chunk_id=f"act{act}_scene{scene}_chunk{chunk_counter}"
                ))
                chunk_counter += 1
                continue
            
            # Try to extract speaker
            speaker, text = self.extract_speaker_and_text(line)
            
            if speaker:
                # New speaker detected - save previous speech
                if current_speech and current_speaker:
                    speech_text = '\n'.join(current_speech).strip()
                    if speech_text:
                        is_soliloquy = len(current_speech) > 8
                        chunk_type = 'soliloquy' if is_soliloquy else 'dialogue'
                        
                        chunks.append(Chunk(
                            text=speech_text,
                            act=act,
                            scene=scene,
                            speaker=current_speaker,
                            type=chunk_type,
                            chunk_id=f"act{act}_scene{scene}_chunk{chunk_counter}"
                        ))
                        chunk_counter += 1
                
                # Start new speech
                current_speaker = speaker
                current_speech = [text] if text else []
            else:
                # Continue current speech
                if current_speaker:  # Only add if we have a speaker
                    current_speech.append(line)
        
        # Add final speech
        if current_speech and current_speaker:
            speech_text = '\n'.join(current_speech).strip()
            if speech_text:
                is_soliloquy = len(current_speech) > 8
                chunk_type = 'soliloquy' if is_soliloquy else 'dialogue'
                
                chunks.append(Chunk(
                    text=speech_text,
                    act=act,
                    scene=scene,
                    speaker=current_speaker,
                    type=chunk_type,
                    chunk_id=f"act{act}_scene{scene}_chunk{chunk_counter}"
                ))
        
        return chunks
    
    def create_chunks(self) -> List[Chunk]:
        """
        Create logical chunks from structured data
        
        CHUNKING STRATEGY:
        1. Scene-based: Each scene is a logical unit
        2. Speech-based: Each character's speech is a separate chunk
        3. Type-aware: Distinguishes soliloquies, dialogue, stage directions
        4. Metadata-rich: Every chunk has act, scene, speaker, type
        
        WHY NOT FIXED-SIZE:
        - Preserves semantic integrity of soliloquies and dialogues
        - Maintains dramatic context
        - Enables precise citation and retrieval
        """
        print("\n" + "="*60)
        print("CHUNKING STRATEGY: Scene-based + Speech-based")
        print("="*60)
        print("Creating chunks with rich metadata...")
        
        structured_data = self.parse_structure()
        all_chunks = []
        global_chunk_counter = 0  # Global counter for unique IDs
        
        for scene_data in tqdm(structured_data, desc="Chunking scenes"):
            scene_chunks = self.chunk_by_speech(scene_data)
            
            # Update chunk IDs to be globally unique
            for chunk in scene_chunks:
                chunk.chunk_id = f"chunk_{global_chunk_counter:04d}_act{chunk.act}_scene{chunk.scene}"
                global_chunk_counter += 1
            
            all_chunks.extend(scene_chunks)
        
        self.chunks = all_chunks
        
        print(f"\n✅ Created {len(self.chunks)} logical chunks")
        print("="*60)
        return self.chunks
    
    def save_chunks(self, output_file: str = "data/chunks.json") -> None:
        """Save chunks with all metadata to JSON for indexing"""
        print(f"\nSaving {len(self.chunks)} chunks to {output_file}...")
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        chunks_data = [asdict(chunk) for chunk in self.chunks]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chunks_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Chunks saved successfully")
    
    def run_pipeline(self, pdf_path: str, output_file: str = "data/chunks.json") -> List[Chunk]:
        """
        Run the complete ETL pipeline
        Handles non-trivial Folger Shakespeare PDF format
        """
        print("\n" + "🎭"*30)
        print("SHAKESPEARE ETL PIPELINE - Non-trivial PDF Parsing")
        print("🎭"*30)
        
        # Extract raw pages from PDF (table-based)
        pages = self.extract_text(pdf_path)
        
        # Clean each page (remove FTLN, headers, footers)
        self.cleaned_text = self.clean_text(pages)
        
        # Parse dramatic structure (acts, scenes)
        structured_data = self.parse_structure()
        
        # Create logical chunks (scene + speech based)
        chunks = self.create_chunks()
        
        # Save chunks with metadata
        self.save_chunks(output_file)
        
        # Print statistics
        self.print_statistics()
        
        print("\n" + "🎭"*30)
        print("✅ ETL PIPELINE COMPLETE")
        print("🎭"*30)
        
        return chunks
    
    def print_statistics(self) -> None:
        """Print detailed statistics about the processed data"""
        print("\n" + "="*60)
        print("📊 ETL STATISTICS")
        print("="*60)
        
        if not self.chunks:
            print("No chunks created yet!")
            return
        
        # Count by type
        type_counts = defaultdict(int)
        for chunk in self.chunks:
            type_counts[chunk.type] += 1
        
        # Count by act
        act_counts = defaultdict(int)
        for chunk in self.chunks:
            act_counts[chunk.act] += 1
        
        # Count by speaker
        speaker_counts = defaultdict(int)
        for chunk in self.chunks:
            if chunk.speaker:
                speaker_counts[chunk.speaker] += 1
        
        print(f"\n📝 Total Chunks: {len(self.chunks)}")
        print(f"📖 Total Characters (raw text): {sum(len(chunk.text) for chunk in self.chunks):,}")
        
        print("\n🎭 Chunk Types:")
        for chunk_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {chunk_type:20s}: {count:4d}")
        
        print("\n📚 Chunks by Act:")
        for act in sorted(act_counts.keys()):
            print(f"  Act {act}: {act_counts[act]:4d} chunks")
        
        print("\n👥 Top 10 Speakers:")
        for speaker, count in sorted(speaker_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {speaker:20s}: {count:4d} speeches")
        
        print("\n💬 Sample Chunk (first dialogue):")
        for chunk in self.chunks[:20]:
            if chunk.type == 'dialogue':
                print(f"  Act {chunk.act}, Scene {chunk.scene}")
                print(f"  Speaker: {chunk.speaker}")
                print(f"  Text: {chunk.text[:200]}...")
                break
        
        print("="*60)


def main():
    """Main execution"""
    print("\n" + "🎭"*30)
    print("JULIUS CAESAR ETL PIPELINE")
    print("Processing Folger Shakespeare PDF (Non-trivial format)")
    print("🎭"*30)
    
    # Paths
    pdf_path = "data/julius-caesar_PDF_FolgerShakespeare.pdf"
    output_file = "data/chunks.json"
    
    # Initialize and run ETL
    etl = JuliusCaesarETL()
    chunks = etl.run_pipeline(pdf_path, output_file)
    
    print("\n✅ ETL Complete! Next steps:")
    print("1. Run indexing: python src/A2_indexing.py")
    print("2. Start API: docker-compose up --build")
    print("3. Test queries via frontend or API")


if __name__ == "__main__":
    main()

