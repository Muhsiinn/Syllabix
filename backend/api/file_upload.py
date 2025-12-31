from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import os
import uuid
from pathlib import Path
import aiofiles
from pix2text import Pix2Text
import fitz
from PIL import Image
import io
from typing import Dict, List, Optional, Tuple, AsyncGenerator
from pydantic import BaseModel
from enum import Enum
import asyncio
from datetime import datetime
import json
from parse_doc import PatternLearner, QuestionParser, parse_pattern_response

router = APIRouter()

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("converted")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}

p2t = Pix2Text()

class ProcessingStage(str, Enum):
    PENDING = "pending"
    READING_FILES = "reading_files"
    EXTRACTING_PAGES = "extracting_pages"
    PARSING_QUESTIONS = "parsing_questions"
    STRUCTURING = "structuring"
    COMPLETED = "completed"
    FAILED = "failed"

class ProcessingStatus(BaseModel):
    job_id: str
    stage: ProcessingStage
    total_files: int
    processed_files: int
    total_pages: int
    processed_pages: int
    current_file: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

processing_jobs: Dict[str, ProcessingStatus] = {}
progress_streams: Dict[str, asyncio.Queue] = {}

async def save_uploaded_file(file: UploadFile) -> Tuple[Path, int]:
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type {file_ext} not supported. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
    
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}{file_ext}"
    
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    page_count = 0
    if file_ext == '.pdf':
        try:
            pdf_doc = fitz.open(str(file_path))
            page_count = len(pdf_doc)
            pdf_doc.close()
        except:
            pass
    
    return file_path, page_count

async def send_progress_update(job_id: str, update: dict):
    if job_id in progress_streams:
        await progress_streams[job_id].put(update)

async def process_file_with_ocr(file_path: Path, job_id: Optional[str] = None, status: Optional[ProcessingStatus] = None) -> str:
    try:
        file_ext = file_path.suffix.lower()
        
        if file_ext == '.pdf':
            pdf_doc = fitz.open(str(file_path))
            total_pages = len(pdf_doc)
            all_text = []
            
            for page_num in range(total_pages):
                if status and job_id:
                    status.processed_pages += 1
                    status.updated_at = datetime.now()
                    
                    await send_progress_update(job_id, {
                        "type": "page_progress",
                        "processed_pages": status.processed_pages,
                        "total_pages": status.total_pages,
                        "current_page": page_num + 1,
                        "current_file": status.current_file
                    })
                
                page = pdf_doc[page_num]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                
                result = p2t.recognize(img)
                if isinstance(result, dict):
                    page_text = result.get('text', '')
                else:
                    page_text = str(result)
                
                if page_text.strip():
                    all_text.append(page_text)
                
                await asyncio.sleep(0.01)
            
            pdf_doc.close()
            return '\n\n'.join(all_text)
        else:
            result = p2t.recognize(str(file_path))
            if isinstance(result, dict):
                return result.get('text', '')
            return str(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

async def process_files_async(file_paths: List[Path], job_id: str):
    status = processing_jobs[job_id]
    
    try:
        status.stage = ProcessingStage.READING_FILES
        status.total_files = len(file_paths)
        status.updated_at = datetime.now()
        
        await send_progress_update(job_id, {
            "type": "stage_change",
            "stage": "reading_files",
            "total_files": len(file_paths)
        })
        
        total_pages = 0
        for file_path in file_paths:
            if file_path.suffix.lower() == '.pdf':
                try:
                    pdf_doc = fitz.open(str(file_path))
                    total_pages += len(pdf_doc)
                    pdf_doc.close()
                except:
                    pass
        
        status.total_pages = total_pages
        status.processed_pages = 0
        status.stage = ProcessingStage.EXTRACTING_PAGES
        status.updated_at = datetime.now()
        
        await send_progress_update(job_id, {
            "type": "stage_change",
            "stage": "extracting_pages",
            "total_pages": total_pages
        })
        
        all_markdown = []
        
        for idx, file_path in enumerate(file_paths):
            status.current_file = file_path.name
            status.processed_files = idx
            status.updated_at = datetime.now()
            
            await send_progress_update(job_id, {
                "type": "file_change",
                "current_file": file_path.name,
                "processed_files": idx,
                "total_files": len(file_paths)
            })
            
            try:
                markdown_content = await process_file_with_ocr(file_path, job_id, status)
                file_id = file_path.stem
                output_path = OUTPUT_DIR / f"{file_id}.md"
                
                async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
                    await f.write(markdown_content)
                
                all_markdown.append({
                    "file_id": file_id,
                    "filename": file_path.name,
                    "output_file": str(output_path)
                })
                
                if file_path.exists():
                    os.remove(file_path)
            except Exception as e:
                status.error = str(e)
                status.stage = ProcessingStage.FAILED
                status.updated_at = datetime.now()
                await send_progress_update(job_id, {
                    "type": "error",
                    "error": str(e)
                })
                raise
        
        status.processed_files = len(file_paths)
        status.stage = ProcessingStage.PARSING_QUESTIONS
        status.updated_at = datetime.now()
        
        await send_progress_update(job_id, {
            "type": "stage_change",
            "stage": "parsing_questions",
            "total_files": len(file_paths)
        })
        
        parsed_questions_data = []
        
        for idx, markdown_item in enumerate(all_markdown):
            await send_progress_update(job_id, {
                "type": "parsing_progress",
                "current_file": markdown_item["filename"],
                "processed_files": idx,
                "total_files": len(all_markdown)
            })
            
            try:
                markdown_file_path = Path(markdown_item["output_file"])
                if markdown_file_path.exists():
                    async with aiofiles.open(markdown_file_path, 'r', encoding='utf-8') as f:
                        exam_text = await f.read()
                    
                    if exam_text.strip():
                        sample_text = exam_text[:2000] if len(exam_text) > 2000 else exam_text
                        
                        await send_progress_update(job_id, {
                            "type": "parsing_status",
                            "status": "learning_patterns",
                            "current_file": markdown_item["filename"]
                        })
                        
                        loop = asyncio.get_event_loop()
                        pattern_learner = PatternLearner()
                        pattern_result = await loop.run_in_executor(
                            None, 
                            pattern_learner.learn_patterns, 
                            sample_text
                        )
                        parsed_patterns = parse_pattern_response(pattern_result['response'])
                        
                        await send_progress_update(job_id, {
                            "type": "parsing_status",
                            "status": "extracting_questions",
                            "current_file": markdown_item["filename"]
                        })
                        
                        parser = QuestionParser(parsed_patterns)
                        questions = await loop.run_in_executor(
                            None,
                            parser.parse_questions,
                            exam_text
                        )
                        
                        questions_json = [q.model_dump() for q in questions]
                        
                        parsed_output_path = OUTPUT_DIR / f"{markdown_item['file_id']}_parsed.json"
                        async with aiofiles.open(parsed_output_path, 'w', encoding='utf-8') as f:
                            await f.write(json.dumps(questions_json, indent=2, ensure_ascii=False))
                        
                        parsed_questions_data.append({
                            "file_id": markdown_item["file_id"],
                            "filename": markdown_item["filename"],
                            "questions_count": len(questions),
                            "parsed_output": str(parsed_output_path),
                            "markdown_output": markdown_item["output_file"]
                        })
            except Exception as e:
                await send_progress_update(job_id, {
                    "type": "parsing_warning",
                    "warning": f"Failed to parse {markdown_item['filename']}: {str(e)}",
                    "current_file": markdown_item["filename"]
                })
                parsed_questions_data.append({
                    "file_id": markdown_item["file_id"],
                    "filename": markdown_item["filename"],
                    "questions_count": 0,
                    "error": str(e),
                    "markdown_output": markdown_item["output_file"]
                })
        
        status.stage = ProcessingStage.STRUCTURING
        status.updated_at = datetime.now()
        
        await send_progress_update(job_id, {
            "type": "stage_change",
            "stage": "structuring"
        })
        
        await asyncio.sleep(0.5)
        
        status.stage = ProcessingStage.COMPLETED
        status.updated_at = datetime.now()
        
        await send_progress_update(job_id, {
            "type": "stage_change",
            "stage": "completed"
        })
        
        return {
            "markdown_files": all_markdown,
            "parsed_questions": parsed_questions_data
        }
    except Exception as e:
        if job_id in processing_jobs:
            status.stage = ProcessingStage.FAILED
            status.error = str(e)
            await send_progress_update(job_id, {
                "type": "error",
                "error": str(e)
            })
        raise
    finally:
        if job_id in progress_streams:
            await progress_streams[job_id].put(None)

@router.post("/upload-files")
async def upload_files(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required")
    
    pdf_files = []
    for file in files:
        file_ext = Path(file.filename).suffix.lower()
        if file_ext != '.pdf':
            raise HTTPException(status_code=400, detail=f"Only PDF files are supported. Found: {file_ext}")
        pdf_files.append(file)
    
    job_id = str(uuid.uuid4())
    status = ProcessingStatus(
        job_id=job_id,
        stage=ProcessingStage.PENDING,
        total_files=0,
        processed_files=0,
        total_pages=0,
        processed_pages=0,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    processing_jobs[job_id] = status
    
    file_paths = []
    file_info = []
    
    try:
        for file in pdf_files:
            file_path, page_count = await save_uploaded_file(file)
            file_paths.append(file_path)
            file_info.append({
                "filename": file.filename,
                "page_count": page_count,
                "file_id": file_path.stem
            })
        
        progress_streams[job_id] = asyncio.Queue()
        asyncio.create_task(process_files_async(file_paths, job_id))
        
        return JSONResponse({
            "job_id": job_id,
            "message": "Files uploaded successfully. Processing started.",
            "files": file_info
        })
    
    except HTTPException:
        if job_id in processing_jobs:
            del processing_jobs[job_id]
        raise
    except Exception as e:
        if job_id in processing_jobs:
            del processing_jobs[job_id]
        for file_path in file_paths:
            if file_path.exists():
                try:
                    os.remove(file_path)
                except:
                    pass
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

async def stream_progress(job_id: str) -> AsyncGenerator[str, None]:
    if job_id not in processing_jobs:
        yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
        return
    
    if job_id not in progress_streams:
        progress_streams[job_id] = asyncio.Queue()
    
    status = processing_jobs[job_id]
    
    yield f"data: {json.dumps({
        'type': 'initial_status',
        'stage': status.stage.value,
        'total_files': status.total_files,
        'processed_files': status.processed_files,
        'total_pages': status.total_pages,
        'processed_pages': status.processed_pages,
        'current_file': status.current_file,
    })}\n\n"
    
    queue = progress_streams[job_id]
    
    try:
        while True:
            update = await queue.get()
            
            if update is None:
                break
            
            yield f"data: {json.dumps(update)}\n\n"
            
            if update.get("type") == "stage_change" and update.get("stage") == "completed":
                break
            if update.get("type") == "error":
                break
    except asyncio.CancelledError:
        pass
    finally:
        if job_id in progress_streams:
            del progress_streams[job_id]

@router.get("/processing-stream/{job_id}")
async def get_processing_stream(job_id: str):
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return StreamingResponse(
        stream_progress(job_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )