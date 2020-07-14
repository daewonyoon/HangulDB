import sys
import os

import numpy as np
from PIL import Image


max_wh = [0, 0]


N_CHOSEONG = 19
N_JUNGSEONG = 21
N_JONGSEONG = 28


class HguImage:
    def __init__(self, code, w, h, t, r, d):
        self.code = code
        self.ch = code.decode("cp949")
        hangul_ord = ord(self.ch) - ord("가")
        self.labels = np.array(
            (
                hangul_ord // (N_JUNGSEONG * N_JONGSEONG),
                (hangul_ord % (N_JUNGSEONG * N_JONGSEONG)) // N_JONGSEONG,
                hangul_ord % N_JONGSEONG,
            )
        )
        self.label = self.labels[0]
        self.width = w
        self.height = h
        self.type = t
        self.reserved = r
        self.data = np.ones((h, w), dtype=np.uint8) * 0xFF
        self.databytes = d

        for y in range(h):
            for x in range(w):
                v = int(d[w * y + x])
                if v != 0xFF:
                    self.data[y][x] = v

    def norm_size(self):
        """
            change size to (100, 100)
            align center
        """
        """
        w, h = self.width, self.height
        new_data = [ [ 0xFF for x in range(100)] for y in range(100) ]
        ox, oy = (100-w)//2, (100-h)//2
        for y in range(h):
            for x in range(w):
                if self.data[y][x] != 0xFF:
                    new_data[oy+y][ox+x] = self.data[y][x]
        self.data = new_data                    
        """
        w, h = self.width, self.height
        ox, oy = (100 - w) // 2, (100 - h) // 2
        new_data = np.ones((100, 100), dtype=np.uint8) * 0xFF
        new_data[oy : oy + h, ox : ox + w] = self.data
        self.data = new_data
        new_databytes = b""
        for y in range(100):
            line = bytes(self.data[y])
            new_databytes += line
        self.databytes = new_databytes
        self.width, self.height = 100, 100
        return


def core_load_data(name, label_opt="cho", dont_use_cache=False, n_fold=1):
    assert name in {"pe92", "seri", "handb"}, "name `%s` incorrect!" % (name,)
    assert label_opt in {"cho", "jung", "jong", 0, 1, 2}, "label_opt `%s` incorrect!" % (label_opt,)

    if label_opt in (0, 1, 2):
        label_idx = label_opt
    else:
        label_idx = {"cho": 0, "jung": 1, "jong": 2}[label_opt]

    cache_name = "%s.npz" % (name)

    cache_path = get_cache_path(cache_name)
    if os.path.exists(cache_path) and not dont_use_cache:
        with np.load(cache_path) as f:
            X_train, y_train, X_test, y_test = f["X_train"], f["y_train"], f["X_test"], f["y_test"]
            return nfold_filter(
                (X_train, y_train[:, label_idx]), (X_test, y_test[:, label_idx]), n_fold
            )
    else:
        (X_train, y_train), (X_test, y_test) = load_data(name)
        if os.path.exists(cache_path):
            os.remove(cache_path)
        np.savez_compressed(
            cache_path, X_train=X_train, y_train=y_train, X_test=X_test, y_test=y_test
        )
    return nfold_filter((X_train, y_train[:, label_idx]), (X_test, y_test[:, label_idx]), n_fold)


def pe92_load_data(label_opt="cho", dont_use_cache=False, n_fold=1):
    print("pe92_load_data")

    return core_load_data(
        name="pe92", label_opt=label_opt, dont_use_cache=dont_use_cache, n_fold=n_fold
    )


def seri_load_data(label_opt="cho", dont_use_cache=False, n_fold=1):
    print("seri_load_data")

    return core_load_data(
        name="seri", label_opt=label_opt, dont_use_cache=dont_use_cache, n_fold=n_fold
    )


def handb_load_data(label_opt="cho", dont_use_cache=False, n_fold=1):
    print("handb_load_data")

    return core_load_data(
        name="handb", label_opt=label_opt, dont_use_cache=dont_use_cache, n_fold=n_fold
    )


def nfold_filter(xy1, xy2, n_fold=1):
    if n_fold == 1:
        return xy1, xy2
    x, y = xy1
    idx_filter = [i for i in range(len(x)) if i % n_fold == 0]
    x = x[idx_filter]
    y = y[idx_filter]
    xy1 = x, y
    x, y = xy2
    idx_filter = [i for i in range(len(x)) if i % n_fold == 0]
    x = x[idx_filter]
    y = y[idx_filter]
    xy2 = x, y
    return xy1, xy2


def get_cache_path(name):
    base_dir = os.path.dirname(__file__)
    if base_dir == "":
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, name)


def get_datafolder_path(name):
    base_dir = os.path.dirname(__file__)
    if base_dir == "":
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, name)


def load_data(dataname):
    assert dataname in ("pe92", "handb", "seri"), "`%s` unknown dataname!" % (dataname,)

    X_train, y_train = read_hgu1_folder(dataname + "_train")
    X_test, y_test = read_hgu1_folder(dataname + "_test")

    return (X_train, y_train), (X_test, y_test)


def read_hgu1_folder(foldername):
    # assert folder existence
    assert os.path.exists(
        foldername
    ), "`%s` folder doesn't exist. You must first extract the provided zip file." % (foldername,)
    xs = []
    ys = []
    folderpath = get_datafolder_path(foldername)
    for r, _dirnames, filenames in os.walk(folderpath):
        for i, filename in enumerate(filenames):
            # if i == 201:
            #    break
            if i % 100 == 0:
                print(i)
            if not filename.endswith(".hgu1"):
                continue
            filepath = os.path.join(r, filename)
            for x, y in read_imgs(filepath):
                xs.append(x)
                ys.append(y)
        break
    assert len(xs) > 100, "no .hgu file is found in `%s`" % (foldername,)
    return np.array(xs), np.array(ys)


def convert_file(filepath, dirpath):
    os.makedirs(dirpath, exist_ok=True)
    with open(filepath, "rb") as f:
        file_header = f.read(8)
        assert file_header[:4] == b"HGU1", "fileheader incorrect!"
        # print("file_header = %s"%(str(file_header)))

        for n, image in enumerate(read_hgu1(f)):
            # if n == 10:
            #    break
            if image == None:
                break
            img_filepath = os.path.join(dirpath, "%s_%03d.png" % (image.ch, n))

            save_to_png(img_filepath, image)

            if max_wh[0] < image.width:
                max_wh[0] = image.width
            if max_wh[1] < image.height:
                max_wh[1] = image.height

            # input("press enter to continue")
        print("max wh = %s" % (max_wh))
    return


def read_imgs(filepath):
    with open(filepath, "rb") as f:
        file_header = f.read(8)
        assert file_header[:4] == b"HGU1", "header incorrect! `%s`" % (filepath,)
        # print("file_header = %s"%(str(file_header)))

        for n, image in enumerate(read_hgu1(f)):
            # if n == 10:
            #    break
            if image == None:
                break
            yield image.data, image.labels

            # input("press enter to continue")
        # print('max wh = %s'%(max_wh))
    return


def save_to_png(img_filepath, image):
    img = Image.frombytes("L", (image.width, image.height), image.databytes)
    img.save(img_filepath)


def read_hgu1(f):
    while True:
        img_hdr = f.read(6)
        if len(img_hdr) == 0:
            break
        code = img_hdr[:2]
        w, h = int(img_hdr[2]), int(img_hdr[3])
        t, r = int(img_hdr[4]), int(img_hdr[5])
        # print("w, h, t, r = %d, %d, %d, %d"%(w, h, t, r))
        data_bytes = f.read(w * h)
        image = HguImage(code, w, h, t, r, data_bytes)
        image.norm_size()
        yield image
    return


if __name__ == "__main__":
    name = "pe92"
    if len(sys.argv) < 2:
        print("%s <dataset name>" % (sys.argv[0]))
        print(" dataset name : `pe92`, `seri`, `handb` ")
        sys.exit(0)

    name = sys.argv[1].strip().lower()

    if name == "pe92":
        _load_data = pe92_load_data
    elif name == "seri":
        _load_data = seri_load_data
    elif name == "handb":
        _load_data = handb_load_data
    else:
        print("%s <dataset name>" % (sys.argv[0]))
        print(" dataset name : `pe92`, `seri`, `handb` ")
        sys.exit(0)

    (X_train, y_train), (X_test, y_test) = _load_data()
    print("dataname   = %s" % name)
    print("X shape    = %s" % (X_train.shape,))
    print("y shape    = %s" % (y_train.shape,))
    print("train size = %s" % len(y_train))
    print("test size  = %s" % len(y_test))

