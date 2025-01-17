#!/usr/bin/env python
import argparse
from pathlib import Path
import numpy as np

from pyreg.iohandling.ImageObject import ImageObject

SUCCESS = 0
ERROR = 1

def main() -> int:
    # argument parsing
    parser = argparse.ArgumentParser(description="Join two images vertically, crop top and bottom borders", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('image1', type=Path, help="Path to the first image")
    parser.add_argument('image2', type=Path, help="Path to the second image")
    parser.add_argument('-i', '--image3', type=Path, help="Optional path to the third image")
    parser.add_argument('-r', '--height-factor', type=float, default=0.8, help='Specify the new height factor for one of the images (default: 0.8)')
    parser.add_argument('-s', '--separator-factor', type=float, default=0.05, help='Specify the separator factor for one of the images (default: 0.05)')
    args = parser.parse_args()

    return join_images(args.image1, args.image2, args.image3, args.height_factor, args.separator_factor)

def join_images(image1:Path, image2:Path, image3:Path, height_factor:float, separator_factor:float) -> int:
    image_paths = [image1, image2]
    if image3:
        image_paths.append(image3)

    cropped_images:list[ImageObject] = []
    for image_path in image_paths:
        if not image_path.is_file():
            print(f"Error: {image_path} not found")
            return ERROR
        
        img = ImageObject(image_path)
        img.crop(0,int(img.shape[0]*(1-height_factor)*0.5), img.shape[1], int(img.shape[0]*height_factor))
        cropped_images.append(img)

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
        current_y += img.shape[0] + separator_height//(len(cropped_images)-1)
    ImageObject(joined_image).write(image1.parent/("joined"+image1.suffix))

if __name__ == "__main__":
    main()