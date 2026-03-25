import os
import cv2

from preprocess import preprocess_image
from ocr import easyocr_extract, trocr_extract


def main():

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    input_image = os.path.join(
        BASE_DIR,
        "input",
        "note1.jpg"
    )

    print("Preprocessing image...")

    processed = preprocess_image(input_image)

    processed_path = os.path.join(
        BASE_DIR,
        "output",
        "processed.jpg"
    )

    cv2.imwrite(processed_path, processed)

    print("Running EasyOCR...")

    easy_text = easyocr_extract(processed)

    print("\n----- EasyOCR OUTPUT -----\n")
    print(easy_text)


    print("\nRunning TrOCR...")

    trocr_text = trocr_extract(input_image)

    print("\n----- TrOCR OUTPUT -----\n")
    print(trocr_text)


    with open(
        os.path.join(BASE_DIR, "output", "result.txt"),
        "w",
        encoding="utf-8"
    ) as f:

        f.write("=== EasyOCR ===\n")
        f.write(easy_text)

        f.write("\n\n=== TrOCR ===\n")
        f.write(trocr_text)


    print("\nSaved to output/result.txt")


if __name__ == "__main__":
    main()