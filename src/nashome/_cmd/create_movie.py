import cv2
import os
import argparse

def parse_args():
    # argument parsing
    parser = argparse.ArgumentParser(description="Create movie using images.", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('indir', help="Path to the input images.")
    parser.add_argument('-o', "--outfile", help="Path to the output video file. (default: <indir>/video.avi)")
    parser.add_argument('-f', '--fps', type=int, default=25, help='Set the rate of frames per second (default: 25)')
    args = parser.parse_args()

    create_movie(args.indir, args.outfile, args.fps)

def create_movie(indir:str, outpath:str, fps:int):
    if not outpath:
        outpath = os.path.join(indir, "video.avi")

    images = sorted([img for img in os.listdir(indir) if img.lower().endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"))])
    frame = cv2.imread(os.path.join(indir, images[0]))
    height, width, layers = frame.shape

    video = cv2.VideoWriter(outpath, 0, fps, (width,height))

    for image in images:
        video.write(cv2.imread(os.path.join(indir, image)))

    cv2.destroyAllWindows()
    video.release()


if __name__ == "__main__":
    parse_args()

