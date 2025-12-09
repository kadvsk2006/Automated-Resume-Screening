"""
THE SERVER. This file runs the website and connects the Frontend to the AI.
"""
from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List
import os
import logging
import time
from pathlib import Path
import tempfile
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Robust Path Setup
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Mounts
os.makedirs(str(STATIC_DIR), exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Import logic
from app.utils import (
    load_model,
    extract_text_from_pdf,
    calculate_similarity_scores,
    format_score,
    generate_embeddings,
)
from app.csv_loader import CSVResumeDatabase
from app.text_preprocessor import TextPreprocessor
from app.skill_extractor import skill_extractor

# Create uploads directory if it doesn't exist
UPLOADS_DIR = BASE_DIR / "uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Global instances
csv_database: CSVResumeDatabase = None

@app.on_event("startup")
async def startup_event():
    global csv_database
    
    # Load Sentence-Transformer model
    load_model()
    
    # Initialize CSV database (non-blocking - build in background thread)
    try:
        csv_path = str(BASE_DIR / "Resume.csv")
        csv_database = CSVResumeDatabase(csv_path=csv_path)
        # Check if index exists, if not build in background
        if not os.path.exists(csv_database.index_path):
            logger.info("CSV index not found. Building in background...")
            loop = asyncio.get_event_loop()
            executor = ThreadPoolExecutor(max_workers=1)
            loop.run_in_executor(executor, csv_database.build_index)
        else:
            # Load existing index (fast)
            csv_database.build_index()
        logger.info("✅ CSV Database ready!")
    except Exception as e:
        logger.warning(f"⚠️ CSV Database initialization failed: {e}")
        csv_database = None
    
    logger.info("🚀 Resume Ranker Pro is ready!")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/screen-resumes")
async def screen_resumes(
    job_description: str = Form(...),
    files: List[UploadFile] = File(default=[]),
    threshold: float = Form(70.0),
    include_csv: bool = Form(True)
):
    start_time = time.time()
    
    if not job_description.strip():
        return JSONResponse(status_code=400, content={"detail": "Job description cannot be empty"})
    
    uploaded_results = []
    database_results = []
    temp_files = []
    
    try:
        # 1. Generate JD embedding
        jd_embedding = generate_embeddings([job_description])[0]
        
        # 2. PDF Processing (Optional)
        if files:
            pdf_resume_data = []
            
            for file in files:
                if not file.filename:
                    continue
                
                try:
                    # Read file content
                    content = await file.read()
                    
                    if len(content) == 0:
                        continue
                    
                    # Extract text from PDF
                    text = extract_text_from_pdf(content, file.filename)
                    print(f"DEBUG RAW TEXT ({file.filename}): {text[:200]!r}")
                    
                    # Check if extraction was successful
                    if text.startswith("[Error") or text.startswith("[Warning"):
                        continue
                    
                    if len(text.strip()) < 20:
                        continue
                    
                    # Save file temporarily for download
                    temp_path = os.path.join(str(UPLOADS_DIR), file.filename)
                    with open(temp_path, "wb") as f:
                        f.write(content)
                    temp_files.append(temp_path)
                    
                    # Preprocess text to clean encoding artifacts
                    clean_text = TextPreprocessor.preprocess(text)
                    print(f"DEBUG CLEAN TEXT ({file.filename}): {clean_text[:200]!r}")

                    # Extract skills from cleaned text
                    skills = skill_extractor.extract(clean_text)

                    pdf_resume_data.append({
                        "filename": file.filename,
                        "text": text,
                        "skills": skills,
                    })
                    
                except Exception as e:
                    logger.error(f"PDF Error: {e}")
                    continue
            
            if pdf_resume_data:
                # Calculate similarity scores for PDFs
                resume_texts = [r["text"] for r in pdf_resume_data]
                resume_filenames = [r["filename"] for r in pdf_resume_data]
                
                pdf_results = calculate_similarity_scores(
                    job_description,
                    resume_texts,
                    resume_filenames
                )
                
                for rank, (filename, text, score) in enumerate(pdf_results, start=1):
                    match_score = format_score(score)

                    # Retrieve precomputed skills for this filename
                    pdf_data = next((r for r in pdf_resume_data if r["filename"] == filename), None)
                    skills = pdf_data["skills"] if pdf_data else []

                    # Basic safety check for very short resumes
                    warnings = []
                    if len(text.strip()) < 50:
                        warnings.append("Scanned/Empty PDF detected")
                    
                    # Apply threshold filter
                    if match_score >= threshold:
                        uploaded_results.append({
                            "rank": 0,  # Will be re-ranked
                            "filename": filename,
                            "source": "pdf",
                            "candidate_name": filename.replace('.pdf', ''),
                            "match_score": round(match_score, 1),
                            "skills": skills,
                            "resume_text": text,
                            "warnings": warnings,
                        })
        
        # 3. CSV Search (if enabled and database is ready)
        if include_csv and csv_database and csv_database.index is not None and csv_database.index.ntotal > 0:
            try:
                csv_results = csv_database.search(jd_embedding, top_k=10)
                
                for csv_result in csv_results:
                    try:
                        full_text = csv_result.get("full_text", "")
                        clean_full_text = TextPreprocessor.preprocess(full_text) if full_text else ""

                        # Extract skills from cleaned CSV text
                        skills = skill_extractor.extract(clean_full_text) if clean_full_text else []

                        match_score = format_score(csv_result.get("score", 0.0))

                        # Apply threshold filter
                        if match_score >= threshold:
                            database_results.append({
                                "rank": 0,  # Will be re-ranked
                                "filename": csv_result.get("filename", "Unknown"),
                                "source": "csv",
                                "candidate_name": csv_result.get("filename", "Unknown").replace('.csv', '').replace('resume_', ''),
                                "match_score": round(match_score, 1),
                                "skills": skills,
                                "resume_text": full_text,
                            })
                    except Exception as e:
                        logger.error(f"Error processing CSV result: {e}")
                        continue
            except Exception as e:
                logger.error(f"Error searching CSV database: {e}")
        
        # 4. Rank & Return (separate ranking for each source)
        uploaded_results.sort(key=lambda x: x["match_score"], reverse=True)
        for rank, result in enumerate(uploaded_results, start=1):
            result["rank"] = rank
        
        database_results.sort(key=lambda x: x["match_score"], reverse=True)
        for rank, result in enumerate(database_results, start=1):
            result["rank"] = rank

        response_payload = {
            "total_processed": len(uploaded_results) + len(database_results),
            "total_qualified": len(uploaded_results) + len(database_results),
            "processing_time_ms": round((time.time() - start_time) * 1000, 1),
            "uploaded_results": uploaded_results,
            "database_results": database_results,
        }
        print("DEBUG FINAL RESPONSE:", response_payload)

        return JSONResponse(response_payload)
    
    except Exception as e:
        # Cleanup temp files on error
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
        
        logger.error(f"Error in screen_resumes: {e}")
        return JSONResponse(status_code=500, content={"detail": str(e)})

@app.get("/download/{filename}")
async def download_resume(filename: str):
    """Download a resume file."""
    file_path = os.path.join(str(UPLOADS_DIR), filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    from fastapi.responses import FileResponse
    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=filename
    )
