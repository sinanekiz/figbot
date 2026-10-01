# Third-party notices for the detector experiment

The test detector is trained from a YOLO11n checkpoint and therefore remains
subject to the applicable Ultralytics license terms (AGPL-3.0 unless a separate
Ultralytics enterprise license applies). Review licensing before distributing or
commercializing an APK that contains the model.

Bootstrap images/annotations are derived from:

- Dry Fruit Image Dataset, Choudhary, Kale, Rajput, Meshram and Meshram
  (Mendeley Data, 2023), DOI `10.17632/yfhgn8py5f.1`, CC BY 4.0. The APK model
  uses the dried-fig images; approximate detection boxes were generated locally.
- LVIS v1 (`fig_(fruit)` category): https://www.lvisdataset.org/
- Fruits-And-Vegetables-Detection-Dataset (MIT repository, LVIS-derived):
  https://github.com/henningheyen/Fruits-And-Vegetables-Detection-Dataset

The field-adapted checkpoint also used reviewed dried-fig teacher examples derived
from these Wikimedia Commons files:

- `2014-01-04-Figen (11748534465).jpg`, Ole Palnatoke Andersen, CC BY-SA 2.0:
  https://commons.wikimedia.org/wiki/File:2014-01-04-Figen_(11748534465).jpg
- `Anjir qoqi.jpg`, Oybarchin0302, CC0:
  https://commons.wikimedia.org/wiki/File:Anjir_qoqi.jpg
- `Dried figs (1).jpg`, Francois Nguyen, CC BY 2.0:
  https://commons.wikimedia.org/wiki/File:Dried_figs_(1).jpg
- `Dried figs (2).jpg`, Fumikas Sagisavas, CC0:
  https://commons.wikimedia.org/wiki/File:Dried_figs_(2).jpg
- `Fichi essiccati - fichi calijati in Calabria.jpg`, Marcuscalabresus,
  CC BY-SA 4.0:
  https://commons.wikimedia.org/wiki/File:Fichi_essiccati_-_fichi_calijati_in_Calabria.jpg

LVIS-linked images can have source-specific licenses. This repository does not
redistribute the training images. The APK contains only the resulting experimental
weights. Source-image and trained-weight licensing still require review before
external distribution.

The Android app uses ONNX Runtime Mobile and Google ARCore under their respective
upstream terms.
