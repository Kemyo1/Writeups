import sys
import os
from PIL import Image

xmax=296
ymax=128

din="!"
clk='"'
cs="#"
dc="$"

write=0x24

def parse_vcd(path):
    signaux={din:0,clk:0,cs:0,dc:0}
    bytes=[]
    bit_count=0
    current_byte=0

    with open(path,"r") as f:
        for line in f:
            line=line.strip()
            if not line:
                continue

            if line[0]=="#":
                continue

            if len(line)==2 and line[1] in signaux:
                val=int(line[0])
                sig=line[1]

                old_clk=signaux[clk]
                signaux[sig]=val
                new_clk=signaux[clk]

                if sig==clk and old_clk==0 and new_clk==1 and signaux[cs]==0:
                    current_byte=(current_byte<<1)|signaux[din]
                    bit_count+=1

                    if bit_count==8:
                        bytes.append((signaux[dc],current_byte&0xFF))
                        bit_count=0
                        current_byte=0
    return bytes

def extract_commands(bytes):
    commands=[]
    current_cmd=None

    for dc,byte in bytes:
        if dc==0:
            if current_cmd is not None:
                commands.append(current_cmd)
            current_cmd={"cmd":byte,"data":[]}
        else:
            if current_cmd is not None:
                current_cmd["data"].append(byte)

    if current_cmd is not None:
        commands.append(current_cmd)
    return commands

def create_image(fb):
    img=Image.new("1",(ymax,xmax),1)
    pixels=img.load()

    bytes_per_row=ymax//8

    for row in range(xmax):
        for col_byte in range(bytes_per_row):
            byte=fb[row*bytes_per_row+col_byte]
            for bit in range(8):
                x=col_byte*8+bit
                if x<ymax:
                    pixels[x,row]=(byte>>(7-bit))&1
    return img

bytes=parse_vcd("tortoise-say.vcd")
commands=extract_commands(bytes)
compteur=0
for cmd in commands:
    if cmd["cmd"]==write:
        img=create_image(cmd["data"])
        filename=os.path.join(".",f"{compteur}.png")
        img.save(filename)
        compteur+=1
