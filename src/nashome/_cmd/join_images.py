#!/usr/bin/env python
import argparse
from pathlib import Path
import numpy as np
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from PIL import Image
import io

from pyreg.iohandling.ImageObject import ImageObject

SUCCESS = 0
ERROR = 1

def main() -> int:
    # argument parsing
    parser = argparse.ArgumentParser(description="Join two images vertically, crop top and bottom borders", formatter_class=argparse.RawTextHelpFormatter)
    # Accept raw strings so we can handle both local paths and URLs
    parser.add_argument('image1', type=str, help="Path or URL to the first image")
    parser.add_argument('image2', type=str, help="Path or URL to the second image")
    parser.add_argument('-i', '--image3', type=str, help="Optional path or URL to the third image")
    parser.add_argument('-r', '--height-factor', type=float, default=0.8, help='Specify the new height factor for one of the images (default: 0.8)')
    parser.add_argument('-s', '--separator-factor', type=float, default=0.05, help='Specify the separator factor for one of the images (default: 0.05)')
    args = parser.parse_args()

    return join_images(args.image1, args.image2, args.image3, args.height_factor, args.separator_factor)

def _is_url(s: str) -> bool:
    try:
        p = urlparse(s)
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False


def _build_session() -> requests.Session:
    # Lightweight session similar to other modules
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; nashome-join-images/1.0)",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    })
    return session


def _find_image_in_page(page_url: str, session: requests.Session) -> str | None:
    """Given a page URL, return the best candidate image absolute URL or None."""
    try:
        r = session.get(page_url, timeout=20)
    except Exception:
        return None
    soup = BeautifulSoup(r.content, "html.parser")

    # 1) Common meta tags
    meta_props = [
        ('property', 'og:image'),
        ('name', 'twitter:image'),
        ('name', 'image'),
    ]
    for attr, val in meta_props:
        tag = soup.find('meta', attrs={attr: val})
        if tag and tag.get('content'):
            return urljoin(page_url, tag.get('content'))

    # 2) link rel=image_src
    link = soup.find('link', rel='image_src')
    if link and link.get('href'):
        return urljoin(page_url, link.get('href'))

    # 3) img with largest size heuristic: prefer images with width/height in attributes or srcset
    candidates = []
    for img in soup.find_all('img'):
        src = img.get('src') or img.get('data-src')
        if not src:
            continue
        src = urljoin(page_url, src)
        # try srcset first (choose first entry)
        srcset = img.get('srcset')
        if srcset:
            parts = [p.strip() for p in srcset.split(',') if p.strip()]
            # take the last (usually largest) candidate
            last = parts[-1]
            url_part = last.split()[0]
            candidates.append(urljoin(page_url, url_part))
        else:
            candidates.append(src)

    # return the first candidate if any
    return candidates[0] if candidates else None


def _fetch_image_as_numpy(image_ref: str, session: requests.Session) -> tuple[np.ndarray, str]:
    """Return (ndarray, suffix) for a local path or URL (page or direct image)."""
    # Local file
    if not _is_url(image_ref):
        p = Path(image_ref)
        if not p.is_file():
            raise FileNotFoundError(image_ref)
        img_obj = ImageObject(p)
        return img_obj, p.suffix

    # If it's a URL pointing directly to an image (by extension), download it
    parsed = urlparse(image_ref)
    suffix = Path(parsed.path).suffix or '.jpg'

    # Try to GET the URL and examine content-type
    r = session.get(image_ref, timeout=20)
    content_type = r.headers.get('content-type', '')
    if 'text/html' in content_type:
        # Search page for an image
        img_url = _find_image_in_page(image_ref, session)
        if not img_url:
            raise ValueError(f"No image found at webpage: {image_ref}")
        r = session.get(img_url, timeout=20)
        suffix = Path(urlparse(img_url).path).suffix or suffix

    if r.status_code != 200:
        raise ValueError(f"Failed to download image {image_ref}: {r.status_code}")

    # Load into PIL and convert to numpy array
    pil = Image.open(io.BytesIO(r.content)).convert('RGB')
    arr = np.array(pil)
    imgobj = ImageObject(arr)
    return imgobj, suffix


def join_images(image1:str, image2:str, image3:str, height_factor:float, separator_factor:float) -> int:
    image_refs = [image1, image2]
    if image3:
        image_refs.append(image3)

    session = _build_session()
    cropped_images:list[ImageObject] = []
    suffix = '.jpg'
    output_parent = Path.cwd()
    for idx, image_ref in enumerate(image_refs):
        try:
            img_obj, sfx = _fetch_image_as_numpy(image_ref, session)
        except FileNotFoundError:
            print(f"Error: {image_ref} not found")
            return ERROR
        except Exception as e:
            print(f"Error fetching {image_ref}: {e}")
            return ERROR

        # determine output parent from first local input if available
        if idx == 0 and not _is_url(image_ref):
            output_parent = Path(image_ref).parent
            suffix = sfx

        # crop as before
        img_obj.crop(0,int(img_obj.shape[0]*(1-height_factor)*0.5), img_obj.shape[1], int(img_obj.shape[0]*height_factor))
        cropped_images.append(img_obj)

    # now compute output shape and join
    new_shape = np.array(cropped_images[0].shape)
    new_height = sum([img.shape[0] for img in cropped_images])
    separator_height = int(new_height*separator_factor)
    new_height += separator_height
    new_width = max([img.shape[1] for img in cropped_images])
    new_shape[:2] = (new_height, new_width)

    joined_image = np.zeros(shape=tuple(new_shape), dtype=cropped_images[0].dtype)
    current_y = 0
    for img in cropped_images:
        joined_image[current_y:current_y + img.shape[0], :img.shape[1]] = img.data[:]
        current_y += img.shape[0] + separator_height//(len(cropped_images)-1 if len(cropped_images)>1 else 1)

    outname = output_parent/("joined"+suffix)
    ImageObject(joined_image).write(outname)
    print(f"Wrote joined image to {outname}")
    return SUCCESS

if __name__ == "__main__":
    main()