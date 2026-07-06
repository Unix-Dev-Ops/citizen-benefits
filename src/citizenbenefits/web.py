import os
import aiosqlite
from contextlib import asynccontextmanager
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import ValidationError
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai import types

from citizenbenefits.agent import root_agent
from citizenbenefits.schemas import EligibilityRequest, ProgramResult, SessionRecord, LikelyEligible

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database table on startup
    db_path = os.environ.get("SESSIONS_DB_PATH", "./sessions.db")
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                request TEXT NOT NULL,
                results TEXT NOT NULL
            )
            """
        )
        await db.commit()
    yield

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="src/citizenbenefits/static"), name="static")

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "font-src 'self' https://fonts.gstatic.com https://fonts.googleapis.com https://esm.run; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://esm.run; "
        "script-src 'self'; "
        "connect-src 'self'; "
        "img-src 'self' data:;"
    )
    return response

# Global Session Service for ADK
session_service = InMemorySessionService()

@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request, exc: ValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    # Print or log exception locally for debugging, but never return it to client
    print(f"ERROR: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."},
    )

@app.get("/")
async def serve_index():
    static_file = os.path.join(os.path.dirname(__file__), "static", "index.html")
    return FileResponse(static_file)


@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/eligibility")
async def check_eligibility(req: EligibilityRequest):
    # Create ADK Session
    session = session_service.create_session_sync(user_id="anonymous", app_name="citizenbenefits")
    runner = Runner(agent=root_agent, session_service=session_service, app_name="citizenbenefits")
    
    # Serialize to JSON string for safety gate / regex checks
    json_input = req.model_dump_json()
    message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=json_input)]
    )
    
    # Run the workflow
    events = list(
        runner.run(
            new_message=message,
            user_id="anonymous",
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE)
        )
    )
    
    if not events:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Workflow did not return any events."
        )
        
    final_event = events[-1]
    
    # Extract results and summary
    summary_text = ""
    if final_event.content and final_event.content.parts:
        text_parts = [p.text for p in final_event.content.parts if p.text]
        summary_text = "\n".join(text_parts)
        
    output_data = final_event.output
    
    # If PII or invalid route occurred
    if isinstance(output_data, str):
        # Returned a warning message instead of list of ProgramResult
        return {
            "results": [],
            "summary": output_data
        }
        
    # Standard eligibility results path
    if isinstance(output_data, list):
        results = []
        for item in output_data:
            if isinstance(item, dict):
                results.append(ProgramResult.model_validate(item))
            elif isinstance(item, ProgramResult):
                results.append(item)
                
        # Sort results before returning: LIKELY, POSSIBLY, UNLIKELY, NOT_AVAILABLE_FOR_STATUS
        sort_order = {
            LikelyEligible.LIKELY: 0,
            LikelyEligible.POSSIBLY: 1,
            LikelyEligible.UNLIKELY: 2,
            LikelyEligible.NOT_AVAILABLE_FOR_STATUS: 3,
        }
        results.sort(key=lambda r: sort_order.get(r.likely_eligible, 99))

        # Persist Session Record
        record = SessionRecord(
            request=req,
            results=results
        )
        
        db_path = os.environ.get("SESSIONS_DB_PATH", "./sessions.db")
        async with aiosqlite.connect(db_path) as db:
            await db.execute(
                "INSERT INTO sessions (id, created_at, request, results) VALUES (?, ?, ?, ?)",
                (
                    str(record.id),
                    record.created_at.isoformat(),
                    req.model_dump_json(),
                    record.model_dump_json()
                )
            )
            await db.commit()
            
        return {
            "results": [r.model_dump() for r in results],
            "summary": summary_text
        }
        
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Unexpected workflow output type."
    )
