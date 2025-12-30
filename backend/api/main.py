from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from parse_doc import router as parse_doc_router

app = FastAPI(title="Syllabix", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(parse_doc_router)
app.include_router(finetune_router)
app.include_router(fileupload_router)
app.include_router(process_doc_router)
app.include_router(model_router)
app.include_router(model_list_router)


@app.get("/")
async def root():
    return {
        "message": "Syllabix",
        "version": "1.0.0",
        "endpoints": {
            "download_model": "POST /download-model",
            "load_model": "POST /load-model",
            "upload_file": "POST /upload-large"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}