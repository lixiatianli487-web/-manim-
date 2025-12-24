import subprocess
import os
import uuid
import re
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("media", exist_ok=True)
os.makedirs("temp_files", exist_ok=True)
os.makedirs("examples", exist_ok=True)
app.mount("/media", StaticFiles(directory="media"), name="media")
app.mount("/examples", StaticFiles(directory="examples"), name="examples")

class CodeRequest(BaseModel):
    code: str
    quality: str = "ql"



# ladning
@app.get("/", response_class=HTMLResponse)
async def get_landing():
    
    if os.path.exists("landing.html"):
        with open("landing.html", encoding="utf-8") as f:
            return f.read()
    return "请创建 landing.html"

# editor
@app.get("/editor", response_class=HTMLResponse)
async def get_editor():
    with open("index.html", encoding="utf-8") as f:
        return f.read()

# 渲染
@app.post("/render")
async def render_manim(request: CodeRequest, req_info: Request):

    all_scenes = re.findall(r"class\s+(\w+)\s*\(.*Scene.*\):", request.code)
    scene_name = all_scenes[-1] if all_scenes else "MyScene"
    
    task_id = str(uuid.uuid4())[:8]
    py_filename = f"temp_files/{task_id}.py"
    
    with open(py_filename, "w", encoding="utf-8") as f:
        f.write(request.code)

    quality_map = {
        "ql": {"flag": "-ql", "folder": "480p15"},
        "qm": {"flag": "-qm", "folder": "720p30"},
        "qh": {"flag": "-qh", "folder": "1080p60"},
    }
    selected = quality_map.get(request.quality, quality_map["ql"])
    video_output_path = f"media/{task_id}"
    
    cmd = ["manim", selected["flag"], "--media_dir", video_output_path, py_filename, scene_name]
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        video_rel_path = f"media/{task_id}/videos/{task_id}/{selected['folder']}/{scene_name}.mp4"
        if not os.path.exists(video_rel_path):
            return {"status": "error", "error_log": "渲染失败"}
        return {"status": "success", "video_url": f"{req_info.base_url}{video_rel_path}"}
    except Exception as e:
        return {"status": "error", "error_log": str(e)}
#大功告成！
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)