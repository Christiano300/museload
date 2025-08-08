from playwright.sync_api import sync_playwright, Response
import re
import pypdf
from io import BytesIO
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Shape, Drawing, Group
from tqdm import tqdm

score_pattern = re.compile(r"/score_(\d{1,3})\.(svg|png)\?")
pages = {}
limit = -1


def on_response(response: Response):
    match = score_pattern.search(response.url)
    if match is not None:
        index = int(match.groups()[0])
        pages[index] = response.body()
        if limit != -1:
            print(f"\rLoaded page {index + 1} ({len(pages)} of {limit})", end="")
            if len(pages) == limit:
                print()
        else:
            print(f"Loaded first page")


def fix_neg_dasharray(node: Shape):
    if isinstance(node, Drawing):
        for element in node.contents:
            fix_neg_dasharray(element)
    elif isinstance(node, Group):
        for element in node.contents:
            fix_neg_dasharray(element)

    props = node.getProperties()
    if "strokeDashArray" in props:
        dash_array = props["strokeDashArray"]
        if isinstance(dash_array, list) and any(
            isinstance(x, (int, float)) and x < 0 for x in dash_array
        ):
            node.setProperties({"strokeDashArray": [abs(x) for x in dash_array]})


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.on("response", on_response)
    link = input("Enter the URL of the MuseScore page: ")
    print("Loading pages...")
    page.goto(link)
    page_elements = page.evaluate(
        'document.querySelectorAll("#jmuse-scroller-component > div:not(:last-child)")'
    )
    limit = len(page_elements)
    header = page.query_selector("#aside-layout span")
    name = header.inner_text()
    scroll_container = page.query_selector("#jmuse-scroller-component")
    scroll_pixels = page.evaluate(
        "container => container.scrollHeight", scroll_container
    )
    for scroll_y in range(0, scroll_pixels, 150):
        page.evaluate(
            "([container, y]) => container.scroll(0, y)", [scroll_container, scroll_y]
        )
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(25)

    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    # Go over each missing page
    for i in range(limit):
        if i not in pages:
            print(f"Page {i + 1} is missing, trying to load it again")
            page.evaluate(
                "([element, container]) => {element.scrollIntoView(); container.scrollBy(0, -200)}",
                [page_elements[i], scroll_container],
            )
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(500)
            if i in pages:
                print(f"Page {i + 1} loaded successfully")
            else:
                print(f"Failed to load page {i + 1}")

    browser.close()

page_bytes = [BytesIO(pages[i]) for i in range(len(pages))]
merger = pypdf.PdfWriter()

print("Converting to PDF...")

for page in tqdm(page_bytes):
    drawing = svg2rlg(page)
    fix_neg_dasharray(drawing)
    pdf = BytesIO()
    renderPDF.drawToFile(drawing, pdf)
    merger.append(pdf)

with open(name + ".pdf", "wb") as file_out:
    merger.write(file_out)
