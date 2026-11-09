import sys
from pathlib import Path
ROOT=Path("D:/FallLine");sys.path.insert(0,str(ROOT/"Scripts"))
exec(compile((ROOT/"Scripts/CaptureCombinedRuntime.py").read_text(),"CaptureCombinedRuntime.py","exec"),globals())
