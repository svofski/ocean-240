#!/usr/bin/env python
import sys
import os
from math import *
from operator import itemgetter
from utils import *
from base64 import b64encode

class Stubnik:
    def __init__(self):
        dir,_ = os.path.split(sys.argv[0])
        stubpath = os.path.join(dir, "stub.tpl")
        with open(stubpath, "r") as fi:
            self.text = fi.read()
    
    def gettext(self, label, db, palidx):
        return self.text % (label, palidx, label, label, label, db)
   
class Colornik:
    RED = getNearest233((255,0,0,255))
    MAGENTA = getNearest233((255,0,255,255))
    GREEN = getNearest233((0,255,0,255))
    BLUE = getNearest233((0,0,255,255))
    YELLOW = getNearest233((255,255,0,255))
    CYAN = getNearest233((0,255,255,255))
    WHITE = getNearest233((255,255,255,255))
    BLACK = getNearest233((0,0,0,255))

    ALL = [RED,MAGENTA,GREEN,BLUE,YELLOW,CYAN,WHITE,BLACK]
    NAMES = {RED: "красный", MAGENTA: "малиновый", GREEN: "зеленый", 
            BLUE: "синий", YELLOW: "жёлтый", CYAN: "голубой", WHITE: "белый", 
            BLACK: "черный"}

    LUT0T = (BLACK,RED,GREEN,BLUE)
    LUT1T = (WHITE,RED,GREEN,BLUE)
    LUT2T = (RED,GREEN,CYAN,YELLOW)
    LUT3T = (BLACK,RED,MAGENTA,WHITE)
    LUT4T = (BLACK,RED,YELLOW,BLUE)
    LUT5T = (BLACK,BLUE,GREEN,YELLOW)
    LUT6T = (GREEN,WHITE,YELLOW,BLUE)
    LUT7T = (BLACK,BLACK,BLACK,BLACK)

    LUTS = (LUT0T,LUT1T,LUT2T,LUT3T,LUT4T,LUT5T,LUT6T,LUT7T)

    def __init__(self, pic, origname):
        self.pic = pic
        self.hpixels = len(pic[0])//4
        self.vlines = len(pic)
        self.origname = origname
        self.forced = None
     
    def which(self, mystery):
        m = c233toRGB(mystery)
        dist = [(colordist(c233toRGB(x), m),x) for x in Colornik.NAMES.keys()]
        return sorted(dist)[0][1]

    def match_histogram(self, h):
        keys = set([self.which(entry[0]) for entry in h])
        try:
            names = [Colornik.NAMES[self.which(entry[0])] for entry in h]
            print ("Нашлись такие цвета: %s" % ", ".join(names))
            lut_sets = [set(x) for x in Colornik.LUTS]
            palette = lut_sets.index(keys)
            print ("Угадана палитра №%d" % palette)
        except:
            print ("Не получилось угадать палитру, принимаем 0 (NRGB)")
            palette = 0
        self.palette_index = palette
        return palette

    def histogram(self):
        h = [0]*256

        for line in self.pic:
            for rgba in chunker(line, 4):
                h[getNearest233(rgba)] += 1
        h2 = [(i,x) for i,x in enumerate(h)]
        h3 = sorted(h2, key=itemgetter(1), reverse=True) 

        return h3[:4]

    def force_palette(self, n):
        if n >= 0 and n < 8:
            self.forced = n
            self.palette_index = n
        else:
            raise Exception("Палитра может быть от 0 до 7")

    def identify(self):
        if self.forced == None:
            h = self.histogram()
            self.lut = Colornik.LUTS[self.match_histogram(h)]
        else:
            self.lut = Colornik.LUTS[self.forced]

    # quantize and convert to indexed bytes with values 0,1,2,3
    def quantize(self):
        outpic = []
        for line in pic:
            outline = bytearray(self.hpixels)
            outpic.append(outline)
            for i,rgba in enumerate(chunker(line, 4)):
                dists = [(colordist(c233toRGB(x),rgba[:3]),i) for i,x in 
                        enumerate(self.lut)]
                color = sorted(dists)[0][1]
                outline[i] = color
        return outpic

    # take indexed 1 byte per pixel image and output Okean-240 columns
    def columnify(self, indexed):
        ncolumns = self.hpixels//4   # 8 byte pixels -> (column|column)
        data = bytearray(self.vlines * ncolumns)
        dataidx = 0

        for colidx in range(ncolumns):
            xbase = (colidx & ~1) * 4
            for y in range(len(indexed)):
                ocho = indexed[y][xbase:xbase+8]
                # even columns take bit 1, odd columns bit 0
                if colidx & 1 == 0:
                    octet = sum([(x & 1) << i for i,x in enumerate(ocho)])
                else:
                    octet = sum([((x & 2)>>1) << i for i,x in enumerate(ocho)])
                data[dataidx] = octet
                dataidx += 1
        return ncolumns, self.vlines, data                

    def process(self):
        self.identify()
        indexed = self.quantize()
        return self.columnify(indexed)

    def get_data_label(self):
        return self.origname

    def get_dimensions(self):
        return self.hpixels/4, self.vlines

    def get_palette_index(self): return self.palette_index

class Encodnik:
    BYTES = 0
    BASE64 = 1

    def __init__(self, source, mode=BYTES):
        self.source = source
        self.mode = mode

    def encode(self):
        label = self.source.get_data_label()
        nc,nr,octets = self.source.process()

        result = '%s_nc:\tdb %d\n' % (label,nc)
        result += '%s_nr:\tdb %d\n' % (label,nr)
        if self.mode == Encodnik.BASE64:
            result += '%s:\tdb64 %s\n' % (label, b64encode(octets).decode('latin1'))
        else:
            result += '%s:\tdb ' % (label) + \
                '\n\tdb '.join([','.join(['$%02x'%x for x in chunk]) 
                    for chunk in chunker(octets,16)])
       
        return result

def usagi():
    basename = os.path.basename(sys.argv[0])
    m1 = ["Конвертер картинок PNG для Океана-240\n",
        "Запуск: %s [-base64][-stub][-pal#] input.png [ouput.asm]\n" % basename,
        "\t-base64\tделать db64 для компактности",
        "\t-stub\tгенерировать целый исполняемый файл (нужен stub.tpl)",
        "\t-pal#\tфорсировать выбор палитры № #\n",
        "Цвета картинки на входе должны примерно соответствовать одной из "+
        "палитр Океана-240:"]
    m1 = m1 + ["  " + str(i) + " " + 
            ",".join([Colornik.NAMES[x] for x in y]) 
            for i,y in enumerate(Colornik.LUTS)]
    print("\n".join(m1))

def getparams():
    inputname=None
    asmname=None
    encodage=Encodnik.BYTES
    stub=False
    palette=None

    for i,v in enumerate(sys.argv[1:]):
        if v[0] == '-':
            if v[1:] == 'base64':
                encodage=Encodnik.BASE64
            elif v[1:] == 'stub':
                stub=True
            elif v[1:4] == 'pal':
                try:
                    palette = int(v[4])
                except:
                    print("Форсирование палитры с индексом 3: -pal3")
                    exit(1)
            else:
                print("Нет такой опции: ", v)
                exit(0)
            continue

        if inputname == None:
            inputname = v
        elif asmname == None:
            asmname = v
        else:
            print("Многовато параметров. Не знаю, что с ними делать.")
            exit(1)

    if asmname == None:
        (origname, ext) = os.path.splitext(inputname)
        asmname = origname + ['.inc','.asm'][stub]

    basename = os.path.basename(inputname)
    (shortname, ext) = os.path.splitext(basename)

    return inputname,asmname,shortname,encodage,stub,palette


if len(sys.argv) < 2:
    usagi()
    exit(1)

inputname,asmname,shortname,encodage,stub,palette = getparams()

nc,nr,pic = readPNG(inputname)
if pic == None:
    print("Чего-то не так с картинкой, должен быть цветной PNG")
    exit(0)

print ('Открылась картинка %s %dx%d' % (inputname, nc, nr))

k = Colornik(pic, shortname)
if palette != None:
    k.force_palette(palette)

encodnik = Encodnik(k, encodage)

print("Записываем результат в %s" % asmname)

with open(asmname, "w") as fo:
    if stub:
        fo.write(Stubnik().gettext(shortname, encodnik.encode(), 
            k.get_palette_index()))
    else:
        fo.write(encodnik.encode())


