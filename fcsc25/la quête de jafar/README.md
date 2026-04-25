Ce challenge vous propose d'analyser un cryptosystème de type SPN avec 20 rounds qui précédent et suivent une multiplication avec la clef. 

Vous pouvez demander 3 requêtes à un oracle de chiffrement (ou déchiffrement) et ensuite forger un couple clair/chiffré original.


Le challenge consiste à analyser la Sbox et la Permutation pour trouver une différentielle intéressante, puis l’utiliser pour implémenter une attaque ‘Boomerang’.


En procédant à une analyse différentielle de la Sbox S, on remarque lors de l'étude de sa DDT (differential distribution table) que l'Uniformité Différentielle UD de S est 256.
```
#Une fonction python pour la ddt; parcourir ensuite la table à partir de la ligne 2
#pour voir où l'uniformité différentielle (=le max de la table hormis celle en 0) est atteinte et en quelle sortie
def ddt(sbox):
 n = len(sbox)
 ddt = [[0] * n for _ in range(n)]
 for a in range(n):
 for x in range(n):
 y = x ^ a
 dout = sbox[x] ^ sbox[y]
 ddt[a][dout] += 1
 return ddt
 ```
Or S s'applique sur des octets, donc des entrées ayant 256 valeurs différentes possibles. 
De plus, pas moins de 3 valeurs non triviales atteignent l'UD : 0x18,0x4a,0x52. Cela signifie que :

-pour n'importe quelle paire (x, x+Δ)

-si Δ = 0x18,0x4a ou 0x52 (ou 0x00)


alors S agira comme une fonction linéaire avec probabilité 256/256=1 : S(x+Δ)=S(x)+S(Δ). 

Il s'agit d'une grande vulnérabilité qui va nous permettre de forger un chiffré.

Avant de commencer à opérer sur le chiffrement, il peut-être utile d'expliciter le raisonnement derrière nos manipulations :

L'étape suivante est d'utiliser ces différentielles au niveau de l'octet pour construire des différentielles au niveau de la la taille des entrées du chiffrement, soit des 16-bytes.

Pour une différentielle d'entrée, plusieurs différentielles de sorties sont possibles. 
Leurs probabilités respectives (dont la somme vaut 1) sont calculées en multipliant les probabilités de chaque Sbox activée durant chaque round du chiffrement.

On veut vérifier qu'il existe une différentielle d'entrée pour laquelle il y a une seule différentielle de sortie, avec donc de probabilité égale à 1.

En effet ce n'est pas parce qu'il y a des différentielles au niveau de l'octet avec proba 1 qu'il y aura forcément des différentielles de proba 1 au niveau du 16-byte, car à chaque round l'état passe par une permutation P.

Comme la sortie de P au round K est donnée en entrée à S du round K+1, on souhaite donc avoir une différentielle composée d'éléments de 
```
Z={0x00,0x18,0x4a,0x5b}
```

dont le passage par S puis P donne une autre différentielle de ce type, et ce pour les 20 rounds qui précédent la multiplication.
Comme il n'y a que 4 valeurs possibles pour chaque byte, on a 4^16 = 2^32 possibilités.

C'est brute-forçable par un algorithme, mais nous allons le faire à la main pour se familiariser avec ce qu'on peut faire en cryptanalyse différentielle.

Nous allons donc étudier une table qui regroupe les différentielles de poids 1.

```
#Code pour générer la table :
k = os.urandom(16)
cipher = Jafar(k)
with open("ref.txt", "w") as f:
  base = bytes([0] * 16)
  base_ct = cipher.Encrypt(base)
  f.write("pos val diff\n")
  f.write("        00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15\n")
  for pos in range(16):
    for val in [0x18, 0x4a, 0x52]:
        modified = bytearray(16)
        modified[pos] = val
        ct = cipher.Encrypt(bytes(modified))
        diff = bytes(a ^ b for a, b in zip(base_ct, ct))
        # build a list of hex‐pairs, blank out '00'
        diff_str = ' '.join(seg if seg != '00' else ' ' for seg in (diff.hex()[i:i+2] for i in range(0, len(diff.hex()), 2)))
        f.write(f"{pos:02} {val:02x} {diff_str}\n")
````

```
pos val diff
      00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15
00 18       04                            40         
00 4a       04                            0a         
00 52                                     4a         
01 18                            20    10            
01 4a       48                   20                  
01 52       48                         10            
02 18                                  80    02      
02 4a                08             10       02      
02 52                08             10 80            
03 18                         42                     
03 4a             10    80    40                     
03 52             10    80    02                     
04 18                                  20          08
04 4a             02                04             08
04 52             02                04 20            
05 18                      c0                        
05 4a    10                42                        
05 52    10                82                        
06 18                                           20 20
06 4a       80                            80    20   
06 52       80                            80       20
07 18                         10          10         
07 4a       02                         08 10         
07 52       02                10       08            
08 18                                        41      
08 4a                40             08       01      
08 52                40             08       40      
09 18                   10                         80
09 4a                            12                80
09 52                   10       12                  
10 18          10          10                        
10 4a                      10 01    02               
10 52          10             01    02               
11 18                02                      08      
11 4a       10    01 02                              
11 52       10    01                         08      
12 18             80                               01
12 4a             80                20          02   
12 52                               20          02 01
13 18          08       08                           
13 4a    42    08                                    
13 52    42             08                           
14 18          40                            10      
14 4a          44 04                                 
14 52          04 04                         10      
15 18    80          80                              
15 4a    80    20                                  04
15 52          20    80                            04
```

!!! Conseil ! Copiez la table originale dans un nouveau fichier en éditeur de texte pour ne pas avoir à remonter ce readme à chaque fois !!! 


Comment lire cette table?

(pos,val,diff) décrit une différentielle d’entrée donnée à la Sbox S, et la différentielle obtenue en sortie de la permutation P.

Ainsi la ligne (01,18,00 00 00 00 00 00 00 00 00 20 00 10 00 00 00 00) signifie que

P(S(00 18 00 00 00 00 00 00 00 00 00 00 00 00 00 00))=00 00 00 00 00 00 00 00 00 20 00 10 00 00 00 00

Nous cherchons une différentielle X traçable le long des 20 premiers rounds avec probabilité 1.

Ceci est possible si X est la somme de certaines lignes de cette table, tant qu’aucune ligne n’ ”occupe” la position
d’une autre.

Comme la sortie de P au round K est fournie en entrée à la Sbox du round K+1, nous voulons donc que P(S(X)) soit composée
Uniquement de bytes faisant partie de Z={00,18,4a,52}. On aimerait donc que P(S(X))=X’ tel que X’ respecte les mêmes
Conditions, de même que X’’=P(S(X’)) etc.

Comme les permutations sont toujours linéaires, on peut construire K à partir des lignes du tableau, car c'est justement pour ces
lignes (et uniquement pour ces lignes) que S agit de façon linéaire.

Si K = L1+L2, P(K)=P(L1)+P(L2)=diff(L1)+diff(L2) (Attention toutes les additions sont des Xor)

En supposant qu’il existe une différentielle K respectant ces conditions, comment savoir quelles sont les lignes qui
Permettent de la construire? Pour cela analysons les bytes non triviaux de Z :

18
4a
52

On observe certaines choses sur ces bytes:

-La colonne C1 vaut 1,4 ou 5. L’octet correspondant n’a donc au plus que 2 bits positionnés : le bit 0 (pour 1 et 5), et celui
en position 2 (pour 4 et 5).

Que pouvons nous conclure de ceci ?
```
=> Si une ligne à un byte dont le half byte de poids fort possitionne des bits pour 2 et 8
alors il faut ajouter une autre ligne (à position différente) qui partage cette valeur au même endroit pour l’annuler
(rappel l’opération c’est le Xor)
```
-De même, C2 vaut 8,a ou 2. Donc au plus, les bit 3 (pour 8 et a) et 1 (pour 2 et a) sont positionnés.
```
=>La même conclusion peut être tirée pour les lignes ayant un byte avec un half byte de poids faible
Tel que les bits de 1 et 4 sont positionnés
```
Nous allons donc pouvoir commencer à éliminer des lignes en analysant leur bytes et les eventuelles lignes qui pourraient se sommer à ces dernières.

0) Aucune ligne n’a d’octet valant f ou e ou d.

1) Une seule ligne a un half byte c : 05 18 . c’est le 7éme byte “c0”. Comme c n’est pas dans C1 et qu’il n’y a pas d’autres lignes
Dont le 7eme byte vaut “cX”, on peut enlever cette ligne

2) 00 4a possède un byte ‘0a’. a est dans C2, mais 0a n’est pas dans Z. il faut donc soit annuler ce 0a soit ajouter une ligne
ayant un byte permettant d’obtenir un élément de Z – ici seul 4a est possible .
Or 4a+0a=40 et Seul 00 18 possède ‘40’ à la même colonne. Comme ces lignes partagent la même pos 00, on peut enlever cette ligne.

3) 00 18 a un byte ‘40’. qui n'est pas dans Z, or toutes les autres lignes ont ‘00’ à cette position, sauf 00 52. Comme on ne peut pas ajouter deux lignes ayant la même pos, on peut enlever cette ligne.

4) Pas de ligne avec un half byte à ‘9’, mais en observant les lignes ayant ‘80’, beaucoup vont s’éliminer : 

-09 18 et 09 4a sont les seules lignes à avoir 80 en 16eme byte. Or Il faut annuler ceci car 8 n’est pas dans C1.
Mais ces lignes ne peuvent pas s’annuler entre elles car elles sont à la même position.
(Comme max(c1)=5<8 on ne peut pas compléter le byte en un byte non trivial de Z : seule l’annulation est possible)

  -06 4a et 06 52 Pareil, mais au 13éme byte au lieu de 16

  -02 18 et 02 52 Pareil (12 éme)

  -03 4a et 03 52 Pareil (7)

  -15 18 et 15 52 Pareil (6)

  -15 4a a ‘80’ en 2eme byte. Aucune autre ligne a un 2 eme byte ‘8X’ donc on ne peut l’annuler.

  -12 18 et 12 4a Pareil (5)

  -06 4a et 06 52 Pareil (3)

5) On réitère avec ‘01’ : 1 n’est pas dans C2, et, plus fort, le bit en question n’est jamais activé dans C2.
Donc on ne peut pas ‘compléter’ les lignes ayant un ‘01’, il faut forcément annuler ce byte.

  -10 4a,10 52 et 11 4a,11 52 et 08 18,08 4a s’éliminent pour les mêmes raisons qu’avant

  -12 52 est le seul à avoir ‘01’ en byte 16.

6) On réitère encore avec ‘20’ : 2 n’est pas dans C1, et le bit en question n’est jamais activé dans C1 donc on doit l’annuler.

  -01 18,01 4a,04 18,04 52,06 18 sont éliminées (cette dernière car elle est la seule ligne a àvoir 20 en byte 16)

7) En cherchant ‘04’, on élimine 14 4a,14 52 et 04 4a (même raisonnement que les points précédents)

8) Nous avons étudié les 4 bytes qui ne pouvaient que s’annuler et non être complétés.
Regardons les bytes qui peuvent aussi se compléter désormais : il y a peut-être encore des ‘éliminations faciles’
Les bytes pouvant se compléter en éléments de Z (différents de 00) sont donc :
’10’ avec ‘08’ OU avec ‘40’ ET ‘02’.
’40’ avec ‘0a’ OU avec ‘10’ ET ‘02' OU avec ‘08’ ET ‘02’.
’50’ avec ‘02’.

-07 18 et 07 4a ont ‘10’ au 13eme byte, et les autres lignes ont 00 à cet endroit, sauf 00 52 qui a ‘4a’.
Les lignes 07 ne peuvent s’entre-annuler et ‘4a’+’10’=’5a’ qui n’est pas dans Z : on élimine ces deux lignes.
Les autres lignes ayant ‘10’ ont des candidats pour se sommer en un élément de Z : on ne les étudie pas en profondeur.
(on veut juste éliminer le plus de lignes avant de vraiment se plonger dans l’analyse)

-Toutes les lignes ayant ‘08’ ont des candidats pour une somme qui pourrait fonctionner à première vue

-14 18 est la seule ligne avec ‘40’ qui n’a aucune ligne avec qui s’ajouter ou se compléter en un membre de Z

-Aucune ligne a ‘0a’ ou ‘50’, et toutes les lignes ayant ‘02’ semblent se compléter avec d’autres.

Une fois les dernières éliminations faites on peut commencer à vraiment chercher un bon candidat pour notre différentielle.
Notre table devient donc :

```
pos val diff
      00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15
00 52                                     4a         
01 52       48                         10            
02 4a                08             10       02      
03 18                         42                     
05 4a    10                42                        
05 52    10                82                        
07 52       02                10       08            
08 52                40             08       40      
09 52                   10       12                  
10 18          10          10                        
11 18                02                      08      
13 18          08       08                           
13 4a    42    08                                    
13 52    42             08                           
```

00 52 est-t-elle une ligne qui permette de construire la différentielle qu’on cherche?

P(S(00 52) =00 00 00 00 00 00 00 00 00 00 00 00 4a 00 00 00
Et 4a est bien dans Z! Donc cette ligne est traçable jusqu’à la sortie de la Sbox du round 2.

Mais elle n’est pas traçable après l’application de la permutation du round 2 : en effet notre table n’a plus de ligne 12 4a
Car elle a été éliminée avant. Donc 00 52 peut être éliminée.

Au tour de 01 52 : P(S(01 52))=00 00 48 00 00 00 00 00 00 00 00 10 00 00 00 00
Toutes les lignes ont des 00 aux colonnes 3 et 11, sauf 07 52.

Or P(S(07 52))=00 00 02 00 00 00 00 00 10 00 00 08 00 00 00 00
Ce qui donne 00 00 4a 00 00 00 00 00 10 00 00 18 00 00 00 00
Il faut compléter le 10 en 18 . Or à cet colonne, seule 03 18 à un byte non nul, qui vaut 08. Parfait!

Donc K=(01 52 + 03 18 + 07 52)= 00 52 00 18 00 00 00 52 00 00 00 00 00 00 00 00 fonctionne pour 1 round
Et P(K)=00 00 4a 00 00 00 00 00 52 00 00 18 00 00 00 00 00 doit être vérifiée ! 

Or les lignes 02 4a,08 52 et 11 18 sont encore présentes dans la table !

K’=P(S(K)) n’est donc pas éliminée. Mais que vaut P(K’) ?

Regardons si la somme de ces trois lignes (et seulement ces trois lignes!) donne quelque chose de valide !

  00 00 00 00 00 08 00 00 00 00 10 00 00 02 00 00 +
 
00 00 00 00 00 40 00 00 00 00 08 00 00 40 00 00 + 

00 00 00 00 00 02 00 00 00 00 00 00 00 08 00 00 nous donne 

00 00 00 00 00 4a 00 00 00 00 18 00 00 4a 00 00

C’est aussi une ligne composée d’éléments de Z ! Donc K’ est traçable sur un round également.

Vérifions à nouveau si K’’=P(S(K')) fonctionne :

Les lignes 05 4a,10 18 et 13 4a sont encore dans la table ! Donc K’’ n’est pas éliminée.
Que vaut P(K”)?

  00 10 00 00 00 00 00 42 00 00 00 00 00 00 00 00 +
 
00 00 00 10 00 00 00 10 00 00 00 00 00 00 00 00 + 

00 42 00 08 00 00 00 00 00 00 00 00 00 00 00 00 nous donne

00 52 00 18 00 00 00 52 00 00 00 00 00 00 00 00=K !

Nous avons donc trouvé trois différentielles de probabilité 1 qui cyclent entre elles après chaque passage de round :

Si la différentielle d'entrée est K1= 00 52 00 18 00 00 00 52 00 00 00 00 00 00 00 00

après le round 1 elle devient K2=00 00 4a 00 00 00 00 00 52 00 00 18 00 00 00 00 00

après le round 2 elle devient K3=00 00 00 00 00 4a 00 00 00 00 18 00 00 4a 00 00

après le round 3 elle redevient K1

Comme il y a 20 rounds avant la multiplication et 20 est congru à 2 mod 3, on en conclut qu'après le round 20 la différentielle vaut K3.

```
Utilisons donc nos 2 première requetes sur P0=0x00 * 16, et P1=P0+K1.
```
Notons Si l'état donné en entrée à la multiplication du Middle et S'i l'état à sa sortie. Après le round 20 il y a la multiplication donc S1=S0+K3 avec ce qu'on a vu.

La multiplication est linéaire mais elle se fait avec la clef donc on ne connait pas sa sortie.

On peut donc juste dire que :
```
S'1=M(S0+k3)=M(S0)+M(K3)=S'0+M(K3) par définition de S'i
```
Il reste 1 requête et on devine qu'il faut qu'elle soit une demande de déchiffrement pour "pénétrer l'autre coté"

Soit C0 et C1 les chiffrés de P0 et P1. 
```
Choississons de déchiffrer C2=C1+K1.
```
Le déchiffrement se faisant avec des opérations inverses du chiffrement, on obtient qu'après 1 round de déchiffrement la différentielle vaut K3.

Elle vaut K2 après le 2eme round et K1 après le troisième etc... 20 est congru à 2 mod 3 donc S'2=S'1+K2

Nous n'avons plus de requêtes. 

Il est temps de forger un couple original. Comment? Regardons les relations que nous avons.
```
S'2=S'1+K2 or S'1=S'0+M(K3)
=> S'2=K2+S'0+M(K3)
```
On comprend donc comment procéder : on veut chiffrer quelque chose avec une différentielle telle que :

-on connaisse son état après les 20 premiers rounds ->On doit construire un état à partir de P2=Decrypt(C2) car c'est le seul qu'on connait et qu'on a pas encore utilisé


-après les 20 premiers rounds la différentielle vaut K3 ->La différentielle d'entrée de chiffrement vaut K1


Donc le clair du couple forgé est P3=P2+K1, qui aura pour états :
```
S3=S2+K3
=> S'3=S'2+M(K3)
or S'2=K2+S'0+M(K3)
=> S'3=S'0+K2
```

Comme on l'a vu, Si la différentielle vaut K1 en entrée de Dé-chiffrement, alors elle vaut K2 en sortie de 20 rounds de déchiffrement.

Le chiffré de P0 est connu :On conclut que P3 a pour chiffré C3=C0+K1

Il ne reste qu'à rentrer les réponses du serveur dans un script pour obtenir les données plus rapidement et on obtient le flag.

Merci à Graniter pour ce challenge et à l'équipe du FCSC pour l'édition de cette année !