import sys


max_wh = [0, 0]


class HguImage:
    def __init__(self, code, w, h, t, r, d):
        self.code = code
        self.ch = code.decode("cp949")
        self.width = w
        self.height = h
        self.type = t
        self.reserved = r
        self.data = []
        self.databytes = d
        for y in range(h):
            self.data.append([])
            for x in range(w):
                self.data[y].append(int(d[w * y + x]))


def dispaly_main():
    if len(sys.argv) < 2:
        print("Usage: %s <.hgu1 filename>" % (sys.argv[0],))
        return
    display_file(sys.argv[1])
    return


def display_file(filepath):
    with open(filepath, "rb") as f:
        file_header = f.read(8)
        assert file_header[:4] == b"HGU1"
        print("file_header = %s" % (str(file_header)))

        max_wh = [0, 0]

        for n, image in enumerate(read_hgu1(f)):
            if image == None:
                break
            print("image %d" % (n,))

            # write_hgu1(out_file, image)

            display_image(image)
            log_image(image, filepath + "_display.log")
            if max_wh[0] < image.width:
                max_wh[0] = image.width
            if max_wh[1] < image.height:
                max_wh[1] = image.height

            # input("press enter to continue")
        print("max wh = %s" % (max_wh))
    return


def display_image(image):
    print(
        "code = [%x%x], ch = %s, w x h = %d, %d, type = %d, reserved = %d"
        % (
            image.code[0],
            image.code[1],
            image.ch,
            image.width,
            image.height,
            image.type,
            image.reserved,
        )
    )

    for y in range(image.height):
        for x in range(image.width):
            print("%02x" % (image.data[y][x]), end="")
        print("")

    return


def log_image(image, filename):
    with open(filename, "a", encoding="utf-8") as f:
        print(
            "code = [%x%x], ch = %s, w x h = %d, %d, type = %d, reserved = %d"
            % (
                image.code[0],
                image.code[1],
                image.ch,
                image.width,
                image.height,
                image.type,
                image.reserved,
            ),
            file=f,
        )

        for y in range(image.height):
            for x in range(image.width):
                print("%02x" % (image.data[y][x]), end="", file=f)
            print("", file=f)
    return


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
        yield image
    return


if __name__ == "__main__":
    dispaly_main()
