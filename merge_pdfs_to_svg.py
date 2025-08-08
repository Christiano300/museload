import os
import pypdf
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from tempfile import NamedTemporaryFile

from tkinter.filedialog import askdirectory
from tqdm import tqdm

path = askdirectory(title='Select Folder')

def get_all_with_ext(folder: str, ext: str):
    return [f for f in os.listdir(folder) if f.endswith(ext)]

svgs = get_all_with_ext(path, ".svg")
for i in tqdm(svgs, "Converting SVGs"):
    file = os.path.join(path, i)
    with open(file) as f, open(f"{path}/{i[:-4]}.pdf", "wb") as out_file:
        drawing = svg2rlg(f)
        if not drawing:
            print(f"Failed to convert file: {file}")
        renderPDF.drawToFile(drawing, out_file) # type: ignore

merger = pypdf.PdfWriter()

pdfs = sorted(get_all_with_ext(path, ".pdf"), key=lambda x: int(x.split(".")[0].split("_")[1]))
for i in tqdm(pdfs, "Merging PDFs"):
    file = os.path.join(path, i)
    merger.append(file)
    
with open(os.path.join(path, "score.pdf"), "wb") as out_file:
    merger.write(out_file)
    
print("Done!")