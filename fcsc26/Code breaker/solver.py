#!/usr/bin/env python3

import os
import json
import numpy as np
from galois import GF
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

def rang_carré(Fq, C):
	G = Fq(C)
	k, n = G.shape

	rows=[]
	for i in range(k):
		for j in range(i,k):
			rows.append(G[i]*G[j])

	M = Fq(np.vstack(rows))
	return M.row_space().shape[0]
	
if __name__=="__main__":
	with open("output.txt", "r") as f:
		raw=json.load(f)

	d = {}
	for k,v in raw.items():
		if k.isdigit():
			d[int(k)]=v
		elif k=="params":
			d[k]=tuple(v)
		else:
			d[k] =v
	key=[]
	Fq=GF(d["params"][0])
	for i in range(256):
		C=d[i]
		C2 = np.array(C)
		C3 = C2.reshape((d["params"][1],d["params"][2]))
		z=rang_carré(Fq,C3)
		if z==39:
			key.append(0)
		else:
			key.append(1)
	iv=bytes.fromhex(d["enc"]["iv"])
	c=bytes.fromhex(d["enc"]["c"])
	key=sum(b<<i for i,b in enumerate(key)).to_bytes(32)
	E=AES.new(key,AES.MODE_CBC,iv)
	flag=E.decrypt(c).decode()
	res=""
	for x in flag:
		if x != '\n':
			res+=x
	print(res)