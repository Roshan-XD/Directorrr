"""Fixed CPU conversion using the already validated WSL PyAV/libx264 environment."""
import json
import subprocess
from pathlib import Path
from director.installations.verifier import assert_no_links

# The Stage 9 conversion, parameterized only with Director-generated local paths.
CONVERT_SCRIPT = r'''
import av, json, os, sys, hashlib
from fractions import Fraction
from pathlib import Path
source, output = map(Path, sys.argv[1:])
temporary = output.with_suffix('.partial.mp4')
for path in (source, output, temporary):
 for parent in (path, *path.parents):
  if parent.is_symlink(): raise ValueError('Linked conversion path')
if output.exists() or temporary.exists(): raise ValueError('Existing conversion output')
with av.open(str(source)) as original, av.open(str(temporary), 'w', format='mp4', options={'movflags': '+faststart'}) as converted:
 if original.streams.audio: raise ValueError('Audio preservation needs a validated audio adapter')
 video_source=original.streams.video[0]
 width,height=video_source.width,video_source.height
 if width%16 or height%16 or not (64<=width<=512 and 64<=height<=512) or video_source.average_rate!=Fraction(16,1): raise ValueError('Unapproved source geometry/rate')
 stream = converted.add_stream('libx264', rate=16)
 stream.width=width; stream.height=height; stream.pix_fmt='yuv420p'
 stream.options={'crf':'18','preset':'medium'}
 count=0
 for i,frame in enumerate(original.decode(video=0)):
  if i >= 129 or (frame.width,frame.height)!=(width,height): raise ValueError('Unexpected source frames')
  frame=frame.reformat(width=width,height=height,format='yuv420p')
  frame.pts=i; frame.time_base=Fraction(1,16)
  for packet in stream.encode(frame): converted.mux(packet)
  count+=1
 if count not in (17,33,65,97,129): raise ValueError('Unexpected frame count')
 for packet in stream.encode(): converted.mux(packet)
source_count=count
with av.open(str(temporary)) as check:
 video=check.streams.video[0]
 count=sum(1 for _ in check.decode(video=0))
 if (video.codec_context.name,video.codec_context.format.name,video.width,video.height,count,video.average_rate)!=('h264','yuv420p',width,height,count,Fraction(16,1)): raise ValueError('Converted video validation failed')
 duration=float(video.duration*video.time_base)
 if count!=source_count or duration!=source_count/16: raise ValueError('Invalid duration')
size=temporary.stat().st_size
if not 0<size<=32*1024*1024: raise ValueError('Invalid output size')
os.rename(temporary,output)
print(json.dumps({'codec':'h264','container':'mp4','pixel_format':'yuv420p','width':width,'height':height,'frames':count,'fps':16,'duration_seconds':duration,'size_bytes':size,'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'pyav_version':av.__version__,'decoded_all_frames':True}))
'''


class WslVideoConverter:
    def __call__(self, source: Path, output: Path):
        def linux_path(path):
            # Only controlled normal Windows drive paths are passed to WSL.
            if not path.is_absolute() or len(path.drive) != 2 or path.drive[1] != ":":
                raise ValueError("Conversion requires a Windows drive path")
            return "/mnt/" + path.drive[0].lower() + "/" + path.as_posix()[3:]
        result = subprocess.run(
            ["wsl.exe", "-d", "Director-GPU-Dev", "-u", "root", "--exec",
             "/opt/director-gpu-dev/venv/bin/python", "-c", CONVERT_SCRIPT,
             linux_path(source), linux_path(output)],
            capture_output=True, text=True, timeout=120, shell=False,
        )
        if result.returncode or len(result.stdout) > 4096:
            raise ValueError("WSL PyAV conversion failed")
        return json.loads(result.stdout)


class WindowsVideoConverter:
    """Use only the owned native candidate; requests never select an executable."""
    def __init__(self, project_root: Path):
        self.root = project_root.resolve()
        self.python = self.root / "runtime/windows-dev-001/venv/Scripts/python.exe"

    def __call__(self, source: Path, output: Path):
        for path in (self.python, source, output):
            assert_no_links(path)
        allowed = self.root / "generated_videos/development"
        if (source.parent != output.parent or not source.resolve().is_relative_to(allowed)
                or not output.resolve().is_relative_to(allowed)
                or source.suffix != ".webm" or output.suffix != ".mp4"
                or not self.python.is_file()):
            raise ValueError("Invalid owned Windows conversion paths")
        result = subprocess.run(
            [str(self.python), "-I", "-B", "-c", CONVERT_SCRIPT, str(source), str(output)],
            capture_output=True, text=True, timeout=120, shell=False,
        )
        if result.returncode or len(result.stdout) > 4096:
            raise ValueError("Windows PyAV conversion failed")
        return json.loads(result.stdout)
