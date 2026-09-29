"""Product pictures cut out of brochure pages.

    python3 tests/test_pictures.py
"""

from __future__ import annotations

import asyncio
from io import BytesIO

import support
from support import check, done

from mealie_planner import crops, extraction
from mealie_planner.offers import OfferBook

# Boxes as the AI may give them.
check("a box in fractions", crops.clean_box([0.1, 0.2, 0.5, 0.6]), (0.1, 0.2, 0.5, 0.6))
check("a box in percent", crops.clean_box([10, 20, 50, 60]), (0.1, 0.2, 0.5, 0.6))
check("a box over the edge is held in", crops.clean_box([-0.1, 0.5, 1.2, 0.9]), (0.0, 0.5, 1.0, 0.9))
check("a box too small is no box", crops.clean_box([0.1, 0.1, 0.11, 0.5]), None)
check("anything else is no box", (crops.clean_box(None), crops.clean_box([1, 2]), crops.clean_box(["a", 1, 2, 3])), (None, None, None))
check("file names are safe", crops.file_name("lidl:brochure:abc/1"), "lidl_brochure_abc_1.jpg")

try:
    from PIL import Image
except ImportError:
    Image = None
    print("skip cropping: Pillow is not installed here (Home Assistant has it)")

if Image is not None:
    page = Image.new("RGB", (1000, 1400), "white")
    page.paste((200, 30, 30), (100, 280, 500, 840))   # the product, 400 x 560
    raw = BytesIO()
    page.save(raw, "JPEG")
    cut = crops.crop(raw.getvalue(), (0.1, 0.2, 0.5, 0.6))
    with Image.open(BytesIO(cut)) as picture:
        width, height = picture.size
        centre = picture.getpixel((width // 2, height // 2))
    check("the picture is small", max(width, height) <= 480, True)
    check("and keeps the product's shape", round(width / height, 2), round(420 / 588, 2))
    check("and shows the product", centre[0] > 150 and centre[1] < 100, True)
    check("a broken page gives no picture", crops.crop(b"not an image", (0.1, 0.1, 0.5, 0.5)), None)


# Reading a brochure: each offer keeps its page, and gets its cut-out picture.
class FakeAI:
    def __init__(self, answers):
        self.answers = list(answers)

    async def chat_json(self, system, content, **kwargs):
        return self.answers.pop(0), {"prompt": 1, "completion": 1}


async def fake_fetch(session, url, limit=0, timeout=0):
    return url.encode(), "image/jpeg"


extraction.fetch_bytes = fake_fetch
brochure = {"id": "lidl:brochure:w", "chain": "lidl", "title": "Седмични предложения", "valid_from": "2026-09-28",
            "valid_to": "2026-10-04", "pages": [f"https://x/{n}.jpg" for n in range(1, 7)], "pdf": None}
first = {"offers": [
    {"name": "Сьомга филе", "category": "fish", "price": 9.99, "img": 3, "box": [0.1, 0.1, 0.5, 0.4]},
    {"name": "Картофи", "category": "vegetables", "price": 0.79, "img": 1, "box": None},
]}
second = {"offers": [{"name": "Боб", "category": "legumes", "price": 1.49, "img": 2, "box": [5, 5, 45, 30]}]}
cut = []


async def cropper(data, box, offer_id):
    cut.append((data, box, offer_id))
    return f"/mealie_planner/pictures/{crops.file_name(offer_id)}"


async def main():
    offers, _ = await extraction.read_brochure(FakeAI([first, second]), None, brochure, 40, cropper=cropper)
    found = {o["name"]: o for o in offers}
    salmon = found["Сьомга филе"]
    check("page from the image it is on", (salmon["page"], salmon["page_image"]), (3, "https://x/3.jpg"))
    check("its picture is cut from that page", (cut[0][0], cut[0][1]), (b"https://x/3.jpg", (0.1, 0.1, 0.5, 0.4)))
    check("and shown", salmon["image"].startswith("/mealie_planner/pictures/lidl_"), True)
    check("the box is not kept", "box" in salmon, False)
    check("no box: the whole page is shown", found["Картофи"]["image"], "https://x/1.jpg")
    check("second request: pages count on", (found["Боб"]["page"], found["Боб"]["page_image"]), (6, "https://x/6.jpg"))
    check("a box in percent is cut too", cut[1][1], (0.05, 0.05, 0.45, 0.3))

    # Without a cropper (or Pillow), the page is the picture.
    offers, _ = await extraction.read_brochure(FakeAI([first, second]), None, brochure, 40)
    check("no cropper: the page", {o["name"]: o["image"] for o in offers}["Сьомга филе"], "https://x/3.jpg")


asyncio.run(main())

# Offers read before this get their page as a picture.
book = OfferBook({
    "offers": {"a": {"id": "a", "source_id": "lidl:brochure:w", "page": 2, "image": None},
               "b": {"id": "b", "source_id": "lidl:web", "page": None, "image": None},
               "c": {"id": "c", "source_id": "lidl:brochure:w", "page": 99, "image": None}},
    "sources": {"lidl:brochure:w": {"kind": "brochure", "brochure": brochure}},
})
book.fill_page_images()
check("an old brochure offer shows its page", book.offers["a"]["image"], "https://x/2.jpg")
check("a web offer is left alone", book.offers["b"]["image"], None)
check("a page that is not there gives nothing", book.offers["c"]["image"], None)

done()
